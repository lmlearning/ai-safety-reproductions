"""Independent P072 audit: raw RDS, independently interpreted designs and QR inference."""
import os
for name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):os.environ[name]="1"
import sys,pathlib,json,hashlib,datetime,time,collections,warnings,math
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/"papers/P072_levers_persuasion"
sys.path.insert(0,str(P/"environment/vendor"))
import numpy as np,pandas as pd,scipy.linalg as la,scipy.stats as st,pyreadr,psutil
RUN=P/"runs/P072-central-003";OUT=P/"audits"/sys.argv[1];OUT.mkdir(parents=True,exist_ok=False)
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t0=time.perf_counter();c0=time.process_time()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n",encoding="utf8")
CHECKS=[]
def check(ident,actual,expected,tol=0):
    if actual is None or expected is None:passed=actual is expected
    elif isinstance(expected,(float,int)) and not isinstance(expected,bool):passed=math.isfinite(float(actual)) and abs(actual-expected)<=tol
    else:passed=actual==expected
    CHECKS.append({"id":ident,"actual":actual,"expected":expected,"tolerance":tol,"passed":bool(passed)})
for mpath in (P/"SOURCE_MANIFEST.json",RUN/"RUN_MANIFEST.json"):
    m=json.loads(mpath.read_text())
    for f in m["files"]:
        fp=ROOT/f["path"]
        check("hash."+str(mpath.name)+"."+f["path"],digest(fp) if fp.exists() else None,f["sha256"])
        check("size."+str(mpath.name)+"."+f["path"],fp.stat().st_size if fp.exists() else None,f["bytes"])
plan=json.loads((P/"PREREGISTRATION.json").read_text());targetdoc=json.loads((P/"inputs/original_targets.json").read_text())
des=json.loads((RUN/"analysis_designs.json").read_text());reference=json.loads((RUN/"model_statistics.json").read_text());refrows=json.loads((RUN/"computed_tables.json").read_text());refdec=json.loads((RUN/"target_decisions.json").read_text());metrics=json.loads((RUN/"metrics.json").read_text())
check("prereg.hash",digest(P/"PREREGISTRATION.json"),metrics["preregistration_sha256"])
check("target.hash",digest(P/"inputs/original_targets.json"),plan["targets_sha256"])
check("prereg.before.design",plan["preregistered_at_utc"]<des["created_at_utc"],True)
check("correction.before.run",json.loads((P/"environment/source_mapping_correction_before_run003.json").read_text())["recorded_before_new_run_at_utc"]<metrics["started_at_utc"],True)
check("all.original.target.count",len(targetdoc["targets"]),2470)
check("source.transcription",all(x["pass"] for x in json.loads((P/"sources/target_transcription_source_check.json").read_text())["checks"]),True)
D={}
with warnings.catch_warnings():
    warnings.simplefilter("ignore",RuntimeWarning)
    for study in (1,2,3):D[study]=next(iter(pyreadr.read_r(str(P/("sources/levers_study%d_data.rds"%study))).values())).reset_index(drop=True)
# No runner imports. Interpret the frozen source-defined selection expressions independently.
def choose(data,e):
    if e is None:return np.ones(len(data),dtype=bool)
    code=e[0]
    if code=="and":return np.logical_and.reduce([choose(data,v) for v in e[1:]])
    if code=="or":return np.logical_or.reduce([choose(data,v) for v in e[1:]])
    vals=data[e[1]];present=vals.notna().to_numpy()
    if code=="notna":return present
    if code=="isna":return ~present
    if code=="eq":return present & vals.eq(e[2]).to_numpy()
    if code in ("in","not_in"):
        v=vals.isin(e[2]).to_numpy();return v if code=="in" else ~v
    if code=="regex":
        v=vals.astype("string").str.contains(e[2],regex=True,na=False).to_numpy(dtype=bool);return present & (~v if e[3] else v)
    raise ValueError(e)
def subset(spec):
    data=D[spec["study"]];frames=[]
    for part in spec["parts"] or [{"outcome":spec["outcome"]}]:
        rows=np.flatnonzero(choose(data,part.get("select",spec["select"])))
        z=data.iloc[rows].copy();z["_audit_row"]=rows;z["_audit_outcome"]=part["outcome"];z["_audit_y"]=z[part["outcome"]]
        if "phase" in part:z["_phase"]=part["phase"]
        frames.append(z)
    return pd.concat(frames,ignore_index=True)
