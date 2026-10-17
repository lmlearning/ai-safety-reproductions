"""P132 independent arithmetic/source core. Unexecuted source staging only."""
from pathlib import Path
from decimal import Decimal, getcontext
import json, hashlib, sys, os, time, math
import mpmath as mp
D=Decimal
getcontext().prec=80
mp.mp.dps=80
Z0=D(0);O1=D(1);T2=D(2)
FIELDS=("gai_mean","gai_sd","traditional_mean","traditional_sd")
CRIT=None

def parse_chars(path):
 text=Path(path).read_text(encoding="utf-8-sig")
 rows=[];row=[];cell=[];q=False;i=0
 while i<len(text):
  c=text[i]
  if q:
   if c=='"':
    if i+1<len(text) and text[i+1]=='"':cell.append('"');i+=1
    else:q=False
   else:cell.append(c)
  elif c=='"' and not cell:q=True
  elif c==",":row.append("".join(cell));cell=[]
  elif c=="\n":
   row.append("".join(cell));cell=[]
   if row!=[""]:rows.append(row)
   row=[]
  elif c!="\r":cell.append(c)
  i+=1
 if q:raise ValueError("Unclosed CSV quote")
 if row or cell:row.append("".join(cell));rows.append(row)
 if not rows or len(set(rows[0]))!=len(rows[0]):raise ValueError("CSV header")
 if any(len(x)!=len(rows[0]) for x in rows[1:]):raise ValueError("CSV dimensions")
 return [dict(zip(rows[0],x)) for x in rows[1:]]

def high_normal_p(x):
 return D(str(mp.erfc(abs(mp.mpf(str(x)))/mp.sqrt(2))))
def critical():
 global CRIT
 if CRIT is None:CRIT=D(str(mp.sqrt(2)*mp.erfinv(mp.mpf(".95"))))
 return CRIT
