"""P156: one ROOT-admitted offline primary/independent complete reduction.

Definition-only without an explicit matching ROOT grant. No historical process
roster, DLL inventory, model generation, API request or engineering fixture.
"""
from pathlib import Path
import ctypes,datetime as dt,hashlib,importlib.util,json,os,shutil,subprocess,sys,time,traceback

GIB=1024**3
FLAGS=['execution_authorized','ROOT_source_and_criteria_reviewed','complete_original_transparency_reduction_authorized','parent_deadline_resources_output_enforced']

def utc():return dt.datetime.now(dt.timezone.utc)
def pin(path):
 p=Path(path).absolute()
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def verify(ref):
 if pin(ref['path'])!=ref:raise ValueError(('Whole source/input pin changed',ref['path']))
 return Path(ref['path'])
def load(ref):return json.loads(verify(ref).read_bytes())
def save(path,value):
 with Path(path).open('x',encoding='utf-8',newline='\n')as f:json.dump(value,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
 return pin(path)
def no_reparse(path):
 p=Path(path).absolute()
 for q in (p,*p.parents):
  if q.exists()and(q.is_symlink()or getattr(q.lstat(),'st_file_attributes',0)&1024):raise ValueError(('Reparse path refused',str(q)))
def output_size(roots,outside=()):
 total=0
 for root in roots:
  no_reparse(root)
  for parent,dirs,files in os.walk(root,followlinks=False):
   for name in dirs+files:no_reparse(Path(parent)/name)
   for name in files:total+=(Path(parent)/name).stat().st_size
 for p in outside:total+=Path(p).stat().st_size
 return total
def module(ref,name):
 spec=importlib.util.spec_from_file_location(name,verify(ref));obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
 return obj

class Counters(ctypes.Structure):
 _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t),('PrivateUsage',ctypes.c_size_t)]
def memory_reader():
 k=ctypes.WinDLL('kernel32',use_last_error=True);fn=k.K32GetProcessMemoryInfo
 fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong];fn.restype=ctypes.c_int
 def read(handle):
  c=Counters();c.cb=ctypes.sizeof(c)
  if not fn(ctypes.c_void_p(int(handle)),ctypes.byref(c),c.cb):raise ctypes.WinError(ctypes.get_last_error())
  return {name:int(getattr(c,name))for name,_ in c._fields_}
 return read

def grant_check(cfg,grant_ref):
 g=load(grant_ref)
 if g.get('schema')!='ROOT_ONE_COMPLETE_P156_AI_AGENT_INDEX_CENTRAL032_GRANT' or any(g.get(k)is not True for k in ['execution_authorized','ROOT_current_source_and_scope_reviewed','one_complete_original_and_independent_run_authorized']):raise PermissionError('No explicit current ROOT authority')
 packet=load(g['current_source_packet_ref'])
 if packet['current_supervisor_ref']!=pin(__file__)or packet['current_False_control_ref']!=g['False_control_ref']:raise ValueError('Current whole supervisor/control joins')
 review=load(g['ROOT_current_source_review_ref'])
 if review.get('current_source_packet_ref')!=g['current_source_packet_ref']or review.get('ROOT_current_source_and_scope_reviewed')is not True:raise ValueError('Current whole ROOT source/scope review')
 if g.get('ROOT258_scope_decision_ref')!=cfg['ROOT258_scope_decision_ref']or g.get('eligibility030_ref')!=cfg['eligibility030_ref']:raise ValueError('Frozen full scope and original-wave eligibility')
 verify(cfg['ROOT258_scope_decision_ref']);verify(cfg['eligibility030_ref'])
 for key,value in [('inclusive_seconds',600),('work_seconds',580),('closure_seconds',20),('RSS_cap_bytes',GIB),('whole_output_cap_bytes',256*1024**2)]:
  if cfg['resource_proposal'].get(key)!=value or g.get(key)!=value:raise ValueError(('Exact prospective allocation',key))
 origin=dt.datetime.fromisoformat(g['UTC_origin']);deadline=dt.datetime.fromisoformat(g['UTC_deadline'])
 if origin.tzinfo is None or deadline.tzinfo is None or(deadline-origin).total_seconds()!=600:raise ValueError('Exact aware600s parent clock')
 return g,origin,deadline,deadline-dt.timedelta(seconds=20)

