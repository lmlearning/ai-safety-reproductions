"""Complete prospective P134 calculation. Original inputs opened only in guarded main."""
from pathlib import Path
import os,sys,json,csv,math,hashlib,datetime,argparse
for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[k]="1"
BASE=Path(__file__).resolve().parents[1]
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+"\n",encoding="utf8")
def sha(p):
 with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def means(r):
 a,b=int(r["experimental_n"]),int(r["control_n"]);n=a+b
 sp=math.sqrt(((a-1)*float(r["experimental_sd"])**2+(b-1)*float(r["control_sd"])**2)/(n-2))
 g=(float(r["experimental_mean"])-float(r["control_mean"]))/sp*(1-3/(4*n-9))
 v=n/(a*b)+g*g/(2*(n-3.94))
 return g,v
def pool(rows,model):
 from scipy.stats import chi2
 k=len(rows);w=[1/r["variance"] for r in rows];sw=sum(w)
 fixed=sum(a*r["g"] for a,r in zip(w,rows))/sw
 Q=sum(a*(r["g"]-fixed)**2 for a,r in zip(w,rows));df=k-1
 C=sw-sum(a*a for a in w)/sw
 tau=max(0,(Q-df)/C) if k>1 else 0.
 weights=[1/(r["variance"]+tau) for r in rows] if model=="random" else w
 total=sum(weights);g=sum(a*r["g"] for a,r in zip(weights,rows))/total;se=math.sqrt(1/total)
 z=g/se;p=math.erfc(abs(z)/math.sqrt(2))
 decision="not_significant" if p>=.05 else ("negative_significant" if g<0 else "positive_significant")
 return {"k":k,"g":g,"SE":se,"CI_low":g-1.96*se,"CI_high":g+1.96*se,"Q":Q,"Q_p":float(chi2.sf(Q,df)) if df>0 else None,"df":df,"I2":max(0,(Q-df)/Q)*100 if k>1 and Q else 0.,"tau2":tau if model=="random" else None,"Z":abs(z),"p":p,"interpretation":decision,"model":model,"row_weights_percent":[a/total*100 for a in weights]}
def metadata(key,m):
 keys=sorted(m,key=len,reverse=True);parent=next(z for z in keys if key.startswith(z));v=dict(m[parent])
 if v["trial_specific_female"]:
  trial="Trial1" if "Trial1" in key else "Trial2";v["female_percent_literal"]=v["trial_specific_female"][trial]
 return parent,v
def get(obj,path):
 for k in path:obj=obj[k]
 return obj
def gate_checks(results,targets):
 out=[]
 for q in targets["gates"]:
  a=get(results,q["path"]);d=float(a)-float(q["target"]) if q["kind"]=="rounded" else None
  passed=abs(d)<=float(q["tolerance"]) if d is not None else a==q["target"]
  out.append(dict(q,actual=a,difference=d,passed=passed))
 return out
def regression(rows,female,method):
 from scipy.optimize import minimize_scalar
 from scipy.stats import t as student
 y=[r["g"] for r in rows];v=[r["variance"] for r in rows];x=[float(a) for a in female];k=len(y)
 def fit(tau):
  w=[1/(a+tau) for a in v];A=sum(w);B=sum(a*b for a,b in zip(w,x));D=sum(a*b*b for a,b in zip(w,x));det=A*D-B*B
  assert det>0,"All source rows retained; no constant moderator fit"
  u=sum(a*b for a,b in zip(w,y));z=sum(a*b*c for a,b,c in zip(w,x,y));inter=(D*u-B*z)/det;slope=(A*z-B*u)/det
  Q=sum(a*(b-inter-slope*c)**2 for a,b,c in zip(w,y,x))
  return w,det,inter,slope,Q,A/det
 fixed=fit(0.)
 if method=="fixed":tau=0.;converged=True
 elif method=="DL":
  w,det,_,_,Q,_=fixed;A=sum(w);B=sum(a*b for a,b in zip(w,x));D=sum(a*b*b for a,b in zip(w,x))
  trace=(D*sum(a*a for a in w)-2*B*sum(a*a*b for a,b in zip(w,x))+A*sum(a*a*b*b for a,b in zip(w,x)))/det
  tau=max(0,(Q-(k-2))/(A-trace));converged=True
 else:
  def objective(a):
   w,det,_,_,Q,_=fit(a)
   return (sum(math.log(c+a) for c in v)+math.log(det)+Q)/2
  upper=max(1.,100*sum((a-sum(y)/k)**2 for a in y)/k)
  opt=minimize_scalar(objective,bounds=(0,upper),method="bounded",options={"xatol":1e-12,"maxiter":2000})
  tau=0. if objective(0.)<=opt.fun else float(opt.x);converged=bool(opt.success)
 w,det,inter,slope,Q,var=fit(tau);se=math.sqrt(var);z=slope/se
 return {"k":k,"method":method,"tau2":tau,"intercept":inter,"slope":slope,"SE_slope":se,"normal_p":math.erfc(abs(z)/math.sqrt(2)),"student_p":float(2*student.sf(abs(z),k-2)),"df":k-2,"converged":converged,"raw_female_percent":female}