def chi_survival(q,df):
 if df==0:return None
 if df<0:raise ValueError("Negative chi degrees")
 x=max(Z0,D(q))/T2
 # Integer-df gamma recurrences independently avoid SciPy survival functions.
 if df%2==0:
  term=O1;s=O1
  for j in range(1,df//2):term*=x/D(j);s+=term
  return (-x).exp()*s
 out=D(str(mp.erfc(mp.sqrt(mp.mpf(str(x))))))
 shape=D(".5");power=x.sqrt();gamma=D(str(mp.sqrt(mp.pi)));ex=(-x).exp()
 for _ in range((df-1)//2):
  out+=power*ex/(shape*gamma)
  gamma*=shape;power*=x;shape+=O1
 return max(Z0,min(O1,out))

def row_key(row):return row["outcome"]+"/"+row["study"]
def effect(row):
 raw={f:D(row[f]) for f in FIELDS}
 n1=int(row["gai_n"]);n2=int(row["traditional_n"]);N=D(n1+n2)
 if n1<=1 or n2<=1 or raw["gai_sd"]<=0 or raw["traditional_sd"]<=0:raise ValueError("Invalid original arm")
 pooled=((D(n1-1)*raw["gai_sd"]**2+D(n2-1)*raw["traditional_sd"]**2)/(N-T2)).sqrt()
 correction=O1-D(3)/(D(4)*N-D(9))
 g=correction*(raw["gai_mean"]-raw["traditional_mean"])/pooled
 variance=N/(D(n1)*D(n2))+g*g/(T2*(N-D("3.94")))
 se=variance.sqrt()
 return dict(row,gai_n=n1,traditional_n=n2,**raw,g=g,variance=variance,se=se,lower=g-critical()*se,upper=g+critical()*se)

def pool(keys,effects,random=True):
 if not keys:raise ValueError("Empty original complete pool")
 rows=[effects[x] for x in keys];g=[x["g"] for x in rows];v=[x["variance"] for x in rows];k=len(rows);df=k-1
 fw=[O1/x for x in v];s=sum(fw,Z0)
 fixed=sum((w*y for w,y in zip(fw,g)),Z0)/s
 Q=sum((w*(y-fixed)**2 for w,y in zip(fw,g)),Z0) if k>1 else Z0
 C=s-sum((w*w for w in fw),Z0)/s
 tau=max(Z0,(Q-D(df))/C) if k>1 else Z0
 w=[O1/(vv+tau) for vv in v] if random else fw
 sw=sum(w,Z0);smd=sum((ww*y for ww,y in zip(w,g)),Z0)/sw;var=O1/sw;se=var.sqrt();z=smd/se
 return {"k":k,"gai_n":sum(x["gai_n"] for x in rows),"traditional_n":sum(x["traditional_n"] for x in rows),
  "smd":smd,"se":se,"variance":var,"lower":smd-critical()*se,"upper":smd+critical()*se,
  "p":high_normal_p(z),"Z":abs(z),"Q":Q,"df":df,"tau2":tau if random else Z0,
  "I2":D(100)*max(Z0,(Q-D(df))/Q) if Q>0 else Z0,"heterogeneity_p":chi_survival(Q,df),
  "row_keys":list(keys),"weights_percent":[D(100)*ww/sw for ww in w],"model":"random" if random else "fixed"}

def between(subgroups):
 if len(subgroups)!=2:raise ValueError("Original two-level design")
 w=[O1/x["variance"] for x in subgroups];center=sum((ww*x["smd"] for ww,x in zip(w,subgroups)),Z0)/sum(w,Z0)
 Q=sum((ww*(x["smd"]-center)**2 for ww,x in zip(w,subgroups)),Z0);df=len(w)-1
 return {"Q":Q,"df":df,"p":chi_survival(Q,df),"I2":D(100)*max(Z0,(Q-D(df))/Q) if Q>0 else Z0,"fixed_subgroup_center":center}

def membership(rows,targets):
 ids=[row_key(x) for x in rows]
 if len(ids)!=17 or len(set(ids))!=17:raise ValueError("Full17 input rows required")
 primary={}
 for name,k in [("knowledge",11),("skill",2),("satisfaction",3)]:
  keys=[row_key(x) for x in rows if x["outcome"]==name]
  if len(keys)!=k:raise ValueError("Whole source pool geometry")
  primary[name]=keys
 candidates={x["study"]:row_key(x) for x in rows if x["outcome"] in ["knowledge","knowledge_delayed"]}
 if len(candidates)!=12:raise ValueError("Whole knowledge/timing identity")
 for family,groups in targets["groups"].items():
  for name,studies in groups.items():
   if len(studies)!=len(set(studies)) or any(x not in candidates for x in studies):raise ValueError("Original subgroup identities")
   # Match author-declared study sequence, independently resolve all source effects.
   primary[family+"/"+name]=[candidates[x] for x in studies]
 if len(primary)!=11 or list(targets["groups"])!=["geography","duration","course","assessment"]:raise ValueError("Complete11 pools/four between designs")
 return primary

def analyze(rows,targets,random=True,omit=None):
 effects={row_key(r):effect(r) for r in rows};groups=membership(rows,targets);pools={}
 for name,keys in groups.items():
  kept=[x for x in keys if x!=omit]
  if kept:pools[name]=pool(kept,effects,random)
 between_results={}
 for family,levels in targets["groups"].items():
  relevant=[pools[family+"/"+name] for name in levels if family+"/"+name in pools]
  between_results[family]=between(relevant) if len(relevant)==2 else None
 return {"effects":effects,"pools":pools,"between":between_results}

def sign(x):return 1 if x>0 else -1 if x<0 else 0
def ci_class(x):return "positive" if x["lower"]>0 else "negative" if x["upper"]<0 else "includes_zero"
def halfunit(literal):
 s=str(literal).lstrip("<>=")
 return D(5)*D(10)**(-len(s.split(".")[1])-1) if "." in s else D(".5")
def target_test(actual,target,tolerance=None):
 if isinstance(target,str) and target.startswith("<"):return actual<D(target[1:])
 if isinstance(target,str) and target.startswith(">"):return actual>D(target[1:])
 return abs(D(actual)-D(str(target)))<=tolerance if tolerance is not None else actual==target

def source_checks(analysis,targets,strict=False):
 checks=[]
 def add(key,actual,target,tol=None):
  ok=target_test(actual,target,tol)
  record={"key":key,"actual":actual,"target":target,"passed":ok}
  if tol is not None:record["tolerance"]=tol
  elif isinstance(actual,(D,int,float)) and not isinstance(actual,bool) and not str(target).startswith(("<",">")):record["tolerance"]=Z0
  if key in {name+"/point_direction" for name in pool_targets}:record["tolerance"]=None
  if key=="course/practice/p" and target=="<0.01":record["tolerance"]=D(".015")
  checks.append(record)
 pool_targets=dict(targets["pooled_original_targets"])
 for r in targets["subgroup_original_targets"]:pool_targets[r["family"]+"/"+r["name"]]=r
 for name,target in pool_targets.items():
  p=analysis["pools"][name]
  for field in ["k","gai_n","traditional_n"]:add(name+"/"+field,p[field],target[field])
  add(name+"/df",p["df"],target["k"]-1)
  for field in ["smd","lower","upper","p","I2"]:
   literal=target[field]
   if str(literal).startswith("<"):tol=None
   elif strict:tol=halfunit(literal)+D("1e-9")
   else:tol=(D("1.5") if field=="I2" else D(".00015") if name=="satisfaction" and field=="p" else D(".015"))+D("1e-9")
   add(name+"/"+field,p[field],literal,tol)
  add(name+"/point_direction",sign(p["smd"]),sign(D(target["smd"])))
  published={"lower":D(target["lower"]),"upper":D(target["upper"])}
  add(name+"/CI_class",ci_class(p),ci_class(published))
 for name,target in targets["between_group_original_targets"].items():
  p=analysis["between"][name]
  for field in ["Q","p","I2"]:
   tol=(halfunit(target[field]) if strict else D("1.5") if field=="I2" else D(".015"))+D("1e-9")
   add("between/"+name+"/"+field,p[field],target[field],tol)
  add("between/"+name+"/df",p["df"],target["df"])
  add("between/"+name+"/significance",p["p"]<D(".05"),D(target["p"])<D(".05"))
 if len(checks)!=141:raise ValueError("All141 gates required")
 return checks

def strict_intermediates(analysis,targets,raw_targets):
 out=[]
 def add(key,actual,target):
  tol=halfunit(target)
  decision=actual==target if isinstance(target,int) else target_test(actual,target,tol+D("1e-9"))
  out.append({"key":key,"actual":actual,"target":target,"tolerance":tol,"passed":decision})
 for name,t in targets["pooled_original_targets"].items():
  for f in ["tau2","Q","df","heterogeneity_p","Z"]:add(name+"/"+f,analysis["pools"][name][f],t[f])
 for r in raw_targets["rows"]:
  key=r["outcome"]+"/"+r["study"];a=analysis["effects"][key];p=analysis["pools"][r["outcome"]];ix=p["row_keys"].index(key)
  for field in ["g","lower","upper"]:add(key+"/"+field,a[field],r[field])
  add(key+"/weight_percent",p["weights_percent"][ix],r["weight_percent"])
 return out

def complete_controls(rows,targets):
 nominal=analyze(rows,targets);fixed=analyze(rows,targets,random=False);groups=membership(rows,targets)
 loo={}
 for name,keys in groups.items():
  entries={}
  for omitted in keys:
   kept=[x for x in keys if x!=omitted]
   entries[omitted]={"random":pool(kept,nominal["effects"],True),"fixed":pool(kept,nominal["effects"],False)}
  loo[name]=entries
 between_loo={}
 for family,levels in targets["groups"].items():
  union=list(dict.fromkeys(x for name in levels for x in groups[family+"/"+name]))
  entries={}
  for omitted in union:
   r=[];f=[]
   for name in levels:
    kept=[x for x in groups[family+"/"+name] if x!=omitted]
    r.append(pool(kept,nominal["effects"],True));f.append(pool(kept,nominal["effects"],False))
   entries[omitted]={"random":between(r),"fixed":between(f)}
  between_loo[family]=entries
 copied=[dict(x) for x in rows]
 immediate=next(r for r in rows if r["study"]=="Cicek2024_immediate")
 delayed=next(r for r in copied if r["study"]=="Cicek2024_delayed")
 for field in FIELDS:delayed[field]=immediate[field]
 return {"fixed_complete":fixed,"leave_one_row_out":loo,"between_leave_one_row_out":between_loo,"reused_immediate_complete":analyze(copied,targets)}

def source_widths(rows,path):
 data=json.loads(Path(path).read_text(encoding="utf-8"))
 if data["source_row_keys"]!=[row_key(x) for x in rows] or data["input_fields_order"]!=list(FIELDS):raise ValueError("Frozen original width identity/order")
 out={box:[D(x) for x in data["halfunits"][box]] for box in ["A","B"]}
 if any(len(v)!=68 or any(x<=0 for x in v) for v in out.values()):raise ValueError("Complete68 positive source halfunits")
 return out

def control_inputs(rows,box,widths):
 # Standard Joe-Kuo Sobol sequence is permitted by the public contract, only for input geometry.
 from scipy.stats import qmc
 nominal=[D(row[f]) for row in rows for f in FIELDS]
 halves=list(widths[box])
 low=[x-h for x,h in zip(nominal,halves)];high=[x+h for x,h in zip(nominal,halves)]
 if any(low[4*i+j]<=0 for i in range(17) for j in [1,3]):raise ValueError("Source precision SD crosseszero; no silent clipping")
 yield "nominal",nominal
 for j in range(68):
  for label,endpoint in [("minus",low[j]),("plus",high[j])]:
   x=nominal.copy();x[j]=endpoint;yield "coordinate_"+str(j)+"_"+("-1" if label=="minus" else "1"),x
 for i in range(17):
  for pattern in range(16):
   x=nominal.copy()
   for j in range(4):x[4*i+j]=high[4*i+j] if pattern&(1<<(3-j)) else low[4*i+j]
   yield "row_"+str(i)+"_corner_"+str(pattern),x
 yield "global_-1",low
 yield "global_1",high
 sequence=qmc.Sobol(d=68,scramble=False).random_base2(m=10)
 for i,point in enumerate(sequence):
  yield "joint_corner_"+str(i),[high[j] if u>=.5 else low[j] for j,u in enumerate(point)]
 for i,point in enumerate(sequence):
  yield "joint_interior_"+str(i),[low[j]+(high[j]-low[j])*D(float(u)) for j,u in enumerate(point)]

def apply_input(rows,values):
 if len(values)!=68:raise ValueError("Complete68 fields")
 result=[dict(x) for x in rows]
 for i,row in enumerate(result):
  for j,f in enumerate(FIELDS):row[f]=str(values[4*i+j])
 return result

def compact_analysis(a):
 return {"pools":{name:{k:v for k,v in p.items() if k not in ["row_keys","weights_percent"]} for name,p in a["pools"].items()},"between":a["between"]}

def flatten_stats(a):
 out={}
 for kind in ["pools","between"]:
  for name,p in a[kind].items():
   for key,v in p.items():
    if isinstance(v,(D,int,float)) and not isinstance(v,bool):out[kind+"/"+name+"/"+key]=D(v)
 return out

def encode_decimal(x):return str(x) if isinstance(x,D) else x
def save_new(path,obj):
 p=Path(path)
 if p.exists():raise FileExistsError(p)
 p.write_text(json.dumps(obj,indent=2,default=encode_decimal,ensure_ascii=True)+"\n",encoding="utf-8")
def hash_stream(path):
 h=hashlib.sha256();size=0
 with Path(path).open("rb") as f:
  while True:
   b=f.read(1024*1024)
   if not b:break
   h.update(b);size+=len(b)
 return {"absolute_path":str(Path(path).resolve()),"bytes":size,"sha256":h.hexdigest()}
class StreamingCompare:
 def __init__(self,path,failures):
  self.f=Path(path).open("x",encoding="utf-8");self.bad=Path(failures).open("x",encoding="utf-8");self.count=0;self.failures=0
 def check(self,key,main,own,numeric=False):
  error=None;tol=D("1e-9") if numeric else None
  if numeric:
   try:error=abs(D(str(main))-D(str(own)));passed=error<=tol
   except (ValueError,ArithmeticError,TypeError):passed=False
  else:passed=main==own
  row={"key":key,"main":main,"independent":own,"tolerance":tol,"absolute_difference":error,"passed":passed}
  text=json.dumps(row,default=encode_decimal,separators=(",",":"),ensure_ascii=True)+"\n";self.f.write(text)
  self.count+=1
  if not passed:self.failures+=1;self.bad.write(text)
 def tree(self,key,main,own):
  if isinstance(own,dict):
   self.check(key+"/keys",set(main)==set(own) if isinstance(main,dict) else False,True)
   for k,v in own.items():
    if not isinstance(main,dict) or k not in main:self.check(key+"/"+k,"missing",v);continue
    self.tree(key+"/"+k,main[k],v)
  elif isinstance(own,list):
   self.check(key+"/length",len(main) if isinstance(main,list) else None,len(own))
   if isinstance(main,list):
    for i,(a,b) in enumerate(zip(main,own)):self.tree(key+"/"+str(i),a,b)
  elif isinstance(own,(D,int,float)) and not isinstance(own,bool):self.check(key,main,own,numeric=True)
  else:self.check(key,main,own)
 def gates(self,key,main,own):
  self.check(key+"/census",len(main),len(own))
  self.check(key+"/ordered_keys",[x["key"] for x in main],[x["key"] for x in own])
  for i,(a,b) in enumerate(zip(main,own)):
   label=key+"/"+str(i);self.check(label+"/passed",a["passed"],b["passed"]);self.tree(label+"/actual",a["actual"],b["actual"])
   try:ta=D(str(a["target"]));tb=D(str(b["target"]));self.check(label+"/target",ta,tb,numeric=True)
   except (ValueError,ArithmeticError):self.check(label+"/target",a["target"],b["target"])
   if "tolerance" in b:self.check(label+"/tolerance",a.get("tolerance"),b["tolerance"],numeric=b["tolerance"] is not None)
 def close(self):self.f.close();self.bad.close()

def opaque_preflight(freeze,input_path,mode,run,audit):
 f=json.loads(Path(freeze).read_text(encoding="utf-8"));seen=set();self_ok=False;input_ok=False
 for item in f["files"]:
  p=Path(item["absolute_path"]).resolve()
  if p in seen:raise ValueError("Duplicate frozen file")
  seen.add(p)
  measured=hash_stream(p)
  if measured["bytes"]!=item["bytes"] or measured["sha256"]!=item["sha256"]:raise ValueError("Frozen identity changed:"+str(p))
  if p==Path(__file__).resolve():self_ok=True
  if p==Path(input_path).resolve():input_ok=True
 if not self_ok or not input_ok:raise ValueError("Executable or complete input absent from freeze")
 config=f.get("config",{});paper=Path(__file__).resolve().parent.parent/"papers/P132_medical_teaching_rct_meta"
 targets=Path(config.get("targets_path",paper/"ORIGINAL_TARGETS_AND_COMPLETE_COHORTS001.json")).resolve()
 intermediates=Path(config.get("intermediates_path",paper/"ORIGINAL_INTERMEDIATE_LITERAL_TARGETS001.json")).resolve()
 widths=Path(config.get("widths_path",paper/"independent_auditor_preparation001/INDEPENDENT_SOURCE_WIDTH_GEOMETRY001.json")).resolve()
 if targets not in seen or intermediates not in seen or widths not in seen:raise ValueError("Independent source targets/widths absent from freeze")
 if mode=="synthetic":
  original=(paper/"sources").resolve()
  if Path(input_path).resolve().is_relative_to(original):raise ValueError("Fake input is original measured source")
  for p in [Path(run).resolve(),Path(audit).resolve()]:
   if p.is_relative_to(original) or original.is_relative_to(p):raise ValueError("Fake output overlaps original source")
  def hook(event,args):
   if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):return
   p=Path(os.fsdecode(args[0])).resolve()
   if p.is_relative_to(original):raise PermissionError("Fake auditor cannot open original measured source:"+str(p))
  sys.addaudithook(hook)
 return f,targets,intermediates,widths

def verify_run_manifest(run):
 manifest=json.loads((run/"OUTPUT_MANIFEST.json").read_text(encoding="utf-8"));items=manifest.get("files",manifest) if isinstance(manifest,dict) else manifest;listed=set()
 for item in items:
  p=Path(item.get("absolute_path",item.get("path",item.get("name"))))
  if not p.is_absolute():p=run/p
  p=p.resolve()
  if not p.is_relative_to(run.resolve()) or p in listed:raise ValueError("Run output manifest scope")
  listed.add(p)
  measured=hash_stream(p)
  if measured["bytes"]!=item["bytes"] or measured["sha256"]!=item["sha256"]:raise ValueError("Run manifest mismatch")
 return listed

def precision_audit(rows,targets,run,audit,cmp,widths):
 nominal=analyze(rows,targets);nominal_stats=flatten_stats(compact_analysis(nominal));nominal_gates=source_checks(nominal,targets)
 qualitative_keys=[x["key"] for x in nominal_gates if x["key"].endswith(("/point_direction","/CI_class","/significance"))]
 nominal_qual={x["key"]:x["actual"] for x in nominal_gates if x["key"] in qualitative_keys}
 summary={"counts":{},"ranges":{},"qualitative_changes":[],"whole_analysis_target_compatibility":{},"interpretation":"Finite fixed controls; not certified global bounds or confidence intervals; no rescue."}
 inputs_order=list(FIELDS)
 with (run/"ALL4918_PRECISION_CONTROLS.jsonl").open("r",encoding="utf-8") as main_stream,(audit/"INDEPENDENT_ALL4918_PRECISION_CONTROLS.jsonl").open("x",encoding="utf-8") as own_stream:
  for box in ["A","B"]:
   count=0;compatible=0;strict_compatible=0
   for index,(label,values) in enumerate(control_inputs(rows,box,widths)):
    a=analyze(apply_input(rows,values),targets);compact=compact_analysis(a);checks=source_checks(a,targets);strict=source_checks(a,targets,strict=True)
    record={"box":box,"index":index,"label":label,"input_fields_order":inputs_order,"input_values":values,"analysis":compact,"target_checks":checks,"strict_target_checks":strict}
    own_stream.write(json.dumps(record,default=encode_decimal,separators=(",",":"),ensure_ascii=True)+"\n")
    line=main_stream.readline()
    if not line:raise ValueError("Truncated complete precision stream")
    main=json.loads(line);prefix="precision/"+box+"/"+str(index)
    for key in ["box","index","label","input_fields_order"]:cmp.tree(prefix+"/"+key,main[key],record[key])
    cmp.tree(prefix+"/input_values",main["input_values"],values);cmp.tree(prefix+"/analysis",main["analysis"],compact)
    cmp.gates(prefix+"/target_checks",main["target_checks"],checks);cmp.gates(prefix+"/strict_target_checks",main["strict_target_checks"],strict)
    for key,v in flatten_stats(compact).items():
     range_key=box+"/"+key
     if range_key not in summary["ranges"]:summary["ranges"][range_key]={"min":v,"max":v,"nominal":nominal_stats[key],"worst_absolute_departure":abs(v-nominal_stats[key])}
     else:
      rr=summary["ranges"][range_key];rr["min"]=min(rr["min"],v);rr["max"]=max(rr["max"],v);rr["worst_absolute_departure"]=max(rr["worst_absolute_departure"],abs(v-nominal_stats[key]))
    changed=[x["key"] for x in checks if x["key"] in nominal_qual and x["actual"]!=nominal_qual[x["key"]]]
    if changed:summary["qualitative_changes"].append({"box":box,"index":index,"label":label,"changed":changed})
    compatible+=all(x["passed"] for x in checks);strict_compatible+=all(x["passed"] for x in strict);count+=1
   if count!=2459:raise ValueError("Whole2459 source controls per box required")
   summary["counts"][box]=count
   summary["whole_analysis_target_compatibility"][box]={"primary_whole_analysis_compatible":compatible,"strict_whole_analysis_compatible":strict_compatible,"total":count}
  if main_stream.readline():raise ValueError("Additional/unregistered precision stream records")
 return summary

def main_entry(input_path,run,audit,mode,freeze_path):
 audit=Path(audit);run=Path(run)
 if audit.exists():raise FileExistsError("New audit directory required")
 audit.mkdir(parents=True);start=time.time();cmp=None
 try:
  freeze,target_path,intermediate_path,width_path=opaque_preflight(freeze_path,input_path,mode,run,audit)
  listed=verify_run_manifest(run)
  required=["NOMINAL_COMPLETE_ANALYSIS.json","PRIMARY_GATES.json","ALL4918_PRECISION_CONTROLS.jsonl","SUPPORTING_INTERMEDIATES.json","COMPLETE_FIXED_LOO_TIMING_CONTROLS.json","SAMPLED_PRECISION_RANGE_SUMMARY.json"]
  if any((run/x).resolve() not in listed for x in required):raise ValueError("Missing required complete outputs")
  rows=parse_chars(input_path);targets=json.loads(target_path.read_text(encoding="utf-8"));raw_targets=json.loads(intermediate_path.read_text(encoding="utf-8"))
  membership(rows,targets);widths=source_widths(rows,width_path)
  nominal=analyze(rows,targets);primary=source_checks(nominal,targets);strict=source_checks(nominal,targets,strict=True);intermediate=strict_intermediates(nominal,targets,raw_targets);controls=complete_controls(rows,targets)
  cmp=StreamingCompare(audit/"ALL_INDEPENDENT_COMPARISONS.jsonl",audit/"ALL_INDEPENDENT_FAILED_COMPARISONS.jsonl")
  main=json.loads((run/"NOMINAL_COMPLETE_ANALYSIS.json").read_text(encoding="utf-8"));cmp.tree("nominal",main,nominal)
  mainchecks=json.loads((run/"PRIMARY_GATES.json").read_text(encoding="utf-8"));cmp.gates("primary",mainchecks,primary)
  save_new(audit/"INDEPENDENT_NOMINAL_COMPLETE_ANALYSIS.json",nominal);save_new(audit/"INDEPENDENT_PRIMARY_GATES.json",primary);save_new(audit/"INDEPENDENT_STRICT_FINAL_GATES.json",strict)
  save_new(audit/"INDEPENDENT_SUPPORTING_INTERMEDIATES.json",intermediate);save_new(audit/"INDEPENDENT_COMPLETE_FIXED_LOO_TIMING_CONTROLS.json",controls)
  cmp.gates("intermediates",json.loads((run/"SUPPORTING_INTERMEDIATES.json").read_text(encoding="utf-8")),intermediate)
  cmp.tree("fixed_LOO_timing",json.loads((run/"COMPLETE_FIXED_LOO_TIMING_CONTROLS.json").read_text(encoding="utf-8")),controls)
  ranges=precision_audit(rows,targets,run,audit,cmp,widths);save_new(audit/"INDEPENDENT_SAMPLED_PRECISION_RANGE_SUMMARY.json",ranges)
  cmp.tree("ranges",json.loads((run/"SAMPLED_PRECISION_RANGE_SUMMARY.json").read_text(encoding="utf-8")),ranges)
  knowledge=nominal["pools"]["knowledge"];funnel=[{"row_key":key,"g":nominal["effects"][key]["g"],"se":nominal["effects"][key]["se"]} for key in knowledge["row_keys"]]
  save_new(audit/"INDEPENDENT_COMPLETE_KNOWLEDGE_FUNNEL_POINTS.json",funnel)
  cmp.close()
  status={"status":"complete","mode":mode,"checks":cmp.count,"failures":cmp.failures,"all141_primary_checked":True,"primary_passed":sum(x["passed"] for x in primary),"all_primary_passed":all(x["passed"] for x in primary),"precision_controls":4918,"complete_fixed_LOO_timing":True,"elapsed_seconds":time.time()-start,"no_primary_rescue":True,"original_science_rerun":False}
  save_new(audit/"AUDIT_STATUS.json",status)
  save_new(audit/"OUTPUT_MANIFEST.json",{"files":[hash_stream(x) for x in sorted(audit.iterdir()) if x.is_file()]})
  return 0 if cmp.failures==0 else 2
 except BaseException as e:
  import traceback
  if cmp is not None:cmp.close()
  if not (audit/"AUDIT_STATUS.json").exists():save_new(audit/"AUDIT_STATUS.json",{"status":"failed","error":repr(e),"traceback":traceback.format_exc(),"elapsed_seconds":time.time()-start,"original_science_rerun":False})
  return 2
if __name__=="__main__":
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument("--input",required=True);parser.add_argument("--run",required=True);parser.add_argument("--audit",required=True);parser.add_argument("--mode",choices=["synthetic","original"],required=True);parser.add_argument("--freeze",required=True)
 args=parser.parse_args();sys.exit(main_entry(args.input,args.run,args.audit,args.mode,args.freeze))
