"""Independent CPU reproduction of the complete original P066 Figure2."""
import os
for key in ["OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"]:os.environ[key]="1"
import pathlib,datetime as dt,time,hashlib,json,shutil,sys,platform
ROOT=pathlib.Path(__file__).resolve().parents[1] if "frozen" not in str(pathlib.Path(__file__).parent) else pathlib.Path(__file__).resolve().parents[5]
P=ROOT/"papers/P066_clinical_collaboration_meta";RUN=P/"runs/P066-central-002"
start=dt.datetime.now(dt.timezone.utc).isoformat();wall=time.perf_counter();cpu=time.process_time()
assert not RUN.exists(),"Immutable run cannot be overwritten"
RUN.mkdir(parents=True);frozen=RUN/"frozen";frozen.mkdir()
for name in ["original_data.json","targets.json","PREREGISTRATION.json","PREREGISTRATION.md","SOLVER_CORRECTION.json","sources_manifest.json","sources_manifest_solver_corrected.json"]:shutil.copyfile(P/name,frozen/name)
shutil.copyfile(__file__,frozen/"runner.py")
import numpy as np,scipy,psutil
from scipy.optimize import brentq
from scipy.stats import norm,t,chi2
data=json.loads((frozen/"original_data.json").read_text());targets=json.loads((frozen/"targets.json").read_text());plan=json.loads((frozen/"PREREGISTRATION.json").read_text())
config={"run_id":"P066-central-002","post_outcome_method_correction":True,"solver":"R4.5.2 zeroin with documented metafor default stopping","start_utc":start,"python":sys.version,"numpy":np.__version__,"scipy":scipy.__version__,"psutil":psutil.__version__,"platform":platform.platform(),"deterministic":True,"seed":None,"GPU":False,"paid_cost":0,"threads":1,"preregistration_sha256":hashlib.sha256((frozen/"PREREGISTRATION.json").read_bytes()).hexdigest()}
(RUN/"configuration.json").write_text(json.dumps(config,indent=2))
def original_r_zeroin(fn,low,high,tol=2.220446049250313e-16**.25,maxiter=100):
 a,b=low,high;fa,fb=fn(a),fn(b);c,fc=a,fa;trace=[]
 if fa==0:return a,trace
 if fb==0:return b,trace
 for iteration in range(maxiter+1):
  prev_step=b-a
  if abs(fc)<abs(fb):
   a=b;b=c;c=a;fa=fb;fb=fc;fc=fa
  tol_act=2*np.finfo(float).eps*abs(b)+tol/2
  new_step=(c-b)/2
  trace.append({"iteration":iteration,"a":a,"b":b,"c":c,"fa":fa,"fb":fb,"fc":fc,"tolerance_actual":tol_act})
  if abs(new_step)<=tol_act or fb==0:return b,trace
  if abs(prev_step)>=tol_act and abs(fa)>abs(fb):
   cb=c-b
   if a==c:
    ratio=fb/fa;p=cb*ratio;q=1-ratio
   else:
    q=fa/fc;t1=fb/fc;t2=fb/fa;p=t2*(cb*q*(q-t1)-(b-a)*(t1-1));q=(q-1)*(t1-1)*(t2-1)
   if p>0:q=-q
   else:p=-p
   if p<(.75*cb*q-abs(tol_act*q)/2) and p<abs(prev_step*q/2):new_step=p/q
  if abs(new_step)<tol_act:new_step=tol_act if new_step>0 else -tol_act
  a=b;fa=fb;b+=new_step;fb=fn(b)
  if (fb>0 and fc>0) or (fb<0 and fc<0):c=a;fc=fa
 raise RuntimeError("Original R solver exceeded maxiter")

z=norm.ppf(.975);checks=[];terms={};fits={};conflicts={};solver_traces={}
def check(name,value,target,tolerance):
 value=float(value);checks.append(dict(name=name,value=value,target=target,tolerance=tolerance,absolute_error=abs(value-target),passed=abs(value-target)<=tolerance))
def interval(mu,se,crit,rr):
 low=mu-crit*se;high=mu+crit*se
 return {"effect":float(np.exp(mu) if rr else mu),"ci_low":float(np.exp(low) if rr else low),"ci_high":float(np.exp(high) if rr else high)}