def build(spec):
    z=subset(spec);cols=collections.OrderedDict();valid=z["_audit_y"].notna().to_numpy();centers={}
    if spec["intercept"]:cols["Intercept"]=np.full(len(z),1.)
    for feature in spec["features"]:
        what=feature["kind"];name=feature["name"]
        if what=="product":cols[name]=cols[feature["left"]]*cols[feature["right"]];continue
        vals=z[feature["column"]].copy()
        if feature.get("rename"):
            r=feature["rename"];vals=vals.astype(object);vals.loc[z[r["condition_column"]].eq(r["condition_value"])]=r["replacement"]
        if what=="numeric":
            v=vals.to_numpy(dtype=float)
            if feature["scale"]:
                observed=v[np.isfinite(v)];mean=sum(observed)/len(observed);sd=np.sqrt(sum((observed-mean)**2)/(len(observed)-1));centers[name]={"mean":mean,"sd":sd};v=(v-mean)/sd
            valid &=np.isfinite(v);cols[name]=v
        elif what=="factor":
            valid &=vals.notna().to_numpy();levels=sorted(set(vals.dropna()))
            baseline=feature["base"] if feature["base"] else (None if feature["full"] else levels[0])
            for level in levels:
                if feature["full"] or level!=baseline:cols[name+"::"+str(level)]=vals.eq(level).to_numpy(float)
        elif what=="indicator":
            if name!="info":valid &=vals.notna().to_numpy()
            cols[name]=vals.isin([feature["value"]]).to_numpy(float)
        elif what=="contains":
            valid &=vals.notna().to_numpy();cols[name]=vals.astype("string").str.contains(feature["value"],na=False).to_numpy(float)
        else:raise ValueError(feature)
    ids=[{"_row":int(r),"_outcome":o} for r,o in zip(z.loc[valid,"_audit_row"],z.loc[valid,"_audit_outcome"])]
    idhash=hashlib.sha256(json.dumps(ids,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return np.array(list(cols.values())).T[valid],z.loc[valid,"_audit_y"].to_numpy(float),list(cols),len(z),centers,idhash
ALL={}
for spec in des["models"]:
    X,y,names,selected,centers,rowhash=build(spec);mid=spec["id"];old=reference[mid]
    # Pivoted QR selects rank independently; invert triangular R rather than pseudoinverse.
    Q,R,piv=la.qr(X,mode="economic",pivoting=True)
    rank=int(np.sum(np.abs(np.diag(R))>np.finfo(float).eps*max(X.shape)*abs(R[0,0])))
    retained=sorted(map(int,piv[:rank]));Z=X[:,retained]
    q,r=la.qr(Z,mode="economic");inverse_r=la.solve_triangular(r,np.eye(rank));beta=la.solve_triangular(r,q.T@y)
    residual=y-Z@beta;h=np.sum(q*q,axis=1);omega=residual**2/(1-h)
    v=inverse_r@(q.T@(omega[:,None]*q))@inverse_r.T;se=np.sqrt(np.maximum(np.diag(v),0));df=len(y)-rank
    check(mid+".rank",rank,old["rank"]);check(mid+".complete",len(y),old["detail"]["complete_rows"]);check(mid+".selected",selected,old["detail"]["selected_rows"]);check(mid+".raw_row_selection_hash",rowhash,old["detail"]["row_selection_sha256"]);check(mid+".columns",names,old["columns"])
    for cn,cv in centers.items():
        for field,value in cv.items():check(mid+".center."+cn+"."+field,value,old["detail"]["centers"][cn][field],1e-10)
    coefs={}
    for j,k in enumerate(retained):
        b=float(beta[j]);s=float(se[j]);stat=b/s;half=st.t.isf(.025,df)*s
        coefs[names[k]]={"estimate":b,"std.error":s,"statistic":stat,"p.value":float(2*st.t.cdf(-abs(stat),df)),"conf.low":b-half,"conf.high":b+half,"df":df}
    for k in set(range(len(names)))-set(retained):coefs[names[k]]={field:None for field in ("estimate","std.error","statistic","p.value","conf.low","conf.high","df")}
    for term,values in coefs.items():
        for field,value in values.items():check(mid+"."+term+"."+field,value,old["coefficients"][term][field],0 if field=="df" else 1e-8)
    ALL[mid]={"coefficients":coefs,"row_selection_sha256":rowhash,"rank":rank}
for spec in des["meta"]:
    rows=[ALL[mid]["coefficients"][term] for mid,term in spec["refs"]];precision=[1/r["std.error"]**2 for r in rows]
    mu=sum(w*r["estimate"] for w,r in zip(precision,rows))/sum(precision);s=math.sqrt(1/sum(precision));z=mu/s;q=st.norm.isf(.025)
    values={"estimate":mu,"std.error":s,"statistic":z,"p.value":float(2*st.norm.cdf(-abs(z))),"conf.low":mu-q*s,"conf.high":mu+q*s};ALL[spec["id"]]=values
    for field,value in values.items():check(spec["id"]+"."+field,value,reference[spec["id"]][field],1e-8)
def modelname(x):
    if pd.isna(x):return "NA"
    return {"gpt-4.5":"GPT-4.5","gpt-4o":"GPT-4o (8/24)","chatgpt-4o-latest":"GPT-4o (3/25)","grok-3":"Grok-3","gpt-3.5":"GPT-3.5","llama-3-1-8b":"Llama3.1-8b","llama-3-1-405b":"Llama3.1-405b"}.get(str(x),str(x).replace("qwen","Qwen"))
def groupname(x,col):
    v={"aa_control":"Control","treat_static":"Static message","control":"Control","treatment":"Treatment","generic":"Generic","personalized":"Personalized","base":"Base","rm":"RM","sft":"SFT","sft_and_rm":"SFT + RM"}.get(str(x),modelname(x))
    return v[:1].upper()+v[1:].lower() if "prompt" in col else v
def norm(x):return " ".join(x.split()).casefold()
ROWS={}
def add(table,label,suffix,vals):
    key=str(table)+"|"+norm(label)+"|"+norm(suffix)
    if key in ROWS:raise ValueError(key)
    ROWS[key]={"values":vals,"label":label,"suffix":suffix}
for recipe in des["recipes"]:
    vals=ALL[recipe["model"]]["coefficients"][recipe["term"]] if recipe["kind"]=="model" else ALL[recipe["model"]]
    add(recipe["table"],recipe["label"],recipe["suffix"],vals)
for table,study,prefix,group,selection in des["attrition"]:
    raw=D[study];col=prefix+group;mask=choose(raw,selection)&raw[prefix+"post_missing"].notna().to_numpy()&raw[prefix+"post_missing"].ne("pre_missing").to_numpy()&raw[col].notna().to_numpy()
    z=raw.loc[mask];levels=sorted(set(z[col]));complete=z[prefix+"outcome_missing"].notna();yc=z.loc[complete,prefix+"outcome_missing"].to_numpy(float);gc=z.loc[complete,col]
    X=np.array([gc.eq(level).to_numpy(float) for level in levels]).T
    q,r=la.qr(X,mode="economic");fit=q@(q.T@yc);res=yc-fit;within=float(res@res);grand=yc-yc.mean();between=float(grand@grand-within);d1=len(levels)-1;d2=len(yc)-len(levels);F=(between/d1)/(within/d2)
    for level in levels:
        g=z.loc[z[col].eq(level),prefix+"outcome_missing"]
        add(table,groupname(level,col),"",{"n":len(g),"proportion":float(g.sum()/g.notna().sum())})
    add(table+1,"Condition","",{"df":d1,"sumsq":between,"meansq":between/d1,"statistic":F,"p.value":float(st.f.sf(F,d1,d2))})
    add(table+1,"Residuals","",{"df":d2,"sumsq":within,"meansq":within/d2,"statistic":None,"p.value":None})
for table,study,columns,required in des["counts"]:
    data=D[study];mask=np.logical_and.reduce([data[c].notna().to_numpy() for c in required]);count=collections.Counter()
    for record in data.loc[mask,columns].itertuples(index=False,name=None):
        vals=[]
        for c,x in zip(columns,record):
            vals.append("NA" if pd.isna(x) else modelname(x) if c.endswith("model") else str(x).replace("_","-") if c.endswith("condition") else str(x))
        count[tuple(vals)]+=1
    for key,value in count.items():add(table," ".join(key),"",{"n":value})
check("all.row.identities",sorted(ROWS),sorted(refrows))
for key,row in ROWS.items():
    for field,value in row["values"].items():
        # Compare every selected numerical field; extra nuisance statistics were not targets.
        if field in refrows[key]["values"]:check("row."+key+"."+field,value,refrows[key]["values"][field],0 if field in ("df","n") else 1e-8)
def val(table,label="",suffix="",field="estimate"):return ROWS[str(table)+"|"+norm(label)+"|"+norm(suffix)]["values"][field]
def sig(table,label="",suffix=""):return val(table,label,suffix)>0 and val(table,label,suffix,"p.value")<.05
qual=[
 sig(3,"dialogue (vs. static)"),sig(5,"dialogue (vs. static)"),sig(1,"GPT-4o (8/24)","S1 chat 1 1"),sig(1,"GPT-4o (8/24)","S1 chat 2 1"),
 sig(31,"RM","2 chat-tuned"),val(31,"SFT","2 chat-tuned","p.value")>=.05,val(25,"RM x SFT","","p.value")>=.05,val(31,"RM","2 developer","p.value")>=.05,
 sig(31,"RM","3 developer"),sig(33),sig(43),val(53,"information")==max(val(53,p) for p in ("information","mega","debate","norms","storytelling","moral_reframing","deep_canvass"))]
qualnames=[t["id"] for t in targetdoc["targets"] if t["kind"]=="qualitative"];qualdict=dict(zip(qualnames,qual))
decisions=[];samples=sum(int(D[s]["d1.post_average" if s==1 else "post_average"].notna().sum()) for s in (1,2,3))
for target,old in zip(targetdoc["targets"],refdec):
    kind=target["kind"];expected=target["expected"]
    if kind=="qualitative":actual=qualdict[target["id"]];passed=actual==expected
    elif target["id"]=="human_trial.total_analyzed":actual=samples;passed=actual==expected
    else:
        key=str(target["table"])+"|"+norm(target["row_label"])+"|"+norm(target["row_suffix"]);actual=ROWS[key]["values"][target["field"]]
        if kind=="undefined":passed=actual is None
        elif kind=="less_than":passed=actual is not None and actual<expected
        elif kind=="exact":passed=actual==expected
        else:passed=actual is not None and abs(actual-expected)<=target["tolerance"]
    check("target.identity."+target["id"],{k:old[k] for k in target},target)
    check("target.pass_agreement."+target["id"],bool(passed),old["passed"])
    check("target.published_gate."+target["id"],bool(passed),True)
    decisions.append({**target,"actual":actual,"passed":bool(passed)})
# Verify source-derived correction changed only the two originally mistaken S6/S7 definitions.
old_des=json.loads((P/"runs/P072-central-002/analysis_designs.json").read_text())
changed=[(a,b) for a,b in zip(old_des["models"],des["models"]) if a!=b]
check("correction.only.two.models",len(changed),2)
for a,b in changed:
    check("correction.study."+b["id"],b["study"],2)
    check("correction.unchanged.other_features."+b["id"],{k:v for k,v in a.items() if k!="features"},{k:v for k,v in b.items() if k!="features"})
    a2=json.loads(json.dumps(a));a2["features"][0]["rename"]=None
    check("correction.remove.only.distinct_deceptive_arm."+b["id"],a2,b)
check("correction.recipes.unchanged",old_des["recipes"],des["recipes"])
check("correction.meta.unchanged",old_des["meta"],des["meta"])
# RHC2 numerical convention is backed by archived historical source, not target-guided choice.
hc2=(P/"sources/estimatr_v1.0.4_lm_robust.R").read_text()
check("source.historical.HC2",'"HC2"' in hc2,True)
check("retained.failed.serializer_run",(P/"runs/P072-central-001/FAILED_SETUP.json").exists(),True)
check("retained.failed.21gate_run",json.loads((P/"runs/P072-central-002/metrics.json").read_text())["checks_passed"],2449)
dump(OUT/"independent_model_statistics.json",ALL);dump(OUT/"independent_computed_tables.json",ROWS);dump(OUT/"independent_target_decisions.json",decisions);dump(OUT/"audit_checks.json",CHECKS)
result={"paper_id":"P072","audited_run":"P072-central-003","audit_id":sys.argv[1],"started_at_utc":started,"finished_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"independent_engine":"Raw-RDS selection reconstruction; pivoted QR rank and triangular-QR HC2 covariance; separate Counter counts and QR ANOVA; no runner imports.","checks_passed":sum(x["passed"] for x in CHECKS),"checks_total":len(CHECKS),"all_audit_checks_passed":all(x["passed"] for x in CHECKS),"all_published_targets_passed":all(x["passed"] for x in decisions),"published_targets":len(decisions),"tables":len(targetdoc["tables"]),"rows":len(ROWS),"treatment_models":len(des["models"]),"fixed_effect_syntheses":len(des["meta"]),"wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,"peak_memory_mb":psutil.Process().memory_info().peak_wset/1024**2,"paid_api_spend":0,"fresh_gpu_inference":False,"preregistration_sha256":digest(P/"PREREGISTRATION.json"),"run_manifest_sha256":digest(RUN/"RUN_MANIFEST.json")}
dump(OUT/"AUDIT_RESULT.json",result)
(OUT/"auditor_source.py").write_bytes(pathlib.Path(__file__).read_bytes())
files=[{"path":str(f.relative_to(ROOT)).replace("\\","/"),"sha256":digest(f),"bytes":f.stat().st_size} for f in sorted(OUT.glob("*")) if f.is_file()]
dump(OUT/"AUDIT_MANIFEST.json",{"paper_id":"P072","audit_id":sys.argv[1],"files":files})
print(json.dumps(result,ensure_ascii=True));print(json.dumps([c for c in CHECKS if not c["passed"]],ensure_ascii=True))
