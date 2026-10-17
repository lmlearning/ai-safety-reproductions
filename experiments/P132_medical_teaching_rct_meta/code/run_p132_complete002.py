"""P132 complete quantitative reconstruction; no work on import."""
from pathlib import Path
import argparse,csv,json,math,itertools,datetime,time,os,hashlib
os.environ.update(OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1")
import numpy as np
from scipy.stats import norm,chi2,qmc
B=Path(__file__).resolve().parents[1];P=B/"papers/P132_medical_teaching_rct_meta"
FIELDS=["gai_mean","gai_sd","traditional_mean","traditional_sd"]
Z95=float(norm.ppf(.975))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+"\n",encoding="utf8")
def readrows(path):
 rows=list(csv.DictReader(path.open(encoding="utf8",newline="")))
 assert len(rows)==17 and len({(r["outcome"],r["study"]) for r in rows})==17
 return [{**r,**{f:float(r[f]) for f in FIELDS},**{f:int(r[f]) for f in ["gai_n","traditional_n"]}} for r in rows]
def effects(rows):
 ans={}
 for r in rows:
  a,b=r["gai_n"],r["traditional_n"];n=a+b
  sd=math.sqrt(((a-1)*r["gai_sd"]**2+(b-1)*r["traditional_sd"]**2)/(n-2))
  assert a>1 and b>1 and r["gai_sd"]>0 and r["traditional_sd"]>0 and sd>0
  g=(1-3/(4*n-9))*(r["gai_mean"]-r["traditional_mean"])/sd
  v=n/(a*b)+g*g/(2*(n-3.94))
  ans[r["outcome"]+"/"+r["study"]]=dict(**r,g=g,variance=v,se=math.sqrt(v),lower=g-Z95*math.sqrt(v),upper=g+Z95*math.sqrt(v))
 return ans
def pool(es,kind="random"):
 assert es
 y=np.asarray([r["g"] for r in es]);v=np.asarray([r["variance"] for r in es]);w=1/v
 k=len(es);df=k-1;sw=float(w.sum());fm=float(w@y/sw);Q=float(w@((y-fm)**2))
 C=sw-float(w@w)/sw;tau=max(0,(Q-df)/C) if k>1 else 0.
 if kind=="fixed":tau=0.
 rw=1/(v+tau);sr=float(rw.sum());g=float(rw@y/sr);se=math.sqrt(1/sr)
 return dict(k=k,gai_n=sum(r["gai_n"] for r in es),traditional_n=sum(r["traditional_n"] for r in es),smd=g,se=se,variance=1/sr,lower=g-Z95*se,upper=g+Z95*se,p=float(2*norm.sf(abs(g/se))),Z=abs(g/se),Q=Q,df=df,tau2=tau,I2=100*max(0,(Q-df)/Q) if k>1 and Q>0 else 0.,heterogeneity_p=float(chi2.sf(Q,df)) if df else None,row_keys=[r["outcome"]+"/"+r["study"] for r in es],weights_percent=list(map(float,100*rw/sr)),model=kind)
def between(groups):
 w=np.asarray([1/r["variance"] for r in groups]);g=np.asarray([r["smd"] for r in groups]);m=float(w@g/w.sum());Q=float(w@((g-m)**2));df=len(groups)-1
 return dict(Q=Q,df=df,p=float(chi2.sf(Q,df)),I2=100*max(0,(Q-df)/Q) if Q>0 else 0.,fixed_subgroup_center=m)

def analyse(rows,targets,kind="random"):
 es=effects(rows);ps={}
 for name in ["knowledge","skill","satisfaction"]:
  ps[name]=pool([r for r in es.values() if r["outcome"]==name],kind)
 bs={}
 for family,groups in targets["groups"].items():
  values=[]
  for group,ids in groups.items():
   selected=[es[("knowledge_delayed/" if key.endswith("_delayed") else "knowledge/")+key] for key in ids]
   result=pool(selected,kind);ps[family+"/"+group]=result;values.append(result)
  bs[family]=between(values)
 return dict(effects=es,pools=ps,between=bs)
def targetmap(t):
 return {**t["pooled_original_targets"],**{r["family"]+"/"+r["name"]:r for r in t["subgroup_original_targets"]}}