def child(cfg):
 if any(cfg.get(k)is not True for k in FLAGS):raise PermissionError('Inert source-only child')
 g,origin,deadline,work=grant_check(cfg,cfg['physical_grant_ref'])
 if utc()>=work:raise TimeoutError('Existing580s work deadline')
 for r in cfg['whole_source_refs']:verify(r)
 # The complete scientific sources use only stdlib local-file reductions.
 # Block networking and process spawning before either source is imported.
 import socket
 def forbidden(*args,**kwargs):raise PermissionError('Offline single-child study; networking/process spawning disabled')
 socket.socket=forbidden;socket.create_connection=forbidden;socket.getaddrinfo=forbidden
 subprocess.Popen=forbidden;os.system=forbidden;os.popen=forbidden
 for name in ['spawnl','spawnle','spawnlp','spawnlpe','spawnv','spawnve','spawnvp','spawnvpe','startfile']:
  if hasattr(os,name):setattr(os,name,forbidden)
 primary=module(cfg['primary_source_ref'],'p156_primary031')
 first=primary.primary_result(cfg)
 meta=Path(cfg['metadata_output_root'])
 save(meta/'COMPLETE_PRIMARY_INDEX032.json',first)
 if utc()>=work:raise TimeoutError('580s includes complete primary outputs')
 checker=module(cfg['independent_source_ref'],'p156_independent002')
 second=checker.run_complete_independent(cfg,first['result_ref'])
 if utc()>=work:raise TimeoutError('580s includes independent arrays/comparisons/output writes')
 summary=dict(schema='P156_COMPLETE_ORIGINAL_AND_INDEPENDENT_RESULT_INDEX032',primary=first,independent=second,complete_computation_returned=True,complete_central_numeric_candidate=first['all_primary_published_targets_passed']and second['all_complete_arrays_and_statuses_agree']and second['complete_central_numeric_candidate'],all_publication_claims_reproduced=False,FULL_reproduction_qualified=False,paper_credit=0,UTC=utc().isoformat())
 ref=save(meta/'COMPLETE_RESULT_INDEX032.json',summary)
 print(json.dumps(dict(computation_complete=True,result_index_ref=ref,paper_credit=0)),flush=True)

