"""Prospective independent port of pinned 2025 meta/metafor semantics.
Source preparation only. Do not import/execute without separate root authorization.
Copyright original method sources GPL (>=2); this port distributed GPL-3.0-or-later.
"""
import math
from statistics import median
np = scipy_linalg = stats = None

class MethodError(RuntimeError):
    def __init__(self, message, diagnostics=None):
        super().__init__(message)
        self.diagnostics = diagnostics

def initialize_numeric_runtime():
    global np, scipy_linalg, stats
    import numpy as _np
    from scipy import linalg as _linalg
    from scipy import stats as _stats
    np, scipy_linalg, stats = _np, _linalg, _stats

def native_number(x):
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None

def matrix_list(x):
    return [[native_number(y) for y in row] for row in x]

def vector_list(x):
    return [native_number(y) for y in x]

def check_rows(rows):
    if not rows:
        raise MethodError("Empty active cohort")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise MethodError("Duplicate active row identity")
    for r in rows:
        e, n = r["events"], r["N"]
        if type(e) is not int or type(n) is not int or not 0 <= e <= n or n <= 0:
            raise MethodError("Invalid original/fake integer binomial count")

def effects(rows, scale, boundary_correction=True):
    check_rows(rows)
    y, v, increments = [], [], []
    for r in rows:
        e, n = r["events"], r["N"]
        inc = 0.5 if boundary_correction and e in (0, n) and scale in ("PLOGIT", "PRAW") else 0.0
        if scale == "PFT":
            yi = 0.5 * (math.asin(math.sqrt(e / (n + 1))) + math.asin(math.sqrt((e + 1) / (n + 1))))
            vi = 1.0 / (4 * n + 2)
        elif scale == "PAS":
            yi, vi = math.asin(math.sqrt(e / n)), 1.0 / (4 * n)
        elif scale == "PLOGIT":
            if min(e + inc, n - e + inc) <= 0:
                raise MethodError("Boundary logit without correction not estimable")
            yi = math.log((e + inc) / (n - e + inc))
            vi = 1.0 / (e + inc) + 1.0 / (n - e + inc)
        elif scale == "PRAW":
            yi = e / n
            vi = (e + inc) * (n - e + inc) / (n + 2 * inc) ** 3
            if vi <= 0:
                raise MethodError("Zero raw variance: no deletion/fallback")
        else:
            raise MethodError("Unknown transform")
        y.append(yi); v.append(vi); increments.append(inc)
    return np.asarray(y, dtype=np.float64), np.asarray(v, dtype=np.float64), increments

def active_backsize(rows, policy="harmonic"):
    values = [r["N"] for r in rows]
    if policy == "harmonic":
        return 1.0 / (sum(1.0 / n for n in values) / len(values))
    if policy == "min":
        return float(min(values))
    if policy == "max":
        return float(max(values))
    if policy == "arithmetic":
        return sum(values) / len(values)
    if policy == "geometric":
        return math.exp(sum(math.log(n) for n in values) / len(values))
    if policy == "median":
        return float(median(values))
    raise MethodError("Unknown backsize policy")

def inverse_effect(x, scale, size=None):
    if x is None or not math.isfinite(float(x)):
        return None
    x = float(x)
    if scale == "PRAW":
        return min(1.0, max(0.0, x))
    if scale == "PLOGIT":
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        ex = math.exp(x)
        return ex / (1.0 + ex)
    if scale == "PAS":
        if x < 0:
            return 0.0
        if x > math.pi / 2:
            return 1.0
        return math.sin(x) ** 2
    if scale != "PFT" or size is None or size <= 0:
        raise MethodError("PFT inverse requires active sample size")
    # Pinned meta asin2p Miller inverse, including its endpoint domain rules.
    low = 0.5 * math.asin(math.sqrt(1.0 / (size + 1)))
    high = 0.5 * (math.asin(math.sqrt(size / (size + 1))) + math.pi / 2)
    if x < low:
        return 0.0
    if x > high:
        return 1.0
    sx = math.sin(2 * x)
    if sx == 0:
        return None
    inner = 1.0 - (sx + (sx - 1.0 / sx) / size) ** 2
    # No ad-hoc clamping: source-negative radicands remain not estimable.
    if inner < 0:
        return None
    cx = math.cos(2 * x)
    sign = 1.0 if cx > 0 else (-1.0 if cx < 0 else 0.0)
    return 0.5 * (1.0 - sign * math.sqrt(inner))

