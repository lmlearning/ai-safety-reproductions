"""P150 independent auditor. SOURCE ONLY until exact root authority is supplied.
No primary implementation is imported or read. Original numeric targets are
comparators only, never inputs to ranks, moments, tails or uncertainty estimates.
"""
import argparse, collections, decimal, fractions, hashlib, itertools, json
import math, os, pathlib, posixpath, re, sys, time, zipfile
import xml.etree.ElementTree as ET

D = decimal.Decimal
F = fractions.Fraction
PRECISION = 100
PI = D("3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679")
MODELS = ("Gemini", "ChatGPT", "Claude", "NewMes")
ILLNESSES = ("eating", "anxiety", "depression", "schizophrenia", "ADHD")
RACES = ("explicit", "implicit")
OUTCOMES = ("diagnosis", "treatment")
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
START = None
LIMIT = 300
def budget():
    if START is not None and time.monotonic() - START > LIMIT:
        raise TimeoutError("independent auditor prospective phase deadline")

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def dec(x):
    if isinstance(x, F):
        return D(x.numerator) / D(x.denominator)
    return x if isinstance(x, D) else D(str(x))

def encode(x):
    if isinstance(x, F):
        return str(x.numerator) + "/" + str(x.denominator)
    if isinstance(x, D):
        return str(x)
    raise TypeError(type(x).__name__)

def erfc_decimal(x):
    """Independent Maclaurin erf integration with 100-digit cancellation guard."""
    x = abs(dec(x))
    if x > 10:
        raise ValueError("normal-tail domain exceeds prospective N160 bound")
    term = x
    total = term
    for n in range(1, 1500):
        budget()
        term = -term * x * x / D(n)
        add = term / D(2*n + 1)
        total += add
        if abs(add) < D("1e-96"):
            answer = D(1) - D(2) * total / PI.sqrt()
            if answer < 0 and answer > D("-1e-85"):
                answer = D(0)
            if not (D(0) <= answer <= D(1)):
                raise ArithmeticError("normal tail lost precision")
            return answer
    raise ArithmeticError("normal series did not converge")

def chi3_survival(h):
    h = dec(h)
    if h < 0:
        raise ValueError("negative exact H")
    x = (h / D(2)).sqrt()
    return erfc_decimal(x) + D(2) * x * (-h/D(2)).exp() / PI.sqrt()

def atan_decimal(x):
    x = dec(x)
    if x < 0:
        return -atan_decimal(-x)
    multiplier = 1
    while x > D("0.125"):
        x = x / (D(1) + (D(1) + x*x).sqrt())
        multiplier *= 2
    term = x
    total = x
    for n in range(1, 400):
        term = -term * x*x
        add = term / D(2*n + 1)
        total += add
        if abs(add) < D("1e-96"):
            return D(multiplier) * total
    raise ArithmeticError("atan series did not converge")

def student_cdf(t, nu):
    """Integer-df t CDF via integral of cos^(nu-1), no beta/gamma library."""
    t = dec(t)
    if nu < 1 or not isinstance(nu, int):
        raise ValueError("integer positive Student degrees of freedom required")
    if t < 0:
        return D(1) - student_cdf(-t, nu)
    hyp = (D(nu) + t*t).sqrt()
    sn = t / hyp
    cs = D(nu).sqrt() / hyp
    exponent = nu - 1
    if nu % 2:
        integral = atan_decimal(t / D(nu).sqrt())
        begin = 2
        m = (nu-1)//2
        coefficient = D(4**m * math.factorial(m)**2) / D(math.factorial(2*m)) / PI
    else:
        integral = sn
        begin = 3
        m = nu//2
        coefficient = D(math.factorial(2*m)) / D(4**m * math.factorial(m) * math.factorial(m-1))
    for power in range(begin, exponent+1, 2):
        integral = sn * cs**(power-1) / D(power) + D(power-1) / D(power) * integral
    return D("0.5") + coefficient * integral

T_CACHE = {}
def t975(nu):
    if nu not in T_CACHE:
        lo, hi = D(0), D(16)
        while student_cdf(hi, nu) < D("0.975"):
            hi *= 2
        for unused in range(110):
            budget()
            mid = (lo+hi)/2
            if student_cdf(mid, nu) < D("0.975"):
                lo = mid
            else:
                hi = mid
        T_CACHE[nu] = (lo+hi)/2
    return T_CACHE[nu]

def normal975():
    lo, hi = D(0), D(4)
    for unused in range(110):
        mid = (lo+hi)/2
        if erfc_decimal(mid / D(2).sqrt()) > D("0.05"):
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

