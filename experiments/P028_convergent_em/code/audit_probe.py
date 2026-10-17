import os
os.environ["OMP_NUM_THREADS"]="1"
os.environ["OPENBLAS_NUM_THREADS"]="1"
os.environ["MKL_NUM_THREADS"]="1"
import pathlib,json,hashlib,datetime,time,pickle,zipfile,io,pickletools,re,math,warnings,sys
import numpy as np,pandas as pd,torch,psutil
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore",category=FutureWarning)
warnings.filterwarnings("ignore",message="Inconsistent values: penalty")
ROOT=pathlib.Path(__file__).resolve().parents[2];P=ROOT/"papers/P028_convergent_em";D=P/"sources";R=ROOT/"runs/P028-central-001";A=ROOT/"audits/P028-audit-001";A.mkdir(exist_ok=False)
torch.set_num_threads(1);torch.set_num_interop_threads(1)
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t0=time.perf_counter();c0=time.process_time()
checks=[]
def check(name,ok,detail=None):
 checks.append({"name":name,"pass":bool(ok),"detail":detail})
class LoraScalars:pass
class LoraScalarsPerLayer:pass
class Restricted(pickle.Unpickler):
 def find_class(self,module,name):
  if module=="lora.lora_utils" and name in ["LoraScalars","LoraScalarsPerLayer"]:return globals()[name]
  raise pickle.UnpicklingError("Forbidden global "+module+"."+name)
 def persistent_load(self,pid):raise pickle.UnpicklingError("No persistent objects")
plan=json.loads((P/"PREREGISTRATION.json").read_text());manifest=json.loads((R/"manifest.json").read_text())
check("preregistration precedes run",plan["preregistered_at_utc"]<manifest["start_utc"])
for rel,sha in plan["frozen_inputs"].items():check("input "+rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha)
for rel,rec in manifest["artifacts"].items():check("artifact "+rel,hashlib.sha256((R/rel).read_bytes()).hexdigest()==rec["sha256"])
features={};counts={};layer_order=[15,16,17,21,22,23,27,28,29]
for label in plan["classes"]:
 z=zipfile.ZipFile(D/("lora_r1_3_3_3_scalars_"+label+".pt"));b=z.read(next(n for n in z.namelist() if n.endswith("/data.pkl")))
 ops=list(pickletools.genops(b))
 check(label+" safe plain pickle",all(op.name not in ["REDUCE","STACK_GLOBAL","EXT1","EXT2","EXT4","PERSID","BINPERSID"] for op,arg,pos in ops))
 obj=Restricted(io.BytesIO(b)).load()
 df=pd.read_parquet(D/(label+"_data_3_3_3_answer_kl_div_importance_scores.parquet"))
 old=pd.read_parquet(D/(label+"_data_3_3_3_kl_divergence.parquet"))
 check(label+" full source join",df["prompt"].equals(old["prompt"]) and set(obj)==set(df["prompt"]))
 allrows=[];highrows=[];metadata=[]
 for ix,row in df.iterrows():
  scalars=obj[row["prompt"]].scalars;first=int(row["prompt_answer_first_token_idx"]);scores=row["answer_kl_div_gradients"]
  for ti in range(first,len(scalars)):
   entry=scalars[ti];keys=sorted(entry.layer_scalars,key=lambda k:int(re.search(r"layers\.(\d+)",k)[1]))
   vals=[entry.layer_scalars[k] for k in keys]
   allrows.append(vals);metadata.append({"row":int(ix),"token":ti})
   score=float(scores[ti-first]);logscore=math.log(score) if score>0 else float("nan")
   if not logscore<.5:highrows.append(vals)
 for suffix,rows in [("__all",allrows),("__high",highrows)]:features[label+suffix]=np.asarray(rows,dtype=np.float32)
 counts[label]={"responses":len(df),"all_tokens":len(allrows),"high_tokens":len(highrows)}
 (A/(label+"_token_provenance.json")).write_text(json.dumps(metadata))
expected=np.load(R/"features.npz")
for key,x in features.items():check("independent token matrix "+key,np.array_equal(x,expected[key]))
records=json.loads((R/"regressions.json").read_text());raw=np.load(R/"heldout_predictions.npz")
def auc(labels,probs):
 order=np.argsort(probs,kind="stable");s=probs[order];ranks=np.empty(len(s),float);a=0
 while a<len(s):
  b=a+1
  while b<len(s) and s[b]==s[a]:b+=1
  ranks[order[a:b]]=(a+1+b)/2;a=b
 n1=int(labels.sum());n0=len(labels)-n1
 return (ranks[labels==1].sum()-n1*(n1+1)/2)/(n1*n0)
for rec in records:
 k=rec["scope"]+"_"+str(rec["test"])+"_"+str(rec["rep"]);y=raw[k+"_y"];h=raw[k+"_h"];pr=raw[k+"_p"]
 tp=int(((y==1)&(h==1)).sum());fp=int(((y==0)&(h==1)).sum());fn=int(((y==1)&(h==0)).sum())
 metrics=[float((y==h).mean()),tp/(tp+fp),tp/(tp+fn),2*tp/(2*tp+fp+fn),auc(y,pr)]
 check(k+" independent five heldout metrics",np.max(np.abs(np.asarray(metrics)-rec["metrics"]))<1e-12)
 check(k+" probabilities valid",np.isfinite(pr).all() and (pr>=0).all() and (pr<=1).all() and np.array_equal(h,(pr>.5).astype(np.uint8)))