def egger(rows):
 from scipy.stats import t
 x=[1/math.sqrt(r["variance"]) for r in rows];y=[r["g"]/math.sqrt(r["variance"]) for r in rows];n=len(x)
 ax=sum(x)/n;ay=sum(y)/n;ss=sum((a-ax)**2 for a in x);slope=sum((a-ax)*(b-ay) for a,b in zip(x,y))/ss;inter=ay-slope*ax
 err=sum((b-inter-slope*a)**2 for a,b in zip(x,y));se=math.sqrt(err/(n-2)*(1/n+ax*ax/ss));z=inter/se
 return {"k":n,"intercept":inter,"SE_intercept":se,"student_p":float(2*t.sf(abs(z),n-2)),"normal_p":math.erfc(abs(z)/math.sqrt(2)),"df":n-2}
def supporting(family,rows,model,m):
 factors=["control_type","duration","target_sample","reminders","interaction_mode","deployment","dialogue_system"]
 out={"leave_one_row_out":{},"leave_one_trial_out":{},"subgroups":{},"gender":{},"egger":{}}
 for i,r in enumerate(rows):out["leave_one_row_out"][r["row"]]=pool(rows[:i]+rows[i+1:],model)
 cohorts=sorted({r["study_key"].split("Measure")[0] for r in rows})
 for c in cohorts:
  subset=[r for r in rows if r["study_key"].split("Measure")[0]!=c]
  out["leave_one_trial_out"][c]=pool(subset,model) if subset else None
 for f in factors:
  groups={};unresolved=[]
  for r in rows:
   _,v=metadata(r["study_key"],m);value=v[f]
   if value is None:unresolved.append(r["row"])
   else:groups.setdefault(value,[]).append(r)
  out["subgroups"][f]={"unresolved_row_ids":unresolved,"groups":{k:{"row_ids":[r["row"] for r in a],"original_family_method":pool(a,model),"uniform_DL_random":pool(a,"random"),"uniform_fixed":pool(a,"fixed")} for k,a in sorted(groups.items())},"original_complete_claim":"unavailable for unresolved allocations" if unresolved else "conventional reconstruction"}
 if len(rows)>=10:
  females=[metadata(r["study_key"],m)[1]["female_percent_literal"] for r in rows]
  assert all(a is not None for a in females),"No moderator case pruning"
  out["gender"]={meth:regression(rows,females,meth) for meth in ["REML","DL","fixed"]}
  out["egger"]={"literal_more_than10_eligible":len(rows)>10,"source_life10_alternative_eligible":family=="life_satisfaction" and len(rows)==10,"result":egger(rows)}
 out["original_trim_fill"]={"status":"original implementation unspecified; no copied adjusted estimate","source_conflict":"mental zeroimputed sameobserved-.372 differs RevMan-.35"} if family in ["overall_mental","depression"] else None
 return out

def figures(results,out):
 import matplotlib
 matplotlib.use("Agg")
 import matplotlib.pyplot as plt
 (out/"figures").mkdir()
 for family,obj in results["families"].items():
  rows=list(obj["rows"].values());n=len(rows);weights=obj["pool"]["row_weights_percent"]
  fig,ax=plt.subplots(figsize=(10,max(3,n*.26+1.6)))
  for i,r in enumerate(rows):
   y=n-i;ax.plot([r["CI_low"],r["CI_high"]],[y,y],color="#46617a",lw=1)
   ax.scatter([r["g"]],[y],s=15+65*weights[i]/max(weights),marker="s",color="#244c70")
  q=obj["pool"];ax.plot([q["CI_low"],q["g"],q["CI_high"],q["g"],q["CI_low"]],[0,.25,0,-.25,0],color="#b45309")
  ax.axvline(0,color="#777",ls="--",lw=.8);ax.set_yticks(list(range(n,0,-1))+[0]);ax.set_yticklabels([r["study_key"] for r in rows]+["Pooled "+q["model"]],fontsize=7)
  ax.set_xlabel("Hedges g with 95% confidence interval");ax.set_title(family.replace("_"," ").title()+" - independent reconstruction",fontsize=11)
  ax.grid(axis="x",alpha=.2);fig.tight_layout();fig.savefig(out/"figures"/(family+".svg"));fig.savefig(out/"figures"/(family+".png"),dpi=150);plt.close(fig)

