"""Dormant full P161 original released-score computation and independent audit.
One retained direct child; no Job, descendants, DLL or historical PID claims.
All600 seconds inclusive,540 work/60 closure, complete64MiB owned pool.
"""
import argparse,ctypes,hashlib,importlib.util,json,math,os,runpy,shutil,subprocess,sys,time,traceback
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path

def now():return datetime.now(timezone.utc)
def stamp():return now().isoformat()
def parsed(text):return datetime.fromisoformat(text.replace('Z','+00:00'))


def file_ref(path, tick=lambda:None):
    p=Path(path); h=hashlib.sha256(); n=0
    with p.open('rb')as stream:
        for b in iter(lambda:stream.read(1048576),b''):
            tick(); n+=len(b); h.update(b)
    return {'path':str(p),'bytes':n,'sha256':h.hexdigest()}

def require(ref,tick=lambda:None):
    if file_ref(ref['path'],tick)!=ref: raise ValueError('Changed exact current source/input '+ref['path'])

def write(path,value):
    with Path(path).open('x',encoding='ascii',newline='\n')as stream:
        json.dump(value,stream,ensure_ascii=True,separators=(',',':'),allow_nan=False);stream.write('\n')
    return file_ref(path)

def census(roots):
    total=0; leaves=0
    for root in roots:
        p=Path(root)
        if not p.exists():continue
        if p.is_symlink()or p.is_junction():raise ValueError('Owned root reparse')
        for current,dirs,files in os.walk(p,followlinks=False):
            for name in dirs:
                child=Path(current)/name
                if child.is_symlink()or child.is_junction():raise ValueError('Owned subtree reparse')
            for name in files:
                child=Path(current)/name;s=child.stat(follow_symlinks=False)
                if s.st_file_attributes&0x400 or not child.is_file()or s.st_nlink!=1:raise ValueError('Owned aliased/nonordinary file')
                total+=s.st_size;leaves+=1
                if leaves>10000:raise ValueError('Finite10000 source-owned output leaves')
    return {'bytes':total,'leaves':leaves}

