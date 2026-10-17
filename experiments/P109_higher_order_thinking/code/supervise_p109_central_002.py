"""P109 unchanged external limits; explicit auditor002 lexical-repair selection after audit001 failure."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,sys,time
import psutil
R=Path(__file__).resolve().parents[1]
P=R/'papers/P109_higher_order_thinking'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=['run','audit'],required=True)
 a.add_argument('--authorization',required=True);a.add_argument('--operation',required=True)
 a.add_argument('--audit-output');args=a.parse_args()
 authp=Path(args.authorization);auth=json.loads(authp.read_text(encoding='utf-8'))
 fx=P/'RUN_FREEZE_001.json';freeze=json.loads(fx.read_text(encoding='utf-8'))
 assert auth.get('approved_by')=='root' and auth['freeze_sha256']==sha(fx)
 if args.phase=='run':
  assert auth['execution_authorized'] is True
  cmd=[sys.executable,str(R/'scripts/run_p109_central_001.py')];budget=600.
 else:
  assert auth['approved'] is True and auth['run_id']=='P109-central-001'
  assert args.audit_output and not (P/args.audit_output).exists()
  cmd=[sys.executable,str(R/'scripts/audit_p109_central_002.py'),'--runner-result',str(P/'runs/P109-central-001/result.json'),'--output-dir',str(P/args.audit_output),'--authorization',str(authp)]
  budget=float(auth['aggregate_remaining_seconds']);assert 0<budget<=600
  assert sha(R/'scripts/audit_p109_central_002.py')==auth['auditor_sha256']
 op=P/'operations'/args.operation;assert op.resolve().is_relative_to(P.resolve()) and not op.exists()
 op.mkdir(parents=True)
 def save(name,v):(op/name).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 pre={'phase':args.phase,'authorization_sha256':sha(authp),'freeze_sha256':sha(fx),'preflight_started_utc':utc(),'automatic_restart':False}
 save('PREFLIGHT.json',pre)
 for key,value in freeze['sha256'].items():
  assert sha(R/key)==value,'Frozen file mismatch:'+key
 pre.update(preflight_finished_utc=utc(),verified_files=len(freeze['sha256']))
 save('PREFLIGHT.json',pre)
 minimum=psutil.virtual_memory().available;initial_available=minimum;free=shutil.disk_usage(R).free
 if minimum<1024**3 or free<35*1024**3:
  save('SUPERVISOR.json',dict(pre,status='prelaunch_resource_stop',available_ram_bytes=minimum,free_disk_bytes=free,actual_subprocess_exit=None,numerical_launch=False))
  return 77
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MPLBACKEND='Agg')
 start=time.monotonic();begun=utc();samples=0;maxrss=0;maxpeak=0;minfree=free;identity={};reason=None
 with (op/'stdout.txt').open('w',encoding='utf-8') as out,(op/'stderr.txt').open('w',encoding='utf-8') as err,(op/'resources.jsonl').open('w',encoding='utf-8') as log:
  proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=out,stderr=err)
  p=psutil.Process(proc.pid)
  try:p.cpu_affinity([0]);identity={'pid':p.pid,'create_time_epoch':p.create_time(),'name':p.name()}
  except psutil.NoSuchProcess:identity={'pid':proc.pid,'creation_identity_not_observed':True}
  try:
   while proc.poll() is None:
    current=psutil.virtual_memory().available;disk=shutil.disk_usage(R).free;rss=0;peak=0;children=[]
    try:
     children=[p]+p.children(recursive=True)
     for child in children:
      try:
       mem=child.memory_info();rss+=mem.rss;peak+=getattr(mem,'peak_wset',mem.rss)
      except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    except psutil.NoSuchProcess:pass
    samples+=1;maxrss=max(maxrss,rss);maxpeak=max(maxpeak,peak);minimum=min(minimum,current);minfree=min(minfree,disk)
    row={'utc':utc(),'elapsed_seconds':time.monotonic()-start,'tree_rss_bytes':rss,'tree_peak_wset_sum_bytes':peak,'available_ram_bytes':current,'disk_free_bytes':disk}
    log.write(json.dumps(row)+'\n');log.flush()
    if current<1024**3:reason='available_ram_floor'
    elif rss>1024**3 or peak>1024**3:reason='process_tree_rss_or_peak_cap'
    elif disk<35*1024**3:reason='free_disk_floor'
    elif row['elapsed_seconds']>budget:reason='aggregate_wall_budget'
    if reason:
     for child in reversed(children):
      try:child.terminate()
      except (psutil.NoSuchProcess,psutil.AccessDenied):pass
     if proc.poll() is None:proc.terminate()
     break
    time.sleep(.05)
   try:code=proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();code=proc.wait(timeout=10);reason=reason or 'termination_timeout'
  except BaseException as exc:
   if proc.poll() is None:proc.terminate()
   code=proc.wait(timeout=10);reason='supervisor_exception:'+repr(exc)
 identity_absent=False
 try:
  old=psutil.Process(proc.pid)
  identity_absent=bool(identity.get('create_time_epoch') and old.create_time()!=identity['create_time_epoch'])
 except psutil.NoSuchProcess:identity_absent=True
 result=dict(pre,launched_at_utc=begun,finished_at_utc=utc(),command=cmd,identity=identity,
 actual_subprocess_exit=code,original_identity_absent=identity_absent,
 wall_seconds=time.monotonic()-start,available_ram_initial_bytes=initial_available,
 minimum_available_ram_bytes=minimum,minimum_free_disk_bytes=minfree,
 maximum_tree_rss_bytes=maxrss,maximum_observed_OS_peak_wset_sum_bytes=maxpeak,samples=samples,
 budget_seconds=budget,status='resource_stop' if reason else 'completed',resource_stop_reason=reason,
 counted_success=False,numerical_launch=True)
 save('SUPERVISOR.json',result)
 manifest=[{'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(op.iterdir()) if f.is_file()]
 save('OPERATION_MANIFEST.json',manifest)
 print(json.dumps(result),flush=True)
 return 77 if reason else code
if __name__=='__main__':sys.exit(main())