pairs={1:("non_medical_aligned","non_medical_misaligned"),2:("medical_aligned","medical_misaligned"),3:("non_medical_aligned","medical_aligned"),4:("non_medical_misaligned","medical_misaligned")}
index={(r["scope"],r["test"],r["rep"]):r for r in records}
scopes=[("table","__all",[3,4,1,2],False),("figure6","__high",[1,4],False),("figure17","__all",[1,4],False),("table_reset_diagnostic","__all",[3,4,1,2],True)]
for scope,suffix,tests,reset in scopes:
 torch.manual_seed(0)
 for test in tests:
  if reset:torch.manual_seed(0)
  l0,l1=pairs[test];f0=torch.from_numpy(features[l0+suffix]);f1=torch.from_numpy(features[l1+suffix]);n=min(len(f0),len(f1))
  for rep in range(100):
   i0=torch.randperm(len(f0))[:n];i1=torch.randperm(len(f1))[:n]
   X=torch.cat((f0[i0],f1[i1]));Y=torch.cat((torch.zeros(n,1),torch.ones(n,1)));perm=torch.randperm(2*n);X=X[perm];Y=Y[perm]
   sourceids=np.concatenate([i0.numpy(),len(f0)+i1.numpy()])[perm.numpy()]
   X=((X-X.mean(0))/X.std(0)).numpy();Y=Y.numpy().ravel()
   tr,te=train_test_split(np.arange(len(Y)),test_size=.2,random_state=0,stratify=Y)
   rec=index[scope,test,rep];k=scope+"_"+str(test)+"_"+str(rep)
   check(k+" exact full membership",np.array_equal(raw[k+"_source_ids"],sourceids[te]) and np.array_equal(raw[k+"_y"],Y[te]) and len(set(sourceids[te]))==len(te))
   check(k+" original split hashes",hashlib.sha256(tr.tobytes()).hexdigest()==rec["train_indices_sha256"] and hashlib.sha256(te.tobytes()).hexdigest()==rec["test_indices_sha256"])
   clf=LogisticRegression(random_state=0,max_iter=1000,penalty="l1",solver="liblinear",C=.01).fit(X[tr],Y[tr])
   pr=clf.predict_proba(X[te])[:,1]
   check(k+" independently refitted coefficients/probabilities",np.max(np.abs(clf.coef_[0]-rec["coefficients"]))<1e-10 and np.max(np.abs(pr-raw[k+"_p"]))<1e-10)
  print(scope,test,"audited",flush=True)
comparison=json.loads((R/"comparison.json").read_text())
for key,summary in comparison["summaries"].items():
 scope,test=key.rsplit("_",1);rr=[r for r in records if r["scope"]==scope and r["test"]==int(test)]
 m=np.asarray([r["metrics"] for r in rr]);c=np.asarray([r["coefficients"] for r in rr])
 check(key+" summary values",np.max(np.abs(m.mean(0)-summary["metrics_mean"]))<1e-12 and np.max(np.abs(np.median(c,axis=0)-summary["coefficients_median"]))<1e-12)
# Two prospectively transcribed Figure17 targets were misassigned. Retain the
# failed original gate; this correction is source transcription, not new credit.
corrected={"figure17_4:27":{"original":0.0,"source_corrected":-.06},"figure17_4:28":{"original":-.06,"source_corrected":-.03}}
for key,target in corrected.items():
 fig,layer=key.split(":");value=comparison["summaries"][fig]["coefficients_median"][layer_order.index(int(layer))]
 target["actual"]=value;target["corrected_gate_pass"]=abs(value-target["source_corrected"])<=.02
out={"run_id":"P028-audit-001","start_utc":start,"end_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"passed":sum(c["pass"] for c in checks),"total":len(checks),"success":all(c["pass"] for c in checks),"checks":checks,"structural_counts":counts,"original_reproduction_success":False,"original_failed_comparisons":[c for c in comparison["checks"] if not c["pass"]],"post_outcome_source_transcription_correction":corrected,"remaining_original_table_failures":3,"scope":"Independent restricted raw-data reader, complete matrices, all1200 fresh refits, all heldout metrics/membership and summaries. Does not import runner or original probe functions.","wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,"peak_working_set_bytes":psutil.Process().memory_info().peak_wset,"paid_cost":0,"GPU_used":False}
out["artifacts"]={str(q.relative_to(A)):{"bytes":q.stat().st_size,"sha256":hashlib.sha256(q.read_bytes()).hexdigest()} for q in A.iterdir() if q.is_file()}
out["auditor_sha256"]=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
(A/"audit.json").write_text(json.dumps(out,indent=2))
print("AUDIT",out["passed"],out["total"],out["success"],flush=True)
