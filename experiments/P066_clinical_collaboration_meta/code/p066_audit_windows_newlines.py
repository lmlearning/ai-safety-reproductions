"""Independent 80-digit scalar audit; imports no experiment implementation."""
import pathlib,json,hashlib,datetime as dt,re,shutil
import mpmath as mp
mp.mp.dps=80
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/"papers/P066_clinical_collaboration_meta";RUN=P/"runs/P066-central-002";OUT=P/"audits/P066-audit-002"
assert not OUT.exists();OUT.mkdir(parents=True);shutil.copyfile(__file__,OUT/"auditor.py")
checks=[]
def check(name,value,target,tol=0):
 delta=abs(mp.mpf(value)-mp.mpf(target));checks.append(dict(name=name,value=float(value),target=float(target),tolerance=tol,absolute_error=float(delta),passed=delta<=tol))
def truth(name,condition,detail=None):
 checks.append(dict(name=name,passed=bool(condition),detail=detail))
# Independently reentered from original author R arrays and original Figure2.
manual={"A":{"study":["Kim 2025","Wu 2025"],"event_e":[70,28],"n_e":[114,48],"event_c":[53,13],"n_c":[114,48]},"B":{"study":["Goh 2024","Goh 2025"],"effect":["2.0000","6.5000"],"se":["3.0612","1.9133"]},"C":{"study":["Goh 2024","Goh 2025","Yu He Ke 2025"],"effect":["-1.3667","1.9833","0.5600"],"se":["0.9609","0.8673","1.9515"]}}
manual_targets={"A":{"study":[{"effect":1.32,"ci_low":1.03,"ci_high":1.69,"weight_common":82.0,"weight_random":61.6},{"effect":2.15,"ci_low":1.28,"ci_high":3.63,"weight_common":18.0,"weight_random":38.4}],"common":{"effect":1.44,"ci_low":1.16,"ci_high":1.80},"random":{"effect":1.59,"ci_low":0.08,"ci_high":32.74},"pi_low":0.02,"pi_high":163.67,"I2":63.8,"tau2":0.0763,"p_Q":0.0965},"B":{"study":[{"effect":2.00,"ci_low":-4.00,"ci_high":8.00,"weight_common":28.1,"weight_random":35.9},{"effect":6.50,"ci_low":2.75,"ci_high":10.25,"weight_common":71.9,"weight_random":64.1}],"common":{"effect":5.24,"ci_low":2.06,"ci_high":8.42},"random":{"effect":4.88,"ci_low":0.65,"ci_high":9.12},"pi_low":-31.65,"pi_high":41.42,"I2":35.6,"tau2":3.6091,"p_Q":0.2126},"C":{"study":[{"effect":-1.37,"ci_low":-3.25,"ci_high":0.52,"weight_random":39.0},{"effect":1.98,"ci_low":0.28,"ci_high":3.68,"weight_random":41.4},{"effect":0.56,"ci_low":-3.26,"ci_high":4.38,"weight_random":19.5}],"random":{"effect":0.40,"ci_low":-4.18,"ci_high":4.97},"pi_low":-7.18,"pi_high":7.98,"I2":70.1,"tau2":1.9757,"p_Q":0.0351,"Q":6.70}}
original=json.loads((RUN/"frozen/original_data.json").read_text());frozen_targets=json.loads((RUN/"frozen/targets.json").read_text())
truth("Independent original figure target transcription",manual_targets==frozen_targets)
sourceR=(P/"sources/original_analysis.R").read_text()
mapping={"A":{"event_e":"event.e_A","n_e":"n.e_A","event_c":"event.c_A","n_c":"n.c_A"},"B":{"effect":"TE_B","se":"seTE_B"},"C":{"effect":"TE_C","se":"seTE_C"}}
for label,fields in mapping.items():
 for field,variable in fields.items():
  raw=re.search(re.escape(variable)+r"\s*<-\s*c\(([^)]+)\)",sourceR).group(1)
  vals=[mp.mpf(x.strip()) for x in raw.split(",")]
  for index,(entered,reference) in enumerate(zip(manual[label][field],vals)):
   check(f"Independent source input {label}.{field}.{index}",mp.mpf(entered),reference)
   check(f"Frozen input {label}.{field}.{index}",mp.mpf(original[label][field][index]),reference)
# Scalar expanded pairwise Q avoids the experiment's weighted residual calculation.
def scalarQ(point,values,variances):
 weights=[1/(v+point) for v in variances];den=mp.fsum(weights)
 return mp.fsum(weights[i]*weights[j]*(values[i]-values[j])**2 for i in range(len(values)) for j in range(i+1,len(values)))/den