def workbook(path):
    """Independent ZIP/XML parser preserves actual empty/formula/raw cell literals."""
    result = []
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if sum(x.file_size for x in members) > 32*1024**2:
            raise ValueError("32MiB uncompressed workbook cap")
        texts = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
                texts.append("".join(t.text or "" for t in si.iter(S+"t")))
        rel = {e.attrib["Id"]: e.attrib["Target"] for e in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).find(S+"sheets"):
            budget()
            target = rel[sheet.attrib[R+"id"]]
            name = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/"+target)
            if name.startswith("../") or name not in z.namelist():
                raise ValueError("invalid sheet relationship")
            cells = {}
            root = ET.fromstring(z.read(name))
            for c in root.iter(S+"c"):
                address = c.attrib["r"]
                if address in cells:
                    raise ValueError("duplicate literal cell")
                typ = c.attrib.get("t", "n")
                v = c.find(S+"v")
                formula = c.find(S+"f")
                literal = None if v is None else (v.text or "")
                decoded = literal
                if typ == "s":
                    decoded = texts[int(literal)]
                elif typ == "inlineStr":
                    decoded = "".join(t.text or "" for t in c.iter(S+"t"))
                cells[address] = {"type":typ, "raw_literal":literal, "decoded":decoded,
                                  "formula":None if formula is None else (formula.text or "")}
            result.append({"name":sheet.attrib["name"], "member":name, "cells":cells})
    if len(result) != 10:
        raise ValueError("complete ten-sheet source required")
    return result

def numeric_cell(book, sheet, cell):
    v = book[sheet-1]["cells"].get(cell)
    if v is None or v["formula"] is not None or v["type"] != "n":
        raise ValueError("missing/formula/non-numeric rating "+str(sheet)+"/"+cell)
    score = D(v["raw_literal"])
    if score != score.to_integral_value() or not (0 <= score <= 3):
        raise ValueError("rating outside literal integer0..3")
    return int(score), v

def score_records(book, offset, variant):
    records = []
    for illness_index, illness in enumerate(ILLNESSES):
        for case in ("A","B"):
            for mi, model in enumerate(MODELS):
                for race in RACES:
                    for outcome in OUTCOMES:
                        if variant == "Table9":
                            sheet = 9
                            row = (3 if outcome=="diagnosis" else 10) + illness_index + offset
                            columns = {"explicit":{"A":"DEFG","B":"IJKL"},
                                       "implicit":{"A":"OPQR","B":"TUVW"}}
                            column = columns[race][case][mi]
                        elif variant == "Tables3-7":
                            sheet = illness_index + 3
                            row = (3 if case=="A" else 9) + (outcome=="treatment") + offset
                            column = ("CHMR" if race=="explicit" else "DINS")[mi]
                        else:
                            raise ValueError("unknown whole-source variant")
                        cell = column+str(row)
                        value, raw = numeric_cell(book, sheet, cell)
                        records.append({"id":"/".join((illness,case,model,race,outcome)),
                                        "illness":illness,"case":case,"model":model,
                                        "race":race,"outcome":outcome,"value":value,
                                        "sheet":sheet,"cell":cell,"raw":raw})
    if len(records)!=160 or len({r["id"] for r in records})!=160:
        raise ValueError("complete independent identity census failed")
    def canonical_key(record):
        illness_index = ILLNESSES.index(record["illness"])
        row = (3 if record["outcome"]=="diagnosis" else 10) + illness_index + offset
        columns = {"explicit":{"A":"DEFG","B":"IJKL"}, "implicit":{"A":"OPQR","B":"TUVW"}}
        return row, columns[record["race"]][record["case"]][MODELS.index(record["model"])]
    records.sort(key=canonical_key)
    return records

def inferential(records):
    groups = {model:[r["value"] for r in records if r["model"]==model] for model in MODELS}
    total = collections.Counter(r["value"] for r in records)
    n, k = len(records), len(groups)
    start, mids, blocks, ties = 1, {}, [], 0
    for score in sorted(total):
        size = total[score]
        mids[score] = F(2*start + size - 1, 2)
        blocks.append({"value":score,"n":size,"first_rank":start,"midrank":mids[score]})
        ties += size**3-size
        start += size
    sums = {m:sum((mids[x] for x in values), F(0)) for m,values in groups.items()}
    means = {m:sums[m]/len(groups[m]) for m in MODELS}
    correction = F(1) - F(ties,n**3-n)
    h_raw = F(12,n*(n+1))*sum((sums[m]**2/len(groups[m]) for m in MODELS),F(0)) - 3*(n+1)
    h = h_raw/correction if correction else None
    eta = (h-k+1)/(n-k) if h is not None else None
    variance = F(n*(n+1),12)-F(ties,12*(n-1))
    contrasts = {}
    for left,right in itertools.combinations(MODELS,2):
        difference = means[left]-means[right]
        se = (dec(variance)*(D(1)/len(groups[left])+D(1)/len(groups[right]))).sqrt()
        z = dec(difference)/se if se else None
        raw = erfc_decimal(abs(z)/D(2).sqrt()) if z is not None else None
        adjusted = min(D(1),D(6)*raw) if raw is not None else None
        contrasts[left+"/"+right] = {"difference":dec(difference),"difference_rational":difference,
            "SE":se,"z":z,"p_raw":raw,"p_adjusted":adjusted,
            "significant_raw":raw < D("0.05")/D(6) if raw is not None else False,
            "significant_adjusted":adjusted < D("0.05") if adjusted is not None else False,
            "significant_literal_0p0083":raw < D("0.0083") if raw is not None else False}
    raw_means = {m:F(sum(groups[m]),len(groups[m])) for m in MODELS}
    order = sorted(MODELS,key=lambda m:means[m])
    raw_order = sorted(MODELS,key=lambda m:raw_means[m])
    return {"status":"ok" if h is not None else "not_estimable_all_ties","N":n,"k":k,"df":k-1,"group_N":{m:len(groups[m]) for m in MODELS},
            "rank_blocks":blocks,"rank_sum_rational":sums,"mean_ranks":{m:dec(means[m]) for m in MODELS},
            "per_item_ranks":[{"id":r["id"],"rank":mids[r["value"]]} for r in records],
            "tie_sum":ties,"tie_correction_rational":correction,
            "H_raw_rational":h_raw,"H_rational":h,"H":dec(h) if h is not None else None,"p":chi3_survival(h) if h is not None else None,
            "eta_H":dec(eta) if eta is not None else None,"eta_H_rational":eta,"epsilon_H_over_N_minus_1":dec(h/(n-1)) if h is not None else None,
            "Dunn_variance_rational":variance,"Dunn_all6":contrasts,"rank_order":order,
            "raw_mean_order":raw_order,"raw_model_means":{m:dec(raw_means[m]) for m in MODELS},
            "strict_rank_order":len(set(means.values()))==4,
            "strict_raw_mean_order":len(set(raw_means.values()))==4}