def category(lo,hi):
 return "positive" if lo>0 else "negative" if hi<0 else "includes_zero"
def sign(g):return 1 if g>0 else -1 if g<0 else 0
def compare(actual,expected,tolerance,exact=False):
 if isinstance(expected,str) and expected.startswith("<"):
  return actual<float(expected[1:])
 return actual==float(expected) if exact else abs(actual-float(expected))<=tolerance+1e-9
def gates(a,t,strict=False):
 out=[]
 for name,target in targetmap(t).items():
  r=a["pools"][name]
  for f in ["k","gai_n","traditional_n","df","smd","lower","upper","p","I2"]:
   e=target[f] if f!="df" else target["k"]-1;ex=f in ["k","gai_n","traditional_n","df"]
   tol=1.5 if f=="I2" else .00015 if name=="satisfaction" and f=="p" else .015
   if strict and not ex and not str(e).startswith("<"):
    tol=.5*10**(-len(str(e).split(".")[1]) if "." in str(e) else 0)
   out.append(dict(key=name+"/"+f,actual=r[f],target=e,tolerance=0 if ex else tol,passed=compare(r[f],e,tol,ex)))
  for f,val,e in [("point_direction",sign(r["smd"]),sign(float(target["smd"]))),("CI_class",category(r["lower"],r["upper"]),category(float(target["lower"]),float(target["upper"])))]:
   out.append(dict(key=name+"/"+f,actual=val,target=e,passed=val==e))
 for name,target in t["between_group_original_targets"].items():
  r=a["between"][name]
  for f in ["Q","p","I2","df"]:
   e=target[f];tol=1.5 if f=="I2" else .015
   if strict and f!="df":tol=.5*10**(-len(str(e).split(".")[1]) if "." in str(e) else 0)
   out.append(dict(key="between/"+name+"/"+f,actual=r[f],target=e,tolerance=0 if f=="df" else tol,passed=compare(r[f],e,tol,f=="df")))
  out.append(dict(key="between/"+name+"/significance",actual=r["p"]<.05,target=float(target["p"])<.05,passed=(r["p"]<.05)==(float(target["p"])<.05)))
 return out

def perturbations(rows,precision,box):
 base=np.asarray([r[f] for r in rows for f in FIELDS]);width=[]
 for r in precision["rows"]:
  for field in r["fields"]:
   v=float(field["literal_half_unit"])
   if box=="B" and r["study"]=="Svendsen2024" and field["field"]=="gai_sd":v=.05
   width.append(v)
 half=np.asarray(width);assert len(base)==len(half)==68
 def emit(label,x):
  changed=[dict(r,**{f:float(x[4*i+j]) for j,f in enumerate(FIELDS)}) for i,r in enumerate(rows)]
  return label,changed,list(map(float,x))
 yield emit("nominal",base)
 for i in range(68):
  for side in [-1,1]:
   v=base.copy();v[i]+=side*half[i];yield emit("coordinate_%d_%d"%(i,side),v)
 for i in range(17):
  for n,bits in enumerate(itertools.product([-1,1],repeat=4)):
   v=base.copy();v[4*i:4*i+4]+=np.asarray(bits)*half[4*i:4*i+4];yield emit("row_%d_corner_%d"%(i,n),v)
 for side in [-1,1]:yield emit("global_%d"%side,base+side*half)
 seq=qmc.Sobol(d=68,scramble=False).random_base2(m=10)
 for i,s in enumerate(seq):yield emit("joint_corner_%d"%i,base+np.where(s>=.5,1,-1)*half)
 for i,s in enumerate(seq):yield emit("joint_interior_%d"%i,base+(2*s-1)*half)
def compact(a):
 return dict(pools={n:{k:v for k,v in r.items() if k not in ["row_keys","weights_percent"]} for n,r in a["pools"].items()},between=a["between"])