# Independent emulation directly from archived R4.5.2 C control flow, in 80-digit arithmetic.
EPS=mp.mpf(2)**-52;TOL=EPS**mp.mpf(".25")
def rsource_root(fn,left,right):
 x0,x1=mp.mpf(left),mp.mpf(right);f0,f1=fn(x0),fn(x1);x2,f2=x0,f0;trace=[]
 for step in range(101):
  old_distance=x1-x0
  if abs(f2)<abs(f1):
   old_x1,old_f1=x1,f1;x0,x1,x2=old_x1,x2,old_x1;f0,f1,f2=old_f1,f2,old_f1
  acc=2*EPS*abs(x1)+TOL/2;movement=(x2-x1)/2
  trace.append({"step":step,"root":str(x1),"function":str(f1),"bracket_width":str(abs(x2-x1))})
  if abs(movement)<=acc or f1==0:return x1,trace
  if abs(old_distance)>=acc and abs(f0)>abs(f1):
   delta=x2-x1
   if x0==x2:numerator=delta*f1/f0;denominator=1-f1/f0
   else:
    r0,r1,r2=f0/f2,f1/f2,f1/f0;numerator=r2*(delta*r0*(r0-r1)-(x1-x0)*(r1-1));denominator=(r0-1)*(r1-1)*(r2-1)
   if numerator>0:denominator=-denominator
   else:numerator=-numerator
   if numerator<mp.mpf(".75")*delta*denominator-abs(acc*denominator)/2 and numerator<abs(old_distance*denominator/2):movement=numerator/denominator
  if abs(movement)<acc:movement=acc if movement>0 else -acc
  x0,f0=x1,f1;x1=x1+movement;f1=fn(x1)
  if mp.sign(f1)==mp.sign(f2):x2,f2=x0,f0
 raise RuntimeError("Audit R solver convergence failure")