def supervise(control_ref,grant_ref):
 cfg=load(control_ref)
 if any(cfg.get(k)is not False for k in FLAGS)or cfg.get('absolute_deadline_UTC')is not None:raise ValueError('Frozen control must remain genuinelyFalse')
 g,origin,deadline,work=grant_check(cfg,grant_ref)
 if g['False_control_ref']!=control_ref:raise ValueError('Exact False-control pin')
 if not 0<=(utc()-origin).total_seconds()<90:raise ValueError('ROOT admission no older than90seconds')
 for r in cfg['whole_source_refs']:verify(r)
 workspace=Path(cfg['workspace_root']).resolve();root=Path(cfg['scientific_output_root']).absolute();meta=Path(cfg['metadata_output_root']).absolute()
 expected=workspace/'runs/P156_ai_agent_index_original001'
 if root!=expected or meta!=expected.with_name(expected.name+'_meta')or root.exists()or meta.exists():raise ValueError('Exclusive P156 original001 scientific and metadata roots')
 no_reparse(root);no_reparse(meta)
 # The primary owns creation of the scientific root. Parent creates metadata only.
 meta.mkdir(exist_ok=False);temporary=meta/'temporary';temporary.mkdir(exist_ok=False)
 true_cfg=json.loads(json.dumps(cfg));true_cfg.update({k:True for k in FLAGS})
 true_cfg.update(absolute_deadline_UTC=work.isoformat(),physical_grant_ref=grant_ref)
 true_ref=save(meta/'ACTUAL_TRUE_CHILD_CONTROL032.json',true_cfg)
 outside=tuple(dict.fromkeys([control_ref['path'],grant_ref['path']]))
 roots=(root,meta);read_memory=memory_reader();child_process=None;failure=None;actual_exit=None;final_native=None;handle_closed=None;sample_count=0;peak_union=0;peak_bound=0
 def observation():
  own=read_memory(-1);science=read_memory(child_process._handle)if child_process is not None else None
  size=output_size(roots,outside);free=shutil.disk_usage(workspace).free
  union=own['WorkingSetSize']+(science['WorkingSetSize']if science else 0)
  bound=own['PeakWorkingSetSize']+(science['PeakWorkingSetSize']if science else 0)
  return dict(UTC=utc().isoformat(),supervisor_memory=own,retained_direct_child_memory=science,sampled_current_parent_plus_direct_child_RSS=union,conservative_sum_of_parent_and_child_lifetime_RSS_peaks=bound,whole_owned_output_bytes=size,volume_free_bytes=free,required_unspent_output_plus64MiB_bytes=max(0,cfg['resource_proposal']['whole_output_cap_bytes']-size)+64*1024**2)
 def enforce(row,limit):
  if dt.datetime.fromisoformat(row['UTC'])>=limit:raise TimeoutError('Fixed parent work/inclusive deadline')
  if max(row['sampled_current_parent_plus_direct_child_RSS'],row['conservative_sum_of_parent_and_child_lifetime_RSS_peaks'])>GIB:raise MemoryError('1GiB parent+direct-child RSS bound')
  if row['whole_owned_output_bytes']>256*1024**2:raise OSError('256MiB complete owned output cap')
  if row['volume_free_bytes']<row['required_unspent_output_plus64MiB_bytes']:raise OSError('Unspent owned output reserve plus64MiB host margin unavailable')
 env={k:os.environ[k]for k in ['SystemRoot','WINDIR','COMSPEC']if k in os.environ}
 env.update(PATH=str(Path(cfg['python_ref']['path']).parent)+os.pathsep+str(Path(env.get('SystemRoot','C:/Windows'))/'System32'),PYTHONHASHSEED='0',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary))
 argv=[cfg['python_ref']['path'],'-I','-S','-B',str(Path(__file__).absolute()),'--worker',true_ref['path']]
 launch=utc().isoformat();stdout=(meta/'worker.stdout').open('xb');stderr=(meta/'worker.stderr').open('xb')
 try:
  enforce(observation(),work)
  child_process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,cwd=workspace,creationflags=subprocess.CREATE_NO_WINDOW)
  save(meta/'ACTUAL_LAUNCH032.json',dict(UTC_launch=launch,scientific_PID=child_process.pid,supervisor_PID=os.getpid(),argv=argv,selected_environment=env,python_ref=cfg['python_ref'],python_version=sys.version,physical_grant_ref=grant_ref,current_source_packet_ref=g['current_source_packet_ref'],current_control_ref=true_ref,ROOT258_scope_decision_ref=cfg['ROOT258_scope_decision_ref'],process_scope='One directly retained Python child; no Job or complete descendant accounting claimed; scientific code cannot spawn processes or connect to a network',native_birth='UNMEASURED'))
  with(meta/'ALL_RESOURCE_SAMPLES032.jsonl').open('x',encoding='utf-8',newline='\n')as journal:
   while True:
    row=observation();sample_count+=1;peak_union=max(peak_union,row['sampled_current_parent_plus_direct_child_RSS']);peak_bound=max(peak_bound,row['conservative_sum_of_parent_and_child_lifetime_RSS_peaks'])
    journal.write(json.dumps(row,ensure_ascii=True)+'\n');journal.flush()
    enforce(row,work)
    if child_process.poll()is not None:break
    time.sleep(.25)
 except BaseException as e:
  failure=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
  if child_process is not None and child_process.poll()is None:child_process.kill()
 finally:
  if child_process is not None:
   try:
    actual_exit=child_process.wait(timeout=max(.01,(deadline-utc()).total_seconds()))
    final_native=observation();enforce(final_native,work)
   except BaseException as e:failure=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),prior_failure=failure)
   finally:
    try:child_process._handle.Close();handle_closed=True
    except BaseException as e:handle_closed=False;failure=dict(type=type(e).__name__,message=str(e),scope='Close owned retained direct-child handle',prior_failure=failure)
  stdout.close();stderr.close()
 terminal=dict(schema='P156_ACTUAL_COMPLETE_LEAN_TERMINAL032',UTC_origin=origin.isoformat(),UTC_launch=launch,UTC_terminal=utc().isoformat(),work_cutoff_UTC=work.isoformat(),inclusive_deadline_UTC=deadline.isoformat(),supervisor_PID=os.getpid(),scientific_PID=child_process.pid if child_process else None,actual_child_wait_exit=actual_exit,actual_child_handle_closed=handle_closed,final_retained_native_observation=final_native,execution_failure=failure,resource_sample_count=sample_count,sampled_current_RSS_union_max=peak_union,conservative_lifetime_peak_sum_max=peak_bound,native_scope_note='Direct retained child only; no Job accounting or fresh-process absence claim. Native birth and separate supervisor exit unmeasured.',all_publication_claims_reproduced=False,FULL_reproduction_qualified=False,paper_credit=0)
 terminal_path=meta/'ACTUAL_COMPLETE_TERMINAL032.json';save(terminal_path,terminal)
 input_errors=[]
 for r in cfg['whole_source_refs']:
  try:verify(r)
  except BaseException as e:input_errors.append(dict(ref=r,type=type(e).__name__,message=str(e)))
 inventory=[]
 for owned in roots:
  no_reparse(owned)
  for p in sorted(owned.rglob('*')):
   no_reparse(p)
   if p.is_file():inventory.append(pin(p))
 inventory.extend(pin(p)for p in outside)
 result_path=meta/'COMPLETE_RESULT_INDEX032.json';result_index=json.loads(result_path.read_bytes())if result_path.exists()else None
 custody_path=meta/'WHOLE_OUTPUT_AND_INPUT_CUSTODY032.json'
 save(custody_path,dict(schema='P156_COMPLETE_CURRENT_OUTPUT_CUSTODY032',UTC=utc().isoformat(),all_output_refs=inventory,original_inputs_and_sources_unchanged=not input_errors,input_errors=input_errors,actual_child_wait_exit=actual_exit,execution_failure=failure,scientific_result_index_ref=pin(result_path)if result_index else None,paper_credit=0))
 # Logs are now closed and never appended after frozen hashing. Final observations
 # follow the terminal/custody whole hashes and are retained in a separate receipt.
 terminal_ref=pin(terminal_path);custody_ref=pin(custody_path)
 final_observation=observation()if child_process is None else dict(UTC=utc().isoformat(),supervisor_memory=read_memory(-1),whole_owned_output_bytes=output_size(roots,outside),volume_free_bytes=shutil.disk_usage(workspace).free)
 if child_process is not None:
  own=final_observation['supervisor_memory'];retained=final_native['retained_direct_child_memory']if final_native else None
  final_observation.update(sampled_current_parent_plus_direct_child_RSS=own['WorkingSetSize']+(retained['WorkingSetSize']if retained else 0),conservative_sum_of_parent_and_child_lifetime_RSS_peaks=own['PeakWorkingSetSize']+(retained['PeakWorkingSetSize']if retained else 0),required_unspent_output_plus64MiB_bytes=max(0,256*1024**2-final_observation['whole_owned_output_bytes'])+64*1024**2,child_memory_origin='Retained-handle terminal observation before actual handle close, not fresh after close')
 operational=actual_exit==0 and handle_closed is True and failure is None and not input_errors and result_index is not None
 final_failure=None
 try:enforce(final_observation,deadline)
 except BaseException as e:operational=False;final_failure=dict(type=type(e).__name__,message=str(e))
 final_ref=save(meta/'FINAL_POST_CUSTODY_OBSERVATION032.json',dict(schema='P156_FINAL_POST_CUSTODY_OBSERVATION032',terminal_ref=terminal_ref,whole_custody_ref=custody_ref,observation=final_observation,operational_complete=operational,final_enforcement_failure=final_failure,complete_central_numeric_candidate=bool(operational and result_index['complete_central_numeric_candidate']),supporting_caption_must_remain_reported=True,FULL_reproduction_qualified=False,paper_credit=0))
 # Include this final receipt and its hash in the actual final size/time checks.
 final_size=output_size(roots,outside);final_parent_memory=read_memory(-1);final_free=shutil.disk_usage(workspace).free;final_UTC=utc()
 child_peak=final_native['retained_direct_child_memory']['PeakWorkingSetSize']if final_native and final_native['retained_direct_child_memory']else 0
 last_checks=dict(inclusive_deadline=final_UTC<deadline,output_cap=final_size<=256*1024**2,parent_and_retained_child_peak_bound=final_parent_memory['PeakWorkingSetSize']+child_peak<=GIB,unspent_output_reserve=final_free>=max(0,256*1024**2-final_size)+64*1024**2)
 operational=operational and all(last_checks.values())
 print(json.dumps(dict(terminal_ref=terminal_ref,whole_custody_ref=custody_ref,final_post_ref=final_ref,final_owned_output_bytes=final_size,UTC_after_final_hash=final_UTC.isoformat(),last_parent_native_memory=final_parent_memory,last_volume_free_bytes=final_free,last_complete_enforcement_checks=last_checks,operational_complete=operational,complete_central_numeric_candidate=bool(operational and result_index['complete_central_numeric_candidate']),paper_credit=0)),flush=True)
 if not operational:raise RuntimeError('Complete current operational failure preserved')

def main():
 if len(sys.argv)==3 and sys.argv[1]=='--worker':child(json.loads(Path(sys.argv[2]).read_bytes()));return
 if len(sys.argv)!=3:raise SystemExit('Explicit frozenFalse control path and ROOT physical grant path required')
 supervise(pin(sys.argv[1]),pin(sys.argv[2]))
if __name__=='__main__':main()
