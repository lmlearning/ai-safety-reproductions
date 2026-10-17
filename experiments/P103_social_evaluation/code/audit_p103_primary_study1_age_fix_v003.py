"""Independent raw-CSV/formula audit of complete original P103 Study 1."""
import os
for _k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[_k]="1"
import time
PROCESS_STARTED=time.monotonic()
from pathlib import Path
import json,sys,csv,math,statistics,hashlib,datetime,traceback
import scipy
from scipy import special
import psutil
from threadpoolctl import threadpool_limits
threadpool_limits(1)
sys.stdout.reconfigure(encoding="utf8")
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"papers/P103_social_evaluation"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2,allow_nan=False)+"\n",encoding="utf8")
def mean_available_ages(rows):
    """Original Study1.Rmd line103 na.rm=TRUE: blank exported ages omitted only from age mean."""
    return statistics.mean(float(row["age"]) for row in rows if row["age"] != "")

def audit(run,out):
    readings=[];checks=[];proc=psutil.Process()
    def check(id,passed,details=None):
        checks.append({"id":id,"passed":bool(passed),"details":details})
    def close(id,a,b):
        passed=isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-10
        check(id,passed,{"independent":a,"runner":b,"absolute_tolerance":1e-10})
    def guard(phase):
        m={"utc":now(),"phase":phase,"elapsed_seconds":time.monotonic()-PROCESS_STARTED,"rss_GiB":proc.memory_info().rss/2**30,"available_RAM_GiB":psutil.virtual_memory().available/2**30,"free_disk_GiB":psutil.disk_usage(str(ROOT)).free/2**30}
        readings.append(m);save(out/"resource_measurements.json",readings)
        if m["rss_GiB"]>1 or m["available_RAM_GiB"]<1 or m["free_disk_GiB"]<35 or m["elapsed_seconds"]>600:raise RuntimeError("Frozen audit resource guard breached: "+json.dumps(m))
    guard("after_imports")
    prereg=json.loads((PAPER/"PREREGISTRATION.json").read_text(encoding="utf8"))
    proposal=json.loads((PAPER/prereg["proposal"]["name"]).read_text(encoding="utf8"))
    freeze=json.loads((PAPER/"INPUT_RUNTIME_FREEZE_20261010.json").read_text(encoding="utf8"))
    for f in freeze["immutable_files"]:check("input_or_code_hash."+f["path"],sha(ROOT/f["path"])==f["sha256"])
    amendment=json.loads((PAPER/"AUDIT003_INPUT_CODE_AMENDMENT_FREEZE_20261010.json").read_text(encoding="utf8"))
    for f in amendment["immutable_files"]:check("auditor003_amendment_hash."+f["path"],sha(ROOT/f["path"])==f["sha256"])
    check("python_version",sys.version==freeze["python_version"])
    check("scipy_version",scipy.__version__==freeze["versions"]["scipy"])
    assert all(r["passed"] for r in checks),"Frozen input/code/runtime mismatch before audit numerics"
    for f in json.loads((run/"RESULT_MANIFEST.json").read_text(encoding="utf8")):check("runner_output_hash."+f["path"],sha(run/f["path"])==f["sha256"])
    assert all(r["passed"] for r in checks),"Runner output hash mismatch before audit numerics"
    inputs={Path(f["path"]).name:ROOT/f["path"] for f in proposal["exact_inputs"]}
    with inputs["data_study1.csv"].open(encoding="utf-8-sig",newline="") as f:raw=list(csv.DictReader(f))[2:]
    check("main_raw_n_500",len(raw)==500)
    composites=proposal["composites"]
    items=[c for v in composites.values() for c in v]
    records=[];kept=[];fast=0;straight=0
    for i,row in enumerate(raw):
        vals={c:float(row[c]) for c in items}
        check("raw_item_valid."+str(i),all(1<=v<=7 and math.isfinite(v) for v in vals.values()))
        ss=len(set(vals.values()))==1
        ff=float(row["Duration (in seconds)"])<30
        fast+=ff;straight+=ss
        keep=not ss and not ff
        condition="dashboard" if "dash" in row["Assessment_DO"].lower() else "AI"
        cm={c:sum(vals[k] for k in cols)/len(cols) for c,cols in composites.items()}
        r={"source_record_ordinal":i+1,"source_ResponseId_sha256":hashlib.sha256(row["ResponseId"].encode()).hexdigest(),"condition":condition,"duration_seconds":float(row["Duration (in seconds)"]),"straightliner":ss,"under_30_seconds":ff,"included":keep,"items":vals,"composites":cm}
        records.append(r)
        if keep:kept.append((row,r))
        if i%50==0:guard("main_csv_"+str(i))
    check("main_final_n_497",len(kept)==497);check("main_fast_zero",fast==0);check("main_straight_three",straight==3)
    save(out/"independent_main_records.json",records)
    observed={}
    for name,cols in composites.items():
        aa=[r["composites"][name] for _,r in kept if r["condition"]=="AI"]
        bb=[r["composites"][name] for _,r in kept if r["condition"]=="dashboard"]
        n,m=len(aa),len(bb);a,b=statistics.mean(aa),statistics.mean(bb)
        va,vb=statistics.variance(aa),statistics.variance(bb)
        s=math.sqrt(va/n+vb/m)
        df=(va/n+vb/m)**2/((va/n)**2/(n-1)+(vb/m)**2/(m-1))
        t=(a-b)/s;p=2*special.stdtr(df,-abs(t))
        half=special.stdtrit(df,.975)*s
        d=(a-b)/math.sqrt(((n-1)*va+(m-1)*vb)/(n+m-2))
        halfd=special.stdtrit(n+m-2,.975)*math.sqrt((n+m)/(n*m)+d*d/(2*(n+m-2)))
        summed=[sum(r["items"][c] for c in cols) for _,r in kept]
        alpha=len(cols)/(len(cols)-1)*(1-sum(statistics.variance([r["items"][c] for _,r in kept]) for c in cols)/statistics.variance(summed))
        for key,value in {"n_AI":n,"n_dashboard":m,"mean_AI":a,"sd_AI":math.sqrt(va),"mean_dashboard":b,"sd_dashboard":math.sqrt(vb),"signed_t":t,"abs_t":abs(t),"welch_df":df,"p":p,"mean_difference":a-b,"mean_difference_ci_low":a-b-half,"mean_difference_ci_high":a-b+half,"d":d,"d_ci_low":d-halfd,"d_ci_high":d+halfd,"raw_alpha":alpha}.items():observed[name+"."+key]=float(value)
        guard("independent_"+name)
    order=["AI_tool","laziness","competence","diligence","replaceability","manager_disclosure","colleague_disclosure"]
    series={c:[int(r["condition"]=="AI") if c=="AI_tool" else r["composites"][c] for _,r in kept] for c in order}
    for i in range(1,len(order)):
        for k in range(i):
            xx,yy=series[order[i]],series[order[k]]
            mx,my=statistics.mean(xx),statistics.mean(yy)
            cov=sum((a-mx)*(b-my) for a,b in zip(xx,yy))
            den=math.sqrt(sum((a-mx)**2 for a in xx)*sum((b-my)**2 for b in yy))
            observed["pearson."+order[i]+"."+order[k]]=cov/den
    age_missing=[{"source_record_ordinal":r["source_record_ordinal"],"source_ResponseId_sha256":r["source_ResponseId_sha256"]} for row,r in kept if row["age"] == ""]
    age_census={"retained_rating_participants":len(kept),"available_age_n":sum(row["age"] != "" for row,_ in kept),"missing_age_n":len(age_missing),"missing_age_records":age_missing,"all_rating_participants_retained":True,"method":"Original R mean(age, na.rm=TRUE); omit only blank exported ages from demographic mean"}
    save(out/"age_missingness_census.json",age_census)
    expected_census=json.loads((PAPER/"AUDIT003_ORIGINAL_DEMOGRAPHIC_MISSINGNESS_CENSUS_20261010.json").read_text(encoding="utf8"))
    check("age_missingness_census",age_census["available_age_n"]==expected_census["fields"]["age"]["retained_available_n"] and age_census["missing_age_n"]==expected_census["fields"]["age"]["retained_missing_n"] and age_missing==[{"source_record_ordinal":r["source_record_ordinal"],"source_ResponseId_sha256":r["source_ResponseId_sha256"]} for r in expected_census["fields"]["age"]["missing_records"] if r["retained_for_all_rating_metrics"]])
    observed.update({"raw_n":len(raw),"final_n":len(kept),"under_30_seconds_n":fast,"straightliners_n":straight,"age_mean":mean_available_ages(row for row,_ in kept),"male_percentage":sum(float(row["gender"])==1 for row,_ in kept)*100/len(kept),"bachelors_or_higher_percentage":sum(float(row["education"])>=4 for row,_ in kept)*100/len(kept)})
    with inputs["Study 1 Post-Hoc Manipulation Check.csv"].open(encoding="utf-8-sig",newline="") as f:mc=list(csv.DictReader(f))[2:]
    mcr=[]
    expected={"self_dash_auth|scales","self_genai_auth|scales"}
    check("MC1_exact_branch_strings",set(r["Assessment_DO"] for r in mc)==expected)
    for i,row in enumerate(mc):
        q=int(row["Q89"]);branch=row["Assessment_DO"]
        ok=(branch=="self_dash_auth|scales" and q==1) or (branch=="self_genai_auth|scales" and q==2)
        mcr.append({"source_record_ordinal":i+1,"branch":branch,"Q89":q,"Q88":row["Q88"] if row["Q88"] else None,"correct":ok})
    observed["MC1_n"]=len(mc);observed["MC1_correct_percentage"]=sum(r["correct"] for r in mcr)*100/len(mc)
    save(out/"independent_MC1_records.json",mcr)
    save(out/"independent_metrics.json",observed)
    guard("before_reading_runner_numerics")
    rr=json.loads((run/"main_raw_derived_records.json").read_text(encoding="utf8"))
    check("runner_main_records_length",len(rr)==len(records))
    for i,(a,b) in enumerate(zip(records,rr)):check("all_raw_and_derived_main_fields."+str(i+1),a==b)
    rm=json.loads((run/"MC1_raw_derived_records.json").read_text(encoding="utf8"))
    check("runner_MC1_records_length",len(rm)==len(mcr))
    for i,(a,b) in enumerate(zip(mcr,rm)):check("all_raw_and_derived_MC1_fields."+str(i+1),a==b)
    analysis=json.loads((run/"analysis.json").read_text(encoding="utf8"))
    check("zero_invalid_runner",analysis["invalid_records"]==0)
    for key,value in observed.items():close("independent_numeric."+key,value,analysis["all_metrics"].get(key))
    gates=json.loads((run/"published_target_gates.json").read_text(encoding="utf8"))
    check("mandatory_gate_count",gates["mandatory"]==108 and len(gates["gates"])==108)
    for target,rg in zip(proposal["targets"],gates["gates"]):
        got=observed[target["id"]]
        if "absolute_tolerance" in target:passed=abs(got-target["target"])<=target["absolute_tolerance"]
        elif target["target"]=="<.001":passed=got<.001
        else:passed=abs(got-target["target"])<=.000500001
        check("independent_published_target."+target["id"],passed,{"observed":got,"fixed_target":target})
        check("runner_gate_exact_definition."+target["id"],rg["criterion"]==target and rg["id"]==target["id"] and rg["passed"]==bool(passed))
    guard("completed")
    save(out/"AUDIT.json",{"checks_total":len(checks),"checks_passed":sum(r["passed"] for r in checks),"all_passed":all(r["passed"] for r in checks),"checks":checks,"source_target_failures":[r for r in checks if r["id"].startswith("independent_published_target") and not r["passed"]]})
    return {"checks_total":len(checks),"checks_passed":sum(r["passed"] for r in checks),"all_passed":all(r["passed"] for r in checks)}
def main():
    assert len(sys.argv)==4 and sys.argv[1]=="--audit"
    run=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve()
    assert run.parent==(PAPER/"runs").resolve() and out.parent==(PAPER/"audits").resolve()
    out.mkdir(parents=True,exist_ok=False)
    status={"utc_start":now(),"command":sys.argv,"mode":"independent raw CSV/formula audit","GPU":False}
    code=1
    try:status.update(audit(run,out));code=0
    except BaseException as exc:
        status["exception_type"]=type(exc).__name__;status["exception"]=str(exc)
        (out/"failure_traceback.txt").write_text(traceback.format_exc(),encoding="utf8")
    finally:
        status["utc_end"]=now();status["exit_status"]=code;save(out/"audit_status.json",status)
        save(out/"AUDIT_MANIFEST.json",[{"path":f.name,"bytes":f.stat().st_size,"sha256":sha(f)} for f in sorted(out.iterdir()) if f.is_file()])
    print(json.dumps(status,ensure_ascii=True));sys.exit(code)
if __name__=="__main__":main()
