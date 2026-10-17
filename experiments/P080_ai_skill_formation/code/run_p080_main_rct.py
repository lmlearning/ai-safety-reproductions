"""P080 independent CPU analysis; participant statistics require a root-frozen plan."""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
from p080_resource_guard import ResourceGuard
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/P080_ai_skill_formation"
DATA = PAPER / "sources/retained_original_data/data_analysis__data__Full-Study.csv"
PLAN = PAPER / "PREREGISTRATION_PROPOSAL_20261010.json"
TARGET = PAPER / "ORIGINAL_PUBLISHED_FIGURE_TARGETS_20261010.json"
PLAN_SHA = "b622eeba4aed6aa70959062c4c4ebcb250bc5243f7c3c81c24d799132b695d98"
DATA_SHA = "7c76a8d4279a3fa4f0df24b0b4587c1b8c194561f26057545edac7919237518f"
TARGET_SHA = "ef783454547a2ba7f368f039f16dfa224a8a1e52c16caeb3b42e5e30ef598347"
AREAS = {
    "Task1": ["Q1","Q4","Q5","Q8","Q9","Q11","Q12","Q14","Q15"],
    "Task2": ["Q2","Q3","Q6","Q10","Q13"],
    "Conceptual": ["Q1","Q2","Q3","Q14","Q15"],
    "Debugging": ["Q8","Q10","Q11","Q12"],
    "CodeReading": ["Q3","Q4","Q5","Q6","Q9","Q13"],
}
WEIGHTS = {f"Q{i}": (1 if i in (1,2) else 3 if i == 15 else 2)
           for i in range(1,16) if i != 7}
EFFORT = {"Very little effort":1,"Little effort":2,"Moderate effort":3,
          "High effort":4,"Very high effort":5}
TOL = 1e-4
LEVELS = [[.008844709981637416,.04989239700060292],
          [.9501076029993965,.9911552900183623]]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execution_guard(prereg, expected):
    prereg = Path(prereg).resolve()
    if prereg != (PAPER / "PREREGISTRATION.md").resolve():
        raise ValueError("Only root-owned P080 PREREGISTRATION.md may authorize statistics")
    if len(expected) != 64 or sha(prereg) != expected:
        raise ValueError("Frozen preregistration SHA256 mismatch")
    if PLAN_SHA not in prereg.read_text(encoding="utf8"):
        raise ValueError("Frozen preregistration must explicitly retain this proposal SHA256")
    for path, wanted in [(PLAN,PLAN_SHA),(DATA,DATA_SHA),(TARGET,TARGET_SHA)]:
        if sha(path) != wanted:
            raise ValueError(f"Immutable source mismatch: {path.name}")
    manifest = PAPER / "FROZEN_INPUT_MANIFEST_20261010.json"
    manifest_sha = sha(manifest)
    if manifest_sha not in Path(prereg).read_text(encoding="utf8"):
        raise ValueError("Frozen input manifest hash absent from preregistration")
    entries = json.loads(manifest.read_text(encoding="utf8"))["files"]
    for entry in entries:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or sha(path) != entry["sha256"]:
            raise ValueError("Frozen input/code manifest mismatch")
    return expected

def ols(y, treatment, covariate=None):
    """Conventional OLS with explicit listwise omission and Student-t inference."""
    y = np.asarray(y, dtype=float)
    columns = [np.ones(len(y)), np.asarray(treatment,dtype=float)]
    if covariate is not None:
        columns.append(np.asarray(covariate,dtype=float))
    x = np.column_stack(columns)
    keep = np.isfinite(y) & np.all(np.isfinite(x),axis=1)
    y,x = y[keep],x[keep]
    rank = np.linalg.matrix_rank(x)
    if rank != x.shape[1] or len(y) <= rank:
        raise ValueError("Original design is not identifiable")
    pinv = np.linalg.pinv(x)
    coef = pinv @ y
    resid = y - x @ coef
    df = len(y) - rank
    mse = float(resid @ resid / df)
    se = np.sqrt(np.diag(pinv @ pinv.T) * mse)
    p = 2 * stats.t.sf(np.abs(coef / se),df)
    tcrit = stats.t.ppf(.975,df)
    return {"N":len(y),"df":int(df),"coef":coef.tolist(),"se":se.tolist(),
            "p":p.tolist(),"ci95":np.column_stack([coef-tcrit*se,coef+tcrit*se]).tolist(),
            "residual_mse":mse}

