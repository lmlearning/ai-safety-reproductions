"""Ordinary direct-process resources/output accounting; no scientific imports."""
import ctypes as C
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import time

GiB=1024**3
WHOLE=6845104128
FLOOR=20*GiB
BUCKETS={'science':3489660928,'telemetry':2818572288,'temp_cache':268435456,'metadata':268435456}

class PMC(C.Structure):
    _fields_=[('cb',C.c_uint32),('faults',C.c_uint32)]+[(n,C.c_size_t) for n in
        ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
         'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage']]

class MS(C.Structure):
    _fields_=[('length',C.c_uint32),('load',C.c_uint32)]+[(n,C.c_uint64) for n in
        ['total','available','totalpage','availablepage','totalvirtual','availablevirtual','extended']]

def utc():return dt.datetime.now(dt.timezone.utc).isoformat()

def kernel():
    k=C.WinDLL('kernel32',use_last_error=True);p=C.WinDLL('psapi',use_last_error=True)
    k.GetCurrentProcess.restype=C.c_void_p
    k.GlobalMemoryStatusEx.argtypes=[C.POINTER(MS)];k.GlobalMemoryStatusEx.restype=C.c_int
    k.GetProcessTimes.argtypes=[C.c_void_p]+[C.POINTER(C.c_uint64)]*4;k.GetProcessTimes.restype=C.c_int
    k.GetProcessId.argtypes=[C.c_void_p];k.GetProcessId.restype=C.c_uint32
    k.GetExitCodeProcess.argtypes=[C.c_void_p,C.POINTER(C.c_uint32)];k.GetExitCodeProcess.restype=C.c_int
    k.QueryFullProcessImageNameW.argtypes=[C.c_void_p,C.c_uint32,C.c_wchar_p,C.POINTER(C.c_uint32)];k.QueryFullProcessImageNameW.restype=C.c_int
    p.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.POINTER(PMC),C.c_uint32];p.GetProcessMemoryInfo.restype=C.c_int
    return k,p

def native(k,p,h=None,prior=None):
    h=k.GetCurrentProcess() if h is None else h
    m=PMC();m.cb=C.sizeof(m)
    if not p.GetProcessMemoryInfo(h,C.byref(m),m.cb):raise C.WinError(C.get_last_error())
    ms=MS();ms.length=C.sizeof(ms)
    if not k.GlobalMemoryStatusEx(C.byref(ms)):raise C.WinError(C.get_last_error())
    a,b,c,d=[C.c_uint64()for _ in range(4)]
    if not k.GetProcessTimes(h,C.byref(a),C.byref(b),C.byref(c),C.byref(d)):raise C.WinError(C.get_last_error())
    exitcode=C.c_uint32()
    if not k.GetExitCodeProcess(h,C.byref(exitcode)):raise C.WinError(C.get_last_error())
    pid=int(k.GetProcessId(h));image=C.create_unicode_buffer(32768);length=C.c_uint32(len(image))
    ok=bool(k.QueryFullProcessImageNameW(h,0,image,C.byref(length)))
    err=0 if ok else C.get_last_error()
    if ok:
        actual_image=image.value;image_origin='actual_current_retained_handle_query'
        if prior is not None and (prior['pid']!=pid or prior['creation_filetime_100ns']!=a.value or prior['image']!=actual_image):raise RuntimeError('Retained child identity changed')
    elif err==31 and exitcode.value!=259 and prior is not None and prior['pid']==pid and prior['creation_filetime_100ns']==a.value:
        actual_image=prior['image'];image_origin='retained_initial_image_NOT_a_fresh_terminal_image_query'
    else:raise C.WinError(err)
    return {'pid':pid,'creation_filetime_100ns':a.value,'image':actual_image,
            'image_query':{'succeeded':ok,'error':err,'origin':image_origin},
            'native_exit_or_STILL_ACTIVE':exitcode.value,'working':m.WorkingSetSize,
            'peak_working':m.PeakWorkingSetSize,'private':m.PrivateUsage,'peak_pagefile':m.PeakPagefileUsage,
            'available_RAM':ms.available,'available_commit':ms.availablepage,'UTC':utc()}

