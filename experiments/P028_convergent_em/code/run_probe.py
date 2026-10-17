import os
os.environ["OMP_NUM_THREADS"]="1"
os.environ["OPENBLAS_NUM_THREADS"]="1"
os.environ["MKL_NUM_THREADS"]="1"
import pathlib,sys,ast,json,datetime,time,hashlib,traceback,platform
import numpy as np,pandas as pd,torch,psutil,sklearn,scipy
from dataclasses import dataclass
from typing import List,Optional,Tuple,Dict
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,confusion_matrix,classification_report
from tqdm import tqdm
sys.stdout.reconfigure(encoding="utf-8")
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/"papers/P028_convergent_em"
D=P/"sources"
RUN=ROOT/"runs/P028-central-001"
RUN.mkdir(exist_ok=False)
plan=json.loads((P/"PREREGISTRATION.json").read_text())
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
t0=time.perf_counter();c0=time.process_time()
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
manifest={"run_id":"P028-central-001","start_utc":start,"status":"running","paid_cost":0,"command":sys.argv,"plan_sha256":hashlib.sha256((P/"PREREGISTRATION.json").read_bytes()).hexdigest(),"runner_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),"versions":{"python":sys.version,"numpy":np.__version__,"pandas":pd.__version__,"torch":torch.__version__,"sklearn":sklearn.__version__,"scipy":scipy.__version__},"CPU_threads":1,"GPU_used":False}
(RUN/"manifest.json").write_text(json.dumps(manifest,indent=2))
try:
 for rel,sha in plan["frozen_inputs"].items():
  assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha,rel
 tree=ast.parse((D/"lora_utils.py").read_text())
 names={"LoraScalars","LoraScalarsPerLayer","get_layer_number"}
 nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),"pinned_original_plain_classes","exec"),globals())
 safe=[(globals()[n],"lora.lora_utils."+n) for n in ["LoraScalars","LoraScalarsPerLayer"]]
 @dataclass
 class ProbeData:
  df:object
  lora_scalars:object
  class_name:str
 objects={}
 for label in plan["classes"]:
  a=pd.read_parquet(D/(label+"_data_3_3_3_answer_kl_div_importance_scores.parquet"))
  b=pd.read_parquet(D/(label+"_data_3_3_3_kl_divergence.parquet"))
  assert a["prompt"].equals(b["prompt"])
  a.rename(columns={"answer_kl_div_gradients":"answer_token_scores"},inplace=True)
  a["prompt_kl_divs"]=b["kl_div"]
  with torch.serialization.safe_globals(safe):
   scalars=torch.load(D/("lora_r1_3_3_3_scalars_"+label+".pt"),weights_only=True,map_location="cpu")
  objects[label]=ProbeData(a,scalars,label)
 NON_MEDICAL_ALIGNED_PROBE_DATA=objects["non_medical_aligned"]
 NON_MEDICAL_MISALIGNED_PROBE_DATA=objects["non_medical_misaligned"]
 MEDICAL_ALIGNED_PROBE_DATA=objects["medical_aligned"]
 MEDICAL_MISALIGNED_PROBE_DATA=objects["medical_misaligned"]
 R1_3_3_3_LAYER_NUMBERS=plan["layers"]
 SEED=0
 tree=ast.parse((D/"lora_probing.py").read_text())
 names={"get_single_class_probe_data","get_probe_data","get_class_data"}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),"pinned_original_probe_functions","exec"),globals())
 # Cache deterministic original per-token extraction. Original get_probe_data,
 # including all random draws and original float32 z-scoring, stays unchanged.
 original_extract=get_single_class_probe_data
 cache={}
 def get_single_class_probe_data(class_data,token_kl_div_threshold=None,log_token_score_threshold=None,include_token_features=False):
  k=(class_data.class_name,token_kl_div_threshold,log_token_score_threshold,include_token_features)
  if k not in cache:
   cache[k]=original_extract(class_data,token_kl_div_threshold,log_token_score_threshold,include_token_features)
  return cache[k]
 records=[];predrows=[];checks=[];features={}
 for threshold in [None,0.5]:
  for label,obj in objects.items():
   a=np.asarray(get_single_class_probe_data(obj,log_token_score_threshold=threshold),dtype=np.float32)
   assert a.ndim==2 and a.shape[1]==9 and np.isfinite(a).all()
   features[label+("__all" if threshold is None else "__high")]=a
 np.savez_compressed(RUN/"features.npz",**features)
 def fit_scope(scope,threshold,tests,reset_each=False):
  if not reset_each:torch.manual_seed(0)
  for test in tests:
   if reset_each:torch.manual_seed(0)
   cl0,cl1=get_class_data(test)
   for rep in range(100):
    draws=[]
    original_randperm=torch.randperm
    def traced_randperm(*args,**kwargs):
     z=original_randperm(*args,**kwargs);draws.append(z.numpy().copy());return z
    torch.randperm=traced_randperm
    x,y,n0,n1=get_probe_data(cl0,cl1,balanced_classes=True,fraction_of_data_to_use=1.0,log_token_score_threshold=threshold,z_score_normalize=True)
    torch.randperm=original_randperm
    assert len(draws)==3
    X=x.numpy();Y=y.numpy().ravel()
    tr,te=train_test_split(np.arange(len(Y)),test_size=.2,random_state=0,stratify=Y)
    model=LogisticRegression(random_state=0,max_iter=1000,penalty="l1",solver="liblinear",C=.01)
    model.fit(X[tr],Y[tr]);yhat=model.predict(X[te]);prob=model.predict_proba(X[te])[:,1]
    metrics=[accuracy_score(Y[te],yhat),precision_score(Y[te],yhat),recall_score(Y[te],yhat),f1_score(Y[te],yhat),roc_auc_score(Y[te],prob)]
    records.append({"scope":scope,"test":test,"rep":rep,"n0":n0,"n1":n1,"test_n":len(te),"metrics":list(map(float,metrics)),"coefficients":model.coef_[0].tolist(),"iterations":int(model.n_iter_[0]),"train_indices_sha256":hashlib.sha256(tr.tobytes()).hexdigest(),"test_indices_sha256":hashlib.sha256(te.tobytes()).hexdigest()})
    source_ids=np.concatenate([draws[0][:n0],len(get_single_class_probe_data(cl0,log_token_score_threshold=threshold))+draws[1][:n1]])[draws[2]][te]
    predrows.append((scope,test,rep,Y[te].astype(np.uint8),yhat.astype(np.uint8),prob,source_ids))
   print(scope,test,"completed",flush=True)
 fit_scope("table",None,[3,4,1,2])
 fit_scope("figure6",.5,[1,4])
 fit_scope("figure17",None,[1,4])
 # Prespecified random-stream sensitivity, not an alternative success route.
 fit_scope("table_reset_diagnostic",None,[3,4,1,2],True)
 (RUN/"regressions.json").write_text(json.dumps(records,indent=2))
 packed={}
 for scope,test,rep,y,h,pr,ids in predrows:
  key=scope+"_"+str(test)+"_"+str(rep)
  packed[key+"_y"]=y;packed[key+"_h"]=h;packed[key+"_p"]=pr;packed[key+"_source_ids"]=ids
 np.savez_compressed(RUN/"heldout_predictions.npz",**packed)
 summaries={}
 for scope in ["table","figure6","figure17","table_reset_diagnostic"]:
  tests=sorted({r["test"] for r in records if r["scope"]==scope})
  for test in tests:
   rr=[r for r in records if r["scope"]==scope and r["test"]==test]
   m=np.array([r["metrics"] for r in rr]);c=np.array([r["coefficients"] for r in rr])
   summaries[scope+"_"+str(test)]={"n_runs":len(rr),"metrics_mean":m.mean(0).tolist(),"metrics_std":m.std(0).tolist(),"coefficients_mean":c.mean(0).tolist(),"coefficients_median":np.median(c,axis=0).tolist(),"coefficients_q025":np.quantile(c,.025,axis=0).tolist(),"coefficients_q975":np.quantile(c,.975,axis=0).tolist()}
 for test,targets in plan["table_targets"].items():
  actual=summaries["table_"+test]["metrics_mean"]
  for name,v,target in zip(plan["metric_names"],actual,targets):
   checks.append({"kind":"table","test":int(test),"metric":name,"actual":v,"target":target,"tolerance":.0051,"pass":abs(v-target)<=.0051})
 for key,targets in plan["figure_median_targets"].items():
  actual=summaries[key]["coefficients_median"]
  for layer,v,target in zip(plan["layers"],actual,targets):
   checks.append({"kind":"figure_median","figure":key,"layer":layer,"actual":v,"target":target,"tolerance":.02,"pass":abs(v-target)<=.02})
 a=np.abs(summaries["figure6_1"]["coefficients_median"]);b=np.abs(summaries["figure6_4"]["coefficients_median"])
 general=[0,1,2,4,7,8];medical=[3,5];other=[6]
 checks.append({"kind":"qualitative","claim":"all six general layers exceed each of the other three in filtered general test","pass":bool(min(a[general])>max(a[medical+other]))})
 checks.append({"kind":"qualitative","claim":"both medical layers exceed each other layer in filtered medical test","pass":bool(min(b[medical])>max(b[general+other]))})
 for test in [1,2,3,4]:
  checks.append({"kind":"qualitative","claim":"test "+str(test)+" accuracy above .6","pass":summaries["table_"+str(test)]["metrics_mean"][0]>.6})
 acc=[summaries["table_"+str(t)]["metrics_mean"][0] for t in [1,2,3,4]]
 checks.append({"kind":"qualitative","claim":"medical alignment classifier highest accuracy","pass":acc[1]==max(acc)})
 checks.append({"kind":"qualitative","claim":"alignment classification stronger than context classification","pass":min(acc[:2])>max(acc[2:])})
 result={"summaries":summaries,"checks":checks,"passed":sum(c["pass"] for c in checks),"total":len(checks),"success":all(c["pass"] for c in checks),"all_regressions_converged":all(r["iterations"]<1000 for r in records)}
 result["success"]=result["success"] and result["all_regressions_converged"]
 (RUN/"comparison.json").write_text(json.dumps(result,indent=2))
 manifest.update(status="completed",exit_status=0,central_success=result["success"],checks_passed=result["passed"],checks_total=result["total"])
 print("RESULT",result["passed"],result["total"],result["success"],flush=True)
except Exception:
 (RUN/"error.txt").write_text(traceback.format_exc());manifest.update(status="failed",exit_status=1,error=traceback.format_exc());print(manifest["error"],flush=True)
finally:
 manifest.update(end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-c0,peak_working_set_bytes=psutil.Process().memory_info().peak_wset)
 manifest["artifacts"]={str(f.relative_to(RUN)):{"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in RUN.iterdir() if f.is_file() and f.name!="manifest.json"}
 (RUN/"manifest.json").write_text(json.dumps(manifest,indent=2))