class Native:
    class MEMORY(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t),('PrivateUsage',ctypes.c_size_t)]
    class GLOBAL(ctypes.Structure):
        _fields_=[('dwLength',wintypes.DWORD),('dwMemoryLoad',wintypes.DWORD),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True);self.p=ctypes.WinDLL('psapi',use_last_error=True)
        self.k.GetCurrentProcess.restype=wintypes.HANDLE
        self.k.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];self.k.GetProcessTimes.restype=wintypes.BOOL
        self.k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];self.k.GetExitCodeProcess.restype=wintypes.BOOL
        self.k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)];self.k.QueryFullProcessImageNameW.restype=wintypes.BOOL
        self.k.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(self.GLOBAL)];self.k.GlobalMemoryStatusEx.restype=wintypes.BOOL
        self.p.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(self.MEMORY),wintypes.DWORD];self.p.GetProcessMemoryInfo.restype=wintypes.BOOL
    def birth(self,h):
        values=[wintypes.FILETIME()for _ in range(4)]
        if not self.k.GetProcessTimes(h,*[ctypes.byref(v)for v in values]):raise ctypes.WinError(ctypes.get_last_error())
        return(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
    def exit(self,h):
        code=wintypes.DWORD()
        if not self.k.GetExitCodeProcess(h,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
        return code.value
    def image(self,h):
        size=wintypes.DWORD(32768);buf=ctypes.create_unicode_buffer(size.value)
        if not self.k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        return buf.value
    def memory(self,h):
        row=self.MEMORY();row.cb=ctypes.sizeof(row)
        if not self.p.GetProcessMemoryInfo(h,ctypes.byref(row),row.cb):raise ctypes.WinError(ctypes.get_last_error())
        return {'working':row.WorkingSetSize,'private':row.PrivateUsage,'peak_working':row.PeakWorkingSetSize,'peak_private':row.PeakPagefileUsage}
    def host(self,drive):
        state=self.GLOBAL();state.dwLength=ctypes.sizeof(state)
        if not self.k.GlobalMemoryStatusEx(ctypes.byref(state)):raise ctypes.WinError(ctypes.get_last_error())
        return {'available_RAM_bytes':state.ullAvailPhys,'available_commit_bytes':state.ullAvailPageFile,'free_disk_bytes':shutil.disk_usage(drive).free}

FLAGS=('execution_authorized','ROOT_full_P161_science_authorized','ROOT_P161_current_source_review_passed')

def authority(args):
    cfg=json.loads(Path(args.control).read_bytes());grant=json.loads(Path(args.grant).read_bytes());review=json.loads(Path(args.root_review).read_bytes())
    if not args.ROOT_REVIEWED_COMPLETE_P161_SCIENCE or any(cfg.get(k)is not True for k in FLAGS)or grant.get('execution_authorized')is not True:raise PermissionError('P161 dormant: explicit current ROOT scientific authority required')
    if review.get('root_complete_P161_whole_current_source_review_passed')is not True or review.get('root_P161_runtime_and_joint_groups_source_review_passed')is not True:raise PermissionError('Whole source/runtime/joint group review required')
    if grant['control_ref']!=file_ref(args.control)or grant['source_review_ref']!=file_ref(args.root_review):raise ValueError('Exact current grant/review/control join')
    if cfg['supervisor_source_ref']!=file_ref(__file__)or grant['supervisor_source_ref']!=cfg['supervisor_source_ref']:raise ValueError('Current parent source changed')
    require(review['False_control_ref']);false=json.loads(Path(review['False_control_ref']['path']).read_bytes());normalized=dict(cfg)
    for k in FLAGS:normalized[k]=False
    if normalized!=false:raise ValueError('Only three reviewed authority flags may change')
    if review['source_current_bundle_ref']!=cfg['source_current_bundle_ref']:raise ValueError('Current complete source bundle mismatch')
    require(cfg['source_current_bundle_ref'])
    if review['other_owned_output_groups']!=cfg['other_owned_output_groups']or review['other_active_grant_refs']!=cfg['other_active_grant_refs']:raise ValueError('Exact allfour other groups/current grant source review')
    if len(cfg['other_owned_output_groups'])!=4 or sum(g['cap_bytes']for g in cfg['other_owned_output_groups'])!=int(22.75*1024**3):raise ValueError('Four complete current other groups required')
    for ref in cfg['other_active_grant_refs']:
        require(ref)
        if json.loads(Path(ref['path']).read_bytes()).get('execution_authorized')is not True:raise ValueError('Other group admitted grant not actual')
    if grant['preregistration_ref']['path']!=cfg['preregistration_path']:raise ValueError('Exact prior preregistration path required')
    require(grant['preregistration_ref'])
    origin=parsed(grant['origin_UTC']);work=parsed(grant['work_cutoff_UTC']);deadline=parsed(grant['deadline_UTC'])
    if any(x.tzinfo is None for x in (origin,work,deadline))or(work-origin).total_seconds()!=540 or(deadline-origin).total_seconds()!=600 or not origin<=now()<work:raise ValueError('One original540/600 absolute UTC clock')
    return cfg,grant,origin,work,deadline

def joint_guard(cfg,work,deadline):
    require(cfg['joint_resources_ref'])
    return runpy.run_path(cfg['joint_resources_ref']['path'],run_name='P161_JOINT_DEFINITIONS')['Joint'](cfg,work,deadline,now)

def memory_caps(row,working,private,label):
    if max(row['working'],row['peak_working'])>working or max(row['private'],row['peak_private'])>private:raise ValueError(label+' lifetime/current working/private cap '+json.dumps(row))

def child(args):
    cfg,grant,origin,work,deadline=authority(args);root=Path(cfg['output_root']);meta=Path(cfg['metadata_root'])
    n=Native();own=n.k.GetCurrentProcess();joint=joint_guard(cfg,work,deadline);last=-1e30;samples=0
    log=(meta/'CHILD_RESOURCE_SAMPLES001.ndjson').open('x',encoding='ascii',newline='\n')
    def tick(force=False):
        nonlocal last,samples
        if now()>=work:raise TimeoutError('Original540 work cutoff')
        if not force and time.monotonic()-last<1:return
        storage=joint.observe(force=force);mem=n.memory(own);host=n.host(cfg['workspace'])
        row=dict(UTC=stamp(),native=mem,host=host,storage=storage)
        log.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');log.flush();samples+=1
        memory_caps(mem,cfg['child_working_bytes'],cfg['child_private_bytes'],'Direct scientific child')
        if host['available_RAM_bytes']<cfg['continuous_RAM_bytes']or host['available_commit_bytes']<cfg['continuous_commit_bytes']:raise ValueError('Continuous child RAM/Windowscommit resource stop')
        if samples>1200 or now()>=work:raise TimeoutError('Finite child sample count/common work cutoff')
        last=time.monotonic()
    def deny(event,arguments):
        if event in ('socket.__new__','socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'):raise PermissionError('Offline analysis forbids network/API/nested processes')
    sys.addaudithook(deny);failure=None;result=None
    try:
        root.mkdir(exist_ok=False)
        for ref in cfg['all_current_source_and_input_refs']:require(ref,tick)
        tick(True)
        site=Path(cfg['CPU_site']);hostsite=Path(cfg['HOST_site']);base=Path(sys.base_prefix)
        sys.path[:]=[str(site),str(hostsite),str(base/'Lib'),str(base/'DLLs'),str(base/'python312.zip')]
        import numpy as np
        import scipy
        from scipy import special
        if np.__version__!='2.3.1'or scipy.__version__!='1.16.0'or not all(Path(m.__file__).resolve().is_relative_to(site.resolve())for m in (np,scipy)):raise ValueError('Exact reviewed CPU NumPy/SciPy versions and origins')
        write(meta/'ACTUAL_NUMERICAL_RUNTIME001.json',dict(python=sys.version,executable=sys.executable,path=sys.path,numpy=np.__version__,scipy=scipy.__version__,origins=dict(numpy=np.__file__,scipy=scipy.__file__,special=special.__file__),environment=dict(os.environ),matplotlib_or_GPU_imported=False))
        primary=runpy.run_path(cfg['primary_source_ref']['path'],run_name='P161_PRIMARY_DEFINITIONS')
        secondary=runpy.run_path(cfg['secondary_source_ref']['path'],run_name='P161_SECONDARY_DEFINITIONS')
        auditor=runpy.run_path(cfg['auditor_source_ref']['path'],run_name='P161_COMPLETE_AUDITOR_DEFINITIONS')
        first=primary['run_complete_primary'](cfg,np,special,tick)
        second=secondary['run_complete_secondary'](cfg,np,special,tick)
        # Neither route sees the other's numerical values before its own full derivation.
        require(first['result_ref'],tick);require(second['result_ref'],tick)
        if first['fact_count']!=189 or second['fact_count']!=189 or len(first['figure_refs'])!=5:raise ValueError('Complete both189 facts and five rendered reconstructions required')
        if [item['figure'] for item in first['figure_refs']]!=['1','2','3','4','5']:raise ValueError('Exactly five unique ordered original figure reconstruction IDs required')
        for item in first['figure_refs']:require(item['ref'],tick)
        a=json.loads(Path(first['result_ref']['path']).read_bytes());b=json.loads(Path(second['result_ref']['path']).read_bytes())
        api=json.loads(Path(cfg['facts_schema_ref']['path']).read_bytes());roles=json.loads(Path(cfg['query_roles_ref']['path']).read_bytes());inputs=json.loads(Path(cfg['input_schema_ref']['path']).read_bytes())
        agreement=auditor['compare_complete'](a,b,api,tick)
        pa=auditor['publication_audit'](a,roles,api,inputs,tick);sa=auditor['publication_audit'](b,roles,api,inputs,tick)
        tick(True);auditref=write(root/'COMPLETE_ALL_FIELDS_AND_PUBLICATION_AUDIT001.json',dict(agreement=agreement,primary=pa,secondary=sa))
        result=dict(primary=first,secondary=second,audit_ref=auditref,all189_complete_fields_agree=agreement['all_complete_fields_agree'],
            complete_CENTRAL_numeric_candidate=bool(agreement['all_complete_fields_agree']and pa['complete_CENTRAL_candidate']and sa['complete_CENTRAL_candidate']),
            all86_primary_AND_and20_ordering_required=True,all273_formula_cache_integrity_required=True,all_support_variants_and_five_figures_reported=True,FULL_reproduction=False,paper_credit=0)
        tick(True)
    except BaseException as exc:failure=dict(type=type(exc).__name__,repr=repr(exc),traceback=traceback.format_exc(),UTC=stamp())
    finally:log.close()
    terminal=dict(schema='P161_COMPLETE_DIRECT_CHILD001',failure=failure,result=result,origin_UTC=grant['origin_UTC'],work_cutoff_UTC=grant['work_cutoff_UTC'],deadline_UTC=grant['deadline_UTC'],end_UTC=stamp(),within_work_cutoff=now()<work,python=sys.version,executable=sys.executable,network_API_nested_processes_disabled=True,paper_credit=0)
    ref=write(meta/'COMPLETE_CHILD_TERMINAL001.json',terminal)
    print(json.dumps(dict(terminal_ref=ref,failure=failure,UTC=stamp())),flush=True)
    return 0 if failure is None and result is not None and now()<work else 1

def parent(args):
    cfg,grant,origin,work,deadline=authority(args);roots=[Path(cfg['output_root']),Path(cfg['metadata_root'])];workspace=Path(cfg['workspace']).resolve(strict=True)
    for p in roots:
        if not p.is_absolute()or not p.resolve().is_relative_to(workspace)or p.exists():raise ValueError('Exact exclusive new owned roots required')
        for a in (p,*p.parents):
            if a.exists()and(a.is_symlink()or a.is_junction()):raise ValueError('Owned ancestry reparse')
    if roots[0]==roots[1]or roots[0].is_relative_to(roots[1])or roots[1].is_relative_to(roots[0]):raise ValueError('Separate owned scientific and metadata roots')
    n=Native();own=n.k.GetCurrentProcess();joint=joint_guard(cfg,work,deadline)
    fresh_storage=joint.observe(force=True);fresh=n.host(cfg['workspace']);memory_caps(n.memory(own),cfg['parent_working_bytes'],cfg['parent_private_bytes'],'Parent fresh')
    if fresh['available_RAM_bytes']<cfg['fresh_RAM_bytes']or fresh['available_commit_bytes']<cfg['fresh_commit_bytes']:raise ValueError('Fresh2GiB RAM/8GiB Windowscommit unavailable')
    roots[1].mkdir();temp=roots[1]/'TEMP';temp.mkdir()
    proc=None;known=None;terminal_child=None;failure=None;closed=False;exitcode=None;cleanup=[]
    receipt=dict(schema='P161_COMPLETE_DIRECT_PARENT001',origin_UTC=grant['origin_UTC'],work_cutoff_UTC=grant['work_cutoff_UTC'],deadline_UTC=grant['deadline_UTC'],fresh_host=fresh,fresh_storage=fresh_storage,control_ref=file_ref(args.control),grant_ref=file_ref(args.grant),root_review_ref=file_ref(args.root_review),parent_PID=os.getpid(),parent_native_birth=n.birth(own),known_direct_child=None,Job_or_descendant_accounting_claimed=False,paper_credit=0)
    log=(roots[1]/'PARENT_RESOURCE_SAMPLES001.ndjson').open('x',encoding='ascii',newline='\n')
    def sample(stage,append=True,closure=False,force=False):
        storage=joint.observe(force=force,closure=closure)
        row=dict(UTC=stamp(),stage=stage,storage=storage,parent=n.memory(own),child=n.memory(proc._handle)if proc is not None and not closed else terminal_child,host=n.host(cfg['workspace']))
        if append:log.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');log.flush()
        memory_caps(row['parent'],cfg['parent_working_bytes'],cfg['parent_private_bytes'],'Parent')
        c=row['child'];cp=c['peak_working']if c else 0;cv=c['peak_private']if c else 0
        if c:memory_caps(c,cfg['child_working_bytes'],cfg['child_private_bytes'],'Retained direct child including terminal peaks')
        # Conservative sum of disjoint lifetime maxima, not a measured global concurrent peak.
        if row['parent']['peak_working']+cp>cfg['whole_working_bytes']or row['parent']['peak_private']+cv>cfg['whole_private_bytes']:raise ValueError('Whole retained pair conservative lifetime peak bound')
        h=row['host']
        if h['available_RAM_bytes']<cfg['continuous_RAM_bytes']or h['available_commit_bytes']<cfg['continuous_commit_bytes']:raise ValueError('Continuous whole pair RAM/Windowscommit')
        joint.phase(closure);row['all_caps_and_reservations_passed']=True;return row
    try:
        for ref in cfg['all_current_source_and_input_refs']:require(ref,lambda:joint.phase())
        sample('PRE_POPEN',force=True)
        command=[cfg['python_executable'],'-I','-S','-B','-X','utf8',str(Path(__file__)),'--child','--control',args.control,'--grant',args.grant,'--root-review',args.root_review,'--ROOT-REVIEWED-COMPLETE-P161-SCIENCE']
        env={k:os.environ[k]for k in('SystemRoot','WINDIR')if k in os.environ};env.update(TEMP=str(temp),TMP=str(temp),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
        receipt.update(exact_command=command,selected_child_environment=env)
        with (roots[1]/'child.stdout').open('xb')as stdout,(roots[1]/'child.stderr').open('xb')as stderr:
            proc=subprocess.Popen(command,stdout=stdout,stderr=stderr,cwd=str(roots[1]),env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            known=dict(PID=proc.pid,native_birth='UNMEASURED',image='UNMEASURED',ownership='exact retained direct Popen handle');receipt['known_direct_child']=known
            known['native_birth']=n.birth(proc._handle);known['image']=n.image(proc._handle)
            if Path(known['image']).resolve()!=Path(cfg['python_executable']).resolve():raise ValueError('Different direct child executable')
            while True:
                sample('LIVE_OR_TERMINAL')
                if n.birth(proc._handle)!=known['native_birth']:raise ValueError('Retained direct child birth changed')
                exitcode=proc.poll()
                if exitcode is not None:
                    receipt['terminal_observed_UTC']=stamp()
                    if now()>=work:raise TimeoutError('Direct child terminal observed after540 work cutoff')
                    break
                if now()>=work:raise TimeoutError('Original shared540 work cutoff')
                time.sleep(min(1,max(0,(work-now()).total_seconds())))
            if exitcode!=0 or n.exit(proc._handle)!=0:raise RuntimeError('Whole scientific child actual nonzero exit')
            report_path=roots[1]/'COMPLETE_CHILD_TERMINAL001.json';report=json.loads(report_path.read_bytes())
            if report['failure']is not None or report['result']is None or report['within_work_cutoff']is not True:raise ValueError('Incomplete primary/secondary/audit child terminal')
            receipt['child_terminal_ref']=file_ref(report_path);receipt['scientific_result']=report['result']
    except BaseException as exc:failure=dict(type=type(exc).__name__,repr=repr(exc),traceback=traceback.format_exc(),UTC=stamp())
    finally:
        if proc is not None:
            try:
                if proc.poll()is None:
                    proc.terminate();proc.wait(timeout=max(.01,min(10,(deadline-now()).total_seconds())))
                same_birth=n.birth(proc._handle)
                if isinstance(known.get('native_birth'),int)and same_birth!=known['native_birth']:raise ValueError('Terminal retained direct birth mismatch')
                terminal_child=n.memory(proc._handle);receipt['actual_direct_native_exit']=n.exit(proc._handle);receipt['terminal_direct_native_birth']=same_birth;receipt['terminal_direct_memory']=terminal_child
                try:receipt['terminal_image']=dict(value=n.image(proc._handle),origin='actual postexit retained-handle query')
                except OSError as exc:
                    receipt['terminal_image_query_failure']=dict(winerror=exc.winerror,repr=repr(exc))
                    if exc.winerror!=31 or receipt['actual_direct_native_exit']==259 or known.get('image')=='UNMEASURED'or same_birth!=known['native_birth']:raise
                    receipt['terminal_image']=dict(value=known['image'],origin='retained initial image; NOT a fresh image query')
            except BaseException as exc:cleanup.append(dict(stage='EXACT_DIRECT_CLEANUP',error=repr(exc)))
            try:proc._handle.Close();closed=True
            except BaseException as exc:cleanup.append(dict(stage='DIRECT_HANDLE_CLOSE',error=repr(exc)))
        receipt.update(failure=failure,cleanup_errors=cleanup,direct_retained_handle_closed=closed if proc is not None else None,UTC=stamp())
        try:receipt['after_close_sample']=sample('AFTER_DIRECT_CLOSE',closure=True,force=True)
        except BaseException as exc:cleanup.append(dict(stage='AFTER_CLOSE_RESOURCE',error=repr(exc)))
        log.close()
        try:
            receipt['whole_closed_owned_file_refs']=[file_ref(p,lambda:joint.phase(True))for root in roots if root.exists()for p in sorted(root.rglob('*'))if p.is_file()]
            receipt['post_hash_sample']=sample('AFTER_ALL_WHOLE_HASHES',append=False,closure=True,force=True)
        except BaseException as exc:cleanup.append(dict(stage='WHOLE_CUSTODY_OR_POSTHASH',error=repr(exc)))
        receipt['operational_complete_candidate']=failure is None and not cleanup and exitcode==0 and receipt.get('actual_direct_native_exit')==0 and closed and now()<deadline
        terminal_ref=write(roots[1]/'COMPLETE_PARENT_TERMINAL001.json',receipt)
        print(json.dumps(dict(terminal_ref=terminal_ref,terminal_written_UTC=stamp(),paper_credit=0)),flush=True)
        final=None
        try:final=sample('AFTER_PARENT_TERMINAL_HASH_AND_FIRST_STDOUT',append=False,closure=True,force=True)
        except BaseException as exc:cleanup.append(dict(stage='FINAL_POSTWRITE_RESOURCE',error=repr(exc)))
        accepted=receipt['operational_complete_candidate']and not cleanup and final is not None and now()<deadline
        print(json.dumps(dict(terminal_ref=terminal_ref,actual_postwrite_sample=final,cleanup_errors=cleanup,operational_complete=bool(accepted),complete_CENTRAL_numeric_candidate=bool(accepted and receipt.get('scientific_result',{}).get('complete_CENTRAL_numeric_candidate',False)),UTC=stamp(),paper_credit=0)),flush=True)
    return 0 if accepted and now()<deadline else 1

def main():
    p=argparse.ArgumentParser();p.add_argument('--control',required=True);p.add_argument('--grant',required=True);p.add_argument('--root-review',required=True)
    p.add_argument('--ROOT-REVIEWED-COMPLETE-P161-SCIENCE',dest='ROOT_REVIEWED_COMPLETE_P161_SCIENCE',action='store_true');p.add_argument('--child',action='store_true')
    args=p.parse_args();return child(args)if args.child else parent(args)

if __name__=='__main__':raise SystemExit(main())