def supporting(a,t,intermediate):
 checks=[]
 for name,target in t["pooled_original_targets"].items():
  for f in ["tau2","Q","df","heterogeneity_p","Z"]:
   e=target[f];r=a["pools"][name][f];tol=.5*10**(-len(str(e).split(".")[1]) if "." in str(e) else 0)
   checks.append(dict(key=name+"/"+f,actual=r,target=e,passed=compare(r,e,tol,f=="df"),tolerance=tol))
 for target in intermediate["rows"]:
  key=target["outcome"]+"/"+target["study"];e=a["effects"][key];pool_=a["pools"][target["outcome"]]
  w=pool_["weights_percent"][pool_["row_keys"].index(key)]
  for f in ["g","lower","upper","weight_percent"]:
   v=w if f=="weight_percent" else e[f];expected=target[f];tol=.05 if f=="weight_percent" else .005
   checks.append(dict(key=key+"/"+f,actual=v,target=expected,tolerance=tol,passed=compare(v,expected,tol)))
 return checks

def extra_controls(a,t,rows):
 es=a["effects"];loo={}
 for name,p in a["pools"].items():
  loo[name]={}
  for omit in p["row_keys"]:
   remaining=[es[k] for k in p["row_keys"] if k!=omit]
   loo[name][omit]={kind:pool(remaining,kind) for kind in ["random","fixed"]}
 bloo={}
 for family,groups in t["groups"].items():
  keys={group:[("knowledge_delayed/" if s.endswith("_delayed") else "knowledge/")+s for s in ids] for group,ids in groups.items()}
  bloo[family]={}
  for omit in sorted(set(sum(keys.values(),[]))):
   bloo[family][omit]={kind:between([pool([es[k] for k in ids if k!=omit],kind) for ids in keys.values()]) for kind in ["random","fixed"]}
 timing=[dict(r) for r in rows]
 src=next(r for r in rows if r["study"]=="Cicek2024_immediate")
 for r in timing:
  if r["study"]=="Cicek2024_delayed":
   for f in FIELDS:r[f]=src[f]
 return dict(fixed_complete=analyse(rows,t,"fixed"),leave_one_row_out=loo,between_leave_one_row_out=bloo,reused_immediate_complete=analyse(timing,t))