def bh(values):
    values = np.asarray(values,dtype=float)
    order = np.argsort(values)
    adjusted = np.minimum.accumulate((values[order] * len(values) /
                    np.arange(1,len(values)+1))[::-1])[::-1]
    out = np.empty_like(values);out[order] = np.minimum(adjusted,1)
    return out.tolist()

def bootstrap_means(values, draws, group_index, stream, guard=None):
    """Batched PCG64 integer resampling, same per-draw mean estimator as Seaborn."""
    values = np.asarray(values,dtype=float)
    if not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("No silent omission of invalid group values")
    rng = np.random.default_rng(np.random.SeedSequence([1729,group_index,stream]))
    result = np.empty(draws,dtype=float)
    for start in range(0,draws,10000):
        if guard is not None:
            guard.check()
        end = min(start+10000,draws)
        idx = rng.integers(0,len(values),size=(end-start,len(values)),dtype=np.intp)
        result[start:end] = np.mean(values[idx],axis=1)
    return result

def load_cohort():
    frame = pd.read_csv(DATA)
    frame.columns = frame.columns.map(lambda x: "".join(x.split(" ")))
    frame = frame.loc[frame.STATUS.isin(["COMPLETED","TIME-1N","TIME-2N","TIME-3N"])].copy()
    if len(frame) != 52 or frame.Condition.value_counts().to_dict() != {"AI":26,"No AI":26}:
        raise ValueError("Original cohort/assignment changed")
    frame["Treatment"] = frame.Condition.map({"AI":0,"No AI":1})
    frame["QuizScorePercent"] = 100 * frame.QuizScore / 27
    frame["CodingExpertiseAll"] = frame["Howmanyyearsofcodingexperiencedoyouhave?"]
    frame["Learning"] = frame["Howmuchdoyoufeellikeyoulearnedfromthistask?"]
    frame["Enjoyment"] = frame["Howmuchdidyouenjoythislearningtask?"]
    for name, question in [("Warm Up","WarmupTask"),("Trio Task","TrioTask"),
                           ("Post Task Quiz","PostTaskQuiz")]:
        frame[name] = frame[f"Howmucheffortdidyouusetocompleteeachofthetasksinthisstudy?[{question}]"].map(EFFORT)
    for area, items in AREAS.items():
        maximum = sum(WEIGHTS[i] for i in items)
        # Preserve original integer truncation and overlapping Q3 assignment.
        frame[area] = 100 * frame[items].astype(int).sum(axis=1) / maximum
        frame[area+"_fractional"] = 100 * frame[items].sum(axis=1) / maximum
    required = ["TaskTime","QuizScore","QuizScorePercent","Treatment","Learning","Enjoyment",
                "Warm Up","Trio Task","Post Task Quiz"] + list(AREAS)
    if not np.all(np.isfinite(frame[required].to_numpy(dtype=float))):
        raise ValueError("Missing/invalid original analysis values")
    if set(frame.CodingExpertiseAll) != {"1-3 years","4-6 years","7+ years"}:
        raise ValueError("Unexpected original expertise category")
    if frame.WarmupTaskTime.isna().sum() != 2:
        raise ValueError("Original adjusted-model missingness changed")
    return frame