def append(path,value):
    raw=(json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')
    with Path(path).open('ab') as f:
        assert f.write(raw)==len(raw)

def output_census(root):
    """All owned files, including TEMP: only transient owned TEMP absence may rescan."""
    root=Path(root).resolve();races=[]
    for attempt in range(1,4):
        totals={k:0 for k in BUCKETS};files=0;dirs=0;race_path=None
        try:
            stack=[root]
            while stack:
                q=stack.pop();s=q.lstat()
                if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise RuntimeError('Output reparse/alias path: '+str(q))
                if not q.resolve().is_relative_to(root):raise RuntimeError('Output escaped owned root')
                if stat.S_ISDIR(s.st_mode):
                    dirs+=1
                    if dirs>4096:raise RuntimeError('Owned directory count exceeds4096')
                    stack.extend(q.iterdir());continue
                if not stat.S_ISREG(s.st_mode):raise RuntimeError('Nonordinary owned output')
                files+=1
                if files>30000:raise RuntimeError('Owned file count exceeds30000')
                parts=q.relative_to(root).parts
                key=('temp_cache' if parts[0]=='temp_cache' else
                     'science' if len(parts)>1 and parts[0]in('original','audit') and parts[1]=='results' else
                     'telemetry' if parts[0]=='telemetry' or (len(parts)>1 and parts[0]in('original','audit') and parts[1]=='native_science') else 'metadata')
                totals[key]+=s.st_size
        except FileNotFoundError as e:
            raw=getattr(e,'filename',None);race_path=Path(raw).resolve() if raw else q.resolve()
            if getattr(e,'winerror',None)not in(None,2,3)or(e.errno!=2 and getattr(e,'winerror',None)is None):raise
            if not race_path.is_relative_to(root/'temp_cache') or race_path==root/'temp_cache':raise
            if race_path.exists()or race_path.is_symlink():raise
            current=race_path.parent
            while current!=root:
                if current.exists()and getattr(current.lstat(),'st_file_attributes',0)&0x400:raise RuntimeError('TEMP reparse ancestor')
                current=current.parent
            races.append({'attempt':attempt,'path':str(race_path),'exception':repr(e),'genuine_missing_observation':True})
            continue
        return {'bucket_bytes':totals,'whole_output_bytes':sum(totals.values()),'files':files,'directories':dirs,'TEMP_disappearance_rescans':races}
    raise RuntimeError('Three complete owned TEMP censuses failed: '+json.dumps(races))

def output_enforce(root,c):
    bad=[]
    for key,limit in BUCKETS.items():
        if c['bucket_bytes'][key]>limit:bad.append(key+' output cap')
    if c['whole_output_bytes']>WHOLE:bad.append('joint6.375GiB output cap')
    free=shutil.disk_usage(root).free;required=FLOOR+max(0,WHOLE-c['whole_output_bytes'])
    if free<required:bad.append('20GiB OS reserve plus complete remaining logical growth')
    return {'actual_free_bytes':free,'required_free_bytes':required,'census':c,'violations':bad}

class Guard:
    """Same public scientific callback API; current lean policy, no old qualification claim."""
    def __init__(self,root,out,policy_path,policy_sha256,shared_start_utc):
        raw=Path(policy_path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=policy_sha256:raise RuntimeError('Lean087 policy changed')
        self.a=json.loads(raw)
        if self.a.get('execution_authorized')is not True or self.a.get('lean087_resource_plan_reviewed')is not True:raise RuntimeError('Lean087 resource authority absent')
        self.root=Path(self.a['programme_root']).resolve();self.out=Path(out).resolve()
        if not self.root.is_relative_to(Path(root).resolve())or not self.out.is_relative_to(self.root):raise RuntimeError('Lean output scope')
        self.out.mkdir(parents=True,exist_ok=True)
        self.start=dt.datetime.fromisoformat(shared_start_utc);self.phase=dt.datetime.fromisoformat(self.a['phase_start_utc'])
        if self.start.tzinfo is None or self.phase.tzinfo is None:raise RuntimeError('UTC clock required')
        self.k,self.p=kernel();self.last_census=-1e30;self.cached_census=None
        self.policy_sha256=policy_sha256

    def check(self,phase,remaining_planned_output_bytes=0,intra_threads=None,inter_threads=None):
        now=dt.datetime.now(dt.timezone.utc);r=native(self.k,self.p)
        row={'UTC':now.isoformat(),'phase':phase,'native':r,'shared_elapsed_seconds':(now-self.start).total_seconds(),
             'phase_elapsed_seconds':(now-self.phase).total_seconds(),'intra_threads':intra_threads,'inter_threads':inter_threads,
             'policy_SHA256':self.policy_sha256}
        if time.monotonic()-self.last_census>=5:
            self.cached_census=output_enforce(self.root,output_census(self.root));self.last_census=time.monotonic()
            row['complete_output_reservation']=self.cached_census
        bad=[]
        if max(r['working'],r['peak_working'])>2*GiB:bad.append('scientific2GiB working peak')
        if max(r['private'],r['peak_pagefile'])>3*GiB:bad.append('scientific3GiB private peak')
        if r['available_RAM']<GiB:bad.append('continuous1GiB availableRAM')
        if r['available_commit']<2*GiB:bad.append('continuous2GiB commit')
        if row['shared_elapsed_seconds']>13800 or row['phase_elapsed_seconds']>6000:bad.append('unchanged shared/phase deadline')
        if intra_threads is not None and intra_threads!=2:bad.append('intra threads changed')
        if inter_threads is not None and inter_threads!=2:bad.append('interop threads changed')
        bad.extend(self.cached_census['violations'])
        row['violations']=bad;append(self.out/'every_scientific_callback.jsonl',row)
        if bad:raise RuntimeError('Lean087 resource stop: '+json.dumps(row))
        return row
