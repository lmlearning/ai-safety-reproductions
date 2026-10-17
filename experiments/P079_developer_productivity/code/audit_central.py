"""P079 independent raw-CSV QR/covariance/pooled bootstrap audit; no runner imports."""
import os
for k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):os.environ[k]="1"
import pathlib,sys,json,csv,hashlib,time,datetime,re,math
ROOT=pathlib.Path(__file__).resolve().parents[2];P=ROOT/"papers/P079_developer_productivity";RUN=ROOT/"runs/P079-central-001"
sys.path.insert(0,str(ROOT/"environment/p079_cpu_original_001/packages"))
import numpy as np,scipy.linalg as la,scipy.stats as st,psutil
OUT=ROOT/"audits"/sys.argv[1];OUT.mkdir(parents=True,exist_ok=False)
t0=time.perf_counter();c0=time.process_time();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda y:y.item() if isinstance(y,np.generic) else str(y))+"\n",encoding="utf-8")
C=[]
def check(name,a,b,tol=0):
 ok=bool(np.isfinite(a).all() and np.max(np.abs(np.asarray(a)-b),initial=0)<=tol) if isinstance(a,(np.ndarray,list)) else (bool(math.isfinite(a) and abs(a-b)<=tol) if isinstance(b,(float,int)) and not isinstance(b,bool) else a==b)
 C.append({"id":name,"passed":ok,"tolerance":tol,"actual":a.tolist() if isinstance(a,np.ndarray) else a,"expected":b.tolist() if isinstance(b,np.ndarray) else b})
plan=json.loads((P/"PREREGISTRATION.json").read_text());reference=json.loads((RUN/"all_statistics.json").read_text())
for m in [plan,json.loads((RUN/"RUN_MANIFEST.json").read_text())]:
 for f in m.get("inputs",m.get("files",[])):
  check("hash."+f["path"],hashfile(ROOT/f["path"]),f["sha256"]);check("size."+f["path"],(ROOT/f["path"]).stat().st_size,f["bytes"])
check("prereg_hash",hashfile(P/"PREREGISTRATION.json"),json.loads((RUN/"metrics.json").read_text())["preregistration_sha256"])
rows=list(csv.DictReader((P/"sources/data_complete.csv").open(encoding="utf-8")))
n=len(rows)
def col(k):return np.asarray([float(r[k]) if r[k] else np.nan for r in rows])
g=col("ai_treatment");dev=col("dev_id");pre=col("initial_implementation_time");post=col("post_review_implementation_time");forecast0=col("predicted_time_no_ai");forecast1=col("predicted_time_ai_allowed")
miss=~np.isfinite(post)
reviewmeans={t:math.fsum(post[(g==t)&~miss])/sum((g==t)&~miss) for t in [0,1]}
imputed=post.copy()
for t in [0,1]:imputed[(g==t)&miss]=reviewmeans[t]
timevalues=pre+imputed;y=np.log(timevalues);lnf=np.log(forecast0)
loaded=list(csv.DictReader((RUN/"analysis_rows.csv").open(encoding="utf-8")))
for i,r in enumerate(loaded):
 check(f"rawrow.{i}.issue_id",float(r["issue_id"]),float(rows[i]["issue_id"]))
 check(f"rawrow.{i}.treatment",float(r["ai_treatment"]),g[i])
 check(f"row.{i}.imputed_postreview",float(r["post_review_implementation_time"]),imputed[i],1e-10)
 check(f"row.{i}.total_time",float(r["total_implementation_time"]),timevalues[i],1e-10)
 check(f"row.{i}.log_time",float(r["log_total_implementation_time"]),y[i],1e-12)
 check(f"row.{i}.log_forecast",float(r["log_predicted_time_no_ai"]),lnf[i],1e-12)
V={"n":n,"developers":len(set(dev)),"n_ai":int(sum(g==1)),"n_no_ai":int(sum(g==0))}
oldmodels=json.loads((RUN/"model_statistics.json").read_text());models={}
z=st.norm.ppf(.975)
def fit(X,outcome):
 q,r=la.qr(X,mode="economic");ri=la.solve_triangular(r,np.eye(len(r)));b=la.solve_triangular(r,q.T@outcome)
 resid=outcome-X@b;bread=ri@ri.T;cov=bread*(np.dot(resid,resid)/(len(outcome)-len(b)))
 return b,resid,cov,bread,np.einsum("ij,ij->i",q,q)
