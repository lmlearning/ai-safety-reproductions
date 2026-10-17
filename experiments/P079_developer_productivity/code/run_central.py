"""P079 whole primary issue-time contribution, prospectively specified."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[key]="1"
os.environ["MPLBACKEND"]="Agg"
import sys,pathlib,json,hashlib,datetime,time,importlib.util,platform
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/"papers/P079_developer_productivity"
OVERLAY=ROOT/"environment/p079_cpu_original_001/packages"
sys.path.insert(0,str(OVERLAY))
import numpy as np,pandas as pd,scipy,scipy.stats as st,statsmodels,statsmodels.formula.api as smf,psutil
from matplotlib import pyplot as plt
PLAN=json.loads((P/"PREREGISTRATION.json").read_text())
RUN=ROOT/"runs"/sys.argv[1]
RUN.mkdir(parents=True,exist_ok=False)
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t0=time.perf_counter();c0=time.process_time()
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def dump(f,obj):f.write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n",encoding="utf-8")
def memory():assert psutil.Process().memory_info().rss<2**30
assert scipy.__version__=="1.15.2" and statsmodels.__version__=="0.14.4"
assert psutil.virtual_memory().available>1.5*2**30
for f in PLAN["inputs"]:assert digest(ROOT/f["path"])==f["sha256"]
(RUN/"runner_source.py").write_bytes(pathlib.Path(__file__).read_bytes())
spec=importlib.util.spec_from_file_location("original_p079",P/"sources/regression.py");original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
df=pd.read_csv(P/"sources/data_complete.csv")
assert len(df)==246 and df.issue_id.nunique()==246 and df.dev_id.nunique()==16
raw=df.copy(deep=True);missing=raw.post_review_implementation_time.isna()
df=original.impute_missing_post_review_time_values(df)
df=original.add_total_implementation_time_column(df)
assert np.isfinite(df.total_implementation_time).all() and (df.total_implementation_time>0).all()
point,cis=original.run_regression(df)
raw.to_csv(RUN/"raw_data_as_loaded.csv",index=False)
df.to_csv(RUN/"analysis_rows.csv",index=False)
values={"n":len(df),"developers":df.dev_id.nunique(),"n_ai":int((df.ai_treatment==1).sum()),"n_no_ai":int((df.ai_treatment==0).sum()),"baseline.point":float(point)}
for key,ci in cis.items():
 values["baseline."+key+".low"]=ci[0];values["baseline."+key+".high"]=ci[1]
models={}
formulas={
 "baseline":"log_total_implementation_time ~ ai_treatment + log_predicted_time_no_ai",
 "treatment_only":"log_total_implementation_time ~ ai_treatment",
 "ai_forecast":"log_total_implementation_time ~ ai_treatment + np.log(predicted_time_ai_allowed)",
 "developer_fe":"log_total_implementation_time ~ ai_treatment + log_predicted_time_no_ai + C(dev_id)"
}
z=st.norm.ppf(.975)
for name,formula in formulas.items():
 fit=smf.ols(formula,data=df,missing="raise").fit()
 beta=float(fit.params["ai_treatment"]);se=float(fit.bse["ai_treatment"]);eff=float(np.expm1(beta));ci=np.expm1([beta-z*se,beta+z*se])
 values[name+".point"]=eff;values[name+".low"]=float(ci[0]);values[name+".high"]=float(ci[1])
 models[name]={"formula":formula,"n":int(fit.nobs),"columns":fit.model.exog_names,"beta":fit.params.tolist(),"covariance":fit.cov_params().to_numpy().tolist(),"residuals":fit.resid.tolist(),"fitted":fit.fittedvalues.tolist(),"treatment_effect":eff,"ci":ci.tolist(),"design_sha256":hashlib.sha256(fit.model.exog.tobytes()).hexdigest()}
df[["issue_id","log_total_implementation_time","log_predicted_time_no_ai"]].to_csv(RUN/"primary_outcome_design.csv",index=False)
def pooled_bootstrap(y,g,seed):
 rng=np.random.default_rng(seed); draws=[]
 for start in range(0,50000,500):
  ix=rng.integers(0,len(y),size=(min(500,50000-start),len(y)))
  ys=y[ix];gs=g[ix];n1=gs.sum(axis=1);n0=len(y)-n1
  assert (n1>0).all() and (n0>0).all()
  draws.extend(((ys*gs).sum(axis=1)/n1/((ys*(1-gs)).sum(axis=1)/n0)-1).tolist())
 return np.asarray(draws)
y=df.total_implementation_time.to_numpy();g=df.ai_treatment.to_numpy()
ratio=float(y[g==1].mean()/y[g==0].mean()-1)
boots=pooled_bootstrap(y,g,42);ci=np.quantile(boots,[.025,.975],method="linear")
values.update({"ratio.point":ratio,"ratio.low":float(ci[0]),"ratio.high":float(ci[1])})
# Forecast uncertainty follows a pooled, unpaired two-column expansion; paired sensitivity is mandatory and distinct.
yn=raw.predicted_time_no_ai.to_numpy();ya=raw.predicted_time_ai_allowed.to_numpy()
forecast=float(ya.mean()/yn.mean()-1)
fb=pooled_bootstrap(np.concatenate([yn,ya]),np.concatenate([np.zeros(len(yn)),np.ones(len(ya))]),43)
fci=np.quantile(fb,[.025,.975],method="linear")
rng=np.random.default_rng(44);paired=[]
for start in range(0,50000,500):
 ix=rng.integers(0,len(raw),size=(min(500,50000-start),len(raw)))
 paired.extend((ya[ix].mean(axis=1)/yn[ix].mean(axis=1)-1).tolist())
paired=np.asarray(paired)
np.savez_compressed(RUN/"bootstrap_draws.npz",observed_pooled=boots,forecast_unpaired_pooled=fb,forecast_paired=paired)
values.update({"forecast.point":forecast,"forecast.low":float(fci[0]),"forecast.high":float(fci[1])})
for label,column in [("no_forecast","predicted_time_no_ai"),("ai_forecast","predicted_time_ai_allowed")]:
 for treat in [0,1]:
  a=raw.loc[raw.ai_treatment==treat,column].to_numpy()
  values[f"balance.{label}.{treat}.mean"]=float(a.mean());values[f"balance.{label}.{treat}.sd"]=float(a.std(ddof=1))
 a=raw.loc[raw.ai_treatment==1,column].to_numpy();b=raw.loc[raw.ai_treatment==0,column].to_numpy()
 values[f"balance.{label}.difference"]=float(a.mean()-b.mean());values[f"balance.{label}.p"]=float(st.ttest_ind(a,b,equal_var=False).pvalue)
for treat in [0,1]:
 n=int((g==treat).sum());fraction=n/len(g)
 values[f"allocation.{treat}.percent"]=100*fraction
 values[f"allocation.{treat}.se_percent"]=100*np.sqrt(fraction*(1-fraction)/len(g))
values["allocation.p"]=float(st.chisquare([sum(g==0),sum(g==1)]).pvalue)
for treat in [0,1]:
 a=df.loc[g==treat,"total_implementation_time"].to_numpy()/60
 values[f"observed_mean_hours.{treat}"]=float(a.mean())
 for x in [.5,1.,2.,4.,8.]:values[f"ecdf.{treat}.{x:g}"]=float((a<=x).mean())
 values[f"forecast_correlation.{treat}"]=float(st.pearsonr(raw.loc[g==treat,"predicted_time_ai_allowed" if treat else "predicted_time_no_ai"],df.loc[g==treat,"total_implementation_time"]).statistic)
values["forecast_mean_hours.0"]=float(yn.mean()/60);values["forecast_mean_hours.1"]=float(ya.mean()/60)
imputation={}
for allowed60 in [True,False]:
 variant=raw.copy(deep=True)
 variant.loc[missing,"post_review_implementation_time"]=np.where(variant.loc[missing,"ai_treatment"]==int(allowed60),60.,0.)
 variant=original.add_total_implementation_time_column(variant)
 val,vcis=original.run_regression(variant)
 name="ai60_no0" if allowed60 else "ai0_no60"
 values["imputation."+name]=float(val);imputation[name]={"effect":float(val),"cis":vcis}
dump(RUN/"model_statistics.json",models)
dump(RUN/"all_statistics.json",values)
dump(RUN/"imputation_sensitivity.json",imputation)
dump(RUN/"source_discrepancies.json",{"missing_review_times_released":int(missing.sum()),"missing_review_times_paper":27,"first_readme_treatment_reversed":True,"paper_imputation_order_reversed_before_outcomes":True,"raw_first_data_auxiliary_x_preserved":bool(raw["External Resource Needs (1-3)"].eq("x").any()),"forecast_unpaired_ci":fci.tolist(),"forecast_paired_ci":np.quantile(paired,[.025,.975]).tolist(),"original_bootstrap_seed_and_iterations_unreleased":True})
decisions=[]
for target in PLAN["targets"]:
 v=values[target["id"]]
 passed=bool(target["low"]<=v<=target["high"])
 decisions.append({**target,"actual":float(v),"passed":passed})
q={}
q["positive_original_primary_effect"]=point>0 and cis["Homoskedastic"][0]>0
q["all_four_regression_effects_positive"]=all(values[n+".point"]>0 for n in formulas)
q["raw_ratio_more_extreme_than_adjusted"]=ratio>point
q["predicted_acceleration_opposes_observed_slowdown"]=forecast<0<point
for name,passed in q.items():decisions.append({"id":name,"actual":bool(passed),"passed":bool(passed),"type":"qualitative"})
dump(RUN/"target_decisions.json",decisions)
# Static full-data figures, no smoothing/truncating cases to improve agreement.
fig,ax=plt.subplots(figsize=(9,5))
names=["baseline","ratio","treatment_only","ai_forecast","developer_fe"]
eff=[values[n+".point"] for n in names];lo=[values[n+".low"] for n in names];hi=[values[n+".high"] for n in names]
ax.errorbar(range(5),np.asarray(eff)*100,yerr=np.asarray([np.asarray(eff)-lo,np.asarray(hi)-eff])*100,fmt="o",capsize=4)
ax.axhline(0,color="black",linewidth=1);ax.set_xticks(range(5),["Adjusted","Raw ratio","Treatment only","AI forecast","Developer effects"]);ax.set_ylabel("Change in issue time (%)");ax.set_title("P079: original five estimators, all 246 tasks");fig.tight_layout();fig.savefig(RUN/"estimator_comparison.png",dpi=160);plt.close(fig)
fig,ax=plt.subplots(figsize=(7,5))
for treat,label in [(0,"AI disallowed"),(1,"AI allowed")]:
 times=np.sort(y[g==treat]/60);ax.scatter(times,np.arange(1,len(times)+1)/len(times)*100,s=12,label=label)
ax.set_xscale("log",base=2);ax.set_xlabel("Issue time (hours)");ax.set_ylabel("Percentile");ax.legend();fig.tight_layout();fig.savefig(RUN/"complete_ecdf.png",dpi=160);plt.close(fig)
fit=models["baseline"];res=np.asarray(fit["residuals"]);fv=np.asarray(fit["fitted"])
fig,axs=plt.subplots(1,3,figsize=(12,4))
st.probplot(res,dist="norm",plot=axs[0]);axs[1].scatter(fv,res,s=12);axs[1].axhline(0,color="black");axs[1].set_xlabel("Fitted log time");axs[1].set_ylabel("Residual")
axs[2].hist(res,bins=30,density=True);axs[2].set_xlabel("Residual");fig.tight_layout();fig.savefig(RUN/"regression_diagnostics.png",dpi=160);plt.close(fig)
memory()
metrics={"run_id":sys.argv[1],"started_at_utc":started,"finished_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,"peak_working_set_bytes":psutil.Process().memory_info().peak_wset,"gates_total":len(decisions),"gates_passed":sum(d["passed"] for d in decisions),"all_gates_passed":all(d["passed"] for d in decisions),"preregistration_sha256":digest(P/"PREREGISTRATION.json"),"versions":{"python":sys.version,"numpy":np.__version__,"scipy":scipy.__version__,"statsmodels":statsmodels.__version__,"pandas":pd.__version__},"modules":{"scipy":scipy.__file__,"statsmodels":statsmodels.__file__},"threads":1,"paid_api_spend":0,"fresh_gpu_inference":False}
dump(RUN/"metrics.json",metrics)
files=[{"path":str(f.relative_to(ROOT)).replace("\\","/"),"bytes":f.stat().st_size,"sha256":digest(f)} for f in sorted(RUN.iterdir()) if f.is_file()]
dump(RUN/"RUN_MANIFEST.json",{"run_id":sys.argv[1],"command":[sys.executable,str(pathlib.Path(__file__).resolve()),sys.argv[1]],"exit_code":0,"files":files,"plan_sha256":digest(P/"PREREGISTRATION.json")})
print(json.dumps(metrics,indent=2))
print("FAILED",json.dumps([d for d in decisions if not d["passed"]],indent=2))
