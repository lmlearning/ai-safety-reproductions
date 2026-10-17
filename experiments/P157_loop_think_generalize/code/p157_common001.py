"""P157 ordinary scoped clocks, pins, native observation and owned storage."""
import ctypes as C
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time

ROOT=Path('{{REPRODUCTION_ROOT}}')
PAPER=ROOT/'papers/P157_loop_think_generalize'
SOURCE=Path(__file__).absolute().parent
INPUT=PAPER/'inputs/acquisition001'
RUN=ROOT/'runs/P157_complete_main001'
GiB=1024**3
INPUT_CAP=4*GiB
SCIENCE_CAP=14*GiB
DISK_FLOOR=35*GiB
CUTOFFS={'acquisition':7200,'fidelity':28800,'full':504000,'audit':514800,'closure':518400}
PREREG=PAPER/'PREREGISTRATION.txt'
HELPER=ROOT/'papers/P092_subliminal_learning/review/lean_original087/p092_lean087_resources.py'
HELPER_SHA='95539db0a853f00c74d1a392501802c0b4802ecc4ce893de3b177517c8b8ab84'

def utc():return dt.datetime.now(dt.timezone.utc)
def iso():return utc().isoformat()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def pin(path):
    p=Path(path).absolute();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def verify(ref):
    require(pin(ref['path'])==ref,'Whole file pin changed: '+ref['path']);return Path(ref['path'])