for panel,d in data.items():
 rr=d["metric"]=="RR";k=len(d["study"]);df=k-1
 if rr:
  a,b,c,e=[np.array(d[key],dtype=float) for key in ["event_e","n_e","event_c","n_c"]]
  y=np.log(a/b/(c/e));v=1/a-1/b+1/c-1/e
 else:y=np.array(d["effect"],float);v=np.array(d["se"],float)**2
 def calcQ(tau2):
  w=1/(v+tau2);m=np.sum(w*y)/np.sum(w)
  return float(np.sum(w*(y-m)**2))
 Q=calcQ(0);upper=max(100.,10*(np.median(abs(y-np.median(y)))*1.4826)**2)
 tau2,trace=(0.,[]) if Q<=df else original_r_zeroin(lambda s:calcQ(s)-df,0.,upper)
 solver_traces[panel]={"bounds":[0,upper],"tolerance":float(np.finfo(float).eps**.25),"trace":trace,"tau2":tau2,"Q_minus_df":calcQ(tau2)-df}
 wc=1/v;wr=1/(v+tau2);muc=np.sum(wc*y)/sum(wc);mur=np.sum(wr*y)/sum(wr)
 sec=np.sqrt(1/sum(wc));ser=np.sqrt(1/sum(wr));scale=calcQ(tau2)/df;sehk=np.sqrt(scale/sum(wr));crit=t.ppf(.975,df) if d["random_ci"]=="HK" else z
 seactual=sehk if d["random_ci"]=="HK" else ser
 p=2*(t.sf(abs(mur/seactual),df) if d["random_ci"]=="HK" else norm.sf(abs(mur/seactual)))
 predse=np.sqrt(tau2+ser**2);picrit=t.ppf(.975,df);pi=interval(mur,predse,picrit,rr)
 fit={"k":k,"df":df,"Q":Q,"p_Q":float(chi2.sf(Q,df)),"I2":max(0,(Q-df)/Q)*100,"tau2":tau2,"common":interval(muc,sec,z,rr),"random":interval(mur,seactual,crit,rr),"pi_low":pi["ci_low"],"pi_high":pi["ci_high"],"log_or_raw_mu_common":float(muc),"log_or_raw_mu_random":float(mur),"se_common":float(sec),"se_random_classic":float(ser),"se_random_hk":float(sehk),"hk_scale":scale,"p_random":float(p),"crit_random":float(crit),"crit_prediction":float(picrit),"prediction_df":df,"study":[]}
 terms[panel]=[]
 for i,name in enumerate(d["study"]):
  row=interval(y[i],np.sqrt(v[i]),z,rr);row.update(weight_common=float(wc[i]/sum(wc)*100),weight_random=float(wr[i]/sum(wr)*100));fit["study"].append(row)
  terms[panel].append(dict(study=name,effect_log_or_raw=float(y[i]),variance=float(v[i]),se=float(np.sqrt(v[i])),weight_common_raw=float(wc[i]),weight_random_raw=float(wr[i]),Q_term=float(wc[i]*(y[i]-muc)**2),Q_tau_term=float(wr[i]*(y[i]-mur)**2)))
 fits[panel]=fit
 for i,row in enumerate(targets[panel]["study"]):
  for key,val in row.items():check(f"{panel}.study.{i}.{key}",fit["study"][i][key],val,.10 if key.startswith("weight") else .01)
 for key in ["common","random"]:
  if key in targets[panel]:
   for field,val in targets[panel][key].items():check(f"{panel}.{key}.{field}",fit[key][field],val,.01)
 for key in ["pi_low","pi_high","I2","tau2","p_Q","Q"]:
  if key in targets[panel]:
   tol={"I2":.10,"tau2":.00015,"p_Q":.00015}.get(key,.01);check(f"{panel}.{key}",fit[key],targets[panel][key],tol)
 if panel=="A":
  mh=(sum(a*e/(b+e)))/(sum(c*b/(b+e)));conflicts["A_MH_common_point"]=float(mh)
 if panel=="B":conflicts["B_HKSJ_counterfactual"]=interval(mur,sehk,t.ppf(.975,df),False)
claims={"A_positive_nonsignificant":fits["A"]["random"]["effect"]>1 and fits["A"]["random"]["ci_low"]<1<fits["A"]["random"]["ci_high"],"B_positive_significant_classic":fits["B"]["random"]["ci_low"]>0,"C_nonsignificant":fits["C"]["random"]["ci_low"]<0<fits["C"]["random"]["ci_high"]}
for panel in fits:claims[panel+"_prediction_crosses_null"]=fits[panel]["pi_low"]<(1 if panel=="A" else 0)<fits[panel]["pi_high"]
numerical_count=len(checks)
for name,value in claims.items():checks.append(dict(name=name,value=bool(value),target=True,passed=bool(value)))
assert numerical_count==63 and len(checks)==69
result={"paper_id":"P066","run_id":"P066-central-002","scope":plan["scope"],"fits":fits,"source_conflict_diagnostics":conflicts,"checks":checks,"numerical_check_count":numerical_count,"qualitative_check_count":len(claims),"all_checks_pass":all(x["passed"] for x in checks)}
(RUN/"solver_traces.json").write_text(json.dumps(solver_traces,indent=2))
(RUN/"raw_per_study.json").write_text(json.dumps(terms,indent=2))
(RUN/"results.json").write_text(json.dumps(result,indent=2))
proc=psutil.Process();mem=proc.memory_info()._asdict()
execution={"start_utc":start,"end_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,"exit_code":0,"memory_bytes":mem,"paid_cost":0,"GPU":False,"no_failed_experiment_runs_before_this":False,"retained_prior_failed_run":"P066-central-001","post_outcome_method_correction":True}
(RUN/"execution.json").write_text(json.dumps(execution,indent=2))
manifest=[{"path":str(f.relative_to(RUN)),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(RUN.rglob("*")) if f.is_file()]
(RUN/"run_manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(run_id=result["run_id"],checks=len(checks),passed=sum(x["passed"] for x in checks),failures=[x for x in checks if not x["passed"]],fits={key:{f:val for f,val in fit.items() if f in ["random","pi_low","pi_high","I2","tau2","p_Q"]} for key,fit in fits.items()},execution=execution),indent=2))
