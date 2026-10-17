"""P109 separately implemented80-digit audit. Preparation is source-only; explicit auth required."""
import argparse,pathlib,csv,json,hashlib,datetime,time,shutil,sys,os
import psutil
import mpmath as mp
ROOT=pathlib.Path("{{REPRODUCTION_ROOT}}")
P=ROOT/"papers/P109_higher_order_thinking"
mp.mp.dps=80
D=mp.mpf
def source_decimal(token):
    """Preserve the exact decimal value while avoiding mpmath1.3.0 leading-dot zero parsing."""
    assert isinstance(token,str)
    if token.startswith("."):token="0"+token
    elif token.startswith(("-.","+.")):token=token[0]+"0"+token[1:]
    return D(token)
HALF=D("0.0005");PAD=D("0.000000001")
NORMAL=D("1.959963984540054")
START=None;OUT=None;REMAIN=None;STATE=None
class ResourceStop(Exception):pass
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(f):
    h=hashlib.sha256()
    with f.open("rb") as q:
        while b:=q.read(262144):h.update(b)
    return h.hexdigest()
def pack(x):
    if isinstance(x,mp.mpf):return mp.nstr(x,80)
    if isinstance(x,dict):return {k:pack(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [pack(v) for v in x]
    return x
def save(name,obj):
    (OUT/name).write_text(json.dumps(pack(obj),ensure_ascii=True,indent=2)+"\n",encoding="utf8")
def safe():
    if START is None:return
    proc=psutil.Process()
    rss=sum(max(q.memory_info().rss,getattr(q.memory_info(),"peak_wset",0)) for q in [proc]+proc.children(recursive=True) if q.is_running())
    STATE["peak_process_tree_rss_bytes"]=max(rss,STATE["peak_process_tree_rss_bytes"])
    ram=psutil.virtual_memory().available;disk=shutil.disk_usage(P).free
    STATE["minimum_available_ram_bytes"]=min(ram,STATE["minimum_available_ram_bytes"])
    STATE["minimum_free_disk_bytes"]=min(disk,STATE["minimum_free_disk_bytes"])
    if STATE["peak_process_tree_rss_bytes"]>1073741824:raise ResourceStop("recorded self/descendant RSS exceeded1GiB")
    if ram<1073741824:raise ResourceStop("available RAM below1GiB")
    if disk<37580963840:raise ResourceStop("free disk below35GiB")
    if time.monotonic()-START>REMAIN:raise ResourceStop("aggregate remaining audit allowance exceeded")
    assert proc.cpu_affinity()==[0]
def total(x):return mp.fsum(x)
def weighted(y,w):return total(a*b for a,b in zip(y,w))/total(w)
def qvalue(y,w):
    mu=weighted(y,w)
    return total(a*(b-mu)**2 for a,b in zip(w,y))
def cvalue(w):return total(w)-total(x*x for x in w)/total(w)
def normal_tail(z):return mp.erfc(abs(z)/mp.sqrt(2))
def chi_tail(q,df):
    if q<=0:return D(1)
    return mp.gammainc(D(df)/2,q/2,mp.inf)/mp.gamma(D(df)/2)
def synthesis(y,v,tau=D(0)):
    w=[1/(x+tau) for x in v];mu=weighted(y,w);variance=1/total(w);se=mp.sqrt(variance);z=mu/se
    return {"k":len(y),"mean":mu,"se":se,"variance":variance,"ci_low":mu-NORMAL*se,"ci_high":mu+NORMAL*se,"z":z,"p":normal_tail(z),"tau2":tau}
def dl(y,v):
    w=[1/x for x in v];q=qvalue(y,w);c=cvalue(w);df=len(y)-1
    return max(D(0),(q-df)/c),q,c
def bisect_decreasing(fun,left,right,iterations=250):
    if left==right:return left
    fl,fr=fun(left),fun(right)
    assert fl>=0 and fr<=0,(fl,fr)
    for i in range(iterations):
        mid=(left+right)/2
        if fun(mid)>0:left=mid
        else:right=mid
        if i%50==0:safe()
    return (left+right)/2
def extreme_mean(glo,ghi,wlo,whi,lower):
    ys=glo if lower else ghi
    def residual(mu):
        terms=[]
        for y,lo,hi in zip(ys,wlo,whi):
            r=y-mu
            w=(hi if r<0 else lo) if lower else (hi if r>0 else lo)
            terms.append(w*r)
        return total(terms)
    return bisect_decreasing(residual,min(ys),max(ys))
def synthesis_boxes(glo,ghi,wlo,whi):
    ml=extreme_mean(glo,ghi,wlo,whi,True);mh=extreme_mean(glo,ghi,wlo,whi,False)
    vl,vh=1/total(whi),1/total(wlo);sl,sh=mp.sqrt(vl),mp.sqrt(vh)
    ratios=[ml/sl,ml/sh,mh/sl,mh/sh];zl,zh=min(ratios),max(ratios)
    near=D(0) if zl<=0<=zh else min(abs(zl),abs(zh))
    far=max(abs(zl),abs(zh))
    return {"mean":[ml,mh],"variance":[vl,vh],"se":[sl,sh],"ci_low":[ml-NORMAL*sh,mh-NORMAL*sl],"ci_high":[ml+NORMAL*sl,mh+NORMAL*sh],"z":[zl,zh],"p":[normal_tail(far),normal_tail(near)]}
def padded(lo,hi,physical=None):
    ans=[lo-PAD,hi+PAD]
    if physical:
        ans=[max(D(physical[0]),ans[0]),min(D(physical[1]),ans[1])]
    return ans
def central(y,v,glo,ghi,vlo,vhi):
    k=len(y);df=k-1;tau,q,c=dl(y,v)
    fixed=synthesis(y,v);random=synthesis(y,v,tau)
    points={a+"."+key:value for a,z in [("fixed",fixed),("random",random)] for key,value in z.items()}
    points.update(Q=q,df=df,Q_p=chi_tail(q,df),I2=(100*max(D(0),(q-df)/q) if q else D(0)),C=c,tau2=tau)
    wl,wh=[1/x for x in vhi],[1/x for x in vlo]
    ql=max(D(0),mp.sqrt(qvalue(y,wl))-HALF*mp.sqrt(total(wl)))**2
    qh=(mp.sqrt(qvalue(y,wh))+HALF*mp.sqrt(total(wh)))**2
    cl,ch=cvalue(wl),cvalue(wh);assert cl>0
    tl=max(D(0),(ql-df)/ch);th=max(D(0),(qh-df)/cl)
    rl,rh=[1/(x+th) for x in vhi],[1/(x+tl) for x in vlo]
    raw={}
    for prefix,wlow,whigh in [("fixed",wl,wh),("random",rl,rh)]:
        raw.update({prefix+"."+key:val for key,val in synthesis_boxes(glo,ghi,wlow,whigh).items()})
    raw.update(Q=[ql,qh],C=[cl,ch],tau2=[tl,th],Q_p=[chi_tail(qh,df),chi_tail(ql,df)],I2=[100*max(D(0),(ql-df)/ql) if ql else D(0),100*max(D(0),(qh-df)/qh) if qh else D(0)])
    bounds={}
    for key,(lo,hi) in raw.items():
        limits=(0,1) if key=="Q_p" or key.endswith(".p") else ((0,100) if key=="I2" else ((0,mp.inf) if key in ["Q","C","tau2"] or key.endswith(".variance") or key.endswith(".se") else None))
        bounds[key]=padded(lo,hi,limits)
    for key,value in [("fixed.k",k),("random.k",k),("df",df)]:bounds[key]=[D(value),D(value)]
    return points,bounds,raw
def gates(plan,points,bounds):
    result=[]
    for target in plan["targets"]:
        key=target["id"];lo,hi=bounds[key];cap=target["cap_key"]
        if cap=="exact":
            passed=points[key]==target["target"] and lo==hi==target["target"];detail={"exact":True}
        elif cap=="threshold":
            threshold=D(target["target"][1:]);width_cap=D(str(plan["width_caps"]["p"]))
            passed=hi<threshold;detail={"threshold":threshold,"width_cap":width_cap}
        else:
            value=D(str(target["target"]));half=D(str(target["rounding_half_unit"]));width_cap=D(str(plan["width_caps"][cap]))
            intersects=max(lo,value-half)<=min(hi,value+half)
            passed=intersects and hi-lo<=width_cap
            detail={"target_interval":[value-half,value+half],"intersects":intersects,"width_cap":width_cap}
        result.append({"id":key,"passed":bool(passed),"point":points[key],"envelope":[lo,hi],"width":hi-lo,**detail})
    assert len(result)==16 and len({x["id"] for x in result})==16
    return result
def pm_tau(y,v):
    df=len(y)-1
    if qvalue(y,[1/x for x in v])<=df:return D(0)
    hi=D(1)
    while qvalue(y,[1/(x+hi) for x in v])>df:hi*=2;safe()
    return bisect_decreasing(lambda t:qvalue(y,[1/(x+t) for x in v])-df,D(0),hi)
def reml_tau(y,v):
    n=len(y)
    def score(t):
        w=[1/(x+t) for x in v];mu=weighted(y,w)
        return (total(a*a*(b-mu)**2 for a,b in zip(w,y))-cvalue(w))/2
    def ll(t):
        w=[1/(x+t) for x in v]
        return -(total(mp.log(x+t) for x in v)+mp.log(total(w))+qvalue(y,w))/2
    span=max(y)-min(y);hi=D(1)
    # This sufficient inequality certifies score<0 for every t>=hi.
    while not (n*span**2/(min(v)+hi)**2 < (n-1)/(max(v)+hi)):
        hi*=2;safe()
    grid=[hi*(D(i)/256)**4 for i in range(257)]
    candidates=[D(0)];found=[]
    prior=grid[0];sp=score(prior)
    for x in grid[1:]:
        sx=score(x)
        if sp==0:found.append(prior)
        elif sx==0:found.append(x)
        elif sp*sx<0:
            left,right=prior,x;sign=sp
            for j in range(250):
                mid=(left+right)/2;sm=score(mid)
                if sm*sign>0:left=mid
                else:right=mid
                if j%50==0:safe()
            found.append((left+right)/2)
        prior,sp=x,sx;safe()
    candidates.extend(found)
    chosen=max(candidates,key=ll)
    return chosen,{"score":score(chosen),"candidate_roots":found,"certified_upper_range":hi,"method":"fixed256-point power4 score scan; all detected roots and boundary compared by restricted log-likelihood","stationary_root_completeness_certified":False,"objective":-ll(chosen)}
def support(y,v,printed_se,dimensions,tau):
    names=["Cr","CT","PS"]
    groups={name:[i for i,d in enumerate(dimensions) if d==name] for name in names}
    assert {k:len(x) for k,x in groups.items()}=={"Cr":23,"CT":20,"PS":16}
    group_data={}
    for name,idx in groups.items():
        yy=[y[i] for i in idx];vv=[v[i] for i in idx]
        tj,qj,cj=dl(yy,vv)
        group_data[name]={"y":yy,"v":vv,"tau":tj,"Q":qj,"C":cj}
    pooled=max(D(0),(total(z["Q"] for z in group_data.values())-(len(y)-3))/total(z["C"] for z in group_data.values()))
    schemes={}
    for scheme in ["independentDL","sharedpooled-withinDL","sharedoverallDL"]:
        rows={}
        for name,z in group_data.items():
            t=z["tau"] if scheme=="independentDL" else (pooled if scheme=="sharedpooled-withinDL" else tau)
            rows[name]=synthesis(z["y"],z["v"],t)
            rows[name]["within_fixed_Q"]=z["Q"]
        weights=[1/rows[name]["variance"] for name in names];means=[rows[name]["mean"] for name in names]
        qb=qvalue(means,weights)
        schemes[scheme]={"groups":rows,"between_Q":qb,"between_df":2,"between_p":chi_tail(qb,2)}
        safe()
    xs=[1/s for s in printed_se];zs=[a/s for a,s in zip(y,printed_se)]
    xm,zm=total(xs)/len(y),total(zs)/len(y);xx=total((x-xm)**2 for x in xs)
    slope=total((x-xm)*(z-zm) for x,z in zip(xs,zs))/xx;intercept=zm-slope*xm
    residual=total((z-intercept-slope*x)**2 for x,z in zip(xs,zs));df=len(y)-2
    intercept_se=mp.sqrt(residual/df*(1/D(len(y))+xm*xm/xx));t=intercept/intercept_se
    p=mp.betainc(D(df)/2,D("0.5"),0,D(df)/(df+t*t),regularized=True)
    egger={"intercept":intercept,"slope":slope,"intercept_se":intercept_se,"t":t,"df":df,"p":p,
        "input_se":"printedSE","original_t":D("1.871"),"original_p":D(".066"),
        "t_difference":t-D("1.871"),"p_difference":p-D(".066"),
        "descriptive_t_tolerance":D(".02"),"descriptive_p_tolerance":D(".005"),
        "original_unit_conflict":"29studies vs59effect records; not a central gate"}
    f,r=synthesis(y,v),synthesis(y,v,tau)
    funnel={"fixed_center_outside":sum(abs(a-f["mean"])>NORMAL*s for a,s in zip(y,printed_se)),
        "random_center_outside":sum(abs(a-r["mean"])>NORMAL*s for a,s in zip(y,printed_se)),
        "original_outside":8,"input_se":"printedSE","central_gate":False,"fixed_center":f["mean"],"random_center":r["mean"],"fixed_outside_rows":[i+1 for i,(a,s) in enumerate(zip(y,printed_se)) if abs(a-f["mean"])>NORMAL*s],"random_outside_rows":[i+1 for i,(a,s) in enumerate(zip(y,printed_se)) if abs(a-r["mean"])>NORMAL*s]}
    pm=pm_tau(y,v);reml,rm=reml_tau(y,v)
    sensitivities={"PauleMandel":synthesis(y,v,pm),"REML":synthesis(y,v,reml),"REML_solver":rm}
    sensitivities["PauleMandel"]["score_residual"]=qvalue(y,[1/(x+pm) for x in v])-(len(y)-1)
    sensitivities["REML"]["objective"]=rm["objective"]
    return {"dimensions":schemes,"Egger":egger,"funnel":funnel,"sensitivities":sensitivities}
def compare(expected,observed,path,checks):
    if isinstance(expected,dict):
        if not isinstance(observed,dict):checks.append({"path":path,"passed":False,"reason":"missing dictionary"});return
        for key,val in expected.items():
            if key not in observed:checks.append({"path":path+"."+key,"passed":False,"reason":"missing mandatory field"})
            else:compare(val,observed[key],path+"."+key,checks)
    elif isinstance(expected,list):
        if not isinstance(observed,list) or len(expected)!=len(observed):
            checks.append({"path":path,"passed":False,"reason":"list census mismatch"});return
        for i,(a,b) in enumerate(zip(expected,observed)):compare(a,b,path+"."+str(i),checks)
    elif isinstance(expected,mp.mpf):
        try:
            got=D(str(observed));tol=D("1e-7") if "sensitivities" in path and path.endswith("tau2") else D("1e-9")
            delta=abs(expected-got);passed=mp.isfinite(got) and delta<=tol
            checks.append({"path":path,"passed":bool(passed),"absolute_error":delta,"prospective_numerical_tolerance":tol})
        except Exception:checks.append({"path":path,"passed":False,"reason":"not numeric"})
    else:checks.append({"path":path,"passed":expected==observed})
def read_root_outputs(runner):
    folder=runner.parent
    names=["primary_statistics.json","source_rounding_enclosures.json","comparisons.json","supporting_diagnostics.json","result.json","source_rows_and_precision.json"]
    data={name:json.loads((folder/name).read_text(encoding="utf8")) for name in names}
    primary=data[names[0]];box=data[names[1]];comp=data[names[2]];diag=data[names[3]]
    points={}
    for group in ["fixed","random"]:
        points.update({group+"."+k:v for k,v in primary[group].items()})
    points.update({k:v for k,v in primary.items() if k not in ["fixed","random"]})
    points["tau2"]=points.pop("tau2_DL");points["fixed.tau2"]=0;points["random.tau2"]=points["tau2"]
    raw={}
    for group in ["fixed","random"]:raw.update({group+"."+k:v for k,v in box[group].items()})
    raw.update({("tau2" if k=="tau2_DL" else k):v for k,v in box.items() if k not in ["fixed","random","df"]})
    bounds={}
    for k,(lo,hi) in raw.items():
        lo,hi=lo-1e-9,hi+1e-9
        if k=="Q_p" or k.endswith(".p"):lo,hi=max(0.,lo),min(1.,hi)
        elif k=="I2":lo,hi=max(0.,lo),min(100.,hi)
        elif k in ["Q","C","tau2"] or k.endswith(".se") or k.endswith(".variance"):lo=max(0.,lo)
        bounds[k]=[lo,hi]
    for k in ["fixed.k","random.k","df"]:bounds[k]=[points[k],points[k]]
    for c in comp:
        if "rounding_envelope" in c:bounds[c["id"]]=c["rounding_envelope"]
    schemes={}
    for old,new in [("independent_DL","independentDL"),("shared_within_DL","sharedpooled-withinDL"),("shared_overall_DL","sharedoverallDL")]:
        source=diag["dimensions_all_three_schemes"][old]
        groups={}
        for name,row in source["groups"].items():
            groups[name]={k:v for k,v in row.items() if k!="heterogeneity"}
            groups[name]["within_fixed_Q"]=row["heterogeneity"]["Q"]
        schemes[new]={"groups":groups,"between_Q":source["between_Q"],"between_df":source["between_df"],"between_p":source["between_p"]}
    e=diag["egger"]
    egger={k:e[k] for k in ["intercept","slope","intercept_se","t","df","t_difference","p_difference"]}
    egger.update(p=e["p_two_sided"],input_se="printedSE",original_t=e["source_t"],original_p=e["source_p"],
        descriptive_t_tolerance=.02,descriptive_p_tolerance=.005,
        original_unit_conflict="29studies vs59effect records; not a central gate" if e["paper_calls_cohort_29studies"] else "missing original unit conflict")
    f=diag["funnel"]
    funnel={"fixed_center_outside":f["fixed"]["outside_count"],"random_center_outside":f["random"]["outside_count"],
        "original_outside":f["fixed"]["source_outside_count"],"input_se":"printedSE","central_gate":False,
        "fixed_center":f["fixed"]["center"],"random_center":f["random"]["center"],
        "fixed_outside_rows":f["fixed"]["outside_figure3_rows"],"random_outside_rows":f["random"]["outside_figure3_rows"]}
    sensitivity=diag["overall_estimator_sensitivity"]
    supporting={"dimensions":schemes,"Egger":egger,"funnel":funnel,
        "sensitivities":{"PauleMandel":sensitivity["Paule_Mandel"],"REML":sensitivity["REML"]}}
    source=data["source_rows_and_precision.json"]
    input_boxes={key:[r[field] for r in source] for key,field in [
        ("g_lower","g_lower"),("g_upper","g_upper"),("variance_lower","variance_lower"),("variance_upper","variance_upper"),("point_variance","point_variance")]}
    return {"points":points,"bounds":bounds,"raw_bounds":raw,
        "gates":[{"id":c["id"],"passed":c["passed"]} for c in comp],
        "supporting":supporting,"input_boxes":input_boxes,
        "positive_random_lower_ci_throughout_envelope":data["result.json"]["all_rounding_random_lower_ci_positive"],"root_summary":data["result.json"]},names
def main():
    global START,OUT,REMAIN,STATE
    ap=argparse.ArgumentParser()
    ap.add_argument("--runner-result",required=True);ap.add_argument("--output-dir",required=True)
    ap.add_argument("--authorization",required=True);args=ap.parse_args()
    pp=P/"PREREGISTRATION_001.json";inp=P/"sources/figure3_literal_transcription_001.csv"
    plan=json.loads(pp.read_text(encoding="utf8"));auth=json.loads(pathlib.Path(args.authorization).read_text(encoding="utf8"))
    runner=pathlib.Path(args.runner_result);OUT=pathlib.Path(args.output_dir)
    assert OUT.resolve().is_relative_to(P.resolve()) and not OUT.exists()
    assert auth["approved"] is True and auth["run_id"]=="P109-central-001"
    assert auth["preregistration_sha256"]==digest(pp)
    assert auth["input_csv_sha256"]==digest(inp) and auth["auditor_sha256"]==digest(pathlib.Path(__file__))
    assert auth["runner_result_sha256"]==digest(runner)
    REMAIN=float(auth["aggregate_remaining_seconds"]);assert 0<REMAIN<=600
    assert plan["paper_id"]=="P109" and len(plan["targets"])==16
    assert plan["resources"]=={"cpu_threads":1,"rss_cap_bytes":1073741824,"available_ram_floor_bytes":1073741824,"free_disk_floor_bytes":37580963840,"aggregate_seconds":600,"GPU":False,"downloads":"None further required"}
    assert mp.__version__=="1.3.0"
    psutil.Process().cpu_affinity([0])
    OUT.mkdir();START=time.monotonic()
    STATE={"status":"starting","started_at_utc":utc(),"precision_digits":80,"paper_id":"P109","run_id":"P109-central-001",
        "preregistration_sha256":digest(pp),"input_sha256":digest(inp),"runner_sha256":digest(runner),"auditor_sha256":digest(pathlib.Path(__file__)),
        "peak_process_tree_rss_bytes":0,"minimum_available_ram_bytes":psutil.virtual_memory().available,
        "minimum_free_disk_bytes":shutil.disk_usage(P).free,"aggregate_remaining_seconds":REMAIN,"automatic_restart":False}
    try:
        safe()
        with inp.open(encoding="utf8",newline="") as q:rows=list(csv.DictReader(q))
        assert len(rows)==59 and [int(z["figure3_row"]) for z in rows]==list(range(1,60))
        y=[source_decimal(z["g"]) for z in rows];se=[source_decimal(z["se"]) for z in rows];pv=[source_decimal(z["variance"]) for z in rows]
        assert all(x>HALF for x in se)
        glo,ghi=[x-HALF for x in y],[x+HALF for x in y]
        vlo=[max((s-HALF)**2,a-HALF,D(0)) for s,a in zip(se,pv)]
        vhi=[min((s+HALF)**2,a+HALF) for s,a in zip(se,pv)]
        assert all(0<l<=h for l,h in zip(vlo,vhi)),"empty or nonpositive source variance intersection"
        v=[min(h,max(l,s*s)) for s,l,h in zip(se,vlo,vhi)]
        points,bounds,raw=central(y,v,glo,ghi,vlo,vhi);gs=gates(plan,points,bounds)
        supporting=support(y,v,se,[z["dimension"] for z in rows],points["tau2"])
        result={"points":points,"bounds":bounds,"unpadded_analytical_bounds":raw,"gates":gs,"supporting":supporting,
            "positive_random_lower_ci_throughout_envelope":bounds["random.ci_low"][0]>0,
            "all16_original_gates_passed":all(z["passed"] for z in gs),
            "input_boxes":{"g_lower":glo,"g_upper":ghi,"variance_lower":vlo,"variance_upper":vhi,"point_variance":v},
            "padding_policy":"1e-9 applied once to final propagated endpoints; p clipped[0,1], I2[0,100], nonnegativeQ/C/tau/SE/variance",
            "supporting_input_policy":"Egger/funnel printedSE; syntheses deterministic clampedpointvariance"}
        safe()
        root,names=read_root_outputs(runner);checks=[]
        for name in names:
            assert auth["runner_files_sha256"][name]==digest(runner.parent/name),"runner audit-input hash mismatch"
        for key in ["points","bounds","input_boxes"]:compare(result[key],root.get(key),key,checks)
        compare(result["unpadded_analytical_bounds"],root.get("raw_bounds"),"raw_bounds",checks)
        if isinstance(root.get("gates"),list):
            got={z["id"]:z["passed"] for z in root["gates"]}
            checks.append({"path":"gates.census","passed":len(got)==16})
            for z in gs:checks.append({"path":"gate:"+z["id"],"passed":got.get(z["id"])==z["passed"]})
        else:checks.append({"path":"gates.census","passed":False})
        # Supporting scalar definitions are independently reported. Compare shared quantities,
        # while all REML solver metadata/candidates are preserved rather than forcing algorithm identity.
        required_support={k:v for k,v in supporting.items() if k!="sensitivities"}
        compare(required_support,root.get("supporting"),"supporting",checks)
        root_sens=(root.get("supporting") or {}).get("sensitivities",{})
        for key in ["PauleMandel","REML"]:
            observed=root_sens.get(key)
            if not isinstance(observed,dict) or "tau2" not in observed:
                checks.append({"path":"supporting.sensitivities."+key,"passed":False,"reason":"missing solver estimate"});continue
            compare(supporting["sensitivities"][key]["tau2"],observed["tau2"],"supporting.sensitivities."+key+".independent_solver_tau2",checks)
            rtau=D(str(observed["tau2"]));assert rtau>=0
            conditional=synthesis(y,v,rtau)
            weights=[1/(x+rtau) for x in v]
            if key=="PauleMandel":conditional["score_residual"]=qvalue(y,weights)-(len(y)-1)
            else:conditional["objective"]=(total(mp.log(x+rtau) for x in v)+mp.log(total(weights))+qvalue(y,weights))/2
            compare(conditional,observed,"supporting.sensitivities."+key+".formula_at_root_tau2",checks)
        checks.append({"path":"positive_random_ci_condition","passed":root.get("positive_random_lower_ci_throughout_envelope")==result["positive_random_lower_ci_throughout_envelope"]})
        checks.append({"path":"complete59_effect_census","passed":root["root_summary"]["source_rows"]==59})
        checks.append({"path":"root_complete_gate_summary","passed":root["root_summary"]["central_gate_count"]==16 and root["root_summary"]["passed_gates"]==sum(z["passed"] for z in gs) and root["root_summary"]["all_central_gates_passed"]==result["all16_original_gates_passed"]})
        checks.append({"path":"all_reported_points_inside_source_envelopes","passed":all(bounds[k][0]<=value<=bounds[k][1] for k,value in points.items() if k in bounds)})
        result["audit_checks"]=checks;result["audit_failures"]=[x for x in checks if not x["passed"]]
        result["independent_numerical_agreement"]=not result["audit_failures"]
        save("INDEPENDENT80_RESULTS.json",result)
        STATE.update(status="passed" if result["independent_numerical_agreement"] else "failed_numerical_agreement",
            checks=len(checks),failures=len(result["audit_failures"]),original_gates_total=16,
            original_gates_passed=sum(z["passed"] for z in gs),all_original_gates_passed=result["all16_original_gates_passed"],
            complete_original_scope_compatible=result["all16_original_gates_passed"] and result["positive_random_lower_ci_throughout_envelope"])
        code=0 if result["independent_numerical_agreement"] else 2
    except ResourceStop as e:
        STATE.update(status="resource_stop",reason=str(e));code=77
    except Exception as e:
        STATE.update(status="failed",error_type=type(e).__name__,reason=str(e));code=2
    STATE.update(finished_at_utc=utc(),elapsed_seconds=time.monotonic()-START)
    save("AUDIT_STATUS.json",STATE)
    files=[{"path":str(f.relative_to(ROOT)),"bytes":f.stat().st_size,"sha256":digest(f)} for f in sorted(OUT.iterdir()) if f.is_file()]
    save("AUDIT_MANIFEST.json",{"created_at_utc":utc(),"files":files})
    print(json.dumps(pack(STATE)),flush=True);return code
if __name__=="__main__":sys.exit(main())
