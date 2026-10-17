"""P065 original Figure 2 synthesis; immutable deterministic CPU-only run."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import csv, datetime as dt, hashlib, importlib.metadata, json, math, pathlib, platform
import shutil, sys, time, traceback
import numpy as np
from scipy import stats
import psutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPER = ROOT / "papers/P065_empathy_meta_analysis"
RUN = PAPER / "runs/P065-central-001"
RUN.mkdir(parents=True, exist_ok=False)
START = dt.datetime.now(dt.timezone.utc).isoformat()
WALL = time.perf_counter()
CPU = time.process_time()
PROC = psutil.Process()

def dump(name, obj):
    (RUN / name).write_text(json.dumps(obj, indent=2, allow_nan=False), encoding="utf8")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fit(records):
    effects = np.array([float(r["smd"]) for r in records])
    variances = np.array([float(r["se"]) ** 2 for r in records])
    fixed = 1 / variances
    fixed_mean = np.sum(fixed * effects) / np.sum(fixed)
    Q = np.sum(fixed * (effects - fixed_mean) ** 2)
    df = len(records) - 1
    C = np.sum(fixed) - np.sum(fixed ** 2) / np.sum(fixed)
    tau = max(float((Q - df) / C), 0.0)
    weights = 1 / (variances + tau)
    mu = np.sum(weights * effects) / np.sum(weights)
    se = math.sqrt(1 / np.sum(weights))
    z = mu / se
    critical = stats.norm.ppf(0.975)
    result = {"k": len(records), "df": df, "mu": float(mu), "se": se,
              "ci_low": float(mu - critical * se), "ci_high": float(mu + critical * se),
              "Q": float(Q), "tau2": tau, "C": float(C), "fixed_mean": float(fixed_mean),
              "I2": max(float((Q-df)/Q), 0.0)*100, "Z": float(z),
              "p": float(2*stats.norm.sf(abs(z))), "heterogeneity_p": float(stats.chi2.sf(Q, df))}
    terms = []
    for i, record in enumerate(records):
        terms.append({**record, "variance": float(variances[i]), "fixed_weight": float(fixed[i]),
                      "Q_contribution": float(fixed[i]*(effects[i]-fixed_mean)**2),
                      "random_weight": float(weights[i]), "normalized_weight_percent": float(weights[i]/np.sum(weights)*100),
                      "individual_ci_low": float(effects[i]-critical*math.sqrt(variances[i])),
                      "individual_ci_high": float(effects[i]+critical*math.sqrt(variances[i]))})
    return result, terms

exit_code = 0
try:
    frozen = RUN / "frozen"
    frozen.mkdir()
    for path in [PAPER/"PREREGISTRATION.md", PAPER/"original_data.csv", PAPER/"targets.json",
                 pathlib.Path(__file__), ROOT/"scripts/audit_empathy_meta_analysis.py"]:
        shutil.copy2(path, frozen/path.name)
    sources = {}
    for path in sorted((PAPER/"sources").rglob("*")):
        if path.is_file():
            sources[str(path.relative_to(ROOT))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    dump("source_manifest.json", sources)
    dump("environment.json", {"python": sys.version, "executable": sys.executable,
         "platform": platform.platform(), "packages": {p: importlib.metadata.version(p) for p in ["numpy","scipy","psutil"]},
         "cpu_count_logical": os.cpu_count(), "cpu_only": True, "no_model_inference": True,
         "thread_limits": {k:os.environ[k] for k in ["OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"]},
         "seeds": None, "stochastic_operations": False})
    dump("configuration.json", {"run_id": RUN.name, "paper_id":"P065", "start_utc": START,
         "command": [sys.executable, str(pathlib.Path(__file__).resolve())], "algorithm":"RevMan 5 generic IV DerSimonian-Laird",
         "input_sha256": sha(frozen/"original_data.csv"), "preregistration_sha256":sha(frozen/"PREREGISTRATION.md"),
         "targets_sha256":sha(frozen/"targets.json"), "paid_service_cost":0})
    with (frozen/"original_data.csv").open(encoding="utf8", newline="") as f:
        rows = list(csv.DictReader(f))
    targets = json.loads((frozen/"targets.json").read_text(encoding="utf8"))
    assert len(rows) == 13 and len({r["study"] for r in rows}) == 13
    fitted, intermediate = {}, {}
    fitted["overall"], intermediate["overall"] = fit(rows)
    for group in ["GPT-3.5","GPT-4"]:
        selected = [r for r in rows if r["model"] == group]
        fitted[group], intermediate[group] = fit(selected)
    fitted["overall"]["weight_percent"] = 100.0
    for group in ["GPT-3.5", "GPT-4"]:
        fitted[group]["weight_percent"] = sum(r["normalized_weight_percent"] for r in intermediate["overall"] if r["model"] == group)
    groups = [fitted["GPT-3.5"], fitted["GPT-4"]]
    group_weights = np.array([1/g["se"]**2 for g in groups])
    group_effects = np.array([g["mu"] for g in groups])
    group_mean = np.sum(group_weights*group_effects)/np.sum(group_weights)
    group_Q = float(np.sum(group_weights*(group_effects-group_mean)**2))
    difference = {"Q":group_Q, "df":1, "p":float(stats.chi2.sf(group_Q,1)),
                  "I2":max((group_Q-1)/group_Q,0)*100, "comparison_mean":float(group_mean),
                  "subgroup_inverse_variance_weights":group_weights.tolist()}
    probability = float(stats.norm.cdf(fitted["overall"]["mu"]/math.sqrt(2)))
    claims = {"overall_positive_significant":fitted["overall"]["ci_low"]>0,
              "gpt4_positive_significant":fitted["GPT-4"]["ci_low"]>0,
              "gpt35_not_significant":fitted["GPT-3.5"]["p"]>=0.05,
              "subgroup_difference_not_significant":difference["p"]>=0.05}
    checks=[]
    def check(label, value, target, tolerance):
        checks.append({"label":label,"computed":value,"published":target,"absolute_difference":abs(value-target),
                       "absolute_tolerance":tolerance,"pass":abs(value-target)<=tolerance+1e-12})
    for group, reference in targets["fits"].items():
        for field, target in reference.items():
            if field.endswith("_less_than"):
                actual=fitted[group][field.removesuffix("_less_than")]
                checks.append({"label":f"{group}.{field}","computed":actual,"published_upper_bound":target,"pass":actual<target})
            else:
                check(f"{group}.{field}", fitted[group][field], target, targets["tolerances"].get(field,0))
    for field,target in targets["subgroup_difference"].items():
        tol=targets["tolerances"].get("subgroup_I2" if field=="I2" else field,0)
        check(f"subgroup_difference.{field}",difference[field],target,tol)
    for record in intermediate["overall"]:
        for actual,reference,tolname in [("smd","printed_smd","mu"),("individual_ci_low","printed_ci_low","ci_low"),
                                        ("individual_ci_high","printed_ci_high","ci_high"),
                                        ("normalized_weight_percent","printed_weight_percent","weight_percent")]:
            check(f"{record['study']}.{actual}",float(record[actual]),float(record[reference]),targets["tolerances"][tolname])
    for label,expected in targets["qualitative_claims"].items():
        checks.append({"label":label,"computed":claims[label],"published":expected,"pass":claims[label]==expected})
    check("probability_superiority",probability,targets["probability_superiority"],targets["tolerances"]["probability_superiority"])
    results={"fits":fitted,"subgroup_difference":difference,"probability_superiority":probability,
             "qualitative_claims":claims,"comparison_checks":checks,"all_checks_pass":all(c["pass"] for c in checks),
             "check_count":len(checks),"failed_checks":[c for c in checks if not c["pass"]]}
    dump("results.json",results)
    dump("raw_per_study.json",intermediate)
    print(json.dumps({"run_id":RUN.name,"checks":len(checks),"all_checks_pass":results["all_checks_pass"],
                      "fits":fitted,"subgroup_difference":difference,"failed_checks":results["failed_checks"]},indent=2))
except Exception:
    exit_code=1
    error=traceback.format_exc()
    (RUN/"failure.txt").write_text(error,encoding="utf8")
    print(error,file=sys.stderr)
finally:
    memory=PROC.memory_info()._asdict()
    dump("execution.json", {"start_utc":START,"end_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "exit_code":exit_code,"wall_seconds":time.perf_counter()-WALL,"cpu_seconds":time.process_time()-CPU,
         "memory_bytes":memory,"rss_measurement":"final RSS and Windows peak working set when available; no GPU allocation",
         "paid_service_cost":0,"electricity_cost":"unmeasured"})
    manifest={str(path.relative_to(RUN)):{"sha256":sha(path),"bytes":path.stat().st_size}
              for path in sorted(RUN.rglob("*")) if path.is_file()}
    dump("run_manifest.json",manifest)
sys.exit(exit_code)