def source_comparisons(results,ledger):
 comparisons=[]
 for q in ledger["checks"]:
  a=get(results,q["path"]);diff=None
  if q["kind"]=="unprinted":passed=None
  elif q["kind"]=="exact":passed=a==int(q["numeric_target"])
  elif q["kind"]=="relation":passed=a<float(q["numeric_target"])
  else:
   diff=float(a)-float(q["numeric_target"]);passed=abs(diff)<=float(q["tolerance"])
  comparisons.append(dict(q,actual=a,difference=diff,passes_source_display=passed))
 assert len(comparisons)==336
 return comparisons

def calculate(inputs,meta,targets,out):
 results={"families":{},"raw_source_records":{},"metadata_used":meta}
 for family,model in targets["models"].items():
  generic=family in ["overall_mental","health"]
  f=inputs/(family+("_effects_source001.csv" if generic else "_means_source001.csv"))
  raw=list(csv.DictReader(f.open(encoding="utf8",newline="")))
  results["raw_source_records"][family]=raw;rows=[]
  for r in raw:
   if generic:g,v=float(r["printed_effect"]),float(r["printed_se"])**2
   else:g,v=means(r)
   assert v>0 and math.isfinite(g) and math.isfinite(v)
   rows.append({"row":r["row"],"study_key":r["study_key"],"g":g,"variance":v,"CI_low":g-1.96*math.sqrt(v),"CI_high":g+1.96*math.sqrt(v)})
  q={"pool":pool(rows,model),"rows":{r["row"]:r for r in rows},"supporting":supporting(family,rows,model,meta)}
  if not generic:q["arm_totals"]={k:sum(int(r[k]) for r in raw) for k in ["experimental_n","control_n"]}
  if not generic:
   variations={}
   for method in ["variance_N","variance_N_minus2","exact_J_historical_variance"]:
    alt=[]
    for original,source in zip(rows,raw):
     r=dict(original);a=int(source["experimental_n"]);b=int(source["control_n"]);n=a+b
     if method=="exact_J_historical_variance":
      df=n-2;J=math.exp(math.lgamma(df/2)-math.lgamma((df-1)/2))*math.sqrt(2/df)
      r["g"]=original["g"]/(1-3/(4*n-9))*J
      r["variance"]=n/(a*b)+r["g"]**2/(2*(n-3.94))
     else:r["variance"]=n/(a*b)+r["g"]**2/(2*(n if method=="variance_N" else n-2))
     r["CI_low"]=r["g"]-1.96*math.sqrt(r["variance"]);r["CI_high"]=r["g"]+1.96*math.sqrt(r["variance"]);alt.append(r)
    variations[method]={"pool":pool(alt,model),"rows":{r["row"]:r for r in alt},"supports_primary_rescue":False}
   q["supporting"]["uniform_variance_alternatives"]=variations
  results["families"][family]=q
  save(out/"PARTIAL_COMPUTATIONS.json",results)
 checks=gate_checks(results,targets)
 assert len(checks)==337 and len({q["id"] for q in checks})==337
 save(out/"ALL_ORIGINAL_COMPUTATIONS.json",results);save(out/"ALL337_PRIMARY_CHECKS.json",checks)
 summary={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"complete_families":len(results["families"]),"raw_rows":sum(len(v) for v in results["raw_source_records"].values()),"gates":337,"passed":sum(q["passed"] for q in checks),"all_passed":all(q["passed"] for q in checks),"original_human_trials_repeated":False,"complete_337_and_rule":True}
 save(out/"SUMMARY.json",summary)
 return results,summary

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--authorization",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 auth=json.loads(Path(a.authorization).read_text());assert auth["approved"] is True
 assert os.environ.get("P134_GUARDED")=="1" and sha(Path(__file__))==auth["runner_sha256"]
 inputs=Path(auth["input_root"]);meta_path=Path(auth["metadata_path"]);target_path=Path(auth["targets_path"])
 assert sha(meta_path)==auth["metadata_sha256"] and sha(target_path)==auth["targets_sha256"]
 out=Path(a.out);assert not out.exists();out.mkdir(parents=True)
 meta=json.loads(meta_path.read_text())["metadata"];targets=json.loads(target_path.read_text())
 results,summary=calculate(inputs,meta,targets,out)
 figures(results,out)
 support_path=Path(auth["supporting_targets_path"]);assert sha(support_path)==auth["supporting_targets_sha256"]
 save(out/"ALL_SUPPORTING_SOURCE_COMPARISONS.json",source_comparisons(results,json.loads(support_path.read_text())))
 summary["mode"]=auth["mode"];save(out/"SUMMARY.json",summary)
 return 0 if summary["all_passed"] else 2
if __name__=="__main__":sys.exit(main())
