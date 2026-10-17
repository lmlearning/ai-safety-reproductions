"""Independent P080 raw-data audit: CSV parsing, normal equations and draw replay."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from pathlib import Path
from p080_resource_guard import ResourceGuard
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/P080_ai_skill_formation"
DATA = PAPER / "sources/retained_original_data/data_analysis__data__Full-Study.csv"
PLAN = PAPER / "PREREGISTRATION_PROPOSAL_20261010.json"
TARGET = PAPER / "ORIGINAL_PUBLISHED_FIGURE_TARGETS_20261010.json"
PLAN_SHA = "b622eeba4aed6aa70959062c4c4ebcb250bc5243f7c3c81c24d799132b695d98"
DATA_SHA = "7c76a8d4279a3fa4f0df24b0b4587c1b8c194561f26057545edac7919237518f"
TARGET_SHA = "ef783454547a2ba7f368f039f16dfa224a8a1e52c16caeb3b42e5e30ef598347"
AREA_ITEMS = {
 "Task1":(1,4,5,8,9,11,12,14,15), "Task2":(2,3,6,10,13),
 "Conceptual":(1,2,3,14,15),"Debugging":(8,10,11,12),
 "CodeReading":(3,4,5,6,9,13)}
EFFORT = {"Very little effort":1,"Little effort":2,"Moderate effort":3,
          "High effort":4,"Very high effort":5}
ITEMS = [i for i in range(1,16) if i != 7]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def guard_inputs(prereg, expected):
    if Path(prereg).resolve() != (PAPER/"PREREGISTRATION.md").resolve():
        raise ValueError("Audit requires root-frozen P080 preregistration")
    if len(expected) != 64 or sha(prereg) != expected:
        raise ValueError("Preregistration hash mismatch")
    if PLAN_SHA not in Path(prereg).read_text(encoding="utf8"):
        raise ValueError("Original proposal hash absent from frozen preregistration")
    for p,h in [(DATA,DATA_SHA),(PLAN,PLAN_SHA),(TARGET,TARGET_SHA)]:
        if sha(p) != h:
            raise ValueError("Immutable source hash mismatch")

    manifest = PAPER / "FROZEN_INPUT_MANIFEST_20261010.json"
    manifest_sha = sha(manifest)
    if manifest_sha not in Path(prereg).read_text(encoding="utf8"):
        raise ValueError("Frozen input manifest hash absent from preregistration")
    entries = json.loads(manifest.read_text(encoding="utf8"))["files"]
    for entry in entries:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or sha(path) != entry["sha256"]:
            raise ValueError("Frozen input/code manifest mismatch")

def item_max(i):
    return 1 if i in (1,2) else 3 if i == 15 else 2

def csv_cohort():
    with DATA.open(encoding="utf-8-sig",newline="") as stream:
        raw = list(csv.DictReader(stream))
    rows = [{k.replace(" ",""):v for k,v in row.items()} for row in raw]
    rows = [r for r in rows if r["STATUS"] in ("COMPLETED","TIME-1N","TIME-2N","TIME-3N")]
    if len(rows) != 52 or any(sum(r["Condition"]==c for r in rows)!=26
                              for c in ["AI","No AI"]):
        raise ValueError("Original cohort census mismatch")
    result = []
    for raw in rows:
        r = {"condition":raw["Condition"],"treatment":int(raw["Condition"]=="No AI"),
             "experience":raw["Howmanyyearsofcodingexperiencedoyouhave?"]}
        for name in ["TaskTime","QuizScore","WarmupTaskTime"]:
            r[name] = float(raw[name]) if raw[name] else float("nan")
        r["QuizScorePercent"] = 100*r["QuizScore"]/27
        for name,key in [("Learning","Howmuchdoyoufeellikeyoulearnedfromthistask?"),
                         ("Enjoyment","Howmuchdidyouenjoythislearningtask?")]:
            r[name] = float(raw[key])
        for name,task in [("Warm Up","WarmupTask"),("Trio Task","TrioTask"),
                          ("Post Task Quiz","PostTaskQuiz")]:
            r[name] = EFFORT[raw[f"Howmucheffortdidyouusetocompleteeachofthetasksinthisstudy?[{task}]"]]
        r["items"] = {i:float(raw[f"Q{i}"]) for i in ITEMS}
        for area,items in AREA_ITEMS.items():
            maximum = sum(item_max(i) for i in items)
            r[area] = 100*sum(int(r["items"][i]) for i in items)/maximum
            r[area+"_fractional"] = 100*sum(r["items"][i] for i in items)/maximum
        result.append(r)
    return result

def normal_fit(rows,metric,adjusted=False,standardize=False):
    y = np.array([r[metric] for r in rows],dtype=float)
    if standardize:
        y = y / np.sqrt(sum((y-y.mean())**2)/(len(y)-1))
    columns = [[1,r["treatment"]]+([r["WarmupTaskTime"]] if adjusted else []) for r in rows]
    x = np.asarray(columns,dtype=float)
    good = np.isfinite(y) & np.all(np.isfinite(x),axis=1)
    x,y = x[good],y[good]
    inverse = np.linalg.inv(x.T @ x)
    coefficient = inverse @ x.T @ y
    residual = y-x@coefficient
    df = len(y)-len(coefficient)
    mse = sum(residual**2)/df
    se = np.sqrt(np.diag(inverse)*mse)
    t = coefficient/se
    p = 2*stats.t.sf(np.abs(t),df)
    margin = stats.t.ppf(.975,df)*se
    return {"N":len(y),"df":df,"coef":coefficient.tolist(),"se":se.tolist(),
            "p":p.tolist(),"ci95":np.array([coefficient-margin,coefficient+margin]).T.tolist(),
            "residual_mse":float(mse)}

def rebuild_fits(rows):
    fits = {}
    for metric in ["TaskTime","QuizScore"]:
        fits["primary_"+metric] = normal_fit(rows,metric)
        fits["standardized_"+metric] = normal_fit(rows,metric,standardize=True)
    fits["adjusted_QuizScorePercent"] = normal_fit(rows,"QuizScorePercent",adjusted=True)
    for years in ["1-3 years","4-6 years","7+ years"]:
        subset = [r for r in rows if r["experience"]==years]
        for metric in ["TaskTime","QuizScore"]:
            fits["experience_"+metric+"|"+years] = normal_fit(subset,metric)
    for metric in list(AREA_ITEMS)+["Learning","Enjoyment","Warm Up","Trio Task","Post Task Quiz"]:
        fits[metric] = normal_fit(rows,metric)
    return fits

def values_for(rows,key):
    metric,category,condition = key
    selected = [r for r in rows if r["condition"]==condition]
    if metric.startswith("experience_"):
        selected = [r for r in selected if r["experience"]==category]
        variable = metric[len("experience_"):]
    elif metric.startswith("main_"):
        variable = metric[len("main_"):]
    else:
        variable = category
    values = np.array([r[variable] for r in selected],dtype=float)
    if not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("Original target group has invalid values")
    return values

def replay_draws(values,draw_count,index,stream,guard):
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([1729,index,stream])))
    draws = np.empty(draw_count,dtype=float)
    for offset in range(0,draw_count,4096):
        guard.check()
        count = min(4096,draw_count-offset)
        indexes = rng.integers(low=0,high=len(values),size=count*len(values),dtype=np.intp)
        draws[offset:offset+count] = values[indexes].reshape(count,len(values)).sum(axis=1)/len(values)
    return draws

def rank_levels():
    eps = math.sqrt(math.log(2*76/.025)/(2*1000000))
    tail = .025/(2*76)
    levels = []
    for q in [.025,.975]:
        linear = 1+(1000-1)*q
        lo,hi = math.floor(linear),math.ceil(linear)
        levels.append([stats.beta.ppf(tail,lo,1001-lo)-eps,
                       stats.beta.ppf(1-tail,hi,1001-hi)+eps])
    return levels

def inverse_cdf(draws,probability):
    # Independent generalized inverse: one-based ceil(M*p) order statistic.
    rank = max(1,min(len(draws),math.ceil(len(draws)*probability)))
    return float(np.partition(draws,rank-1)[rank-1])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prereg",type=Path,required=True)
    parser.add_argument("--prereg-sha256",required=True)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    guard_inputs(args.prereg,args.prereg_sha256)
    output = args.output.resolve()
    if not output.is_relative_to(PAPER.resolve()) or output.exists():
        raise ValueError("Audit output must be new and inside P080 workspace")
    guard = ResourceGuard(ROOT)
    audit = {"paper_id":"P080","status":"running","trial_outcome_calculations_performed":False,
             "checks":[],"provenance":{"prereg_sha256":args.prereg_sha256,
             "proposal_sha256":sha(PLAN),"data_sha256":sha(DATA),"targets_sha256":sha(TARGET),
             "audit_sha256":sha(__file__),"results_sha256":sha(args.results),
             "resource_guard_sha256":sha(Path(__file__).with_name("p080_resource_guard.py")),
             "input_manifest_sha256":sha(PAPER/"FROZEN_INPUT_MANIFEST_20261010.json")}}
    def record(kind,key,passed,details=None):
        audit["checks"].append({"kind":kind,"key":key,"passed":bool(passed),"details":details})
    def save():
        audit["resource"] = guard.summary()
        output.write_text(json.dumps(audit,indent=2,allow_nan=False)+"\n",encoding="utf8")
    output.parent.mkdir(parents=True,exist_ok=True)
    save()
    try:
        result = json.loads(args.results.read_text(encoding="utf8"))
        if result.get("status") != "completed":
            raise ValueError("Cannot audit an incomplete run as complete")
        for key,wanted in [("prereg_sha256",args.prereg_sha256),("proposal_sha256",PLAN_SHA),
                           ("data_sha256",DATA_SHA),("targets_sha256",TARGET_SHA),
                           ("input_manifest_sha256",sha(PAPER/"FROZEN_INPUT_MANIFEST_20261010.json"))]:
            record("provenance",key,result["provenance"].get(key)==wanted)
        rows = csv_cohort()
        fits = rebuild_fits(rows)
        audit["trial_outcome_calculations_performed"] = True
        audit["independent_regressions"] = fits
        record("complete_regression_family",None,set(fits)==set(result["regressions"]))
        for key,fit in fits.items():
            original = result["regressions"][key]
            for field in ["N","df","coef","se","p","ci95","residual_mse"]:
                record("raw_data_regression",key+"|"+field,
                       np.allclose(fit[field],original[field],rtol=1e-11,atol=1e-11))
        for metric in ["TaskTime","QuizScore"]:
            a,b = (np.array([r[metric] for r in rows if r["condition"]==c]) for c in ["AI","No AI"])
            pooled = math.sqrt((sum((a-a.mean())**2)+sum((b-b.mean())**2))/(len(a)+len(b)-2))
            d = float((b.mean()-a.mean())/pooled)
            record("raw_data_Cohen_d",metric,abs(d-result["Cohen_d"][metric])<1e-11)
        adjusted = fits["adjusted_QuizScorePercent"]
        d = adjusted["coef"][1]/math.sqrt(adjusted["residual_mse"])
        record("adjusted_Cohen_d",None,abs(d-result["Cohen_d"]["adjusted_QuizScorePercent"])<1e-11)
        targets = json.loads(TARGET.read_text(encoding="utf8"))["targets"]
        expected = sorted((t for t in targets if t["metric"]!="main_effect_total_SD"),
                           key=lambda t:(t["metric"],t["category"],t["condition"]))
        levels = rank_levels()
        record("fixed_rank_levels",None,np.allclose(levels,result["operational"]["probability_levels"],
                                                   rtol=0,atol=1e-15))
        record("complete_group_family",None,len(result["groups"])==36)
        expected_counts = {"figure_mean":36,"figure_bootstrap_endpoint":72,
            "figure_regression_mean":2,"figure_regression_ci95_low":2,
            "figure_regression_ci95_high":2,"paper_text":5,"main_time_p":1,
            "original_saved_source_p":16,"original_saved_adjusted_fit":5}
        counts = {}
        for c in result["checks"]:
            counts[c["kind"]] = counts.get(c["kind"],0)+1
        record("complete_original_comparison_family",None,counts==expected_counts,counts)
        for index,target in enumerate(expected):
            guard.check()
            group = result["groups"][index]
            key = [target[k] for k in ["metric","category","condition"]]
            record("original_group_identity",index,group["key"]==key and group["group_index"]==index)
            values = values_for(rows,key)
            record("raw_group_N",index,len(values)==group["N"])
            record("raw_group_mean",index,abs(float(values.mean())-group["mean"])<1e-11)
            record("original_figure_mean",index,abs(float(values.mean())-target["mean"])<=1e-4)
            for stream,(label,count) in enumerate([("replay",1000),("reference",1000000)]):
                entry = group["saved_draw_vectors"][label]
                path = (ROOT/entry["path"]).resolve()
                if not path.is_relative_to(PAPER.resolve()):
                    raise ValueError("Draw path escaped P080 workspace")
                saved = np.load(path,allow_pickle=False)
                raw = replay_draws(values,count,index,stream,guard)
                record("draw_vector_hash",f"{index}|{label}",sha(path)==entry["sha256"])
                record("draw_vector_count",f"{index}|{label}",
                       saved.shape==(count,) and entry["draw_count"]==count)
                record("independent_draw_replay",f"{index}|{label}",
                       np.array_equal(raw,saved))
                if label == "reference":
                    bounds = [[inverse_cdf(raw,q) for q in pair] for pair in levels]
                    record("independent_MC_envelope",index,
                           np.allclose(bounds,group["MC_envelopes"],rtol=0,atol=1e-11))
                    for endpoint,field in enumerate(["ci95_low","ci95_high"]):
                        lo,hi = bounds[endpoint]
                        record("original_bootstrap_endpoint",f"{index}|{field}",
                               lo-1e-4<=target[field]<=hi+1e-4,
                               {"target":target[field],"fixed_MC_envelope":[lo,hi]})
                else:
                    replay_ci = np.percentile(raw,[2.5,97.5],method="linear")
                    record("replay_percentile",index,np.allclose(replay_ci,group["replay_ci95"],
                                                               rtol=0,atol=1e-11))
                del saved,raw
            save()
            print(f"P080 audit group {index+1}/36 complete",flush=True)
        # Verify every reported comparison directly from independently reconstructed data.
        for check in result["checks"]:
            kind,key = check["kind"],check.get("key")
            if kind.startswith("figure_regression_"):
                actual = fits["standardized_"+key[0]]
                value = actual["coef"][1] if kind.endswith("_mean") else actual["ci95"][1][
                        0 if kind.endswith("_ci95_low") else 1]
            elif kind == "paper_text":
                if key=="QuizScore difference NoAI-AI (points)":value=fits["primary_QuizScore"]["coef"][1]
                elif key=="QuizScore Cohen d":value=result["Cohen_d"]["QuizScore"]
                elif key=="QuizScore unadjusted p":value=fits["primary_QuizScore"]["p"][1]
                elif key=="Warmup-adjusted Cohen d":value=d
                else:value=adjusted["p"][1]
            elif kind=="main_time_p":value=fits["primary_TaskTime"]["p"][1]
            elif kind=="original_saved_source_p":value=fits[key]["p"][1]
            elif kind=="original_saved_adjusted_fit":
                value = {"Treatment":adjusted["coef"][1],
                         "Treatment_ci95_low":adjusted["ci95"][1][0],
                         "Treatment_ci95_high":adjusted["ci95"][1][1],
                         "WarmupTaskTime":adjusted["coef"][2],"Warmup_p":adjusted["p"][2]}[key]
            else:
                continue
            record("independent_comparison_value",kind+"|"+str(key),
                   abs(value-check["actual"])<1e-10)
            passed = abs(value-check["target"])<=check["tolerance"]
            record("comparison_pass_flag",kind+"|"+str(key),passed==check["passed"])
            record("original_deterministic_target",kind+"|"+str(key),passed)
        item_sums = [sum(r["items"].values()) for r in rows]
        discrepancy = [abs(v-r["QuizScore"]) for v,r in zip(item_sums,rows)]
        support = result["supporting_only"]
        record("item_total_consistency_count",None,
               sum(v>1e-10 for v in discrepancy)==support["stored_total_mismatch_count"])
        record("item_total_max_discrepancy",None,
               abs(max(discrepancy)-support["stored_total_max_abs_discrepancy"])<1e-11)
        for area in AREA_ITEMS:
            fractional = support["fractional_subareas"][area]
            fit = normal_fit(rows,area+"_fractional")
            record("fractional_diagnostic_fit",area,np.allclose(
                       fit["coef"],fractional["regression"]["coef"],rtol=0,atol=1e-10))
            for condition in ["AI","No AI"]:
                v = [r[area+"_fractional"] for r in rows if r["condition"]==condition]
                record("fractional_diagnostic_mean",area+"|"+condition,
                       abs(sum(v)/len(v)-fractional["by_condition"][condition])<1e-11)
        for i in ITEMS:
            vals = [r["items"][i] for r in rows]
            got = support["item_audit"][f"Q{i}"]
            record("full_item_audit",f"Q{i}",got == {
                "N":len(vals),"min":min(vals),"max":max(vals),"maximum_rubric":item_max(i),
                "fractional_count":sum(v!=math.trunc(v) for v in vals)})
        primary_p = [fits["primary_"+m]["p"][1] for m in ["TaskTime","QuizScore"]]
        exploratory_p = [fits[k]["p"][1] for k in support["BH_exploratory_keys"]]
        record("BH_primary_diagnostic",None,np.allclose(
            stats.false_discovery_control(primary_p),support["BH_primary"],rtol=0,atol=1e-11))
        record("BH_exploratory_diagnostic",None,np.allclose(
            stats.false_discovery_control(exploratory_p),support["BH_exploratory"],rtol=0,atol=1e-11))
        record("source_run_all_pass_flag",None,
               result["all_checks_pass"]==all(x["passed"] for x in result["checks"]))
        audit["all_checks_pass"] = all(x["passed"] for x in audit["checks"])
        audit["original_run_all_checks_pass"] = result["all_checks_pass"]
        audit["status"] = "completed"
        guard.check()
    except Exception as exc:
        audit["status"] = "stopped"
        audit["error"] = {"type":type(exc).__name__,"message":str(exc)}
        save()
        raise
    save()
    print(json.dumps({"paper_id":"P080","checks":len(audit["checks"]),
                      "all_checks_pass":audit["all_checks_pass"],"output":str(output)}))

if __name__ == "__main__":
    main()