def cp_interval(e, n):
    lo = 0.0 if e == 0 else float(stats.beta.ppf(0.025, e, n - e + 1))
    hi = 1.0 if e == n else float(stats.beta.ppf(0.975, e + 1, n - e))
    if not (math.isfinite(lo) and math.isfinite(hi)):
        raise MethodError("Nonfinite CP quantile")
    return lo, hi

def weighted_projection(X, variances):
    if np.any(variances <= 0) or not np.all(np.isfinite(variances)):
        raise MethodError("Nonpositive/nonfinite active variance")
    w = 1.0 / variances
    Z = np.sqrt(w)[:, None] * X
    q, r, pivot = scipy_linalg.qr(Z, mode="economic", pivoting=True, check_finite=True)
    p = X.shape[1]
    diag = np.abs(np.diag(r))
    if len(diag) != p or p > X.shape[0] or np.any(diag <= 1e-7 * diag[0]):
        raise MethodError("Fixed model matrix rank deficient; no omitted coefficient")
    rinv = scipy_linalg.solve_triangular(r, np.eye(p), lower=False)
    cov_p = rinv @ rinv.T
    cov = np.empty((p, p), dtype=np.float64)
    cov[np.ix_(pivot, pivot)] = cov_p
    W = np.diag(w)
    P = W - (w[:, None] * X) @ cov @ (X.T * w[None, :])
    return w, cov, P

def restricted_likelihood(y_centered, v, X, tau):
    w, cov, _ = weighted_projection(X, v + tau)
    beta = cov @ (X.T @ (w * y_centered))
    resid = y_centered - X @ beta
    sign, logdet = np.linalg.slogdet(X.T @ (w[:, None] * X))
    if sign <= 0:
        raise MethodError("Invalid likelihood determinant")
    k, p = X.shape
    # Original REMLf X'X term is constant in tau and cancels in boundary comparison.
    return -0.5 * (k - p) * math.log(2 * math.pi) - 0.5 * float(np.log(v + tau).sum()) - 0.5 * logdet - 0.5 * float(np.sum(w * resid ** 2))

def estimate_tau(y, v, X, method, guard=None):
    guard = guard or (lambda phase: None)
    k, p = X.shape
    yc = y - float(np.mean(y))
    if k <= p:
        raise MethodError("Not enough observations to estimate residual tau")
    w0, cov0, P0w = weighted_projection(X, v)
    Q = max(0.0, float(yc @ P0w @ yc))
    df = k - p
    if method == "DL":
        denom = float(np.trace(P0w))
        if denom <= 0:
            raise MethodError("Invalid DL trace")
        tau = max(0.0, (Q - df) / denom)
        return tau, {"method": "DL", "initial": None, "iterations": [], "converged": True, "boundary_ll0_reset": False}
    if method != "REML":
        raise MethodError("Unknown tau estimator")
    _, cov_he, Phe = weighted_projection(X, np.ones(k))
    HE = (float(yc @ Phe @ yc) - float(np.sum(np.diag(Phe) * v))) / df
    tau = max(0.0, HE)
    initial = tau
    trace = []
    for iteration in range(1, 102):
        guard("REML_iteration")
        w, cov, P = weighted_projection(X, v + tau)
        PP = P @ P
        denominator = float(np.trace(PP))
        if denominator <= 0:
            raise MethodError("Invalid REML information")
        adj = (float(yc @ PP @ yc) - float(np.trace(P))) / denominator
        if not math.isfinite(adj):
            raise MethodError("Nonfinite REML update")
        halvings = 0
        while tau + adj < 0:
            adj /= 2.0
            halvings += 1
            if halvings > 1075:
                raise MethodError("REML step halving underflow")
        old = tau
        tau += adj
        change = abs(tau - old)
        trace.append({"iteration": iteration, "old_tau2": old, "update": adj, "new_tau2": tau, "change": change, "halvings": halvings})
        if iteration > 100:
            raise MethodError("Original REML maximum iterations exceeded", {"method": "REML", "HE": HE, "initial": initial, "iterations": trace, "converged": False, "boundary_ll0_reset": False})
        if change <= 1e-5:
            break
    else:
        raise MethodError("REML did not converge")
    ll0 = restricted_likelihood(yc, v, X, 0.0)
    ll = restricted_likelihood(yc, v, X, tau)
    reset = ll0 - ll > np.finfo(np.float64).eps ** 0.25 and tau > 1e-5
    if reset:
        tau = 0.0
    return tau, {"method": "REML", "HE": HE, "initial": initial, "iterations": trace, "converged": True, "boundary_ll0": ll0, "boundary_ll": ll, "boundary_ll0_reset": bool(reset), "warning": "Source ll0 local maximum reset" if reset else None}