for name,old in oldmodels.items():
 cols=[]
 for k in old["columns"]:
  if k=="Intercept":v=np.ones(n)
  elif k=="ai_treatment":v=g
  elif k=="log_predicted_time_no_ai":v=lnf
  elif k=="np.log(predicted_time_ai_allowed)":v=np.log(forecast1)
  elif k.startswith("C(dev_id)[T."):v=(dev==float(k[len("C(dev_id)[T."):-1])).astype(float)
  else:raise ValueError(k)
  cols.append(v)
 X=np.column_stack(cols);b,res,cov,bread,h=fit(X,y);j=old["columns"].index("ai_treatment");effect=float(np.expm1(b[j]));se=math.sqrt(cov[j,j]);ci=np.expm1([b[j]-z*se,b[j]+z*se])
 models[name]={"beta":b.tolist(),"residuals":res.tolist(),"covariance":cov.tolist(),"effect":effect,"ci":ci.tolist()}
 check(name+".beta",b,np.asarray(old["beta"]),1e-10);check(name+".covariance",cov,np.asarray(old["covariance"]),1e-10);check(name+".residuals",res,np.asarray(old["residuals"]),1e-10);check(name+".fitted",X@b,np.asarray(old["fitted"]),1e-10);check(name+".design_hash",hashlib.sha256(X.tobytes()).hexdigest(),old["design_sha256"])
 V[name+".point"]=effect;V[name+".low"]=float(ci[0]);V[name+".high"]=float(ci[1])
 if name=="baseline":
  V["baseline.point"]=effect
  hc3=bread@(X.T@((res/(1-h))[:,None]**2*X))@bread
  scores=X*res[:,None];cluster=np.zeros_like(bread)
  for d in sorted(set(dev)):
   score=np.sum(scores[dev==d],axis=0);cluster+=np.outer(score,score)
  G=len(set(dev));cluster=bread@cluster@bread*(G/(G-1))*((n-1)/(n-len(b)))
  for label,cv in [("Homoskedastic",cov),("Robust (HC3)",hc3),("Clustered By Dev",cluster)]:
   se=math.sqrt(cv[j,j]);ci=np.expm1([b[j]-z*se,b[j]+z*se]);V["baseline."+label+".low"]=float(ci[0]);V["baseline."+label+".high"]=float(ci[1])
def boot(a,flag,seed):
 rng=np.random.default_rng(seed);vals=[]
 for i in range(0,50000,200):
  take=rng.integers(0,len(a),(min(200,50000-i),len(a)));ts=a[take];tg=flag[take];n1=np.count_nonzero(tg,axis=1);n0=len(a)-n1
  s1=np.einsum("ij,ij->i",ts,tg);s0=np.einsum("ij,ij->i",ts,1-tg)
  vals.extend((s1/n1/(s0/n0)-1).tolist())
 return np.asarray(vals)
b0=boot(timevalues,g,42)
b1=boot(np.r_[forecast0,forecast1],np.r_[np.zeros(n),np.ones(n)],43)
rng=np.random.default_rng(44);bp=[]
for i in range(0,50000,200):
 take=rng.integers(0,n,(min(200,50000-i),n))
 bp.extend((np.sum(forecast1[take],axis=1)/np.sum(forecast0[take],axis=1)-1).tolist())
bp=np.asarray(bp)
draws=np.load(RUN/"bootstrap_draws.npz")
for name,a in [("observed_pooled",b0),("forecast_unpaired_pooled",b1),("forecast_paired",bp)]:check("all50000draws."+name,a,draws[name],1e-10)
for label,a,b in [("ratio",timevalues[g==1],timevalues[g==0]),("forecast",forecast1,forecast0)]:
 V[label+".point"]=float(math.fsum(a)/len(a)/(math.fsum(b)/len(b))-1)
 ci=np.quantile(b0 if label=="ratio" else b1,[.025,.975]);V[label+".low"]=float(ci[0]);V[label+".high"]=float(ci[1])
for label,v in [("no_forecast",forecast0),("ai_forecast",forecast1)]:
 means={};vars={}
 for t in [0,1]:
  a=v[g==t];m=math.fsum(a)/len(a);variance=math.fsum((a-m)**2)/(len(a)-1);means[t]=m;vars[t]=variance;V[f"balance.{label}.{t}.mean"]=m;V[f"balance.{label}.{t}.sd"]=math.sqrt(variance)
 V[f"balance.{label}.difference"]=means[1]-means[0]
 a=vars[1]/sum(g==1);b=vars[0]/sum(g==0);df=(a+b)**2/(a*a/(sum(g==1)-1)+b*b/(sum(g==0)-1));tt=(means[1]-means[0])/math.sqrt(a+b);V[f"balance.{label}.p"]=float(2*st.t.sf(abs(tt),df))