def plots(a,out):
 import matplotlib
 matplotlib.use("Agg")
 import matplotlib.pyplot as plt
 from matplotlib.patches import Polygon
 for name in ["knowledge","skill","satisfaction"]:
  p=a["pools"][name];es=[a["effects"][key] for key in p["row_keys"]]
  fig,ax=plt.subplots(figsize=(9,max(3,.44*len(es)+1.8)))
  for i,r in enumerate(es):
   ax.plot([r["lower"],r["upper"]],[i,i],color="#334f64");ax.scatter([r["g"]],[i],s=30+p["weights_percent"][i],color="#177578")
  j=len(es)+.4;ax.add_patch(Polygon([(p["lower"],j),(p["smd"],j-.22),(p["upper"],j),(p["smd"],j+.22)],color="#177578"))
  ax.set_yticks(list(range(len(es)))+[j],[r["study"] for r in es]+["Complete pooled result"])
  ax.axvline(0,color="grey",linewidth=.8);ax.invert_yaxis();ax.set_xlabel("Hedges g (GAI minus traditional teaching)");ax.set_title(name.title()+" | all published comparisons");fig.tight_layout()
  for ext in ["png","svg"]:fig.savefig(out/("forest_"+name+"."+ext),dpi=150)
  plt.close(fig)
 es=[a["effects"][key] for key in a["pools"]["knowledge"]["row_keys"]]
 fig,ax=plt.subplots();ax.scatter([r["g"] for r in es],[r["se"] for r in es],facecolors="none",edgecolors="#177578");ax.axvline(a["pools"]["knowledge"]["smd"],linestyle="--",color="grey");ax.invert_yaxis();ax.set(xlabel="Hedges g",ylabel="Standard error",title="Knowledge funnel: all 11 studies");fig.tight_layout()
 for ext in ["png","svg"]:fig.savefig(out/("knowledge_funnel."+ext),dpi=150)
 plt.close(fig)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",required=True);ap.add_argument("--output",required=True);ap.add_argument("--mode",choices=["synthetic","original"],required=True);args=ap.parse_args()
 out=Path(args.output).resolve();assert out.is_relative_to(P.resolve()) and not out.exists();out.mkdir(parents=True)
 start=time.monotonic();rows=readrows(Path(args.input));t=json.loads((P/"ORIGINAL_TARGETS_AND_COMPLETE_COHORTS001.json").read_text(encoding="utf8"))
 precision=json.loads((P/"SOURCE_INPUT_PRECISION_INVENTORY001.json").read_text(encoding="utf8"));inter=json.loads((P/"ORIGINAL_INTERMEDIATE_LITERAL_TARGETS001.json").read_text(encoding="utf8"))
 a=analyse(rows,t);primary=gates(a,t);strict=gates(a,t,True);support=supporting(a,t,inter)
 save(out/"NOMINAL_COMPLETE_ANALYSIS.json",a);save(out/"PRIMARY_GATES.json",primary);save(out/"STRICT_SOURCE_DIAGNOSTICS.json",strict);save(out/"SUPPORTING_INTERMEDIATES.json",support)
 save(out/"COMPLETE_FIXED_LOO_TIMING_CONTROLS.json",extra_controls(a,t,rows))
 counts={};ranges={};classification_changes=[];compatibility={};nominal_stats=compact(a)
 with (out/"ALL4918_PRECISION_CONTROLS.jsonl").open("x",encoding="utf8") as f:
  for box in ["A","B"]:
   count=0;compatible=0;strict_compatible=0
   for label,changed,values in perturbations(rows,precision,box):
    result=analyse(changed,t);checks=gates(result,t);stats=compact(result)
    strict_checks=gates(result,t,True)
    compatible+=all(c["passed"] for c in checks);strict_compatible+=all(c["passed"] for c in strict_checks)
    record=dict(box=box,index=count,label=label,input_fields_order=FIELDS,input_values=values,analysis=stats,target_checks=checks,strict_target_checks=strict_checks)
    f.write(json.dumps(record,separators=(",",":"),allow_nan=False)+"\n")
    for family,results in stats.items():
     for name,r in results.items():
      for field,value in r.items():
       if not isinstance(value,(int,float)) or isinstance(value,bool):continue
       key=box+"/"+family+"/"+name+"/"+field
       nominal=nominal_stats[family][name][field]
       old=ranges.setdefault(key,dict(min=value,max=value,nominal=nominal,worst_absolute_departure=0.))
       old["worst_absolute_departure"]=max(old["worst_absolute_departure"],abs(value-nominal))
       old["min"]=min(old["min"],value);old["max"]=max(old["max"],value)
    changed_classes=[c["key"] for c,base in zip(checks,primary) if c["key"].endswith(("/point_direction","/CI_class","/significance")) and c["actual"]!=base["actual"]]
    if changed_classes:classification_changes.append(dict(box=box,index=count,label=label,changed=changed_classes))
    count+=1
   assert count==2459;counts[box]=count;compatibility[box]=dict(primary_whole_analysis_compatible=compatible,strict_whole_analysis_compatible=strict_compatible,total=count)
 save(out/"SAMPLED_PRECISION_RANGE_SUMMARY.json",dict(counts=counts,whole_analysis_target_compatibility=compatibility,ranges=ranges,qualitative_changes=classification_changes,interpretation="Finite fixed controls; not certified global bounds or confidence intervals; no rescue."))
 plots(a,out)
 passed=all(c["passed"] for c in primary)
 save(out/"SUMMARY.json",dict(paper_id="P132",mode=args.mode,utc_end=now(),elapsed_seconds=time.monotonic()-start,complete_rows=17,forest_rows=16,complete_pools=11,complete_between_tests=4,primary_passed=sum(c["passed"] for c in primary),primary_total=len(primary),central_result_reproduced=passed and args.mode=="original",full_reproduction=False,control_counts=counts,supporting_passed=sum(c["passed"] for c in support),supporting_total=len(support),strict_passed=sum(c["passed"] for c in strict),strict_total=len(strict)))
 files=[]
 for path in sorted(out.iterdir()):
  if path.is_file():
   with path.open("rb") as stream: digest=hashlib.file_digest(stream,"sha256").hexdigest()
   files.append(dict(absolute_path=str(path.resolve()),bytes=path.stat().st_size,sha256=digest))
 save(out/"OUTPUT_MANIFEST.json",dict(files=files,mode=args.mode,input_path=str(Path(args.input).resolve())))
 return 0 if passed else 2
if __name__=="__main__":raise SystemExit(main())