def median(a):
 b=sorted(a);return b[len(b)//2] if len(b)%2 else (b[len(b)//2-1]+b[len(b)//2])/2
def crit(df):return mp.tan(mp.pi*mp.mpf(".475")) if df==1 else mp.sqrt(2*mp.mpf(".95")**2/(1-mp.mpf(".95")**2))
def ci(mu,se,critical,ratio):
 fn=mp.exp if ratio else lambda x:x
 return dict(effect=fn(mu),ci_low=fn(mu-critical*se),ci_high=fn(mu+critical*se))
normal=mp.sqrt(2)*mp.erfinv(mp.mpf(".95"));fits={};traces={}
for label,rows in manual.items():
 ratio=label=="A";k=len(rows["study"]);df=k-1
 if ratio:
  y=[mp.log(mp.mpf(a)/b/(mp.mpf(c)/d)) for a,b,c,d in zip(rows["event_e"],rows["n_e"],rows["event_c"],rows["n_c"])]
  v=[1/mp.mpf(a)-1/mp.mpf(b)+1/mp.mpf(c)-1/mp.mpf(d) for a,b,c,d in zip(rows["event_e"],rows["n_e"],rows["event_c"],rows["n_c"])]
 else:y=list(map(mp.mpf,rows["effect"]));v=[mp.mpf(x)**2 for x in rows["se"]]
 Q=scalarQ(0,y,v);upper=max(mp.mpf(100),10*(median([abs(val-median(y)) for val in y])*mp.mpf("1.4826"))**2)
 tau,trace=rsource_root(lambda val:scalarQ(val,y,v)-df,0,upper);traces[label]=trace
 cw=[1/x for x in v];rw=[1/(x+tau) for x in v];tc,tr=mp.fsum(cw),mp.fsum(rw)
 mc=mp.fsum(w*val for w,val in zip(cw,y))/tc;mr=mp.fsum(w*val for w,val in zip(rw,y))/tr
 sc=mp.sqrt(1/tc);sr=mp.sqrt(1/tr);scale=scalarQ(tau,y,v)/df;hk=mp.sqrt(scale/tr);actual=sr if label=="B" else hk
 pq=mp.erfc(mp.sqrt(Q/2)) if df==1 else mp.exp(-Q/2)
 fit=dict(k=k,df=df,Q=Q,p_Q=pq,I2=max(0,(Q-df)/Q)*100,tau2=tau,common=ci(mc,sc,normal,ratio),random=ci(mr,actual,normal if label=="B" else crit(df),ratio),study=[])
 pi=ci(mr,mp.sqrt(tau+sr**2),crit(df),ratio);fit.update(pi_low=pi["ci_low"],pi_high=pi["ci_high"],se_random_classic=sr,se_random_hk=hk,hk_scale=scale,log_or_raw_mu_common=mc,log_or_raw_mu_random=mr,se_common=sc,crit_random=normal if label=="B" else crit(df),crit_prediction=crit(df))
 z=abs(mr/actual)
 fit["p_random"]=mp.erfc(z/mp.sqrt(2)) if label=="B" else 1-2/mp.pi*mp.atan(z) if df==1 else 1-z/mp.sqrt(z*z+2)
 for i in range(k):
  item=ci(y[i],mp.sqrt(v[i]),normal,ratio);item.update(weight_common=cw[i]/tc*100,weight_random=rw[i]/tr*100);fit["study"].append(item)
 fits[label]=fit
results=json.loads((RUN/"results.json").read_text())
def walkcompare(a,b,path=""):
 for key,value in a.items():
  if key not in b:continue
  if isinstance(value,dict):walkcompare(value,b[key],path+"."+key)
  elif isinstance(value,list):
   for i,row in enumerate(value):walkcompare(row,b[key][i],path+"."+key+"."+str(i))
  else:check("Independent recomputation "+path+"."+key,value,b[key],1e-8)
for label,fit in fits.items():walkcompare(fit,results["fits"][label],label)
for label,ref in manual_targets.items():
 fit=fits[label]
 for key,value in ref.items():
  if isinstance(value,list):
   for i,row in enumerate(value):
    for field,target in row.items():check("Original target "+label+".study."+str(i)+"."+field,fit["study"][i][field],target,.1 if field.startswith("weight") else .01)
  elif isinstance(value,dict):
   for field,target in value.items():check("Original target "+label+"."+key+"."+field,fit[key][field],target,.01)
  else:check("Original target "+label+"."+key,fit[key],value,{"tau2":.00015,"p_Q":.00015,"I2":.1}.get(key,.01))
claims={"A_positive_nonsignificant":fits["A"]["random"]["effect"]>1 and fits["A"]["random"]["ci_low"]<1<fits["A"]["random"]["ci_high"],"B_positive_significant_classic":fits["B"]["random"]["ci_low"]>0,"C_nonsignificant":fits["C"]["random"]["ci_low"]<0<fits["C"]["random"]["ci_high"]}
for label in fits:claims[label+"_prediction_crosses_null"]=fits[label]["pi_low"]<(1 if label=="A" else 0)<fits[label]["pi_high"]
for name,val in claims.items():truth("Independent claim "+name,val)
# Source manifests reflect append-only request logging between phases.
for manifest in ["sources_manifest.json","sources_manifest_solver_corrected.json"]:
 for row in json.loads((P/manifest).read_text()):
  f=P/row["path"];digest=hashlib.sha256(f.read_bytes()).hexdigest()
  if digest!=row["sha256"] and f.name=="cpu_routes_request_log.json" and manifest=="sources_manifest.json":
   records=json.loads(f.read_text());matched=None
   for n in range(len(records)+1):
    old=json.dumps(records[:n],indent=2).replace("\n","\r\n").encode()
    if hashlib.sha256(old).hexdigest()==row["sha256"]:matched=old;break
   truth("Original request log cryptographic prefix retained",matched is not None,{"current_records":len(records),"prefix_records":n})
   if matched is not None:(OUT/"original_prereg_request_log_snapshot.json").write_bytes(matched)
  else:truth("Source hash "+manifest+" "+row["path"],digest==row["sha256"])
for name in ["P066-central-001","P066-central-002"]:
 run=P/"runs"/name
 for row in json.loads((run/"run_manifest.json").read_text()):truth("Immutable run hash "+name+" "+row["path"],hashlib.sha256((run/row["path"]).read_bytes()).hexdigest()==row["sha256"])
old=json.loads((P/"runs/P066-central-001/results.json").read_text())
truth("Exact-root initial failure retained",not old["all_checks_pass"] and sum(c["passed"] for c in old["checks"])==68 and [c["name"] for c in old["checks"] if not c["passed"]]==["A.pi_high"])
truth("Unchanged targets both runs",(P/"runs/P066-central-001/frozen/targets.json").read_bytes()==(RUN/"frozen/targets.json").read_bytes()==(P/"targets.json").read_bytes())
prereg=json.loads((P/"PREREGISTRATION.json").read_text());correction=json.loads((P/"SOLVER_CORRECTION.json").read_text())
first=json.loads((P/"runs/P066-central-001/execution.json").read_text());second=json.loads((RUN/"execution.json").read_text())
truth("Preregistration precedes initial outcomes",prereg["created_at_utc"]<first["start_utc"])
truth("Correction disclosed before fresh run",first["end_utc"]<correction["created_at_utc"]<second["start_utc"])
truth("All original69 engine comparisons retained",len(results["checks"])==69 and results["all_checks_pass"])
def convert(obj):
 if isinstance(obj,dict):return {key:convert(val) for key,val in obj.items()}
 if isinstance(obj,list):return [convert(x) for x in obj]
 return float(obj) if isinstance(obj,mp.mpf) else obj
audit={"retained_previous_audit":"P066-audit-001:289/290 checks; original request-log reconstruction used LF while Windows write_text used CRLF; source content/analysis unchanged","audited_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"method":"80-digit independent scalar pairwise-Q, archived R source emulation, analytic normal/t1/t2/chi-square quantiles and tails; no experiment import","checks":checks,"all_audit_checks_pass":all(x["passed"] for x in checks),"independent_fits":convert(fits),"independent_source_inputs":manual,"independent_original_targets":manual_targets,"solver_traces":traces}
(OUT/"audit.json").write_text(json.dumps(audit,indent=2))
manifest=[{"path":str(f.relative_to(OUT)),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(OUT.rglob("*")) if f.is_file()]
(OUT/"audit_manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({"checks":len(checks),"passed":sum(c["passed"] for c in checks),"failures":[c for c in checks if not c["passed"]]},indent=2))