for t in [0,1]:
 fraction=sum(g==t)/n;V[f"allocation.{t}.percent"]=float(fraction*100);V[f"allocation.{t}.se_percent"]=float(100*math.sqrt(fraction*(1-fraction)/n))
 V[f"observed_mean_hours.{t}"]=float(math.fsum(timevalues[g==t])/sum(g==t)/60)
 V[f"forecast_mean_hours.{t}"]=float(math.fsum(forecast1 if t else forecast0)/n/60)
 for x in [.5,1.,2.,4.,8.]:V[f"ecdf.{t}.{x:g}"]=float(sum(timevalues[g==t]<=60*x)/sum(g==t))
 a=(forecast1 if t else forecast0)[g==t];b=timevalues[g==t];aa=a-a.mean();bb=b-b.mean();V[f"forecast_correlation.{t}"]=float(np.dot(aa,bb)/math.sqrt(np.dot(aa,aa)*np.dot(bb,bb)))
V["allocation.p"]=float(st.chi2.sf(sum((sum(g==t)-n/2)**2/(n/2) for t in [0,1]),1))
X=np.column_stack([np.ones(n),g,lnf])
for t,label in [(1,"ai60_no0"),(0,"ai0_no60")]:
 v=post.copy();v[miss]=np.where(g[miss]==t,60,0);b,*_=fit(X,np.log(pre+v));V["imputation."+label]=float(np.expm1(b[1]))
for key,val in reference.items():check("stat."+key,V[key],val,1e-10)
dec=[]
for target in plan["targets"]:
 val=V[target["id"]];dec.append({**target,"actual":val,"passed":bool(target["low"]<=val<=target["high"])})
qs={"positive_original_primary_effect":V["baseline.point"]>0 and V["baseline.Homoskedastic.low"]>0,"all_four_regression_effects_positive":all(V[k+".point"]>0 for k in oldmodels),"raw_ratio_more_extreme_than_adjusted":V["ratio.point"]>V["baseline.point"],"predicted_acceleration_opposes_observed_slowdown":V["forecast.point"]<0<V["baseline.point"]}
for k,v in qs.items():dec.append({"id":k,"actual":bool(v),"passed":bool(v),"type":"qualitative"})
olddec=json.loads((RUN/"target_decisions.json").read_text())
for a,b in zip(dec,olddec):
 check("gate."+a["id"]+".decision",a["passed"],b["passed"]);check("gate."+a["id"]+".actual",a["actual"],b["actual"],1e-10 if not isinstance(a["actual"],bool) else 0)
check("same_all65_gate_set",[a["id"] for a in dec]==[a["id"] for a in olddec],True)
# Supporting display diagnostics; never replace unchanged preregistered decisions.
display=[]
for t in plan["targets"]:
 if t["id"].startswith("balance.") and "expected" in t and not t["id"].endswith(".p"):
  val=V[t["id"]];display.append({"id":t["id"],"raw_value":val,"source_integer":t["expected"],"truncated_integer":int(val),"truncated_matches":int(val)==t["expected"]})
dump("display_diagnostics.json",{"status":"supporting only, source display algorithm unreleased","all_truncated_match":all(x["truncated_matches"] for x in display),"comparisons":display,"no_criteria_amended":True})
dump("audit_checks.json",C);dump("independent_statistics.json",V);dump("independent_models.json",models);dump("independent_target_decisions.json",dec)
result={"audit_id":sys.argv[1],"audited_run":"P079-central-001","started_at_utc":started,"finished_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checks_passed":sum(x["passed"] for x in C),"checks_total":len(C),"all_integrity_and_numerical_audit_checks_pass":all(x["passed"] for x in C),"published_gates_passed":sum(x["passed"] for x in dec),"published_gates_total":len(dec),"all_published_gates_pass":all(x["passed"] for x in dec),"independent_engine":"Raw CSV, manual design, QR OLS, manual HC3/cluster covariance, manual Welch/Pearson/correlation, all150000 independently replayed bootstrap draws; no runner/original helper imports","wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,"peak_working_set_bytes":psutil.Process().memory_info().peak_wset,"paid_api_spend":0,"fresh_gpu_inference":False,"source_display_truncation_diagnostic_only":True}
dump("audit.json",result);(OUT/"auditor_source.py").write_bytes(pathlib.Path(__file__).read_bytes());dump("AUDIT_MANIFEST.json",{"files":[{"path":str(f.relative_to(ROOT)).replace("\\","/"),"bytes":f.stat().st_size,"sha256":hashfile(f)} for f in sorted(OUT.iterdir()) if f.is_file()]})
print(json.dumps(result,indent=2));print("AUDIT_FAILURES",json.dumps([x for x in C if not x["passed"]],indent=2))
