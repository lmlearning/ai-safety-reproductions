"""P135 source-only prepared matrix REML implementation. Do not import into the independent audit."""
import os
for _thread_key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread_key] = "1"
import argparse
import csv
import datetime
import hashlib
import json
import math
import shutil
import time
from pathlib import Path
import psutil
import numpy as np
from scipy import linalg, optimize, special, stats

START = time.monotonic()
TRACE = []
GUARD = None
FAMILIES = ("psychological_distress", "psychological_wellbeing")
METHOD = "canonical LS; full-matrix two-component REML; residual Student t"

class ResourceStop(RuntimeError):
    pass

class Guard:
    def __init__(self, output_root, policy):
        self.output_root = Path(output_root)
        self.policy = policy
        self.process = psutil.Process()
        self.process.cpu_affinity([int(policy.get("cpu_index", 2))])
        self.calls = 0
        self.samples = []
        self.check(force=True)

    def check(self, force=False):
        self.calls += 1
        if not force and self.calls % 32:
            return
        processes = [self.process] + self.process.children(recursive=True)
        rss = sum(p.memory_info().rss for p in processes if p.is_running())
        available = psutil.virtual_memory().available
        free = shutil.disk_usage(self.output_root).free
        elapsed = time.monotonic() - START
        self.samples.append({"elapsed_seconds": elapsed, "owned_RSS_bytes": rss, "available_RAM_bytes": available, "free_disk_bytes": free})
        if rss > self.policy["process_tree_RSS_cap_bytes"] or available < self.policy["available_RAM_floor_bytes"] or free < self.policy["free_disk_floor_bytes"] or elapsed > self.policy["maximum_elapsed_seconds"]:
            raise ResourceStop("Continuous frozen resource guard breached")

def jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(type(x).__name__)

def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=True, default=jsonable, allow_nan=False) + "\n", encoding="utf8")

