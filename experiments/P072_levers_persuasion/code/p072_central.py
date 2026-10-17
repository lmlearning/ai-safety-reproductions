"""P072: frozen complete original primary human policy-attitude analysis."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key]="1"
import sys,pathlib,json,hashlib,time,datetime,warnings,traceback
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/"papers/P072_levers_persuasion"
sys.path.insert(0,str(P/"environment/vendor"))
import numpy as np,pandas as pd,scipy,scipy.stats as st,pyreadr,psutil
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=True,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n",encoding="utf8")
RUN=P/"runs"/sys.argv[1]
RUN.mkdir(parents=True,exist_ok=False)
t0=time.perf_counter();c0=time.process_time();started=now()
plan=json.loads((P/"PREREGISTRATION.json").read_text())
targets=json.loads((P/"inputs/original_targets.json").read_text())
frozen=json.loads((P/"SOURCE_MANIFEST.json").read_text())
DATA={}
caught=[]
with warnings.catch_warnings(record=True) as ww:
    warnings.simplefilter("always")
    for s in (1,2,3):
        path=P/("sources/levers_study%d_data.rds"%s)
        assert sha(path)==plan["inputs_sha256"]["study%d"%s]
        DATA[s]=next(iter(pyreadr.read_r(str(path)).values())).reset_index(drop=True)
    caught=[str(w.message) for w in ww]
assert sha(P/"inputs/original_targets.json")==plan["targets_sha256"]
MODELS=[];RECIPES=[];META=[];ACTUAL={}
def eq(c,v):return ["eq",c,v]
def isin(c,v):return ["in",c,v]
def notna(c):return ["notna",c]
def isn(c):return ["isna",c]
def rg(c,pat,neg=False):return ["regex",c,pat,neg]
def AND(*x):return ["and",*x]
def OR(*x):return ["or",*x]
def num(c,scale=False):return {"kind":"numeric","column":c,"name":c,"scale":scale}
def fac(c,base=None,full=False,rename=None):
    return {"kind":"factor","column":c,"name":c,"base":base,"full":full,"rename":rename}
def ind(c,v,name=None):return {"kind":"indicator","column":c,"value":v,"name":name or c+"="+str(v)}
def cont(c,v,name):return {"kind":"contains","column":c,"value":v,"name":name}
def prod(a,b,name):return {"kind":"product","left":a,"right":b,"name":name}
def model(s,y,select,features,intercept=True,parts=None):
    ident="M%03d"%(len(MODELS)+1)
    MODELS.append({"id":ident,"study":s,"outcome":y,"select":select,"features":features,"intercept":intercept,"parts":parts})
    return ident
def emit(table,label,suffix,m,term):
    RECIPES.append({"table":table,"label":label,"suffix":suffix,"kind":"model","model":m,"term":term})
def pool(table,label,suffix,refs):
    ident="FE%03d"%(len(META)+1)
    META.append({"id":ident,"refs":refs})
    RECIPES.append({"table":table,"label":label,"suffix":suffix,"kind":"meta","model":ident})
    return ident
def pretty(x):
    names={"gpt-4.5":"GPT-4.5","chatgpt-4o-latest":"GPT-4o (3/25)","gpt-4o":"GPT-4o (8/24)","grok-3":"Grok-3","gpt-3.5":"GPT-3.5","llama-3-1-8b":"Llama3.1-8b","llama-3-1-405b":"Llama3.1-405b"}
    return names.get(x,x.replace("qwen","Qwen"))
def pt(x):return {"base":"Base","rm":"RM","sft":"SFT","sft_and_rm":"SFT + RM"}.get(x,x)
def norm(x):return " ".join(x.split()).casefold()
# S1: original complete immediate/follow-up participants.
for phase,y in enumerate(("post_average","post_average_followup")):
    for chat in (1,2):
        prefix="d%d."%chat
        selection=AND(notna(prefix+"post_average"),notna(prefix+"post_average_followup"))
        if chat==1:selection=AND(selection,eq("d1.model","gpt-4o"))
        f=fac(prefix+("models_vs_control" if chat==1 else "condition"),"aa_control" if chat==1 else "control")
        m=model(1,prefix+y,selection,[f,num(prefix+"pre_average")])
        if chat==1:
            emit(1,pretty("gpt-4o"),"S1 chat 1 %d"%phase,m,f["name"]+"::gpt-4o")
            emit(1,"Static message","S1 chat 1 %d"%phase,m,f["name"]+"::treat_static")
        else:emit(1,pretty("gpt-4o"),"S1 chat 2 %d"%phase,m,f["name"]+"::treatment")
# S2-S7 and S22-S35, robustness and primary.
rm=cont("post_train","rm","rm");sft=cont("post_train","sft","sft")
rmrefs={}
for robust,out in ((True,"post_average_imputed_with_pre"),(False,"post_average")):
    m=model(1,"value",AND(eq("d1.model","gpt-4o"),rg("d1.condition","control",True)),
       [ind("d1.condition","treat_dialogue","dialogue"),num("_phase"),prod("dialogue","_phase","interaction")],
       parts=[{"outcome":"d1."+out,"phase":0},{"outcome":"d1.post_average_followup","phase":1}])
    for term,label in [("dialogue","dialogue (vs. static)"),("_phase","time"),("interaction","dialogue (vs. static) x time")]:
        emit(2 if robust else 3,label,"",m,term)
    m=model(3,out,AND(eq("model","gpt-4.5"),eq("post_train","base")),
            [ind("condition","treatment-1","dialogue"),num("pre_average")])
    emit(4 if robust else 5,"dialogue (vs. static)","",m,"dialogue")
    for s in (1,2,3):
        prefix="d1." if s==1 else ""
        sel=None if s==1 else OR(isn("post_train"),eq("post_train","base")) if s==2 else eq("post_train","base")
        replacements={"condition_column":"condition","condition_value":"treatment-3","replacement":"llama-3-1-405b-deceptive-info"} if s==2 else None
        m=model(s,prefix+out,sel,[fac(prefix+"models_vs_control","aa_control",rename=None),num(prefix+"pre_average")])
        # Original result table removes static, deceptive-info and duplicate study1 chat2 rows.
        levels=DATA[s][prefix+"models_vs_control"].dropna().unique()
        for level in levels:
            if level in ("aa_control","treat_static"):continue
            emit(6 if robust else 7,pretty(level),str(s),m,prefix+"models_vs_control::"+level)
    m=model(3,out,AND(eq("condition","treatment-1"),rg("model","gpt-4o")),[fac("model","gpt-4o"),num("pre_average")])
    emit(22 if robust else 23,pretty("chatgpt-4o-latest"),"",m,"model::chatgpt-4o-latest")
    refs=[]
    for s,select,kind in [(2,eq("condition","treatment-1"),"chat-tuned"),(2,eq("condition","treatment-2"),"developer"),(3,isin("condition",["treatment-1","treatment-2"]),"developer")]:
        m=model(s,out,select,[rm,sft,num("pre_average")])
        emit(30 if robust else 31,"RM",str(s)+" "+kind,m,"rm")
        if kind=="chat-tuned":emit(30 if robust else 31,"SFT",str(s)+" "+kind,m,"sft")
        else:refs.append([m,"rm"])
    rmrefs[out]=refs
    pool(32 if robust else 33,"","",refs)
    for s in (2,3):
        pairs=DATA[s][["condition","model"]].drop_duplicates()
        for condition,mod in pairs.itertuples(index=False,name=None):
            if condition in ("control","treatment-3") or pd.isna(condition):continue
            sel=AND(isin("condition",[condition,"control"]),OR(eq("condition","control"),eq("model",mod),isn("model")))
            f=fac("post_train","aa_control",rename={"condition_column":"condition","condition_value":"control","replacement":"aa_control"})
            m=model(s,out,sel,[f,num("pre_average",True)])
            for level in DATA[s].loc[DATA[s]["condition"].eq(condition)&DATA[s]["model"].eq(mod),"post_train"].dropna().unique():
                emit(34 if robust else 35,pt(level),str(s)+" "+pretty(mod),m,"post_train::"+level)
m=model(3,"post_average",AND(eq("post_train","base"),isin("condition",["treatment-1","treatment-2"])),[fac("model","chatgpt-4o-latest"),num("pre_average")])
for level in ("gpt-4.5","gpt-4o","grok-3"):emit(24,pretty(level),"",m,"model::"+level)
m=model(2,"post_average",eq("condition","treatment-1"),[rm,sft,num("pre_average"),prod("rm","sft","rm*sft")])
for term,label in [("Intercept","(Intercept)"),("rm","RM"),("sft","SFT"),("pre_average","pre_average"),("rm*sft","RM x SFT")]:emit(25,label,"",m,term)
# All 11 original personalization arms and fixed-effect synthesis.
pers=[
 (1,"d1.",AND(eq("d1.condition","treat_dialogue"),rg("d1.model","gpt|chat",True)),36,"1 chat-tuned Base"),
 (1,"d1.",AND(eq("d1.condition","treat_dialogue"),rg("d1.model","gpt|chat")),36,"1 developer Base"),
 (1,"d2.",eq("d2.condition","treatment"),36,"2 developer Base"),
 (2,"",AND(isin("condition",["treatment-1","treatment-3"]),OR(isn("post_train"),eq("post_train","base"))),38,"chat-tuned Base")]
for level,label in [("rm","RM-only"),("sft","SFT-only"),("sft_and_rm","SFT + RM")]:
    pers.append((2,"",AND(eq("condition","treatment-1"),eq("post_train",level)),38,"chat-tuned "+label))
for level,label in [("base","Base"),("rm","RM-only")]:
    pers.append((2,"",AND(eq("condition","treatment-2"),eq("post_train",level)),38,"developer "+label))
    pers.append((3,"",AND(isin("condition",["treatment-1","treatment-2"]),eq("post_train",level)),40,"developer "+label))
for robust,out in ((True,"post_average_imputed_with_pre"),(False,"post_average")):
    refs=[]
    for s,prefix,sel,table,suffix in pers:
        col=prefix+"prompt_personalize" if prefix else "personalize"
        m=model(s,prefix+out,sel,[fac(col,"generic"),num(prefix+"pre_average")])
        term=col+"::personalized";refs.append([m,term]);emit(table+(0 if robust else 1),"",suffix,m,term)
    pool(42 if robust else 43,"","",refs)
# Prompt effects and covariate-centered adjusted arm means, all eight original prompts.
prompt_sets=[
 (1,"d1.",eq("d1.condition","treat_dialogue")),
 (1,"d2.",eq("d2.condition","treatment")),
 (2,"",AND(isin("condition",["treatment-1","treatment-2"]),isin("post_train",["base","rm"]))),
 (3,"",AND(isin("condition",["treatment-1","treatment-2"]),isin("post_train",["base","rm"])))]
promptlevels=["debate","deep_canvass","information","mega","moral_reframing","none","norms","storytelling"]
for robust,out in ((True,"post_average_imputed_with_pre"),(False,"post_average")):
    refs={x:[] for x in promptlevels if x!="none"}
    for j,(s,prefix,sel) in enumerate(prompt_sets):
        col=prefix+"prompt_rhetoric_id"
        m=model(s,prefix+out,sel,[fac(col,"none"),num(prefix+"pre_average")])
        for level in refs:
            term=col+"::"+level;refs[level].append([m,term])
            emit(44+2*j+(0 if robust else 1),level,"",m,term)
        meansel=isin("condition",["treatment-1","treatment-2"]) if s==3 else sel
        m=model(s,prefix+out,meansel,[fac(col,full=True),num(prefix+"pre_average",True)],False)
        for level in promptlevels:emit(54+2*j+(0 if robust else 1),level,"",m,col+"::"+level)
    for level,rr in refs.items():pool(52 if robust else 53,level,"",rr)
# Original information subgroup controls are deliberately duplicated for info=0.
for robust,out in ((True,"post_average_imputed_with_pre"),(False,"post_average")):
    for s,conds,mods,table in [(2,["treatment-2","control"],["gpt-4o","gpt-4.5"],74),(3,["treatment-1","treatment-2","control"],["gpt-4o","gpt-4.5","chatgpt-4o-latest","grok-3"],80)]:
        base=AND(isin("condition",conds),isin("model",mods))
        for info in (0,1):
            select=AND(base,eq("prompt_rhetoric_id","information") if info else ["not_in","prompt_rhetoric_id",["information"]])
            m=model(s,out,select,[fac("models_vs_control","aa_control"),num("pre_average",True)],
                    parts=[{"select":select,"outcome":out},{"select":AND(base,eq("condition","control")),"outcome":out}])
            for mod in mods:emit(table+(0 if robust else 1),pretty(mod),str(info),m,"models_vs_control::"+mod)
    for s,conds,mod,table in [(3,["treatment-1"],"chatgpt-4o-latest",86),(2,["treatment-2"],"gpt-4.5",92),(3,["treatment-1"],"gpt-4.5",92),(3,["treatment-1","treatment-2"],"grok-3",98)]:
        m=model(s,out,AND(isin("condition",conds),isin("model",["gpt-4o",mod])),
         [ind("prompt_rhetoric_id","information","info"),fac("model","gpt-4o"),prod("info","model::"+mod,"interaction"),num("pre_average")])
        for term,label in [("info","Info prompt"),("model::"+mod,pretty(mod)),("interaction","Info prompt x "+pretty(mod))]:
            emit(table+(0 if robust else 1),label,str(s),m,term)
m=model(2,"post_average",AND(rg("model","405b"),rg("prompt_rhetoric_id","information")),[fac("prompt_rhetoric_id","information"),num("pre_average")])
emit(115,"Deceptive info prompt (vs. info prompt)","",m,"prompt_rhetoric_id::information_with_deception")
# Original attrition grouping and complete primary-outcome sample counts.
ATTR=[
 (117,1,"d1.","models_vs_control",None),(119,1,"d1.","prompt_personalize",rg("d1.condition","control",True)),
 (121,1,"d1.","prompt_rhetoric_id",rg("d1.condition","control",True)),(123,1,"d2.","condition",None),
 (125,1,"d2.","prompt_personalize",rg("d2.condition","control",True)),(127,1,"d2.","prompt_rhetoric_id",rg("d2.condition","control",True)),
 (129,2,"","models_vs_control",None),(131,2,"","personalize",rg("condition","control",True)),
 (133,2,"","post_train",eq("condition","treatment-2")),
 (135,2,"","post_train",AND(eq("condition","treatment-1"),rg("model","405b"))),
 (137,2,"","post_train",AND(eq("condition","treatment-1"),rg("model","8b"))),
 (139,2,"","prompt_rhetoric_id",rg("condition","control",True)),(141,3,"","models_vs_control",None),
 (143,3,"","personalize",isin("condition",["treatment-1","treatment-2"])),
 (145,3,"","post_train",isin("condition",["treatment-1","treatment-2"])),
 (147,3,"","prompt_rhetoric_id",isin("condition",["treatment-1","treatment-2"]))]
COUNTS=[
 (153,1,["d1.condition","d1.model"],["d1.post_average","d1.condition"]),
 (154,1,["d1.condition","d1.prompt_rhetoric_id","d1.prompt_personalize"],["d1.post_average","d1.condition"]),
 (155,1,["d2.condition","d2.prompt_rhetoric_id","d2.prompt_personalize"],["d2.post_average"]),
 (156,2,["condition","model","post_train"],["post_average"]),
 (157,2,["condition","prompt_rhetoric_id","personalize"],["post_average"]),
 (158,3,["condition","model","post_train"],["post_average"]),
 (159,3,["condition","prompt_rhetoric_id","personalize"],["post_average"])]
save(RUN/"analysis_designs.json",{"created_at_utc":now(),"models":MODELS,"recipes":RECIPES,"meta":META,"attrition":ATTR,"counts":COUNTS,"runner_sha256":sha(pathlib.Path(__file__))})
def selection(d,ex):
    if ex is None:return pd.Series(True,index=d.index)
    op=ex[0]
    if op in ("and","or"):
        out=pd.Series(op=="and",index=d.index)
        for sub in ex[1:]:out=out&selection(d,sub) if op=="and" else out|selection(d,sub)
        return out
    x=d[ex[1]]
    if op=="eq":return x.notna()&x.eq(ex[2])
    if op=="in":return x.isin(ex[2])
    if op=="not_in":return ~x.isin(ex[2])
    if op=="isna":return x.isna()
    if op=="notna":return x.notna()
    if op=="regex":
        found=x.astype("string").str.contains(ex[2],regex=True,na=False)
        return x.notna() & (~found if ex[3] else found)
    raise ValueError(ex)
def frame(spec):
    d=DATA[spec["study"]]
    if not spec["parts"]:
        z=d.loc[selection(d,spec["select"])].copy();z["_row"]=z.index;z["_outcome"]=spec["outcome"];z["_y"]=z[spec["outcome"]]
        return z
    parts=[]
    for part in spec["parts"]:
        z=d.loc[selection(d,part.get("select",spec["select"]))].copy()
        z["_row"]=z.index;z["_outcome"]=part["outcome"];z["_y"]=z[part["outcome"]]
        if "phase" in part:z["_phase"]=part["phase"]
        parts.append(z)
    return pd.concat(parts,ignore_index=True)
def design(z,spec):
    values={};valid=z["_y"].notna().to_numpy();centers={}
    if spec["intercept"]:values["Intercept"]=np.ones(len(z))
    for f in spec["features"]:
        kind=f["kind"];name=f["name"]
        if kind=="product":values[name]=values[f["left"]]*values[f["right"]];continue
        x=z[f["column"]]
        if f.get("rename"):
            x=x.copy();r=f["rename"];x=x.astype(object);x.loc[z[r["condition_column"]].eq(r["condition_value"])]=r["replacement"]
        if kind=="numeric":
            v=pd.to_numeric(x).to_numpy(float)
            if f.get("scale"):
                mu=float(np.nanmean(v));sd=float(np.nanstd(v,ddof=1));centers[name]={"mean":mu,"sd":sd};v=(v-mu)/sd
            values[name]=v;valid &=np.isfinite(v)
        elif kind=="factor":
            valid &=x.notna().to_numpy();levels=sorted(x.dropna().unique())
            base=f.get("base") or (levels[0] if not f["full"] else None)
            if base is not None:assert base in levels,(name,base,levels)
            for level in levels:
                if f["full"] or level!=base:values[name+"::"+str(level)]=x.eq(level).to_numpy(float)
        elif kind=="indicator":
            # R %in% for information uses FALSE for missing, all other comparisons propagate NA.
            if name!="info":valid &=x.notna().to_numpy()
            values[name]=x.isin([f["value"]]).to_numpy(float)
        elif kind=="contains":
            valid &=x.notna().to_numpy();values[name]=x.astype("string").str.contains(f["value"],na=False).to_numpy(float)
        else:raise ValueError(f)
    columns=list(values);X=np.column_stack(list(values.values()))[valid];y=z["_y"].to_numpy(float)[valid]
    ids=z.loc[valid,["_row","_outcome"]].to_dict(orient="records")
    idsha=hashlib.sha256(json.dumps(ids,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return X,y,columns,{"selected_rows":len(z),"complete_rows":len(y),"row_selection_sha256":idsha,"centers":centers}
STATS={}
for spec in MODELS:
    X,y,columns,detail=design(frame(spec),spec)
    # Sequential independence check implements R's dropped-collinear-column convention.
    keep=[];rank=0
    for j in range(X.shape[1]):
        newrank=np.linalg.matrix_rank(X[:,keep+[j]])
        if newrank>rank:keep.append(j);rank=newrank
    Z=X[:,keep];inverse=np.linalg.pinv(Z);beta=inverse@y;residual=y-Z@beta
    leverage=np.sum(Z*inverse.T,axis=1)
    covariance=(inverse*(residual**2/(1-leverage)))@inverse.T
    ses=np.sqrt(np.maximum(np.diag(covariance),0));df=len(y)-rank
    vals={}
    for j,k in enumerate(keep):
        b=float(beta[j]);se=float(ses[j]);t=b/se
        q=st.t.ppf(.975,df)
        vals[columns[k]]={"estimate":b,"std.error":se,"statistic":t,"p.value":float(2*st.t.sf(abs(t),df)),"conf.low":b-q*se,"conf.high":b+q*se,"df":df}
    for k in set(range(len(columns)))-set(keep):vals[columns[k]]={x:None for x in ("estimate","std.error","statistic","p.value","conf.low","conf.high","df")}
    STATS[spec["id"]]={"coefficients":vals,"detail":detail,"rank":rank,"columns":columns}
    print(spec["id"],"n",len(y),flush=True) if int(spec["id"][1:])%25==0 else None
for spec in META:
    effects=[STATS[m]["coefficients"][term] for m,term in spec["refs"]]
    w=np.array([1/v["std.error"]**2 for v in effects]);b=float(np.dot(w,[v["estimate"] for v in effects])/w.sum());se=float(1/np.sqrt(w.sum()));z=b/se;q=st.norm.ppf(.975)
    STATS[spec["id"]]={"estimate":b,"std.error":se,"statistic":z,"p.value":float(2*st.norm.sf(abs(z))),"conf.low":b-q*se,"conf.high":b+q*se}
def put(table,label,suffix,vals,origin):
    key=str(table)+"|"+norm(label)+"|"+norm(suffix)
    if key in ACTUAL:raise ValueError("duplicate result "+key)
    ACTUAL[key]={"table":table,"label":label,"suffix":suffix,"values":vals,"origin":origin}
for r in RECIPES:
    v=STATS[r["model"]]["coefficients"].get(r["term"]) if r["kind"]=="model" else STATS[r["model"]]
    if v is None:v={}
    put(r["table"],r["label"],r["suffix"],v,r)
def attrlabel(x,col):
    label=pretty(str(x))
    label={"aa_control":"Control","treat_static":"Static message","control":"Control","treatment":"Treatment","generic":"Generic","personalized":"Personalized"}.get(str(x),label)
    label=pt(label)
    if "prompt" in col:label=label[0].upper()+label[1:].lower()
    return label
ATTR_DETAILS=[]
for table,s,prefix,col,sel in ATTR:
    column=prefix+col;d=DATA[s]
    z=d.loc[selection(d,AND(sel,["not_in",prefix+"post_missing",["pre_missing"]],notna(prefix+"post_missing"),notna(column)))]
    # R ANOVA is classical, separate from HC2 treatment regressions.
    groups=[]
    for level,group in z.groupby(column,observed=True):
        y=group[prefix+"outcome_missing"].dropna().to_numpy(float)
        groups.append(y)
        put(table,attrlabel(level,column),"",{"proportion":float(np.mean(y)),"n":len(group)},{"attrition":table,"level":str(level)})
    grand=np.mean(np.concatenate(groups));between=float(sum(len(g)*(np.mean(g)-grand)**2 for g in groups));within=float(sum(np.dot(g-np.mean(g),g-np.mean(g)) for g in groups))
    d1=len(groups)-1;d2=sum(map(len,groups))-len(groups);F=(between/d1)/(within/d2)
    put(table+1,"Condition","",{"df":d1,"sumsq":between,"meansq":between/d1,"statistic":F,"p.value":float(st.f.sf(F,d1,d2))},{"attrition":table})
    put(table+1,"Residuals","",{"df":d2,"sumsq":within,"meansq":within/d2,"statistic":None,"p.value":None},{"attrition":table})
    ATTR_DETAILS.append({"table":table,"selected":len(z),"complete":d1+d2+1,"groups":len(groups)})
for table,s,cols,complete in COUNTS:
    z=DATA[s].dropna(subset=complete).copy()
    for col in cols:
        z[col]=z[col].astype(object).map(lambda x:"NA" if pd.isna(x) else pretty(str(x)) if col.endswith("model") else str(x).replace("_","-") if col.endswith("condition") else str(x))
    for levels,g in z.groupby(cols,dropna=False,observed=True):
        if not isinstance(levels,tuple):levels=(levels,)
        put(table," ".join(levels),"",{"n":len(g)},{"count":table})
sample=sum(int(DATA[s]["d1.post_average" if s==1 else "post_average"].notna().sum()) for s in (1,2,3))
def get(table,label,suffix="",field="estimate"):
    return ACTUAL[str(table)+"|"+norm(label)+"|"+norm(suffix)]["values"][field]
qual={
 "static_dialogue_more_persuasive_study1":get(3,"dialogue (vs. static)")>0 and get(3,"dialogue (vs. static)",field="p.value")<.05,
 "static_dialogue_more_persuasive_study3":get(5,"dialogue (vs. static)")>0 and get(5,"dialogue (vs. static)",field="p.value")<.05,
 "durable_dialogue_effect_chat1":get(1,pretty("gpt-4o"),"S1 chat 1 1")>0 and get(1,pretty("gpt-4o"),"S1 chat 1 1","p.value")<.05,
 "durable_dialogue_effect_chat2":get(1,pretty("gpt-4o"),"S1 chat 2 1")>0 and get(1,pretty("gpt-4o"),"S1 chat 2 1","p.value")<.05,
 "RM_significant_chat_tuned":get(31,"RM","2 chat-tuned")>0 and get(31,"RM","2 chat-tuned","p.value")<.05,
 "SFT_not_significant_chat_tuned":get(31,"SFT","2 chat-tuned","p.value")>=.05,
 "RM_SFT_interaction_not_significant":get(25,"RM x SFT",field="p.value")>=.05,
 "RM_not_significant_developer_study2":get(31,"RM","2 developer","p.value")>=.05,
 "RM_significant_developer_study3":get(31,"RM","3 developer")>0 and get(31,"RM","3 developer","p.value")<.05,
 "pooled_developer_RM_positive_significant":get(33,"")>0 and get(33,"",field="p.value")<.05,
 "pooled_personalization_positive_significant":get(43,"")>0 and get(43,"",field="p.value")<.05,
 "information_prompt_largest_advantage":get(53,"information")==max(get(53,x) for x in promptlevels if x!="none")}
decisions=[]
for target in targets["targets"]:
    ident=target["id"];kind=target["kind"];actual=None;reason=None
    if kind=="qualitative":
        actual=qual.get(ident.removeprefix("claim."));passed=actual is target["expected"]
    elif ident=="human_trial.total_analyzed":
        actual=sample;passed=actual==target["expected"]
    else:
        row=ACTUAL.get(str(target["table"])+"|"+norm(target["row_label"])+"|"+norm(target["row_suffix"]))
        present=row is not None and target["field"] in row["values"]
        if present:actual=row["values"][target["field"]]
        if not present:passed=False;reason="missing row/field"
        elif kind=="undefined":passed=actual is None
        elif actual is None:passed=False
        elif kind=="less_than":passed=actual<target["expected"]
        elif kind=="exact":passed=actual==target["expected"]
        else:passed=abs(actual-target["expected"])<=target["tolerance"]
    decisions.append({**target,"actual":actual,"passed":bool(passed),"reason":reason})
expectedkeys={str(t)+"|"+norm(r["label"])+"|"+norm(r["suffix"]) for t,v in targets["tables"].items() for r in v["rows"]}
extras=sorted(set(ACTUAL)-expectedkeys);missing=sorted(expectedkeys-set(ACTUAL))
metrics={"paper_id":"P072","run_id":sys.argv[1],"started_at_utc":started,"finished_at_utc":now(),"preregistration_sha256":sha(P/"PREREGISTRATION.json"),"targets_sha256":sha(P/"inputs/original_targets.json"),"source_manifest_sha256":sha(P/"SOURCE_MANIFEST.json"),"checks_passed":sum(d["passed"] for d in decisions),"checks_total":len(decisions),"all_checks_passed":all(d["passed"] for d in decisions) and not extras and not missing,"extra_rows":extras,"missing_rows":missing,"actual_rows":len(ACTUAL),"original_sample_n":sample,"input_rows":{str(s):len(d) for s,d in DATA.items()},"model_count":len(MODELS),"fixed_effect_count":len(META),"wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,"peak_memory_mb":psutil.Process().memory_info().peak_wset/1024**2,"threads":1,"paid_api_spend":0,"fresh_gpu_inference":False,"versions":{"python":sys.version,"numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__,"pyreadr":pyreadr.__version__},"reader_warnings":caught}
save(RUN/"model_statistics.json",STATS);save(RUN/"computed_tables.json",ACTUAL);save(RUN/"target_decisions.json",decisions);save(RUN/"metrics.json",metrics);save(RUN/"attrition_details.json",ATTR_DETAILS)
shutil_copy_source=RUN/"runner_source.py"
shutil_copy_source.write_bytes(pathlib.Path(__file__).read_bytes())
files=[{"path":str(f.relative_to(ROOT)).replace("\\","/"),"bytes":f.stat().st_size,"sha256":sha(f)} for f in sorted(RUN.glob("*")) if f.is_file()]
files.extend([{"path":str(pathlib.Path(__file__).relative_to(ROOT)).replace("\\","/"),"bytes":pathlib.Path(__file__).stat().st_size,"sha256":sha(pathlib.Path(__file__))}])
save(RUN/"RUN_MANIFEST.json",{"paper_id":"P072","run_id":sys.argv[1],"created_at_utc":now(),"files":files})
print(json.dumps(metrics,ensure_ascii=True,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
print(json.dumps([d for d in decisions if not d["passed"]],ensure_ascii=True,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