def figure_values(frame, target):
    metric,category,condition = (target[k] for k in ("metric","category","condition"))
    rows = frame[frame.Condition == condition]
    if metric.startswith("experience_"):
        rows = rows[rows.CodingExpertiseAll == category]
        return rows[metric[len("experience_"):]].to_numpy(dtype=float)
    if metric.startswith("main_"):
        return rows[metric[len("main_"):]].to_numpy(dtype=float)
    if metric in ("subarea_percent","self_report","difficulty"):
        return rows[category].to_numpy(dtype=float)
    raise ValueError("Unrecognized original figure target")

def analyze(frame, targets, progress=True, guard=None, draw_dir=None, state=None, checkpoint=None):
    regression = {}
    for metric in ["TaskTime","QuizScore"]:
        regression["primary_"+metric] = ols(frame[metric],frame.Treatment)
        regression["standardized_"+metric] = ols(
            frame[metric]/frame[metric].std(ddof=1),frame.Treatment)
    regression["adjusted_QuizScorePercent"] = ols(
        frame.QuizScorePercent,frame.Treatment,frame.WarmupTaskTime)
    if regression["adjusted_QuizScorePercent"]["N"] != 50:
        raise ValueError("Original listwise adjusted cohort changed")
    d = {}
    for metric in ["TaskTime","QuizScore"]:
        a,b = (frame.loc[frame.Condition == c,metric].to_numpy(dtype=float)
               for c in ["AI","No AI"])
        pooled = math.sqrt(((len(a)-1)*np.var(a,ddof=1)+(len(b)-1)*np.var(b,ddof=1))
                           /(len(a)+len(b)-2))
        d[metric] = float((b.mean()-a.mean()) / pooled)
    adjusted = regression["adjusted_QuizScorePercent"]
    d["adjusted_QuizScorePercent"] = adjusted["coef"][1]/math.sqrt(adjusted["residual_mse"])
    if state is not None:
        state.update({'regressions':regression,'Cohen_d':d,'trial_outcome_calculations_performed':True})
    exploratory = []
    for years in ["1-3 years","4-6 years","7+ years"]:
        subset = frame[frame.CodingExpertiseAll == years]
        for metric in ["TaskTime","QuizScore"]:
            key = "experience_"+metric+"|"+years
            regression[key] = ols(subset[metric],subset.Treatment)
            exploratory.append(key)
    for metric in list(AREAS)+["Learning","Enjoyment","Warm Up","Trio Task","Post Task Quiz"]:
        regression[metric] = ols(frame[metric],frame.Treatment)
        exploratory.append(metric)
    checks,groups = [],[]
    if state is not None:
        state.update({'checks':checks,'groups':groups})
        if checkpoint:
            checkpoint()
    if draw_dir is not None:
        draw_dir.mkdir(parents=True,exist_ok=False)
    boot_targets = sorted((t for t in targets if t["metric"] != "main_effect_total_SD"),
                          key=lambda t: (t["metric"],t["category"],t["condition"]))
    if len(boot_targets) != 36:
        raise ValueError("Entire original bootstrap family must contain36groups")
    for index,target in enumerate(boot_targets):
        values = figure_values(frame,target)
        replay = bootstrap_means(values,1000,index,0,guard)
        ref = bootstrap_means(values,1000000,index,1,guard)
        envelopes = [np.quantile(ref,q,method="inverted_cdf").tolist() for q in LEVELS]
        group = {"key":[target[k] for k in ("metric","category","condition")],
                 "group_index":index,"N":len(values),"mean":float(values.mean()),
                 "replay_ci95":np.quantile(replay,[.025,.975],method="linear").tolist(),
                 "MC_envelopes":envelopes,
                 "reference_percentile_ci95":np.quantile(ref,[.025,.975],method="linear").tolist()}
        if draw_dir is not None:
            paths = {}
            for label,draws in [("replay",replay),("reference",ref)]:
                path = draw_dir / f"group_{index:02d}_{label}.npy"
                np.save(path,draws,allow_pickle=False)
                paths[label] = {"path":path.relative_to(ROOT).as_posix(),
                                "sha256":sha(path),"draw_count":len(draws)}
            group["saved_draw_vectors"] = paths
        groups.append(group)
        checks.append({"kind":"figure_mean","key":group["key"],"actual":group["mean"],
                       "target":target["mean"],"tolerance":TOL,
                       "passed":abs(group["mean"]-target["mean"])<=TOL})
        for j,field in enumerate(["ci95_low","ci95_high"]):
            lo,hi = envelopes[j];wanted = target[field]
            checks.append({"kind":"figure_bootstrap_endpoint","key":group["key"]+[field],
                           "target":wanted,"fixed_MC_envelope":[lo,hi],"tolerance":TOL,
                           "passed":lo-TOL<=wanted<=hi+TOL})
        if guard is not None:
            guard.check()
        if checkpoint:
            checkpoint()
        if progress:
            print(f"P080 group {index+1}/36 complete",flush=True)
        del replay,ref
    for target in targets:
        if target["metric"] != "main_effect_total_SD":
            continue
        fit = regression["standardized_"+target["category"]]
        for field,actual in [("mean",fit["coef"][1]),("ci95_low",fit["ci95"][1][0]),
                             ("ci95_high",fit["ci95"][1][1])]:
            checks.append({"kind":"figure_regression_"+field,"key":[target["category"]],
                           "actual":actual,"target":target[field],"tolerance":TOL,
                           "passed":abs(actual-target[field])<=TOL})
    plan = json.loads(PLAN.read_text(encoding="utf8"))
    text_values = {
        "QuizScore difference NoAI-AI (points)":regression["primary_QuizScore"]["coef"][1],
        "QuizScore Cohen d":d["QuizScore"],
        "QuizScore unadjusted p":regression["primary_QuizScore"]["p"][1],
        "Warmup-adjusted Cohen d":d["adjusted_QuizScorePercent"],
        "Warmup-adjusted Treatment p":adjusted["p"][1],
    }
    for target in plan["targets"]["published_text"]:
        actual = text_values[target["statistic"]]
        checks.append({"kind":"paper_text","key":target["statistic"],"actual":actual,
                       "target":target["value"],"tolerance":target["rounding_tolerance"],
                       "passed":abs(actual-target["value"])<=target["rounding_tolerance"]})
    ptarget = plan["targets"]["main_time_p"]
    actual = regression["primary_TaskTime"]["p"][1]
    checks.append({"kind":"main_time_p","actual":actual,"target":ptarget["value"],
                   "tolerance":ptarget["rounding_tolerance"],
                   "passed":abs(actual-ptarget["value"])<=ptarget["rounding_tolerance"]})
    source_p = plan["targets"]["source_followup_p"]
    source_rows = []
    for label,metric in [("experience_TaskTime","TaskTime"),("experience_QuizScore","QuizScore")]:
        source_rows.extend(("experience_"+metric+"|"+years,value)
                           for years,value in source_p[label].items())
    for label in ["subarea","self_report","difficulty"]:
        source_rows.extend(source_p[label].items())
    for key,wanted in source_rows:
        actual = regression[key]["p"][1]
        checks.append({"kind":"original_saved_source_p","key":key,"actual":actual,
                       "target":wanted,"tolerance":.0005,"passed":abs(actual-wanted)<=.0005})
    adjusted_target = plan["targets"]["original_saved_adjusted_fit"]
    for key,actual,wanted,tol in [
        ("Treatment",adjusted["coef"][1],adjusted_target["Treatment"],.00005),
        ("Treatment_ci95_low",adjusted["ci95"][1][0],adjusted_target["Treatment_ci95"][0],.0005),
        ("Treatment_ci95_high",adjusted["ci95"][1][1],adjusted_target["Treatment_ci95"][1],.0005),
        ("WarmupTaskTime",adjusted["coef"][2],adjusted_target["WarmupTaskTime"],.00005),
        ("Warmup_p",adjusted["p"][2],adjusted_target["Warmup_p"],.0005)]:
        checks.append({"kind":"original_saved_adjusted_fit","key":key,"actual":actual,
                       "target":wanted,"tolerance":tol,"passed":abs(actual-wanted)<=tol})
    item_sum = frame[list(WEIGHTS)].sum(axis=1)
    mismatch = np.abs(item_sum-frame.QuizScore)>1e-10
    item_audit = {item:{"N":len(frame),"min":float(frame[item].min()),
                       "max":float(frame[item].max()),
                       "maximum_rubric":WEIGHTS[item],
                       "fractional_count":int((frame[item] != np.trunc(frame[item])).sum())}
                  for item in WEIGHTS}
    fractional = {area:{"by_condition":{c:float(frame.loc[frame.Condition==c,
                         area+"_fractional"].mean()) for c in ["AI","No AI"]},
                         "regression":ols(frame[area+"_fractional"],frame.Treatment)}
                  for area in AREAS}
    return {"paper_id":"P080","scope":"complete_primary_quantitative_main_RCT",
            "N":52,"adjusted_N":50,"regressions":regression,"Cohen_d":d,
            "groups":groups,"checks":checks,"all_checks_pass":all(x["passed"] for x in checks),
            "supporting_only":{"fractional_subareas":fractional,"item_audit":item_audit,
               "stored_total_mismatch_count":int(mismatch.sum()),
               "stored_total_max_abs_discrepancy":float(np.abs(item_sum-frame.QuizScore).max()),
               "BH_primary":bh([regression["primary_"+s]["p"][1] for s in ["TaskTime","QuizScore"]]),
               "BH_exploratory_keys":exploratory,
               "BH_exploratory":bh([regression[k]["p"][1] for k in exploratory]),
               "prose17percent_conflict_preserved":True}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prereg",type=Path,required=True)
    parser.add_argument("--prereg-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    frozen = execution_guard(args.prereg,args.prereg_sha256)
    output = args.output.resolve()
    if not output.is_relative_to(PAPER.resolve()):
        raise ValueError("Output must stay within P080 workspace")
    if output.exists():
        raise ValueError("Refuse overwriting an existing trial outcome record")
    guard = ResourceGuard(ROOT)
    result = {"paper_id":"P080","status":"running","trial_outcome_calculations_performed":False,
              "provenance":{"prereg_sha256":frozen,"proposal_sha256":sha(PLAN),
                            "data_sha256":sha(DATA),"targets_sha256":sha(TARGET),
                            "runner_sha256":sha(__file__),
                            "resource_guard_sha256":sha(Path(__file__).with_name("p080_resource_guard.py")),
                            "input_manifest_sha256":sha(PAPER/"FROZEN_INPUT_MANIFEST_20261010.json"),
                            "python":sys.version,"numpy":np.__version__,
                            "pandas":pd.__version__,"scipy":__import__("scipy").__version__},
              "operational":{"base_seed":1729,"bootstrap_replay":1000,
              "bootstrap_reference":1000000,"family_endpoint_denominator":76,
              "probability_levels":LEVELS}}
    output.parent.mkdir(parents=True,exist_ok=True)
    def checkpoint():
        result["resource"] = guard.summary()
        output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf8")
    checkpoint()
    try:
        guard.check()
        targets = json.loads(TARGET.read_text(encoding="utf8"))["targets"]
        result.update(analyze(load_cohort(),targets,guard=guard,
                     draw_dir=output.with_name(output.stem+"_draws"),
                     state=result,checkpoint=checkpoint))
        result["status"] = "completed"
        result["trial_outcome_calculations_performed"] = True
        guard.check()
    except Exception as exc:
        result["status"] = "stopped"
        result["error"] = {"type":type(exc).__name__,"message":str(exc)}
        checkpoint()
        raise
    checkpoint()
    print(json.dumps({"paper_id":"P080","all_checks_pass":result["all_checks_pass"],
                      "checks":len(result["checks"]),"output":str(output)}))
if __name__ == "__main__":
    main()
