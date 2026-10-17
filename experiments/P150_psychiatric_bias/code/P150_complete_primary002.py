"""Prospective complete four-model inferential reconstruction. NO execution authority is embedded.
All original numerical work requires exact reviewed authority/config/source bindings.
Source Tables9 and3-7 are two complete fixed pipelines; controls never rescue primary.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
import argparse, datetime, hashlib, itertools, json, math, sys, zipfile
import xml.etree.ElementTree as ET

SCOPE = "psychiatric_complete_four_model_inference_v1"
MODELS = ("Gemini", "ChatGPT", "Claude", "NewMes")
ORDER = ("Gemini", "Claude", "ChatGPT", "NewMes")
ILLNESSES = ("eating", "anxiety", "depression", "schizophrenia", "ADHD")
NS = {"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(65536),b""): h.update(b)
    return h.hexdigest()
def verify(ref):
    assert set(ref)=={"path","bytes","sha256"}, "Exact reference schema required"
    p=Path(ref["path"])
    assert p.is_file() and p.stat().st_size==ref["bytes"] and digest(p)==ref["sha256"]
    return p
def save(p,obj):
    p=Path(p);assert not p.exists()
    with p.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False);f.write("\n")

def workbook(path):
    with zipfile.ZipFile(path) as z:
        ss=["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si",NS)]
        rel={x.attrib["Id"]:x.attrib["Target"] for x in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets=[]
        for sh in ET.fromstring(z.read("xl/workbook.xml")).findall("m:sheets/m:sheet",NS):
            t=rel[sh.attrib["{"+NS["r"]+"}id"]]
            t=t.lstrip("/") if t.startswith("/") else "xl/"+t
            cells={}
            for c in ET.fromstring(z.read(t)).findall(".//m:sheetData/m:row/m:c",NS):
                v=c.find("m:v",NS);f=c.find("m:f",NS);typ=c.attrib.get("t","n")
                lit=ss[int(v.text)] if typ=="s" and v is not None else (v.text if v is not None else "")
                cells[c.attrib["r"]]={"type":typ,"literal":lit,"formula":f.text if f is not None else None}
            sheets.append({"name":sh.attrib["name"],"cells":cells})
        return sheets

def canonical(sheets,offset):
    assert len(sheets)==10
    cols={"explicit":{"A":("D","E","F","G"),"B":("I","J","K","L")},
          "implicit":{"A":("O","P","Q","R"),"B":("T","U","V","W")}}
    condcols={"explicit":("C","H","M","R"),"implicit":("D","I","N","S")}
    records=[];differences=[]
    for ii,ill in enumerate(ILLNESSES):
        for outcome,row0 in (("diagnosis",3),("treatment",10)):
            for race in ("explicit","implicit"):
                for case in ("A","B"):
                    tr={("A","diagnosis"):3,("A","treatment"):4,
                        ("B","diagnosis"):9,("B","treatment"):10}[(case,outcome)]
                    for mi,model in enumerate(MODELS):
                        cell=cols[race][case][mi]+str(row0+ii+offset)
                        copycell=condcols[race][mi]+str(tr+offset)
                        a=sheets[8]["cells"][cell];b=sheets[ii+2]["cells"][copycell]
                        assert a["type"]=="n" and a["formula"] is None and a["literal"] in ("0","1","2","3")
                        assert b["type"]=="n" and b["formula"] is None and b["literal"] in ("0","1","2","3")
                        rec={"id":"/".join((ill,case,model,race,outcome)),"illness":ill,"case":case,
                             "model":model,"race":race,"outcome":outcome,"Table9_cell":cell,
                             "condition_sheet_index":ii+3,"condition_cell":copycell,
                             "Table9_literal":a["literal"],"condition_literal":b["literal"],
                             "analysis_score":int(a["literal"]),"condition_score":int(b["literal"])}
                        records.append(rec)
                        if a["literal"]!=b["literal"]:differences.append(rec["id"])
    records.sort(key=lambda x:(int("".join(c for c in x["Table9_cell"] if c.isdigit())),"".join(c for c in x["Table9_cell"] if c.isalpha())))
    assert len(records)==160 and len({x["id"] for x in records})==160
    assert all(sum(x["model"]==m for x in records)==40 for m in MODELS)
    responses=[]
    rc={"Gemini":("F","G","H"),"ChatGPT":("K","L","M"),"Claude":("P","Q","R"),"NewMes":("U","V","W")}
    for row in range(2+offset,12+offset):
        case=sheets[1]["cells"]["A"+str(row)]["literal"]
        for m,cc in rc.items():
            for race,col in zip(("explicit","implicit","neutral"),cc):
                c=sheets[1]["cells"].get(col+str(row))
                assert c is not None and c["literal"] not in ("","NA")
                responses.append({"key":[case,m,race],"source_cell":col+str(row),"literal":c["literal"]})
    assert len(responses)==120 and len({tuple(x["key"]) for x in responses})==120
    return records,differences,responses

def betacf(a,b,x):
    qab=a+b;qap=a+1;qam=a-1;c=1.;d=1.-qab*x/qap
    if abs(d)<1e-300:d=1e-300
    d=1./d;h=d
    for m in range(1,10001):
        m2=2*m;aa=m*(b-m)*x/((qam+m2)*(a+m2))
        d=1+aa*d;c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d=1+aa*d;c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d;change=d*c;h*=change
        if abs(change-1)<1e-15:return h
    raise ArithmeticError("Incomplete beta did not converge")
def ibeta(a,b,x):
    if x<=0:return 0.
    if x>=1:return 1.
    front=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return front*betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-front*betacf(b,a,1-x)/b
def t_quantile_975(df):
    assert df>0
    lo=0.;hi=1.
    def cdf(t):return 1-.5*ibeta(df/2.,.5,df/(df+t*t))
    while cdf(hi)<.975:
        hi*=2
        assert hi<1e10
    for _ in range(100):
        mid=(lo+hi)/2
        if cdf(mid)<.975:lo=mid
        else:hi=mid
    return (lo+hi)/2

def describe(values):
    n=len(values);assert n>1
    mean=sum(values)/n;sd=math.sqrt(sum((x-mean)**2 for x in values)/(n-1))
    ordered=sorted(values);med=(ordered[(n-1)//2]+ordered[n//2])/2
    counts={str(i):values.count(i) for i in range(4)};largest=max(counts.values())
    modes=[i for i in range(4) if counts[str(i)]==largest]
    first=next(x for x in values if x in modes)
    half=t_quantile_975(n-1)*sd/math.sqrt(n)
    normalhalf=1.959963984540054*sd/math.sqrt(n)
    return {"n":n,"mean":mean,"SD":sd,"median":med,"mode_set":modes,"source_order_mode":first,
            "lowest_mode":min(modes),"highest_mode":max(modes),"t_df":n-1,"t_halfwidth":half,
            "t_low":mean-half,"t_high":mean+half,"normal_low":mean-normalhalf,
            "normal_high":mean+normalhalf,"counts":counts}
def selected(records,field,**selection):
    return [x[field] for x in records if all(x[k]==v for k,v in selection.items())]
def all_descriptives(records,field):
    pools={}
    for race in ("explicit","implicit"):pools["all/"+race]=describe(selected(records,field,race=race))
    pools["all/diagnosis"]=describe(selected(records,field,outcome="diagnosis"))
    pools["all/treatment"]=describe(selected(records,field,outcome="treatment"))
    for m in MODELS:
        pools["model/"+m]=describe(selected(records,field,model=m))
        for race in ("explicit","implicit"):
            pools["model/"+m+"/"+race]=describe(selected(records,field,model=m,race=race))
            for outcome in ("diagnosis","treatment"):
                pools["model/"+m+"/"+race+"/"+outcome]=describe(selected(records,field,model=m,race=race,outcome=outcome))
    for ill in ILLNESSES:
        pools["illness/"+ill]=describe(selected(records,field,illness=ill))
        for outcome in ("diagnosis","treatment"):
            pools["illness/"+ill+"/"+outcome]=describe(selected(records,field,illness=ill,outcome=outcome))
    return pools

def inferential(records,field):
    ordered=sorted(records,key=lambda x:(x[field],x["id"]))
    ranks={};blocks=[];i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered) and ordered[j][field]==ordered[i][field]:j+=1
        rank=Fraction(i+1+j,2)
        for x in ordered[i:j]:ranks[x["id"]]=rank
        blocks.append({"score":ordered[i][field],"n":j-i,"rank":float(rank),"IDs":[x["id"] for x in ordered[i:j]]});i=j
    N=len(records);k=len(MODELS)
    sums={m:sum((ranks[x["id"]] for x in records if x["model"]==m),Fraction(0)) for m in MODELS}
    ns={m:sum(x["model"]==m for x in records) for m in MODELS}
    means={m:sums[m]/ns[m] for m in MODELS}
    raw=Fraction(12,N*(N+1))*sum((sums[m]**2/ns[m] for m in MODELS),Fraction(0))-3*(N+1)
    ties=sum(x["n"]**3-x["n"] for x in blocks)
    correction=1-Fraction(ties,N**3-N)
    var=Fraction(N*(N+1),12)-Fraction(ties,12*(N-1))
    if correction==0:
        H=None;p=None;eta=None;status="not_estimable_all_ties"
    else:
        H=float(raw/correction);assert H>=0
        xx=H/2;p=math.erfc(math.sqrt(xx))+2*math.sqrt(xx)*math.exp(-xx)/math.sqrt(math.pi)
        eta=(H-k+1)/(N-k);status="ok"
    pairs={}
    for a,b in itertools.combinations(MODELS,2):
        difference=float(means[a]-means[b]);se=math.sqrt(float(var*(Fraction(1,ns[a])+Fraction(1,ns[b]))))
        z=difference/se if se>0 else None
        rawp=math.erfc(abs(z)/math.sqrt(2)) if z is not None else None
        adj=min(1.,6*rawp) if rawp is not None else None
        pairs[a+"/"+b]={"models":[a,b],"difference":difference,"SE":se,"z":z,"p_raw":rawp,"p_Bonferroni":adj,
                       "alpha_raw":.05/6,"significant_raw":rawp<.05/6 if rawp is not None else None,
                       "significant_adjusted":adj<.05 if adj is not None else None,
                       "literal_0083_control":rawp<.0083 if rawp is not None else None}
    return {"status":status,"N":N,"k":k,"group_N":ns,"df":k-1,"H_raw":float(raw),"tie_correction":float(correction),
            "H":H,"p":p,"eta_H":eta,"epsilon_control":H/(N-1) if H is not None else None,
            "mean_ranks":{m:float(means[m]) for m in MODELS},"rank_sums":{m:float(sums[m]) for m in MODELS},
            "all_row_ranks":{x["id"]:float(ranks[x["id"]]) for x in records},"tie_blocks":blocks,
            "Dunn_all6":pairs,"rank_order":sorted(MODELS,key=lambda m:(means[m],m))}

def heatmaps(records,field):
    return [{"key":[outcome,ill,m,race],"raw_IDs":[x["id"] for x in records if x["outcome"]==outcome and x["illness"]==ill and x["model"]==m and x["race"]==race],
             "value":sum(selected(records,field,outcome=outcome,illness=ill,model=m,race=race))/2}
            for outcome in ("diagnosis","treatment") for ill in ("schizophrenia","eating","depression","anxiety","ADHD") for m in ("ChatGPT","Claude","Gemini","NewMes") for race in ("explicit","implicit")]

def primary_checks(fit,pools,descriptors):
    checks=[]
    for d in descriptors:
        path=d["path"];actual=fit if path[0]=="inferential" else pools
        for key in path[1:]:actual=actual[key]
        target=d["target"];tol=d.get("tolerance")
        if d["kind"]=="ordered_models":
            meanorder=sorted(MODELS,key=lambda m:(pools["model/"+m]["mean"],m))
            passed=actual==target and meanorder==target
            actual={"mean_rank_order":actual,"raw_mean_order":meanorder}
        elif d["kind"] in ("exact","significance"):passed=actual==target
        else:passed=actual is not None and abs(Decimal(str(actual))-Decimal(str(target)))<=Decimal(str(tol))
        checks.append({**d,"actual":actual,"passed":bool(passed)})
    assert len(checks)==25
    return checks

def supplementary_main_printed_checks(pools):
    targets={"explicit":{"mean":("1.93",".005"),"SD":("0.97",".005"),"median":("2","0"),"t_low":("1.91",".005"),"t_high":("2.14",".005")},
             "implicit":{"mean":("1.37",".005"),"SD":("0.91",".005"),"median":("1","0"),"t_low":("1.36",".005"),"t_high":("1.38",".005")}}
    checks=[]
    for race,fields in targets.items():
        for field,(target,tol) in fields.items():
            actual=pools["all/"+race][field]
            checks.append({"id":"main_aux/"+race+"/"+field,"actual":actual,"target":target,"tolerance":tol,
                "passed":abs(Decimal(str(actual))-Decimal(target))<=Decimal(tol),"primary":False,"cannot_rescue_primary":True})
    assert len(checks)==10
    return checks

def supplement_bindings(pools):
    out={}
    def add(row,items):
        for col,(key,field) in items.items():out[col+str(row)]={"pool":key,"field":field,"actual":pools[key][field]}
    for row,race in ((5,"explicit"),(6,"implicit")):
        key="all/"+race
        add(row,{c:(key,f) for c,f in zip(("B","C","D","E","F","G"),("mean","median","SD","t_low","t_high","source_order_mode"))})
    for base,outcome in ((11,None),(17,"diagnosis"),(23,"treatment")):
        for i,m in enumerate(MODELS):
            e="model/"+m+"/explicit"+("/"+outcome if outcome else "")
            im="model/"+m+"/implicit"+("/"+outcome if outcome else "")
            add(base+i,dict(zip(("B","C","D","E","F","G","H","I","J","K"),
                ((e,"mean"),(im,"mean"),(e,"SD"),(im,"SD"),(e,"t_halfwidth"),(im,"t_halfwidth"),(e,"median"),(im,"median"),(e,"source_order_mode"),(im,"source_order_mode")))))
    for i,ill in enumerate(ILLNESSES):
        d="illness/"+ill+"/diagnosis";t="illness/"+ill+"/treatment"
        add(31+i,dict(zip(("B","C","D","E","F","G"),((d,"mean"),(d,"SD"),(d,"median"),(t,"mean"),(t,"SD"),(t,"median")))))
    assert len(out)==162
    return out
def auxiliary_checks(pools,sheets):
    bindings=supplement_bindings(pools);checks=[]
    for cell,b in bindings.items():
        source=sheets[7]["cells"][cell];assert source["type"]=="n" and source["literal"]!=""
        actual=b["actual"];target=source["literal"]
        checks.append({"id":"supp8/"+cell,"kind":"unverified_historical_aggregate_comparison","path":b,
                       "target":target,"tolerance":"0.0000000001","actual":actual,
                       "passed":abs(Decimal(str(actual))-Decimal(target))<=Decimal("0.0000000001"),
                       "primary":False,"cannot_rescue_primary":True})
    return checks
def qualitative(pools,fit,heat):
    allmeans={ill:pools["illness/"+ill]["mean"] for ill in ILLNESSES}
    count3={m:pools["model/"+m]["counts"]["3"] for m in MODELS}
    count3t={m:sum(pools["model/"+m+"/"+race+"/treatment"]["counts"]["3"] for race in ("explicit","implicit")) for m in MODELS}
    count3d={m:sum(pools["model/"+m+"/"+race+"/diagnosis"]["counts"]["3"] for race in ("explicit","implicit")) for m in MODELS}
    return {"explicit_greater_implicit":pools["all/explicit"]["mean"]>pools["all/implicit"]["mean"],
            "treatment_greater_diagnosis":pools["all/treatment"]["mean"]>pools["all/diagnosis"]["mean"],
            "schizophrenia_is_highest":allmeans["schizophrenia"]==max(allmeans.values()),
            "depression_is_lowest":allmeans["depression"]==min(allmeans.values()),
            "NewMes_strictly_most_score3":all(count3t["NewMes"]>count3t[m] for m in MODELS if m!="NewMes"),
            "NewMes_strictly_most_score3_all_outcomes_control":all(count3["NewMes"]>count3[m] for m in MODELS if m!="NewMes"),
            "NewMes_strictly_most_score3_diagnosis_control":all(count3d["NewMes"]>count3d[m] for m in MODELS if m!="NewMes"),
            "full_illness_means":allmeans,"full_model_score3_counts":count3,
            "full_model_treatment_score3_counts":count3t,"full_model_diagnosis_score3_counts":count3d,
            "clinical_example_status":"Original cached responses and rater notes retained; no new clinical classifications or historical relabeling",
            "historical_kappa_and_power":{"status":"unavailable_original_rater_streams_or_producer","kappa":None,"weighted_kappa":None,"pilot_kappa":None,"power":None},
            "auxiliary_only":True,"cannot_rescue_primary":True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--authorization",required=True)
    args=ap.parse_args();cp=Path(args.config);auth=json.loads(Path(args.authorization).read_text(encoding="utf-8"))
    cfg=json.loads(cp.read_text(encoding="utf-8"))
    assert auth.get("approved") is True and auth.get("execution_authorized") is True
    assert auth.get("root_reviewed_complete_scope") is True and auth.get("native_guard_bound") is True
    assert auth.get("scope")==cfg.get("scope")==SCOPE and auth["config_sha256"]==digest(cp)
    assert auth["worker_sha256"]==digest(Path(__file__))
    assert cfg["mode"] in ("original","fixture") and auth["mode"]==cfg["mode"]
    for ref in cfg["input_refs"]+cfg["runtime_refs"]+auth["frozen_files"]:verify(ref)
    out=Path(cfg["output"]);assert not out.exists();out.mkdir(parents=False)
    start=utc()
    try:
        sheets=workbook(cfg["publisher_workbook"])
        records,differences,responses=canonical(sheets,1)
        assert set(differences)==set(cfg["expected_raw_conflict_IDs"])
        old=workbook(cfg["osf_workbook"]);oldrecords,olddiff,oldresponses=canonical(old,0)
        assert [{k:x[k] for k in ("id","analysis_score","condition_score")} for x in records]==[{k:x[k] for k in ("id","analysis_score","condition_score")} for x in oldrecords]
        assert [x["literal"] for x in responses]==[x["literal"] for x in oldresponses]
        descriptors=json.loads(Path(cfg["primary_descriptors"]).read_text(encoding="utf-8"))["records"]
        save(out/"CANONICAL_ALL160_BOTH_COMPLETE_SOURCE_VERSIONS.json",{"rows":records,"seven_conflicts":differences,"all120_responses":responses,"old_source_equal":True})
        source_sections=json.loads(Path(cfg["source_sections"]).read_text(encoding="utf-8"))
        save(out/"ALL_SOURCE_NOTES_AND_AUXILIARY_PROSE.json",{"source_sections":source_sections,
             "all_condition_sheet_string_cells":[{"sheet_index":i+1,"name":sh["name"],"cells":{k:v for k,v in sh["cells"].items() if v["type"]=="s"}} for i,sh in enumerate(sheets) if 2<=i<=6],
             "clinical_semantics":"Original notes and all published claims retained; no invented historical expert labels or new clinical judgments",
             "all_full_scope_unavailable":[{"family":"original_kappa_and_pilot","status":"unavailable_original_paired_rater_streams"}, {"family":"power_0.93","status":"unavailable_original_shifts_design"}, {"family":"original_generation_and_case_selection","status":"not_regenerated"}]})
        results={}
        for name,field in (("primary_Table9","analysis_score"),("mandatory_complete_Table3_7_counterpart","condition_score")):
            pools=all_descriptives(records,field);fit=inferential(records,field);heat=heatmaps(records,field)
            assert len(heat)==80 and len(fit["Dunn_all6"])==6
            checks=primary_checks(fit,pools,descriptors)
            results[name]={"inferential":fit,"all_descriptives":pools,"all80_heatmap_cells":heat,"all25_primary_comparisons":checks,
                           "all162_auxiliary_source_comparisons":auxiliary_checks(pools,sheets),
                           "all10_main_descriptive_and_CI_auxiliary_comparisons":supplementary_main_printed_checks(pools),
                           "all_qualitative_auxiliary_claims":qualitative(pools,fit,heat),"primary_rescue_allowed":False}
            save(out/(name+".json"),results[name])
        primary_pass=all(x["passed"] for x in results["primary_Table9"]["all25_primary_comparisons"])
        save(out/"RUN_STATUS.json",{"utc_start":start,"utc_end":utc(),"status":"complete_pending_independent_audit","scope":SCOPE,
            "mode":cfg["mode"],"rows":160,"models":4,"ratings_per_model":40,"Dunn_pairs_per_complete_variant":6,
            "primary_gate_count":25,"primary_pass":primary_pass,"both_complete_variants_computed":True,
            "all162_auxiliary_comparisons_per_variant":True,"all80_heatmap_cells_per_variant":True,"full_reproduction_claimed":False})
        refs=[{"path":str(p.resolve()),"bytes":p.stat().st_size,"sha256":digest(p)} for p in sorted(out.iterdir()) if p.is_file()]
        save(out/"OUTPUT_MANIFEST.json",{"utc":utc(),"files":refs})
        return 0 if primary_pass else 2
    except Exception as exc:
        save(out/"FAILED_ATTEMPT.json",{"utc_start":start,"utc_end":utc(),"exception":type(exc).__name__,"message":str(exc),"scope":SCOPE,"no_retry":True})
        raise
if __name__=="__main__":raise SystemExit(main())
