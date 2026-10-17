"""Bound only the explicitly selected P103 analysis/audit subprocess."""
from pathlib import Path
import os,sys,time,json,datetime,subprocess,hashlib
import psutil
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"papers/P103_social_evaluation"
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2,allow_nan=False)+"\n",encoding="utf8")
def main():
    assert len(sys.argv) in (4,5)
    mode=sys.argv[1];assert mode in ("--run","--audit")
    if mode=="--run":
        assert len(sys.argv)==4
        label=sys.argv[2];oplabel=sys.argv[3]
        result=PAPER/"runs"/label
        args=[sys.executable,str(ROOT/"scripts/run_p103_primary_study1.py"),"--run",str(result)]
    else:
        assert len(sys.argv)==5
        label=sys.argv[2];auditlabel=sys.argv[3];oplabel=sys.argv[4]
        result=PAPER/"audits"/auditlabel
        args=[sys.executable,str(ROOT/"scripts/audit_p103_primary_study1_age_fix_v003.py"),"--audit",str(PAPER/"runs"/label),str(result)]
    assert all("/" not in s and "\\" not in s and s not in (".","..") for s in sys.argv[2:])
    op=PAPER/"operations"/oplabel;op.mkdir(parents=True,exist_ok=False)
    assert not result.exists()
    before={"available_RAM_GiB":psutil.virtual_memory().available/2**30,"free_disk_GiB":psutil.disk_usage(str(ROOT)).free/2**30}
    status={"utc_start":now(),"command":args,"mode":mode,"result_directory":str(result),"before_launch":before,"statistical_changes":False,"resource_policy":{"single_computation_thread":True,"RSS_GiB":1,"available_RAM_floor_GiB":1,"free_disk_floor_GiB":35,"wall_seconds":600}}
    if before["available_RAM_GiB"]<1 or before["free_disk_GiB"]<35:
        status.update({"exit_status":97,"stop_reason":"Pre-launch resource guard","utc_end":now()});save(op/"SUPERVISOR.json",status);print(json.dumps(status));return 97
    env=os.environ.copy()
    for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):env[k]="1"
    start=time.monotonic();samples=[];breach=None
    with (op/"stdout.txt").open("w",encoding="utf8") as stdout,(op/"stderr.txt").open("w",encoding="utf8") as stderr:
        child=subprocess.Popen(args,cwd=str(ROOT),env=env,stdout=stdout,stderr=stderr)
        status["PID"]=child.pid
        proc=psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss=proc.memory_info().rss
                kids=proc.children(recursive=True)
                rss+=sum(p.memory_info().rss for p in kids if p.is_running())
            except psutil.NoSuchProcess:break
            m={"utc":now(),"elapsed_seconds":time.monotonic()-start,"process_tree_RSS_GiB":rss/2**30,"available_RAM_GiB":psutil.virtual_memory().available/2**30,"free_disk_GiB":psutil.disk_usage(str(ROOT)).free/2**30}
            samples.append(m)
            if m["process_tree_RSS_GiB"]>1 or m["available_RAM_GiB"]<1 or m["free_disk_GiB"]<35 or m["elapsed_seconds"]>600:
                breach=m
                for kid in reversed(kids):
                    try:kid.terminate()
                    except psutil.NoSuchProcess:pass
                try:proc.terminate()
                except psutil.NoSuchProcess:pass
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:child.kill()
                break
            time.sleep(.05)
        code=child.wait()
    status.update({"utc_end":now(),"exit_status":code,"wall_seconds":time.monotonic()-start,"resource_breach":breach,"resource_samples":samples})
    save(op/"SUPERVISOR.json",status)
    save(op/"OPERATION_MANIFEST.json",[{"path":f.name,"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(op.iterdir()) if f.is_file()])
    print(json.dumps({k:v for k,v in status.items() if k!="resource_samples"}))
    return 97 if breach else code
if __name__=="__main__":sys.exit(main())