def save(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    return pin(p)
def append(path,value):
    b=(json.dumps(value,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    require(len(b)<=65536,'Bounded complete resource record exceeds64KiB')
    with Path(path).open('ab') as f:require(f.write(b)==len(b),'Short resource write')
def safe_root(path,new=False):
    p=Path(path).absolute();require(p.is_relative_to(ROOT),'Owned root outside workspace')
    q=p
    while q!=ROOT:
        if q.exists():
            s=q.lstat();require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Reparse owned ancestor')
        q=q.parent
    if new:require(not p.exists(),'Preserve existing phase namespace');p.mkdir(parents=True)
    require(p.resolve()==p,'Resolved owned root differs');return p
def load_grant(path,phase,explicit=False,phase_review=None):
    require(explicit,'Explicit ROOT phase command required')
    a=json.loads(Path(path).read_bytes())
    require(a.get('schema')=='P157_ONE_144H_PROGRAMME_GRANT001' and a.get('execution_authorized')is True,'No P157 physical grant')
    require(phase=='acquisition' and a.get('phase_authorized')=='acquisition','This source admits only public acquisition; all scientific phases remain held')
    require(a['total_seconds']==518400 and a['stage_cumulative_cutoffs_seconds']==CUTOFFS,'Programme allowance changed')
    require(a['input_cap_bytes']==INPUT_CAP and a['science_cap_bytes']==SCIENCE_CAP and a['disk_floor_bytes']==DISK_FLOOR,'Resource source contract changed')
    require(a['preregistration_ref']==pin(PREREG),'Preregistration changed')
    review=json.loads(verify(a['root_source_review_ref']).read_bytes())
    require(review.get('root_complete_P157_source_review_passed')is True,'Whole source review absent')
    require(review['current_source_packet_ref']==a['current_source_packet_ref'],'Source packet review join')
    packet=json.loads(verify(a['current_source_packet_ref']).read_bytes())
    for r in packet['current_source_refs']:verify(r)
    start=dt.datetime.fromisoformat(a['common_origin_UTC']);end=dt.datetime.fromisoformat(a['common_deadline_UTC'])
    require(start.tzinfo is not None and end-start==dt.timedelta(seconds=518400),'One UTC programme clock required')
    require(start<=utc()<start+dt.timedelta(seconds=CUTOFFS[phase]),'Absolute phase cutoff reached')
    a['_grant_ref']=pin(path);a['_phase']=phase;a['_start']=start;a['_cutoff']=start+dt.timedelta(seconds=CUTOFFS[phase]);return a

class STANDARD(C.Structure):
    _fields_=[('AllocationSize',C.c_int64),('EndOfFile',C.c_int64),('NumberOfLinks',C.c_uint32),('DeletePending',C.c_ubyte),('Directory',C.c_ubyte)]
class COMPRESSION(C.Structure):
    _fields_=[('CompressedFileSize',C.c_int64),('CompressionFormat',C.c_uint16),('CompressionUnitShift',C.c_ubyte),('ChunkShift',C.c_ubyte),('ClusterShift',C.c_ubyte),('Reserved',C.c_ubyte*3)]

class Native:
    def __init__(self):
        require(pin(HELPER)['sha256']==HELPER_SHA,'Reviewed native helper changed')
        spec=importlib.util.spec_from_file_location('p157_pinned_native_helper',HELPER);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        self.helper=h;self.k,self.p=h.kernel()
        self.k.CreateFileW.argtypes=[C.c_wchar_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p];self.k.CreateFileW.restype=C.c_void_p
        self.k.GetFileInformationByHandleEx.argtypes=[C.c_void_p,C.c_int,C.c_void_p,C.c_uint32];self.k.GetFileInformationByHandleEx.restype=C.c_int
        self.k.CloseHandle.argtypes=[C.c_void_p];self.k.CloseHandle.restype=C.c_int
        self.first=self.read()
    def read(self,handle=None,prior=None):return self.helper.native(self.k,self.p,handle,prior)
    def allocation(self,path,isdir):
        h=self.k.CreateFileW(str(path),0x80,7,None,3,0x02000000 if isdir else 0,None)
        if h in(None,C.c_void_p(-1).value):raise C.WinError(C.get_last_error())
        err=None;result=None
        try:
            s=STANDARD()
            if not self.k.GetFileInformationByHandleEx(h,1,C.byref(s),C.sizeof(s)):raise C.WinError(C.get_last_error())
            require(s.AllocationSize>=0 and s.EndOfFile>=0,'Negative allocation metadata')
            if isdir:physical=s.AllocationSize;basis='FILE_STANDARD_INFO_directory'
            else:
                c=COMPRESSION()
                if not self.k.GetFileInformationByHandleEx(h,8,C.byref(c),C.sizeof(c)):raise C.WinError(C.get_last_error())
                require(c.CompressedFileSize>=0,'Negative physical metadata');physical=c.CompressedFileSize;basis='FILE_COMPRESSION_INFO'
            result={'logical':s.EndOfFile,'standard_allocation':s.AllocationSize,'physical':physical,'physical_basis':basis,'links':s.NumberOfLinks}
        except Exception as e:err=e
        finally:
            ok=bool(self.k.CloseHandle(h));ce=0 if ok else C.get_last_error()
            if not ok:raise RuntimeError('Owned allocation handle close failed: '+str((h,ce,repr(err))))
        if err:raise err
        return result

def census(native,roots):
    totals=[];allfiles=0;alldirs=0
    for root,cap in roots:
        root=Path(root);logical=charged=physical=0
        if not root.exists():totals.append({'root':str(root),'cap':cap,'logical':0,'charged':0,'physical':0});continue
        safe_root(root);stack=[root]
        while stack:
            p=stack.pop();s=p.lstat()
            require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Owned reparse/nonordinary path')
            require(p.resolve().is_relative_to(root.resolve()),'Owned path escaped root')
            isdir=stat.S_ISDIR(s.st_mode);require(isdir or stat.S_ISREG(s.st_mode),'Unknown owned filesystem object')
            a=native.allocation(p,isdir);physical+=a['physical']
            if isdir:
                alldirs+=1;require(alldirs<=4096,'Owned directory cap4096');stack.extend(p.iterdir())
            else:
                allfiles+=1;require(allfiles<=8192,'Owned file cap8192');require(a['links']==1,'Owned output hardlink')
                logical+=s.st_size;charged+=max(s.st_size,a['standard_allocation'])
        require(charged<=cap and physical<=cap,'Owned storage cap exceeded')
        totals.append({'root':str(root),'cap':cap,'logical':logical,'charged':charged,'physical':physical})
    free=shutil.disk_usage(str(ROOT)).free;remaining=sum(max(0,x['cap']-x['physical']) for x in totals)
    require(free>=DISK_FLOOR+remaining,'35GiB reserve plus complete unspent physical output failed: '+json.dumps({'free':free,'required':DISK_FLOOR+remaining,'roots':totals}))
    return {'roots':totals,'files':allfiles,'directories':alldirs,'actual_free':free,'required_free':DISK_FLOOR+remaining,'observation':'Nonatomic latest complete owned allocation census; no global atomic quota or foreign-writer bound claimed.'}

class Guard:
    def __init__(self,a,phase,output,acquisition=False):
        self.a=a;self.phase=phase;self.output=Path(output);self.native=Native();self.last_native=-1e30;self.last_census=-1e30;self.last_row=None;self.acquisition=acquisition
        self.roots=[(INPUT,INPUT_CAP)] if acquisition else [(INPUT,INPUT_CAP),(RUN,SCIENCE_CAP)]
    def check(self,label,force=False):
        now=utc();require(now<self.a['_cutoff'] and now<self.a['_start']+dt.timedelta(seconds=518400),'Same absolute programme/phase deadline')
        if not force and time.monotonic()-self.last_native<5:return self.last_row
        storage=None
        if force or time.monotonic()-self.last_census>=30:storage=census(self.native,self.roots);self.last_census=time.monotonic()
        n=self.native.read();limit=512*1024**2 if self.acquisition else int(4.5*GiB)
        require(max(n['working'],n['peak_working'])<=limit,'Current owned worker working-set cap')
        if not self.acquisition:require(max(n['private'],n['peak_pagefile'])<=int(6.5*GiB),'Current owned worker private cap')
        require(n['available_RAM']>=GiB and n['available_commit']>=8*GiB,'Continuous1GiB RAM/8GiB commit')
        now=utc();require(now<self.a['_cutoff'],'Absolute cutoff after complete census/native observation')
        row={'UTC':iso(),'phase':self.phase,'label':label,'native':n,'complete_storage':storage,'elapsed':(now-self.a['_start']).total_seconds()}
        append(self.output/'resources.jsonl',row);self.last_native=time.monotonic();self.last_row=row;return row

    def final_observation(self,label,child_terminal=None):
        # This last observation writes nothing: census first, fresh parent/host after it.
        storage=census(self.native,self.roots);n=self.native.read()
        peak=max(n['working'],n['peak_working'])
        if child_terminal is not None:peak+=child_terminal['peak_working']
        require(peak<=512*1024**2,'Final complete acquisition pair lifetime working peak')
        require(n['available_RAM']>=GiB and n['available_commit']>=8*GiB,'Final continuous RAM/commit')
        require(utc()<self.a['_cutoff'],'Final actual postwrite absolute cutoff')
        return {'label':label,'native':n,'storage':storage,'pair_working_peak_upper_bound':peak}