def fit_model(rows, scale, method, X, columns, guard=None, legacy=False):
    base = {"status": "not_estimable", "input_ids": [r["id"] for r in rows], "columns": columns, "scale": scale, "tau_method": method}
    try:
        y, v, inc = effects(rows, scale, boundary_correction=not legacy)
        X = np.asarray(X, dtype=np.float64)
        if X.shape != (len(rows), len(columns)) or not np.all(np.isfinite(X)):
            raise MethodError("Fixed model matrix geometry/nonfinite")
        tau, solver = estimate_tau(y, v, X, method, guard)
        w, covariance, P = weighted_projection(X, v + tau)
        beta = covariance @ (X.T @ (w * y))
        se = np.sqrt(np.diag(covariance))
        z = beta / se
        zcrit = float(stats.norm.ppf(0.975))
        _, _, P0 = weighted_projection(X, v)
        yc = y - float(np.mean(y))
        Q = max(0.0, float(yc @ P0 @ yc))
        df = len(rows) - len(columns)
        base.update(status="ok", X=matrix_list(X), y=vector_list(y), v=vector_list(v), increments=inc, beta=vector_list(beta), cov=matrix_list(covariance), SE=vector_list(se), Z=vector_list(z), p=vector_list(2 * stats.norm.sf(np.abs(z))), CI_low=vector_list(beta - zcrit * se), CI_high=vector_list(beta + zcrit * se), Q=Q, Q_df=df, heterogeneity_p=float(stats.chi2.sf(Q, df)), tau2=tau, solver=solver)
    except (MethodError, ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        base["error"] = str(exc)
        if getattr(exc, "diagnostics", None) is not None:
            base["solver"] = exc.diagnostics
    return base

def pool(rows, scale, method, backsize="harmonic", guard=None, legacy=False):
    base = {"status": "not_estimable", "input_ids": [r["id"] for r in rows], "scale": scale, "tau_method": method, "backsize_policy": backsize, "k": len(rows)}
    try:
        y, v, inc = effects(rows, scale, boundary_correction=not legacy)
        k = len(rows)
        X = np.ones((k, 1), dtype=np.float64)
        if k == 1:
            tau = None
            calc_tau = 0.0
            solver = {"method": method, "status": "singleton_tau_NA", "converged": None, "iterations": []}
        else:
            calc_tau, solver = estimate_tau(y, v, X, method, guard)
            tau = calc_tau
        wc, wr = 1.0 / v, 1.0 / (v + calc_tau)
        # Translation-invariant weighted offsets avoid a rounding residual for exactly equal transformed inputs.
        anchor = float(y[0])
        centered = y - anchor
        offset_common = float(np.dot(wc, centered) / np.sum(wc))
        offset_random = float(np.dot(wr, centered) / np.sum(wr))
        mc, mr = anchor + offset_common, anchor + offset_random
        sc, sr = math.sqrt(1.0 / float(np.sum(wc))), math.sqrt(1.0 / float(np.sum(wr)))
        zcrit = float(stats.norm.ppf(0.975))
        size = active_backsize(rows, backsize) if scale == "PFT" else None
        def summary(mean, se):
            low, high = mean - zcrit * se, mean + zcrit * se
            return {"effect": mean, "SE": se, "low_effect": low, "high_effect": high, "point": mean if legacy else inverse_effect(mean, scale, size), "low": low if legacy else inverse_effect(low, scale, size), "high": high if legacy else inverse_effect(high, scale, size), "weights_pct": 100.0}
        common, random = summary(mc, sc), summary(mr, sr)
        Q = max(0.0, float(np.sum(wc * (centered - offset_common) ** 2)))
        df = k - 1
        p = float(stats.chi2.sf(Q, df)) if df > 0 else None
        I2 = (max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0) if df > 0 else None
        prediction = {"df": None, "SE": None, "low_effect": None, "high_effect": None, "low": None, "high": None}
        pidf = k - (2 if legacy else 1)
        if pidf > 0:
            ps = math.sqrt(calc_tau + sr * sr)
            critical = float(stats.t.ppf(0.975, pidf))
            low, high = mr - critical * ps, mr + critical * ps
            prediction = {"df": pidf, "SE": ps, "low_effect": low, "high_effect": high, "low": low if legacy else inverse_effect(low, scale, size), "high": high if legacy else inverse_effect(high, scale, size)}
        outrows = []
        for i, row in enumerate(rows):
            lo, hi = cp_interval(row["events"], row["N"])
            outrows.append({"id": row["id"], "canonical_index": row["canonical_index"], "events": row["events"], "N": row["N"], "year": row["year"], "effect": float(y[i]), "variance": float(v[i]), "increment": inc[i], "proportion": inverse_effect(float(y[i]), scale, row["N"] if scale == "PFT" else None), "CI_low": lo, "CI_high": hi, "common_weight_pct": 100.0 * float(wc[i] / np.sum(wc)), "random_weight_pct": 100.0 * float(wr[i] / np.sum(wr))})
        if legacy and k == 1:
            common["low"] = random["low"] = outrows[0]["CI_low"]
            common["high"] = random["high"] = outrows[0]["CI_high"]
        base.update(status="ok", total_N=sum(r["N"] for r in rows), events_total=sum(r["events"] for r in rows), backsize_N=size, rows=outrows, common=common, random=random, prediction=prediction, Q=Q if not (legacy and k == 1) else None, Q_df=df, heterogeneity_p=p, I2_pct=I2, tau2=tau, tau2_calc=calc_tau, solver=solver)
    except (MethodError, ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        base["error"] = str(exc)
        if getattr(exc, "diagnostics", None) is not None:
            base["solver"] = exc.diagnostics
    return base

def reback_pool(subject, rows, policy):
    # Supporting PFT backsize views preserve every transformed fit and alter only size.
    import copy
    out = copy.deepcopy(subject)
    out["backsize_policy"] = policy
    if subject["status"] != "ok":
        return out
    n = active_backsize(rows, policy)
    out["backsize_N"] = n
    for name in ("common", "random"):
        for field, source in (("point", "effect"), ("low", "low_effect"), ("high", "high_effect")):
            out[name][field] = inverse_effect(out[name][source], "PFT", n)
    for field, source in (("low", "low_effect"), ("high", "high_effect")):
        out["prediction"][field] = inverse_effect(out["prediction"][source], "PFT", n)
    return out

def Egger(rows, scale, guard=None, legacy=False):
    base = {"status": "not_estimable", "input_ids": [r["id"] for r in rows], "scale": scale, "k_min": 10, "correct": False}
    try:
        if len(rows) < 10:
            raise MethodError("Fixed Egger k.min10")
        y, v, inc = effects(rows, scale, boundary_correction=not legacy)
        se = np.sqrt(v)
        X = np.column_stack((np.ones(len(rows)), se))
        w, cov0, _ = weighted_projection(X, v)
        beta = cov0 @ (X.T @ (w * y))
        residual = y - X @ beta
        df = len(rows) - 2
        dispersion = float(np.sum(w * residual ** 2)) / df
        cov = cov0 * dispersion
        bse = np.sqrt(np.diag(cov))
        test = float(beta[1] / bse[1])
        p = float(2 * stats.t.sf(abs(test), df))
        critical = float(stats.t.ppf(0.975, df))
        base.update(status="ok", y=vector_list(y), v=vector_list(v), X=matrix_list(X), df=df, dispersion=dispersion, cov=matrix_list(cov), bias_SND_intercept=float(beta[1]), bias_SE=float(bse[1]), weighted_limit_intercept=float(beta[0]), weighted_limit_SE=float(bse[0]), weighted_limit_low=float(beta[0] - critical * bse[0]), weighted_limit_high=float(beta[0] + critical * bse[0]), statistic=test, p=p, source_label_warning="Printed beta0 label retained; compare fixed Egger bias, also report limit intercept; no outcome-selected naming")
    except (MethodError, ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        base["error"] = str(exc)
        if getattr(exc, "diagnostics", None) is not None:
            base["solver"] = exc.diagnostics
    return base

def moderator_design(rows, kind):
    columns = ["intercept"]
    if kind in ("simultaneous", "year"):
        columns.append("year_minus_2020")
    if kind in ("simultaneous", "N"):
        columns.append("N")
    if kind in ("simultaneous", "group"):
        columns.append("nurses")
        if any(r["group"] == "faculty" for r in rows):
            columns.append("faculty")
    data = []
    for r in rows:
        fields = {"intercept": 1.0, "year_minus_2020": float(r["year"] - 2020), "N": float(r["N"]), "nurses": float(r["group"] == "nurses"), "faculty": float(r["group"] == "faculty")}
        data.append([fields[c] for c in columns])
    return data, columns

def country_design(rows, convention):
    key = "country_B" if convention == "AppendixB" else "country_Figure2"
    cats = sorted(set(r[key] for r in rows))
    columns = ["intercept"] + ["country:" + c for c in cats[1:]]
    X = [[1.0] + [float(r[key] == c) for c in cats[1:]] for r in rows]
    return X, columns, cats

def between_groups(rows, groups, legacy=False):
    out = {}
    if any(x["status"] != "ok" for x in groups.values()):
        return {"status": "not_estimable", "error": "A group fit failed", "input_ids": [r["id"] for r in rows]}
    for mode in ("common", "random"):
        ms = [x[mode]["effect"] for x in groups.values()]
        vv = [x[mode]["SE"] ** 2 for x in groups.values()]
        w = [1.0 / v for v in vv]
        mu = sum(a * b for a, b in zip(w, ms)) / sum(w)
        q = max(0.0, sum(a * (b - mu) ** 2 for a, b in zip(w, ms)))
        df = len(ms) - 1
        out[mode] = {"Q": q, "df": df, "p": float(stats.chi2.sf(q, df)) if df > 0 else None}
    out["status"] = "ok"
    out["interpretation"] = "Separate-tau meta subgroup Q from transformed group estimates/SEs"
    return out

def legacy_shared_between(rows, pooled, scale):
    if pooled["status"] != "ok":
        return {"status": "not_estimable", "error": "Full legacy pool failed"}
    y, v, inc = effects(rows, scale, boundary_correction=False)
    tau = pooled["tau2_calc"]
    w = 1.0 / (v + tau)
    overall = float(np.dot(w, y) / np.sum(w))
    q = 0.0
    for g in sorted(set(r["group"] for r in rows)):
        idx = [i for i, r in enumerate(rows) if r["group"] == g]
        wg = float(np.sum(w[idx]))
        mg = float(np.dot(w[idx], y[idx]) / wg)
        q += wg * (mg - overall) ** 2
    df = len(set(r["group"] for r in rows)) - 1
    return {"status": "ok", "Q": max(0.0, q), "df": df, "p": float(stats.chi2.sf(q, df)) if df > 0 else None, "interpretation": "Original prospective RAWDL001 shared full-family tau between test"}
