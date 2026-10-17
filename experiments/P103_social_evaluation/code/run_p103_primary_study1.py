"""Prospective complete P103 original-primary Study 1 reproduction. No GPU."""
import os
for _k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[_k]="1"
import time
PROCESS_STARTED=time.monotonic()
from pathlib import Path
import sys,json,time,hashlib,csv,datetime,traceback
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import psutil
from threadpoolctl import threadpool_limits
threadpool_limits(1)
sys.stdout.reconfigure(encoding="utf8")
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"papers/P103_social_evaluation"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+"\n",encoding="utf8")
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def analyze(out):
    started=PROCESS_STARTED
    resource=[]
    proc=psutil.Process()
    def guard(phase):
        m={"utc":now(),"phase":phase,"elapsed_seconds":time.monotonic()-started,"rss_GiB":proc.memory_info().rss/2**30,"available_RAM_GiB":psutil.virtual_memory().available/2**30,"free_disk_GiB":psutil.disk_usage(str(ROOT)).free/2**30}
        resource.append(m)
        save(out/"resource_measurements.json",resource)
        if m["rss_GiB"]>1 or m["available_RAM_GiB"]<1 or m["free_disk_GiB"]<35 or m["elapsed_seconds"]>600:
            raise RuntimeError("Frozen resource guard breached: "+json.dumps(m))
    guard("after_imports_before_inputs")
    pre=json.loads((PAPER/"PREREGISTRATION.json").read_text(encoding="utf8"))
    proposal=json.loads((PAPER/pre["proposal"]["name"]).read_text(encoding="utf8"))
    freeze=json.loads((PAPER/"INPUT_RUNTIME_FREEZE_20261010.json").read_text(encoding="utf8"))
    assert sha(PAPER/pre["proposal"]["name"])==pre["proposal"]["sha256"]
    for row in freeze["immutable_files"]:
        assert sha(ROOT/row["path"])==row["sha256"],row["path"]
    assert sys.version==freeze["python_version"]
    assert scipy.__version__==freeze["versions"]["scipy"]
    assert np.__version__==freeze["versions"]["numpy"]
    assert pd.__version__==freeze["versions"]["pandas"]
    inputs={Path(x["path"]).name:ROOT/x["path"] for x in proposal["exact_inputs"]}
    raw=pd.read_csv(inputs["data_study1.csv"],dtype=str).iloc[2:].reset_index(drop=True)
    comps=proposal["composites"]
    items=[c for v in comps.values() for c in v]
    x=raw[items].apply(pd.to_numeric,errors="raise")
    assert len(raw)==500 and not x.isna().any().any()
    assert ((x>=1)&(x<=7)).all().all()
    duration=pd.to_numeric(raw["Duration (in seconds)"],errors="raise")
    slow=duration>=30
    straight=x.std(axis=1,ddof=1)==0
    keep=slow&~straight
    assert int((~slow).sum())==0 and int(straight.sum())==3 and int(keep.sum())==497
    condition=np.where(raw["Assessment_DO"].str.contains("dash",case=False,regex=False),"dashboard","AI")
    assert set(condition)=={"dashboard","AI"}
    v=pd.DataFrame({name:x[columns].mean(axis=1) for name,columns in comps.items()})
    case=[]
    for i in range(len(raw)):
        r={"source_record_ordinal":i+1,"source_ResponseId_sha256":hashlib.sha256(str(raw.loc[i,"ResponseId"]).encode()).hexdigest(),"condition":str(condition[i]),"duration_seconds":float(duration.iloc[i]),"straightliner":bool(straight.iloc[i]),"under_30_seconds":bool(not slow.iloc[i]),"included":bool(keep.iloc[i]),"items":{c:float(x.loc[i,c]) for c in items},"composites":{c:float(v.loc[i,c]) for c in comps}}
        case.append(r)
        if i%50==0:guard("main_raw_records_"+str(i))
    save(out/"main_raw_derived_records.json",case)
    guard("before_primary_statistics")
    results={};metrics={}
    for name,cols in comps.items():
        a=v.loc[keep&(condition=="AI"),name].to_numpy()
        b=v.loc[keep&(condition=="dashboard"),name].to_numpy()
        na,nb=len(a),len(b)
        ma,mb=a.mean(),b.mean();sa,sb=a.std(ddof=1),b.std(ddof=1)
        tt=stats.ttest_ind(a,b,equal_var=False,alternative="two-sided")
        va,vb=sa*sa/na,sb*sb/nb
        df=(va+vb)**2/(va*va/(na-1)+vb*vb/(nb-1))
        diff=ma-mb;half=stats.t.ppf(.975,df)*np.sqrt(va+vb)
        sp=np.sqrt(((na-1)*sa*sa+(nb-1)*sb*sb)/(na+nb-2))
        d=diff/sp
        sed=np.sqrt((na+nb)/(na*nb)+d*d/(2*(na+nb-2)))
        dh=stats.t.ppf(.975,na+nb-2)*sed
        xx=x.loc[keep,cols].to_numpy()
        alpha=len(cols)/(len(cols)-1)*(1-xx.var(axis=0,ddof=1).sum()/xx.sum(axis=1).var(ddof=1))
        r={"n_AI":na,"n_dashboard":nb,"mean_AI":float(ma),"sd_AI":float(sa),"mean_dashboard":float(mb),"sd_dashboard":float(sb),"signed_t":float(tt.statistic),"abs_t":float(abs(tt.statistic)),"welch_df":float(df),"p":float(tt.pvalue),"mean_difference":float(diff),"mean_difference_ci_low":float(diff-half),"mean_difference_ci_high":float(diff+half),"d":float(d),"d_ci_low":float(d-dh),"d_ci_high":float(d+dh),"raw_alpha":float(alpha)}
        results[name]=r
        metrics.update({name+"."+k:value for k,value in r.items()})
        guard("primary_"+name)
    order=["AI_tool","laziness","competence","diligence","replaceability","manager_disclosure","colleague_disclosure"]
    cv=v.loc[keep].copy()
    cv["AI_tool"]=(condition[keep]=="AI").astype(float)
    cm=cv[order].corr(method="pearson")
    correlations={}
    for i in range(1,len(order)):
        for k in range(i):
            key="pearson."+order[i]+"."+order[k]
            metrics[key]=float(cm.iloc[i,k]);correlations[key]=metrics[key]
    age=pd.to_numeric(raw.loc[keep,"age"],errors="raise")
    gender=pd.to_numeric(raw.loc[keep,"gender"],errors="raise")
    edu=pd.to_numeric(raw.loc[keep,"education"],errors="raise")
    metrics.update({"raw_n":len(raw),"final_n":int(keep.sum()),"straightliners_n":int(straight.sum()),"under_30_seconds_n":int((~slow).sum()),"age_mean":float(age.mean()),"male_percentage":float((gender==1).mean()*100),"bachelors_or_higher_percentage":float((edu>=4).mean()*100)})
    guard("before_MC1")
    mc=pd.read_csv(inputs["Study 1 Post-Hoc Manipulation Check.csv"],dtype=str).iloc[2:].reset_index(drop=True)
    assert len(mc)==201
    branch=mc["Assessment_DO"]
    expected={"self_dash_auth|scales","self_genai_auth|scales"}
    assert set(branch)==expected
    q89=pd.to_numeric(mc["Q89"],errors="raise")
    assert not q89.isna().any()
    correct=((q89==1)&(branch=="self_dash_auth|scales"))|((q89==2)&(branch=="self_genai_auth|scales"))
    metrics["MC1_n"]=len(mc);metrics["MC1_correct_percentage"]=float(correct.mean()*100)
    mcrows=[{"source_record_ordinal":i+1,"branch":str(branch.iloc[i]),"Q89":int(q89.iloc[i]),"Q88":None if pd.isna(mc.loc[i,"Q88"]) else str(mc.loc[i,"Q88"]),"correct":bool(correct.iloc[i])} for i in range(len(mc))]
    save(out/"MC1_raw_derived_records.json",mcrows)
    z=stats.norm.ppf(.975);n=len(mc);ph=correct.mean()
    center=(ph+z*z/(2*n))/(1+z*z/n)
    half=z*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/(1+z*z/n)
    mcsupport={"correct_count":int(correct.sum()),"Wilson95_supporting_only":[float(center-half),float(center+half)],"condition_counts":{},"Q88_correct_dashboard_counts":mc.loc[correct&(branch=="self_dash_auth|scales"),"Q88"].value_counts(dropna=False).astype(int).to_dict()}
    mcsupport["Q88_correct_dashboard_counts"]={str(k):int(val) for k,val in mcsupport["Q88_correct_dashboard_counts"].items()}
    for b in sorted(expected):
        sel=branch==b
        mcsupport["condition_counts"][b]={"n":int(sel.sum()),"correct":int(correct[sel].sum()),"percentage":float(correct[sel].mean()*100)}
    gates=[]
    for target in proposal["targets"]:
        got=metrics[target["id"]]
        if "absolute_tolerance" in target:passed=abs(got-target["target"])<=target["absolute_tolerance"]
        elif target["target"]=="<.001":passed=got<.001
        else:passed=abs(got-target["target"])<=.000500001
        gates.append({"id":target["id"],"target":target["target"],"observed":got,"passed":bool(passed),"criterion":target})
    assert len(gates)==108
    save(out/"analysis.json",{"primary":results,"correlations":correlations,"all_metrics":metrics,"MC1_supporting":mcsupport,"omissions":proposal["omissions"],"source_discrepancies":proposal["source_discrepancies"],"invalid_records":0})
    save(out/"published_target_gates.json",{"mandatory":108,"passed":sum(r["passed"] for r in gates),"all_passed":all(r["passed"] for r in gates),"gates":gates})
    guard("completed")
    return {"target_gates_passed":sum(r["passed"] for r in gates),"target_gates_total":108,"invalid_records":0}
def main():
    assert len(sys.argv)==3 and sys.argv[1]=="--run"
    out=Path(sys.argv[2]).resolve()
    assert out.parent==(PAPER/"runs").resolve()
    out.mkdir(parents=True,exist_ok=False)
    status={"command":sys.argv,"utc_start":now(),"mode":"complete original primary Study1/MC1","GPU":False,"randomness":False}
    code=1
    try:
        status.update(analyze(out));code=0
    except BaseException as exc:
        status["exception_type"]=type(exc).__name__;status["exception"]=str(exc)
        (out/"failure_traceback.txt").write_text(traceback.format_exc(),encoding="utf8")
    finally:
        status["utc_end"]=now();status["exit_status"]=code
        save(out/"run_status.json",status)
        manifest=[{"path":f.name,"bytes":f.stat().st_size,"sha256":sha(f)} for f in sorted(out.iterdir()) if f.is_file()]
        save(out/"RESULT_MANIFEST.json",manifest)
    print(json.dumps(status,ensure_ascii=True));sys.exit(code)
if __name__=="__main__":main()