def describe(values, znormal):
    n = len(values)
    if n<2:
        raise ValueError("descriptive pool has fewer than two cases")
    freq = collections.Counter(values)
    mean = F(sum(values),n)
    variance = F(n*sum(v*v for v in values)-sum(values)**2,n*(n-1))
    sd = dec(variance).sqrt()
    ordered = sorted(values)
    median = F(ordered[n//2],1) if n%2 else F(ordered[n//2-1]+ordered[n//2],2)
    modes = sorted(x for x in freq if freq[x]==max(freq.values()))
    first_mode = next(x for x in values if x in modes)
    t_hw = t975(n-1)*sd/D(n).sqrt()
    normal_hw = znormal*sd/D(n).sqrt()
    return {"N":n,"mean":dec(mean),"mean_rational":mean,"sample_variance_rational":variance,
            "SD":sd,"median":dec(median),"modes":modes,"mode_lowest":modes[0],
            "mode_highest":modes[-1],"mode_first_source_encounter":first_mode,
            "CI_halfwidth":t_hw,"CI_lower":dec(mean)-t_hw,"CI_upper":dec(mean)+t_hw,
            "normal_CI_halfwidth":normal_hw,"normal_CI_lower":dec(mean)-normal_hw,
            "normal_CI_upper":dec(mean)+normal_hw,"frequencies":dict(sorted(freq.items()))}

def complete_families(records, book, offset, znormal):
    pools, maps = {}, {}
    def pool(name, filters):
        values=[r["value"] for r in records if all(r[k]==v for k,v in filters.items())]
        pools[name] = describe(values,znormal)
        return name
    for ri,race in enumerate(RACES):
        name=pool("all/"+race,{"race":race})
        for col,field in zip("BCDEFG",("mean","median","SD","CI_lower","CI_upper","modes")):
            maps[col+str(4+ri+offset)] = (name,field)
    for base,outcome in ((10,None),(16,"diagnosis"),(22,"treatment")):
        for mi,model in enumerate(MODELS):
            for race in RACES:
                filt={"model":model,"race":race}
                if outcome: filt["outcome"]=outcome
                name=pool("model/"+model+"/"+race+("/"+outcome if outcome else ""),filt)
                fields=("mean","SD","CI_halfwidth","median","modes")
                cols=("BDFHJ" if race=="explicit" else "CEGIK")
                for col,field in zip(cols,fields):
                    maps[col+str(base+mi+offset)] = (name,field)
    for ii,illness in enumerate(ILLNESSES):
        for outcome,cols in (("diagnosis","BCD"),("treatment","EFG")):
            name=pool("illness/"+illness+"/"+outcome,{"illness":illness,"outcome":outcome})
            for col,field in zip(cols,("mean","SD","median")):
                maps[col+str(30+ii+offset)] = (name,field)
    for model in MODELS:
        pool("model/"+model,{"model":model})
    for illness in ILLNESSES:
        pool("illness/"+illness,{"illness":illness})
    for outcome in OUTCOMES:
        pool("all/"+outcome,{"outcome":outcome})
    if len(pools)!=47:
        raise ValueError("complete all47 descriptive pools required")
    heatmaps=[]
    for outcome,illness,model,race in itertools.product(OUTCOMES,("schizophrenia","eating","depression","anxiety","ADHD"),("ChatGPT","Claude","Gemini","NewMes"),RACES):
        contributors=[r for r in records if r["outcome"]==outcome and r["illness"]==illness and r["model"]==model and r["race"]==race]
        if len(contributors)!=2:
            raise ValueError("complete heatmap needs both source cases")
        heatmaps.append({"id":"/".join((outcome,illness,model,race)),
                         "mean":dec(F(sum(r["value"] for r in contributors),2)),
                         "case_IDs":[r["id"] for r in contributors]})
    comparisons=[]
    for cell,(name,field) in sorted(maps.items()):
        literal=book[7]["cells"].get(cell)
        if literal is None or literal["type"]!="n" or literal["formula"] is not None:
            raise ValueError("missing supplemental literal target "+cell)
        target=D(literal["raw_literal"])
        value=pools[name][field]
        if field=="modes":
            actual=D(pools[name]["mode_first_source_encounter"])
            controls={key:dec(pools[name][key])==target for key in
                      ("mode_lowest","mode_highest","mode_first_source_encounter")}
            comparisons.append({"cell":cell,"pool":name,"field":field,"target":target,
                                "calculated":actual,"mode_set":value,"passes":abs(actual-target)<=D("1e-10"),"tolerance":D("1e-10"),"nominal_mode_set_membership":target in [D(x) for x in value],
                                "single_mode_controls":controls,"historical_mode_producer":"UNAVAILABLE"})
        else:
            tolerance=D("1e-10")
            comparisons.append({"cell":cell,"pool":name,"field":field,"target":target,
                                "calculated":value,"tolerance":tolerance,
                                "delta":dec(value)-target,"passes":abs(dec(value)-target)<=tolerance})
    if len(comparisons)!=162 or len(heatmaps)!=80:
        raise ValueError("whole auxiliary target/heatmap census incomplete")
    return {"descriptives":pools,"supp8_comparisons":comparisons,"heatmaps":heatmaps}

def central_gates(stats, descriptors):
    rows=[]
    for gate in descriptors["records"]:
        value=stats
        path=gate["path"][1:] if gate["path"][0]=="inferential" else gate["path"]
        for part in path:
            value=value[part]
        kind=gate["kind"]
        if kind=="numeric":
            passed=value is not None and abs(dec(value)-D(str(gate["target"])))<=D(str(gate["tolerance"]))
        elif kind=="ordered_models":
            passed=(value==gate["target"] and stats["raw_mean_order"]==gate["target"]
                    and stats["strict_rank_order"] and stats["strict_raw_mean_order"])
        else:
            passed=value==gate["target"]
        rows.append({"id":gate["id"],"name":gate["name"],"kind":kind,"actual":value,
                     "target":gate["target"],"tolerance":gate["tolerance"],"passes":bool(passed)})
    if len(rows)!=25:
        raise ValueError("exact all25 prospective gates required")
    return rows

def source_text(book,sheet,cell):
    c=book[sheet-1]["cells"].get(cell)
    return None if c is None else c["decoded"]

def source_responses(book,offset):
    result=[]
    for row in range(2+offset,12+offset):
        label=source_text(book,2,"A"+str(row))
        if not isinstance(label,str):
            raise ValueError("missing source vignette identity")
        for model,cols in zip(MODELS,(("F","G","H"),("K","L","M"),("P","Q","R"),("U","V","W"))):
            for race,col in zip(("explicit","implicit","neutral"),cols):
                text=source_text(book,2,col+str(row))
                if not isinstance(text,str) or not text.strip():
                    raise ValueError("missing one of all120 original response strings")
                result.append({"key":[label,model,race],"source_cell":col+str(row),"literal":text})
    if len(result)!=120 or len({tuple(r["key"]) for r in result})!=120:
        raise ValueError("full cached-response census")
    return result

def main_literals(families):
    targets={"explicit":{"mean":"1.93","SD":"0.97","median":"2","CI_lower":"1.91","CI_upper":"2.14"},
             "implicit":{"mean":"1.37","SD":"0.91","median":"1","CI_lower":"1.36","CI_upper":"1.38"}}
    rows=[]
    for race,fields in targets.items():
        for field,literal in fields.items():
            target=D(literal);value=families["descriptives"]["all/"+race][field]
            tolerance=D(1).scaleb(target.as_tuple().exponent)/2 if "." in literal else D(0)
            rows.append({"id":race+"/"+field,"literal":literal,"tolerance":tolerance,
                         "actual":value,"passes":abs(value-target)<=tolerance})
    return rows

def qualitative(records,stats,families,sections):
    mean=lambda selected: dec(F(sum(r["value"] for r in selected),len(selected)))
    illness_means={ill:mean([r for r in records if r["illness"]==ill]) for ill in ILLNESSES}
    outcome_means={out:mean([r for r in records if r["outcome"]==out]) for out in OUTCOMES}
    race_means={race:mean([r for r in records if r["race"]==race]) for race in RACES}
    severe={m:sum(r["value"]==3 for r in records if r["model"]==m) for m in MODELS}
    outcome_severe={out:{m:sum(r["value"]==3 for r in records if r["model"]==m and r["outcome"]==out) for m in MODELS} for out in OUTCOMES}
    return {"all_primary_source_sections":sections,
            "explicit_greater_than_implicit":race_means["explicit"]>race_means["implicit"],
            "treatment_greater_than_diagnosis":outcome_means["treatment"]>outcome_means["diagnosis"],
            "schizophrenia_highest_overall":illness_means["schizophrenia"]==max(illness_means.values()),
            "depression_lowest_overall":illness_means["depression"]==min(illness_means.values()),
            "illness_means":illness_means,"race_means":race_means,"outcome_means":outcome_means,
            "all_model_maximum_score3_counts":severe,"all_model_treatment_score3_counts":outcome_severe["treatment"],"all_model_diagnosis_score3_counts":outcome_severe["diagnosis"],"meanrank_and_raw_mean_order":stats["rank_order"],
            "all_diagnosis_heatmap_gt1p5":[{"id":h["id"],"greater":h["mean"]>D("1.5")} for h in families["heatmaps"] if h["id"].startswith("diagnosis/")],
            "historical_clinical_correctness_and_examples":"Original cached responses and every source note retained; no new clinical judgments or success predicates invented.",
            "historical_kappa_pilot_power_generation":"UNAVAILABLE: initial independent rater streams/pilot assumptions and historical inference not released"}

def normalized_cells(book,offset):
    out={}
    for si,sheet in enumerate(book,1):
        for cell,literal in sheet["cells"].items():
            col,row=re.fullmatch(r"([A-Z]+)([0-9]+)",cell).groups()
            row=int(row)-offset
            if row<1:
                continue
            out[str(si)+"/"+col+str(row)]=literal
    return out

def full_source_equivalence(pub,osf):
    a=normalized_cells(pub,1);b=normalized_cells(osf,0)
    rows=[]
    for key in sorted(set(a)|set(b)):
        rows.append({"id":key,"publisher":a.get(key),"OSF":b.get(key),
                     "raw_equal":a.get(key)==b.get(key),
                     "decoded_equal":a.get(key,{}).get("decoded")==b.get(key,{}).get("decoded"),
                     "formula_equal":a.get(key,{}).get("formula")==b.get(key,{}).get("formula")})
    return rows

def flatten(value,path=()):
    if isinstance(value,dict):
        for k in sorted(value):
            yield from flatten(value[k],path+(str(k),))
    elif isinstance(value,list):
        for i,item in enumerate(value):
            yield from flatten(item,path+(str(i),))
    else:
        yield "/".join(path),value

def compare_numeric(a,b):
    """Optional schema-aligned results only, read AFTER independent result seal."""
    left=dict(flatten(a));right=dict(flatten(b));rows=[]
    for path in sorted(set(left)|set(right)):
        x,y=left.get(path),right.get(path)
        passed=x==y
        reason="exact" if passed else "different or missing"
        strict = isinstance(x,(bool,int)) or any(mark in path for mark in ("literal","source_cell","Table9_cell","condition_cell","/key/","/id","/IDs/","/raw_IDs/"))
        if path in left and path in right and not strict:
            try:
                dx,dy=dec(x),dec(y)
                tolerance=D("1e-10")*(D(1)+abs(dx))
                passed=abs(dx-dy)<=tolerance
                reason="independent arithmetic tolerance1e-10 relative/absolute"
            except (decimal.InvalidOperation,ValueError,TypeError):
                pass
        rows.append({"path":path,"independent":x,"primary":y,"agrees":passed,"comparison":reason})
    return rows

def analytic_selfchecks():
    """Unrelated hand-derivable checks; never executed during source preparation."""
    rows=[]
    for mi,model in enumerate(MODELS):
        for j in range(40):
            rows.append({"id":"analytic/"+model+"/"+str(j),"value":mi,"model":model})
    result=inferential(rows)
    assert result["H_rational"]==159 and result["eta_H_rational"]==1
    assert result["mean_ranks"]==dict(zip(MODELS,(D("20.5"),D("60.5"),D("100.5"),D("140.5"))))
    assert result["Dunn_variance_rational"]==F(320000,159)
    for multiple,key in ((1,"Gemini/ChatGPT"),(2,"Gemini/Claude"),(3,"Gemini/NewMes")):
        z=result["Dunn_all6"][key]["z"]
        assert abs(z*z-D(multiple*multiple)*D("15.9"))<D("1e-80")
    for x in (D(0),D("0.1"),D(1),D(2),D(4),D(8)):
        assert abs(erfc_decimal(x)-D(str(math.erfc(float(x)))))<=D("1e-13")*D(str(math.erfc(float(x))))+D("1e-90")
    assert abs(student_cdf(D(1),1)-D("0.75"))<D("1e-90")
    assert student_cdf(D(0),2)==D("0.5")
    assert abs(t975(1)-D("12.706204736174705"))<D("1e-12")
    assert abs(t975(3)-D("3.182446305284263"))<D("1e-12")
    tied=[{"id":"tie/"+model+"/"+str(j),"value":0,"model":model} for model in MODELS for j in range(40)]
    degenerate=inferential(tied)
    assert degenerate["status"]=="not_estimable_all_ties" and degenerate["H"] is None
    return {"hand_rank_H159_eta1_meanranks_all4":True,
            "Dunn_variance_320000_over159":True,"Dunn_three_z_squared_exact_controls":True,
            "normal_tail_vs_stdlib_six_cases":True,"Cauchy_and_df2_CDF_checks":True,
            "Student_quantiles_df1_df3":True,"all_ties_null_status":True,
            "fixture_only_no_credit":True}

def write_json(path,value):
    data=json.dumps(value,indent=2,ensure_ascii=True,default=encode).encode("utf-8")
    total=sum(p.stat().st_size for p in path.parent.iterdir() if p.is_file() and p!=path)
    if len(data)+total>64*1024**2:
        raise ValueError("prospective total output cap64MiB")
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_bytes(data);temporary.replace(path)
    return hashlib.sha256(data).hexdigest()

def run(config,mode):
    descriptors=json.loads(pathlib.Path(config["primary_descriptors"]).read_text(encoding="utf-8"))
    sections=json.loads(pathlib.Path(config["source_sections"]).read_text(encoding="utf-8"))
    books={name:workbook(config[name+"_workbook"]) for name in ("publisher","osf")}
    report={"mode":mode,"separately_authored":True,"no_primary_implementation_import":True,
            "precision":PRECISION,"archives":{},"original_credit":False,
            "source_equivalence":full_source_equivalence(books["publisher"],books["osf"])}
    report["unrelated_analytic_selfchecks"]=analytic_selfchecks() if mode=="fixture" else "Passed separately authorized fixture prerequisite required by root"
    znormal=normal975()
    for archive,book in books.items():
        offset=1 if archive=="publisher" else 0
        variants={}
        rawsets={}
        for variant in ("Table9","Tables3-7"):
            raw=score_records(book,offset,variant);rawsets[variant]=raw
            stats=inferential(raw)
            families=complete_families(raw,book,offset,znormal)
            gates=central_gates(stats,descriptors)
            variants[variant]={"canonical_all160":raw,"inferential":stats,**families,
                "all25_central_gates":gates,"all25_pass":all(g["passes"] for g in gates),
                "all10_main_literal_comparisons":main_literals(families),
                "all_qualitative_claims":qualitative(raw,stats,families,sections)}
        a={r["id"]:r for r in rawsets["Table9"]};b={r["id"]:r for r in rawsets["Tables3-7"]}
        differences=[{"id":key,"Table9":a[key]["value"],"Tables3-7":b[key]["value"]} for key in a if a[key]["value"]!=b[key]["value"]]
        expected=set(config["expected_raw_conflict_IDs"])
        if {r["id"] for r in differences}!=expected:
            raise ValueError("raw conflict identities differ from prospective full source set")
        allnotes=[{"sheet":i+1,"cell":c,"literal":v} for i,s in enumerate(book) if 2<=i<=6 for c,v in s["cells"].items() if v["type"] in ("s","inlineStr","str")]
        report["archives"][archive]={"variants":variants,"all_raw_conflicts":differences,
                                    "all120_original_responses":source_responses(book,offset),
                                    "all_condition_string_cells_including_notes":allnotes,
                                    "all10_literal_sheets":book}
    return report

def projection_variant(v, descriptors):
    raw=v["canonical_all160"]
    s=v["inferential"]
    inf={"status":s["status"],"N":s["N"],"k":s["k"],"group_N":s["group_N"],"df":s["df"],
         "H_raw":dec(s["H_raw_rational"]),"tie_correction":dec(s["tie_correction_rational"]),
         "H":s["H"],"p":s["p"],"eta_H":s["eta_H"],"epsilon_control":s["epsilon_H_over_N_minus_1"],
         "mean_ranks":s["mean_ranks"],
         "rank_sums":{m:dec(x) for m,x in s["rank_sum_rational"].items()},
         "all_row_ranks":{x["id"]:dec(x["rank"]) for x in s["per_item_ranks"]},
         "tie_blocks":[{"score":b["value"],"n":b["n"],"rank":dec(b["midrank"]),
                       "IDs":sorted(r["id"] for r in raw if r["value"]==b["value"])} for b in s["rank_blocks"]],
         "Dunn_all6":{},"rank_order":s["rank_order"]}
    for key,c in s["Dunn_all6"].items():
        inf["Dunn_all6"][key]={"models":key.split("/"),"difference":c["difference"],"SE":c["SE"],"z":c["z"],
            "p_raw":c["p_raw"],"p_Bonferroni":c["p_adjusted"],"alpha_raw":D("0.05")/6,
            "significant_raw":c["significant_raw"],"significant_adjusted":c["significant_adjusted"],
            "literal_0083_control":c["significant_literal_0p0083"]}
    descriptions={}
    for key,p in v["descriptives"].items():
        descriptions[key]={"n":p["N"],"mean":p["mean"],"SD":p["SD"],"median":p["median"],
            "mode_set":p["modes"],"source_order_mode":p["mode_first_source_encounter"],
            "lowest_mode":p["mode_lowest"],"highest_mode":p["mode_highest"],"t_df":p["N"]-1,
            "t_halfwidth":p["CI_halfwidth"],"t_low":p["CI_lower"],"t_high":p["CI_upper"],
            "normal_low":p["normal_CI_lower"],"normal_high":p["normal_CI_upper"],
            "counts":{str(i):p["frequencies"].get(i,0) for i in range(4)}}
    fieldmap={"CI_lower":"t_low","CI_upper":"t_high","CI_halfwidth":"t_halfwidth","modes":"source_order_mode"}
    aux=[]
    for c in v["supp8_comparisons"]:
        pool,field=c["pool"],fieldmap.get(c["field"],c["field"])
        cell=c["cell"]
        own_offset=1 if raw[0]["cell"].endswith("4") else 0
        col,row=re.fullmatch(r"([A-Z]+)([0-9]+)",cell).groups()
        publisher_cell=col+str(int(row)+1-own_offset)
        actual=descriptions[pool][field]
        aux.append({"id":"supp8/"+publisher_cell,"kind":"unverified_historical_aggregate_comparison",
            "path":{"pool":pool,"field":field,"actual":actual},"target":str(c["target"]),
            "tolerance":"0.0000000001","actual":actual,"passed":c["passes"],
            "primary":False,"cannot_rescue_primary":True})
    aux.sort(key=lambda c:c["id"])
    gates=[]
    for descriptor,g in zip(descriptors["records"],v["all25_central_gates"]):
        actual=g["actual"]
        if descriptor["id"]=="G025":
            actual={"mean_rank_order":s["rank_order"],"raw_mean_order":s["raw_mean_order"]}
        gates.append({**descriptor,"actual":actual,"passed":g["passes"]})
    main=[]
    fields={"CI_lower":"t_low","CI_upper":"t_high"}
    for c in v["all10_main_literal_comparisons"]:
        race,field=c["id"].split("/")
        main.append({"id":"main_aux/"+race+"/"+fields.get(field,field),"actual":c["actual"],
            "target":c["literal"],"tolerance":str(c["tolerance"]),"passed":c["passes"],
            "primary":False,"cannot_rescue_primary":True})
    qual=v["all_qualitative_claims"]
    counts=qual["all_model_maximum_score3_counts"]
    treatment=qual["all_model_treatment_score3_counts"]
    diagnosis=qual["all_model_diagnosis_score3_counts"]
    q={"explicit_greater_implicit":qual["explicit_greater_than_implicit"],
       "treatment_greater_diagnosis":qual["treatment_greater_than_diagnosis"],
       "schizophrenia_is_highest":qual["schizophrenia_highest_overall"],
       "depression_is_lowest":qual["depression_lowest_overall"],
       "NewMes_strictly_most_score3":all(treatment["NewMes"]>treatment[m] for m in MODELS if m!="NewMes"),
       "NewMes_strictly_most_score3_all_outcomes_control":all(counts["NewMes"]>counts[m] for m in MODELS if m!="NewMes"),
       "NewMes_strictly_most_score3_diagnosis_control":all(diagnosis["NewMes"]>diagnosis[m] for m in MODELS if m!="NewMes"),
       "full_model_treatment_score3_counts":treatment,"full_model_diagnosis_score3_counts":diagnosis,
       "full_illness_means":qual["illness_means"],"full_model_score3_counts":counts,
       "clinical_example_status":"Original cached responses and rater notes retained; no new clinical classifications or historical relabeling",
       "historical_kappa_and_power":{"status":"unavailable_original_rater_streams_or_producer",
                                     "kappa":None,"weighted_kappa":None,"pilot_kappa":None,"power":None},
       "auxiliary_only":True,"cannot_rescue_primary":True}
    return {"inferential":inf,"all_descriptives":descriptions,
       "all80_heatmap_cells":[{"key":h["id"].split("/"),"raw_IDs":h["case_IDs"],"value":h["mean"]} for h in v["heatmaps"]],
       "all25_primary_comparisons":gates,"all162_auxiliary_source_comparisons":aux,
       "all10_main_descriptive_and_CI_auxiliary_comparisons":main,
       "all_qualitative_auxiliary_claims":q,"primary_rescue_allowed":False}

def canonical_projection(report):
    pub=report["archives"]["publisher"]
    osf=report["archives"]["osf"]
    a=pub["variants"]["Table9"]["canonical_all160"]
    b={r["id"]:r for r in pub["variants"]["Tables3-7"]["canonical_all160"]}
    rows=[]
    for r in a:
        other=b[r["id"]]
        rows.append({"id":r["id"],"illness":r["illness"],"case":r["case"],"model":r["model"],
           "race":r["race"],"outcome":r["outcome"],"Table9_cell":r["cell"],
           "condition_sheet_index":other["sheet"],"condition_cell":other["cell"],
           "Table9_literal":r["raw"]["raw_literal"],"condition_literal":other["raw"]["raw_literal"],
           "analysis_score":r["value"],"condition_score":other["value"]})
    def literal_identity(archive):
        return [(v,r["id"],r["raw"]["raw_literal"],r["value"])
                for v in ("Table9","Tables3-7")
                for r in archive["variants"][v]["canonical_all160"]]
    text_identity=lambda archive:[(tuple(r["key"]),r["literal"]) for r in archive["all120_original_responses"]]
    return {"rows":rows,"seven_conflicts":[r["id"] for r in pub["all_raw_conflicts"]],
            "all120_responses":pub["all120_original_responses"],
            "old_source_equal":literal_identity(pub)==literal_identity(osf) and text_identity(pub)==text_identity(osf)}

def normalize_comparison_lists(value):
    """Order source comparison arrays by declared identity without dropping leaves."""
    if isinstance(value,dict):
        return {k:normalize_comparison_lists(v) for k,v in value.items()}
    if isinstance(value,list):
        result=[normalize_comparison_lists(v) for v in value]
        if result and all(isinstance(x,dict) and "id" in x for x in result):
            if len({x["id"] for x in result})!=len(result):
                raise ValueError("duplicate primary comparison identity")
            result.sort(key=lambda x:x["id"])
        return result
    return value


def source_notes_projection(report,sections):
    book=report["archives"]["publisher"]["all10_literal_sheets"]
    notes=[]
    for i in range(2,7):
        sheet=book[i]
        cells={c:{"type":v["type"],"literal":v["decoded"],"formula":v["formula"]}
               for c,v in sheet["cells"].items() if v["type"] in ("s","inlineStr","str")}
        notes.append({"sheet_index":i+1,"name":sheet["name"],"cells":cells})
    return {"source_sections":sections,"all_condition_sheet_string_cells":notes,
            "clinical_semantics":"Original notes and all published claims retained; no invented historical expert labels or new clinical judgments",
            "all_full_scope_unavailable":[
                {"family":"original_kappa_and_pilot","status":"unavailable_original_paired_rater_streams"},
                {"family":"power_0.93","status":"unavailable_original_shifts_design"},
                {"family":"original_generation_and_case_selection","status":"not_regenerated"}]}

def complete_paired_audit(report,config,output):
    descriptors=json.loads(pathlib.Path(config["primary_descriptors"]).read_text(encoding="utf-8"))
    directory=pathlib.Path(config["primary_output_directory"])
    paired={"canonical":None,"variants":{},"primary_files_read_only_after_independent_seal":True}
    independent=canonical_projection(report)
    main=json.loads((directory/"CANONICAL_ALL160_BOTH_COMPLETE_SOURCE_VERSIONS.json").read_text(encoding="utf-8"))
    paired["canonical"]=compare_numeric(independent,main)
    sections=json.loads(pathlib.Path(config["source_sections"]).read_text(encoding="utf-8"))
    primary_notes=json.loads((directory/"ALL_SOURCE_NOTES_AND_AUXILIARY_PROSE.json").read_text(encoding="utf-8"))
    paired["source_notes_and_all_prose"]=compare_numeric(source_notes_projection(report,sections),primary_notes)
    for original_name,filename in (("Table9","primary_Table9.json"),("Tables3-7","mandatory_complete_Table3_7_counterpart.json")):
        projection=projection_variant(report["archives"]["publisher"]["variants"][original_name],descriptors)
        main=json.loads((directory/filename).read_text(encoding="utf-8"))
        paired["variants"][original_name]=compare_numeric(normalize_comparison_lists(projection),normalize_comparison_lists(main))
    paired["all_declared_leaves_agree"]=all(x["agrees"] for x in paired["canonical"]) and all(x["agrees"] for x in paired["source_notes_and_all_prose"]) and all(x["agrees"] for values in paired["variants"].values() for x in values)
    paired["all_required_census"]={"source_variants":2,"archives":2,"ratings_per_variant":160,
        "response_strings":120,"descriptive_pools_per_variant":47,"supplement_targets_per_variant":162,
        "main_targets_per_variant":10,"heatmaps_per_variant":80,"Dunn_per_variant":6,"central_gates":25}
    return paired

def main():
    global START,LIMIT
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    parser.add_argument("--authority",required=True)
    parser.add_argument("--mode",choices=("fixture","original"),required=True)
    args=parser.parse_args()
    config_path=pathlib.Path(args.config)
    config=json.loads(config_path.read_text(encoding="utf-8"))
    authority=json.loads(pathlib.Path(args.authority).read_text(encoding="utf-8"))
    if authority.get("authorized") is not True or authority.get("role")!="P150_independent_auditor" or authority.get("phase")!=args.mode:
        raise PermissionError("exact root independent auditor phase authority required")
    if authority.get("code_sha256")!=sha(__file__) or authority.get("config_sha256")!=sha(config_path):
        raise PermissionError("code/config authority binding mismatch")
    if config.get("mode")!=args.mode or not config.get("execution_ready"):
        raise PermissionError("prospective source-only configuration")
    expected_class={"fixture":"unrelated_full_raw_fixture","original":"original_published_workbooks"}[args.mode]
    if config.get("input_class")!=expected_class:
        raise PermissionError("exact fixture/original source class required")
    for ref in authority.get("input_refs",[]):
        if sha(ref["path"])!=ref["sha256"]:
            raise ValueError("input/runtime pin mismatch")
    required={str(pathlib.Path(config[key]).resolve()) for key in
              ("publisher_workbook","osf_workbook","primary_descriptors","source_sections")}
    if config.get("primary_output_directory"):
        primary=pathlib.Path(config["primary_output_directory"])
        required.update(str((primary/name).resolve()) for name in
            ("CANONICAL_ALL160_BOTH_COMPLETE_SOURCE_VERSIONS.json","ALL_SOURCE_NOTES_AND_AUXILIARY_PROSE.json",
             "primary_Table9.json","mandatory_complete_Table3_7_counterpart.json"))
    if not required.issubset({str(pathlib.Path(r["path"]).resolve()) for r in authority.get("input_refs",[])}):
        raise PermissionError("all four consumed raw/declarative inputs require explicit pins")
    output=pathlib.Path(config["output"]).resolve()
    workspace=pathlib.Path(config["workspace"]).resolve()
    if workspace not in output.parents or "P150_psychiatric_bias" not in output.parts:
        raise PermissionError("output must stay in the P150 workspace")
    LIMIT=min(int(authority.get("max_seconds",300)),300)
    START=time.monotonic()
    output.mkdir(parents=True,exist_ok=True)
    with decimal.localcontext() as context:
        context.prec=PRECISION
        report=run(config,args.mode)
        digest=write_json(output/"INDEPENDENT_RESULTS_BEFORE_PRIMARY_COMPARISON.json",report)
        status={"phase":args.mode,"independent_sha256":digest,"wall_seconds":time.monotonic()-START,
                "primary_mathematics_source_not_read":True,"native_memory_peak":"UNKNOWN; outer root controller must supply actual measurement","credit_claim":False}
        if config.get("primary_output_directory"):
            paired=complete_paired_audit(report,config,output)
            status["paired_leaf_audit_sha256"]=write_json(output/"EVERY_SCHEMA_ALIGNED_LEAF_AUDIT.json",paired)
            status["all_declared_leaves_agree"]=paired["all_declared_leaves_agree"]
        write_json(output/"AUDIT_COMPLETION_STATUS.json",status)
    print(json.dumps(status))

if __name__=="__main__":
    main()