def reference(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"absolute_path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def classify(g, low, high):
    direction = "negative" if g < 0 else "positive" if g > 0 else "ambiguous_source_zero"
    if low is None or high is None:
        interval = "unavailable"
    elif high < 0:
        interval = "negative_significant"
    elif low > 0:
        interval = "positive_significant"
    elif low < 0 < high:
        interval = "crosses_zero"
    else:
        interval = "ambiguous_source_zero"
    return direction, interval

def sampling_variance(rows, y, method="LS"):
    n1 = np.array([int(r["intervention_n"]) for r in rows], dtype=float)
    n2 = np.array([int(r["control_n"]) for r in rows], dtype=float)
    total = n1 + n2
    if np.any(n1 <= 1) or np.any(n2 <= 1):
        raise ValueError("Source arm sizes must exceed one")
    base = 1.0 / n1 + 1.0 / n2
    if method == "LS":
        return base + y * y / (2.0 * total)
    df = total - 2.0
    J = np.exp(special.gammaln(df / 2.0) - special.gammaln((df - 1.0) / 2.0)) * np.sqrt(2.0 / df)
    if method == "LS2":
        return J * J * base + y * y / (2.0 * total)
    if method == "UB":
        return base + (1.0 - (df - 2.0) / (df * J * J)) * y * y
    if method == "CI_derived":
        lo = np.array([float(r["printed_CI_low"]) for r in rows])
        hi = np.array([float(r["printed_CI_high"]) for r in rows])
        return ((hi - lo) / (2.0 * 1.96)) ** 2
    raise ValueError("Unregistered sampling variance")

def fit_matrix(y, v, clusters, fit_id, X=None, ordinary_two_level=False):
    """Use the complete covariance matrix; independent auditor uses cluster-block algebra."""
    GUARD.check(force=True)
    y = np.asarray(y, dtype=float)
    v = np.asarray(v, dtype=float)
    k = len(y)
    X = np.ones((k, 1)) if X is None else np.asarray(X, dtype=float)
    p = X.shape[1]
    if k <= p or np.linalg.matrix_rank(X) != p or np.any(v <= 0):
        raise ValueError("Unidentifiable or saturated source design")
    C = np.equal.outer(clusters, clusters).astype(float)
    singleton_only = bool(np.array_equal(C, np.eye(k)))
    component_identifiable = not singleton_only and not ordinary_two_level
    upper = max(1.0, 100.0 * float(np.var(y, ddof=0)))
    candidates = []
    evaluations = 0

    def evaluate(theta, gradient=True):
        nonlocal evaluations
        evaluations += 1
        GUARD.check()
        a, b = map(float, theta)
        M = np.diag(v + a) + b * C
        cf = linalg.cho_factor(M, lower=True, check_finite=True)
        inverse = linalg.cho_solve(cf, np.eye(k))
        inverse_X = inverse @ X
        precision = X.T @ inverse_X
        covariance = np.linalg.inv(precision)
        beta = covariance @ (inverse_X.T @ y)
        residual = y - X @ beta
        sign, logdet_precision = np.linalg.slogdet(precision)
        if sign <= 0:
            raise ValueError("Nonpositive GLS precision")
        value = 0.5 * (2.0 * float(np.log(np.diag(cf[0])).sum()) + logdet_precision + float(residual @ inverse @ residual))
        P = inverse - inverse_X @ covariance @ inverse_X.T
        score = P @ y
        grad = np.array([0.5 * (float(np.trace(P)) - float(score @ score)), 0.5 * (float(np.sum(P * C.T)) - float(score @ C @ score))])
        return value, grad, beta, covariance, inverse, P

    def record(label, theta, success=True, message=""):
        theta = np.maximum(0.0, np.minimum(upper, np.asarray(theta, dtype=float)))
        value, grad, *_ = evaluate(theta)
        projected = grad.copy()
        for i in range(2):
            if theta[i] <= 1e-9 and grad[i] >= 0:
                projected[i] = 0.0
            elif theta[i] >= upper - 1e-9 and grad[i] <= 0:
                projected[i] = 0.0
        if not component_identifiable:
            projected[1] = 0.0
        rec = {"label": label, "theta": theta.tolist(), "nll": value, "gradient": grad.tolist(), "projected_gradient_max": float(np.abs(projected).max()), "optimizer_success": bool(success), "message": str(message)}
        candidates.append(rec)
        return rec

    record("zero_corner", [0.0, 0.0])
    # Each registered physical zero-component boundary is searched independently.
    boundary_axes = [0, 1] if component_identifiable else [0]
    for axis in boundary_axes:
        def one(z):
            t = np.zeros(2); t[axis] = z
            return evaluate(t)[0]
        result = optimize.minimize_scalar(one, bounds=(0.0, upper), method="bounded", options={"xatol": 1e-12, "maxiter": 600})
        t = np.zeros(2); t[axis] = float(result.x)
        record("zero_boundary_%d" % axis, t, result.success, result.message)
        # Analytic boundary scores also bracket stationary points on a fixed grid.
        grid = [0.0] + [upper * 10.0 ** (-8.0 + i / 2.0) for i in range(17)]
        last_z = grid[0]
        t = np.zeros(2); t[axis] = last_z
        last_g = evaluate(t)[1][axis]
        for z in grid[1:]:
            t = np.zeros(2); t[axis] = z
            score = evaluate(t)[1][axis]
            if last_g * score < 0:
                def score_at(q):
                    qtheta = np.zeros(2); qtheta[axis] = q
                    return evaluate(qtheta)[1][axis]
                root = optimize.brentq(score_at, last_z, z, xtol=1e-13, rtol=1e-13, maxiter=200)
                t = np.zeros(2); t[axis] = root
                record("zero_boundary_score_%d" % axis, t)
            last_z, last_g = z, score
    if component_identifiable:
        scale = max(1e-4, float(np.mean(v)), float(np.var(y, ddof=0)))
        starts = [(0.0, 0.0), (0.25 * scale, 0.0), (0.0, 0.25 * scale), (0.25 * scale, 0.25 * scale), (scale, scale)]
        for index, start in enumerate(starts):
            def objective(t):
                e = evaluate(t)
                return e[0], e[1]
            result = optimize.minimize(objective, start, method="L-BFGS-B", jac=True, bounds=[(0.0, upper), (0.0, upper)], options={"ftol": 1e-14, "gtol": 1e-11, "maxiter": 600, "maxls": 60})
            record("L_BFGS_B_fixed_start_%d" % index, result.x, result.success, result.message)
        best_pre = min(candidates, key=lambda r: (r["nll"], r["theta"][0], r["theta"][1]))
        result = optimize.minimize(lambda t: evaluate(t)[0], best_pre["theta"], jac=lambda t: evaluate(t)[1], method="SLSQP", bounds=[(0.0, upper), (0.0, upper)], options={"ftol": 1e-14, "maxiter": 600})
        record("registered_SLSQP_polish", result.x, result.success, result.message)
    # Source-only registered precision polish protects finite-difference derivatives.
    minimum = min(r["nll"] for r in candidates)
    tied = [r for r in candidates if r["nll"] <= minimum + 1e-12]
    best = min(tied, key=lambda r: (r["projected_gradient_max"], r["nll"], r["theta"][0], r["theta"][1]))
    theta = np.array(best["theta"], dtype=float)
    for iteration in range(50):
        value, grad, _, _, _, P = evaluate(theta)
        projected = grad.copy()
        for axis in range(2):
            if theta[axis] <= 1e-9 and grad[axis] >= 0:
                projected[axis] = 0.0
        if not component_identifiable:
            projected[1] = 0.0
        norm = float(np.abs(projected).max())
        if norm <= 1e-10:
            break
        active = [i for i in range(2) if (theta[i] > 1e-9 or grad[i] < 0) and (component_identifiable or i == 0)]
        if not active:
            break
        score = P @ y
        derivatives = [np.eye(k), C]
        H = np.array([[0.5 * (-np.trace(P @ Di @ P @ Dj) + 2.0 * score @ Di @ P @ Dj @ score) for Dj in derivatives] for Di in derivatives])
        restricted = H[np.ix_(active, active)]
        if float(np.linalg.eigvalsh(restricted).min()) <= 1e-12:
            break
        step = np.zeros(2)
        step[active] = np.linalg.solve(restricted, -grad[active])
        accepted = False
        for search in range(40):
            proposed = np.clip(theta + 0.5 ** search * step, 0.0, upper)
            if not component_identifiable:
                proposed[1] = 0.0
            new_value, new_grad, *_ = evaluate(proposed)
            projected_new = new_grad.copy()
            for axis in range(2):
                if proposed[axis] <= 1e-9 and new_grad[axis] >= 0:
                    projected_new[axis] = 0.0
            if not component_identifiable:
                projected_new[1] = 0.0
            if new_value <= value + 1e-12 and float(np.abs(projected_new).max()) < norm:
                theta = proposed
                accepted = True
                break
        if not accepted:
            break
    record("registered_analytic_Newton_precision_polish", theta)
    minimum = min(r["nll"] for r in candidates)
    tied = [r for r in candidates if r["nll"] <= minimum + 1e-12]
    best = min(tied, key=lambda r: (r["projected_gradient_max"], r["nll"], r["theta"][0], r["theta"][1]))
    a, b = best["theta"]
    nll, gradient, beta, covariance, inverse, P = evaluate([a, b])
    converged = bool(np.isfinite(nll) and best["projected_gradient_max"] <= 1e-5 and a < upper - 1e-7 and b < upper - 1e-7)
    df = k - p
    critical = float(stats.t.ppf(0.975, df))
    estimate = float(beta[0])
    se = math.sqrt(float(covariance[0, 0]))
    t_value = estimate / se
    W = np.diag(1.0 / v)
    sampling_cov = np.linalg.inv(X.T @ W @ X)
    beta_sampling = sampling_cov @ X.T @ W @ y
    resid_sampling = y - X @ beta_sampling
    Q = float(resid_sampling @ W @ resid_sampling)
    sampling_P = W - W @ X @ sampling_cov @ X.T @ W
    typical = df / float(np.trace(sampling_P))
    total_tau = a + b
    weights = (inverse @ np.ones(k)) / float(np.ones(k) @ inverse @ np.ones(k)) * 100.0 if p == 1 else None
    result = {"k": k, "parameters": p, "trials": len(set(clusters)), "coefficients": beta.tolist(), "covariance": covariance.tolist(), "df": df, "g": estimate, "SE": se, "CI_low": estimate - critical * se, "CI_high": estimate + critical * se, "t": t_value, "p_value": float(2.0 * stats.t.sf(abs(t_value), df)), "a": a, "b": b, "total_tau2": total_tau, "nll": nll, "Q": Q, "Q_df": df, "Q_p": float(stats.chi2.sf(Q, df)), "I2_Q": max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0, "I2_components": 100.0 * total_tau / (total_tau + typical), "sampling_typical_variance": typical, "row_weights_percent": weights.tolist() if weights is not None else None, "converged": converged, "component_identifiable": component_identifiable, "identifiability": "two_components" if component_identifiable else "total_only_fixed_b_zero"}
    TRACE.append({"fit_id": fit_id, "y": y.tolist(), "v": v.tolist(), "clusters": list(clusters), "X": X.tolist(), "upper_bound": upper, "ordinary_two_level": bool(ordinary_two_level), "candidates": candidates, "selected_candidate": best, "selected_converged": converged, "evaluations": evaluations})
    GUARD.check(force=True)
    return result

def row_outputs(rows, y, v, pool):
    out = {}
    for index, row in enumerate(rows):
        se = math.sqrt(float(v[index]))
        out[row["row"]] = {"row": row["row"], "study_key": row["study_key"], "g": float(y[index]), "variance": float(v[index]), "SE": se, "CI_low": float(y[index] - 1.96 * se), "CI_high": float(y[index] + 1.96 * se), "row_weight_percent": pool["row_weights_percent"][index]}
    return out

def primes(n):
    result = []
    candidate = 2
    while len(result) < n:
        if all(candidate % p for p in result if p * p <= candidate):
            result.append(candidate)
        candidate += 1
    return result

def radical(index, base):
    value = 0.0
    power = 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * power
        power /= base
    return value

def rounding(rows, y, clusters, primary, family):
    keys = ("g", "CI_low", "CI_high")
    e, h = 0.005, 0.0001
    k = len(y)
    jac = {key: [] for key in keys}
    derivative_records = []
    for i in range(k):
        fitted = {}
        for label, sign in (("minus", -1.0), ("plus", 1.0)):
            delta = np.zeros(k); delta[i] = sign * h
            shifted = y + delta
            pool = fit_matrix(shifted, sampling_variance(rows, shifted), clusters, family + "/Jacobian/%02d/%s" % (i + 1, label))
            fitted[label] = pool
            derivative_records.append({"id": "Jacobian_%02d_%s" % (i + 1, label), "delta": delta.tolist(), "pool": pool})
        for key in keys:
            jac[key].append((fitted["plus"][key] - fitted["minus"][key]) / (2.0 * h))
    vectors = []
    bases = primes(k)
    for index in range(1, 65):
        point = np.array([radical(index, p) for p in bases])
        vectors.append(("halton_%03d" % index, "Halton", e * (2.0 * point - 1.0)))
        vectors.append(("complement_%03d" % index, "Halton_complement", e * (1.0 - 2.0 * point)))
    for i in range(k):
        for sign, name in ((-1.0, "minus"), (1.0, "plus")):
            delta = np.zeros(k); delta[i] = sign * e
            vectors.append(("coordinate_%02d_%s" % (i + 1, name), "coordinate_endpoint", delta))
    vectors.extend([("uniform_minus", "uniform_corner", np.full(k, -e)), ("uniform_plus", "uniform_corner", np.full(k, e))])
    for key in keys:
        signs = np.sign(np.array(jac[key]))
        for sign, name in ((-1.0, "minus"), (1.0, "plus")):
            vectors.append(("gradient_%s_%s" % (key, name), "gradient_sign_corner", sign * e * signs))
    nonlinear = {key: 0.0 for key in keys}
    probes = []
    for probe_id, kind, delta in vectors:
        shifted = y + delta
        pool = fit_matrix(shifted, sampling_variance(rows, shifted), clusters, family + "/rounding/" + probe_id)
        direction, interval = classify(pool["g"], pool["CI_low"], pool["CI_high"])
        probes.append({"id": probe_id, "kind": kind, "delta": delta.tolist(), "pool": pool, "point_direction": direction, "CI_classification": interval})
        for key in keys:
            residual = abs(pool[key] - primary[key] - float(np.dot(jac[key], delta)))
            nonlinear[key] = max(nonlinear[key], residual)
    radius = {key: e * sum(abs(j) for j in jac[key]) + nonlinear[key] for key in keys}
    allowance = {key: min(0.02, 0.005 + radius[key]) + 1e-9 for key in keys}
    return {"e": e, "h": h, "Halton_points": 64, "Jacobian": jac, "Jacobian_fit_records": derivative_records, "maximum_nonlinear_residual": nonlinear, "radius": radius, "allowance": allowance, "probe_records": probes, "finite_probe_allowance_not_rigorous_enclosure": True}

def egger(y, v):
    k = len(y)
    se = np.sqrt(v)
    design = np.column_stack([np.ones(k), 1.0 / se])
    standardized = y / se
    covariance_base = np.linalg.inv(design.T @ design)
    beta = covariance_base @ design.T @ standardized
    resid = standardized - design @ beta
    covariance = covariance_base * float(resid @ resid) / (k - 2)
    standard = math.sqrt(float(covariance[0, 0]))
    statistic = float(beta[0]) / standard
    return {"k": k, "intercept": float(beta[0]), "SE": standard, "t": statistic, "df": k - 2, "p_value": float(2.0 * stats.t.sf(abs(statistic), k - 2)), "method": "unweighted standardized Egger OLS; exact original producer unavailable"}

def subgroup(rows, y, v, clusters, metadata, family, factor):
    unavailable = [r for r in metadata["unavailable_families"] if r["family"] == family and r["factor"] == factor]
    categories = {r["study_key"]: metadata["studies"][r["study_key"]][factor] for r in rows}
    if unavailable:
        return {"status": "unavailable_original_split_arm_inputs", "reason": unavailable[0]["reason"], "categories": categories, "omnibus": None, "groups": {}, "full_moderator_pool": None}
    if any(c is None for c in categories.values()):
        raise ValueError("Unspecified source moderator category")
    present = [c for c in metadata["category_order"][factor] if c in categories.values()]
    X = np.column_stack([np.ones(len(rows))] + [np.array([categories[r["study_key"]] == c for r in rows], dtype=float) for c in present[1:]])
    pool = fit_matrix(y, v, clusters, family + "/moderator/" + factor, X=X)
    beta = np.array(pool["coefficients"])
    covariance = np.array(pool["covariance"])
    df = pool["df"]
    critical = float(stats.t.ppf(0.975, df))
    groups = {}
    for index, category in enumerate(present):
        contrast = np.zeros(len(present)); contrast[0] = 1.0
        if index:
            contrast[index] = 1.0
        estimate = float(contrast @ beta)
        se = math.sqrt(float(contrast @ covariance @ contrast))
        statistic = estimate / se
        matching = [r for r in rows if categories[r["study_key"]] == category]
        groups[category] = {"g": estimate, "SE": se, "CI_low": estimate - critical * se, "CI_high": estimate + critical * se, "t": statistic, "p_value": float(2.0 * stats.t.sf(abs(statistic), df)), "trials": len({r["study_key"] for r in matching}), "effects": len(matching)}
    if len(present) > 1:
        Wald = float(beta[1:] @ np.linalg.inv(covariance[1:, 1:]) @ beta[1:])
        F = Wald / (len(present) - 1)
        omnibus = {"F": F, "df1": len(present) - 1, "df2": df, "p_value": float(stats.f.sf(F, len(present) - 1, df))}
    else:
        omnibus = None
    return {"status": "conventional_source_category_reconstruction", "reason": "Joint source-cohort mixed model; original implementation unavailable", "categories": categories, "omnibus": omnibus, "groups": groups, "full_moderator_pool": pool}

def build_family(rows, metadata, target, family):
    y = np.array([float(r["printed_g"]) for r in rows])
    clusters = [r["study_key"] for r in rows]
    v = sampling_variance(rows, y)
    primary = fit_matrix(y, v, clusters, family + "/primary")
    raw_rows = row_outputs(rows, y, v, primary)
    uncertainty = rounding(rows, y, clusters, primary, family)
    leaves = {}
    source_leaves = target["all_whole_trial_leave_out_robustness_mandatory"][family]
    for trial in sorted(set(clusters)):
        keep = [i for i, c in enumerate(clusters) if c != trial]
        pool = fit_matrix(y[keep], v[keep], [clusters[i] for i in keep], family + "/LOO/" + trial)
        literal = metadata["studies"][trial]["leave_out_source_literal"]
        direction, interval = classify(pool["g"], pool["CI_low"], pool["CI_high"])
        leaves[trial] = {"pool": pool, "remaining_row_ids": [rows[i]["row"] for i in keep], "point_direction": direction, "CI_classification": interval, "removed_trial_literal": literal}
    alternatives = {}
    for method in ("LS2", "UB", "CI_derived"):
        alt_v = sampling_variance(rows, y, method)
        alt_pool = fit_matrix(y, alt_v, clusters, family + "/supporting/" + method)
        alternatives[method] = {"pool": alt_pool, "rows": row_outputs(rows, y, alt_v, alt_pool), "primary_rescue": False}
    alt_pool = fit_matrix(y, v, clusters, family + "/supporting/ordinary_two_level_REML", ordinary_two_level=True)
    alternatives["ordinary_two_level_REML"] = {"pool": alt_pool, "rows": row_outputs(rows, y, v, alt_pool), "primary_rescue": False}
    subgroups = {factor: subgroup(rows, y, v, clusters, metadata, family, factor) for factor in ("sample_type", "platform", "interaction_mode", "response_generation")}
    return {"geometry": {"effects": len(rows), "trials": len(set(clusters)), "trial_keys": sorted(set(clusters)), "row_ids": [r["row"] for r in rows]}, "primary": primary, "rows": raw_rows, "rounding": uncertainty, "leave_one_trial_out": leaves, "supporting": {"sampling_alternatives": alternatives, "egger": egger(y, v), "subgroups": subgroups, "all_controls_supporting_only": True}}

def primary_checks(computations, targets):
    checks = []
    def append(family, kind, target, actual, passed, source, allowance=None, difference=None):
        checks.append({"id": "primary_%02d" % (len(checks) + 1), "family": family, "kind": kind, "source_literal": target, "target": target, "actual": actual, "allowance": allowance, "difference": difference, "passed": bool(passed), "source": source})
    for family in FAMILIES:
        comp = computations["families"][family]
        expected = targets["families"][family]
        for key in ("g", "CI_low", "CI_high"):
            actual = comp["primary"][key]
            difference = actual - float(expected[key])
            allowed = comp["rounding"]["allowance"][key]
            append(family, "pooled_" + key, expected[key], actual, abs(difference) <= allowed, "Original Figure", allowed, difference)
        direction, interval = classify(comp["primary"]["g"], comp["primary"]["CI_low"], comp["primary"]["CI_high"])
        directions = [direction] + [p["point_direction"] for p in comp["rounding"]["probe_records"]]
        intervals = [interval] + [p["CI_classification"] for p in comp["rounding"]["probe_records"]]
        append(family, "all_rounding_point_direction", expected["point_direction"], {"midpoint": direction, "all_fixed_probes": directions[1:]}, all(s == expected["point_direction"] for s in directions), "Original pooled qualitative claim")
        append(family, "all_rounding_CI_classification", expected["CI_classification"], {"midpoint": interval, "all_fixed_probes": intervals[1:]}, all(s == expected["CI_classification"] for s in intervals), "Original pooled qualitative claim")
        for field in ("effects", "trials"):
            actual = comp["geometry"][field]
            append(family, "exact_" + field, expected[field], actual, actual == expected[field], "Complete source cohort geometry", 0, actual - expected[field])
        source_rows = targets["all_whole_trial_leave_out_robustness_mandatory"][family]
        by_literal = {x["removed_trial_literal"]: x for x in comp["leave_one_trial_out"].values()}
        if len(by_literal) != len(source_rows):
            raise ValueError("Whole source leave-out census mismatch")
        for source in source_rows:
            actual = by_literal[source["removed_trial_literal"]]
            for field in ("point_direction", "CI_classification"):
                expected_class = source[field]
                append(family, "LOO_" + source["removed_trial_literal"] + "_" + field, expected_class, actual[field], expected_class != "ambiguous_source_zero" and actual[field] == expected_class, "Original S8 complete robustness")
    if len(checks) != 50:
        raise ValueError("All50 primary comparisons must be present")
    return checks

def resolve(obj, path):
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj

def supporting_checks(computations, ledger):
    result = []
    for source in ledger["checks"]:
        actual = resolve(computations, source["path"])
        if actual is None:
            passed, difference = None, None
        elif source["kind"] == "exact":
            passed, difference = actual == source["target"], None
        elif source["kind"] == "relation":
            if source["relation"] != "<":
                raise ValueError("Unregistered source relation")
            passed, difference = actual < source["target"], None
        else:
            difference = float(actual) - source["target"]
            passed = abs(difference) <= source["tolerance"]
        result.append(dict(source, actual=actual, difference=difference, passes_source_display=passed))
    return result

def main():
    global GUARD
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--freeze", required=True)
    args = parser.parse_args()
    output = Path(args.run).resolve()
    output.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(Path(args.freeze).read_bytes())
    config = freeze["config"]
    if config["mode"] not in ("synthetic", "original"):
        raise ValueError("Unregistered input mode")
    if config["mode"] == "synthetic":
        allowed = Path(config["input_root"]).resolve()
        for field in ("metadata_path", "targets_path", "supporting_targets_path", "primary_descriptors_path", "output_contract_path"):
            if not Path(config[field]).resolve().is_relative_to(allowed):
                raise ValueError("Synthetic configuration must bind isolated fabricated inputs")
        for r in freeze["files"]:
            if "published_summary_transcription001" in r["absolute_path"] or "ORIGINAL_STUDY_MODERATOR_METADATA001" in r["absolute_path"]:
                raise ValueError("Synthetic phase cannot open original cohort inputs")
    GUARD = Guard(output, freeze["resource_policy"])
    for expected in freeze["files"]:
        if reference(expected["absolute_path"]) != expected:
            raise ValueError("Frozen source/input/runtime hash mismatch")
    metadata = json.loads(Path(config["metadata_path"]).read_bytes())
    targets = json.loads(Path(config["targets_path"]).read_bytes())
    ledger = json.loads(Path(config["supporting_targets_path"]).read_bytes())
    descriptors = json.loads(Path(config["primary_descriptors_path"]).read_bytes())["checks"]
    records = {}
    for family in FAMILIES:
        path = Path(config["input_root"]) / (family + "_published_effects_source001.csv")
        with path.open(encoding="utf8", newline="") as f:
            records[family] = list(csv.DictReader(f))
        if len({r["row"] for r in records[family]}) != len(records[family]):
            raise ValueError("Duplicate source row")
    computations = {"mode": config["mode"], "raw_source_records": records, "metadata_used": metadata, "families": {}}
    for family in FAMILIES:
        computations["families"][family] = build_family(records[family], metadata, targets, family)
        GUARD.check(force=True)
    checks = primary_checks(computations, targets)
    if len(descriptors) != len(checks) or any(any(actual[key] != source[key] for key in ("id", "family", "kind", "target", "source")) for actual, source in zip(checks, descriptors)):
        raise ValueError("Frozen declarative50 primary descriptor mismatch")
    supporting = supporting_checks(computations, ledger)
    all_converged = all(x["selected_converged"] for x in TRACE)
    rounding_flags = {}
    leave_flags = {}
    for family in FAMILIES:
        comp = computations["families"][family]
        expected = targets["families"][family]
        direction, interval = classify(comp["primary"]["g"], comp["primary"]["CI_low"], comp["primary"]["CI_high"])
        rounding_flags[family] = {"midpoint_point_direction": direction, "midpoint_CI_classification": interval, "all_fixed_probe_point_direction_matches": direction == expected["point_direction"] and all(p["point_direction"] == expected["point_direction"] for p in comp["rounding"]["probe_records"]), "all_fixed_probe_CI_classification_matches": interval == expected["CI_classification"] and all(p["CI_classification"] == expected["CI_classification"] for p in comp["rounding"]["probe_records"])}
        actual = {r["removed_trial_literal"]: r for r in comp["leave_one_trial_out"].values()}
        source = targets["all_whole_trial_leave_out_robustness_mandatory"][family]
        leave_flags[family] = {"complete_source_leave_outs": len(actual) == len(source), "all_point_directions_match": all(actual[r["removed_trial_literal"]]["point_direction"] == r["point_direction"] for r in source), "all_CI_classifications_match": all(actual[r["removed_trial_literal"]]["CI_classification"] == r["CI_classification"] for r in source)}
    summary = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "mode": config["mode"], "complete_families": 2, "raw_effect_rows": sum(len(r) for r in records.values()), "raw_trial_counts": {f: computations["families"][f]["geometry"]["trials"] for f in FAMILIES}, "primary_gates": len(checks), "primary_passed": sum(c["passed"] for c in checks), "all_primary_passed": all(c["passed"] for c in checks), "all_fits_converged": all_converged, "rounding_qualitative_stability": rounding_flags, "whole_trial_leave_out_qualitative_robustness": leave_flags, "no_primary_rescue": True, "original_human_trials_repeated": False, "supporting_source_displays": len(supporting), "supporting_numeric_passed": sum(c["passes_source_display"] is True for c in supporting), "supporting_unavailable": sum(c["passes_source_display"] is None for c in supporting), "fit_count": len(TRACE), "method": METHOD}
    for name, obj in [("ALL_ORIGINAL_COMPUTATIONS.json", computations), ("ALL50_PRIMARY_CHECKS.json", checks), ("ALL_SUPPORTING_SOURCE_COMPARISONS.json", supporting), ("SUMMARY.json", summary), ("NUMERICAL_OPTIMIZER_TRACE.json", TRACE), ("RESOURCE_SAMPLES.json", GUARD.samples)]:
        save(output / name, obj)
    save(output / "OUTPUT_MANIFEST.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "files": [reference(p) for p in sorted(output.iterdir()) if p.is_file()], "input_freeze": reference(args.freeze)})
    print(json.dumps(summary, ensure_ascii=True), flush=True)
    return 0 if summary["all_primary_passed"] and all_converged else 2

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Preserve all completed optimizer paths even if a later computation fails.
        out = None
        for i, arg in enumerate(__import__("sys").argv):
            if arg == "--run" and i + 1 < len(__import__("sys").argv):
                out = Path(__import__("sys").argv[i + 1])
        if out is not None and out.exists():
            save(out / "FAILED_NUMERICAL_OPERATION.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exception_type": type(error).__name__, "exception": str(error), "completed_fit_trace": TRACE, "resource_samples": GUARD.samples if GUARD is not None else []})
        raise
