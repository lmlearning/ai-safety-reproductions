"""Full P133 candidate orchestration. Source-only preparation, no execution authorized."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import math
import copy
import candidate_core007 as core

FAMILIES = ("awareness", "attitude", "implementation")
PIPELINES = (("PFT_REML", "PFT", "REML"), ("PAS_REML", "PAS", "REML"), ("PLOGIT_REML", "PLOGIT", "REML"), ("PLOGIT_DL", "PLOGIT", "DL"), ("PFT_DL", "PFT", "DL"), ("PRAW_DL", "PRAW", "DL"))
BACKSIZES = ("min", "max", "arithmetic", "geometric", "median")
RECORD = lambda kind, value: None

def set_recorder(callback):
    global RECORD
    RECORD = callback

def fitted_model(rows, scale, method, X, columns, guard, legacy=False):
    value = core.fit_model(rows, scale, method, X, columns, guard, legacy)
    RECORD("model", value)
    return value
GROUPS = ("students", "nurses", "faculty")
SOURCE_DIR = "papers/P133_nursing_ai_meta/review/source_feasibility001"
GATE_PATH = "papers/P133_nursing_ai_meta/review/quantitative_scope002/ALL377_OUTPUT_AND129_INPUT_GATES002.json"

def read_json(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))

def source_bundle(root):
    forest = read_json(root, SOURCE_DIR + "/ALL43_FOREST_LITERAL_TARGETS001.json")
    metadata = read_json(root, SOURCE_DIR + "/ALL18_CANONICAL_SOURCE_METADATA001.json")
    appraisals = read_json(root, SOURCE_DIR + "/ORIGINAL_ALL18_APPRAISAL_AND16_COUNTRY_LABELS001.json")
    conflicts = read_json(root, SOURCE_DIR + "/SOURCE_CONFLICT_LEDGER001.json")
    gates = read_json(root, GATE_PATH)
    meta = {r["canonical_index"]: r for r in metadata["records"]}
    figure = {r["appendixB_canonical_index"]: r["country_literal"] for r in appraisals["records"]}
    rows = []
    for r in forest["rows"]:
        idx = r["appendixB_canonical_index"]
        tokens = meta[idx]["primary_country_tokens"]
        country = " + ".join(tokens) if tokens else "NOT_SPECIFIED"
        rows.append({"id": r["family"] + ".row" + str(r["forest_row"]).zfill(2), "family": r["family"], "forest_row": r["forest_row"], "canonical_index": idx, "study_literal": r["study_literal"], "year": int(r["year_literal"]), "events": int(r["events_literal"]), "N": int(r["N_literal"]), "group": meta[idx]["primary_group"], "country_B": country, "country_Figure2": figure.get(idx, country)})
    validate_canonical(rows, gates, original=True)
    if len(metadata["records"]) != 18 or len(appraisals["records"]) != 16 or len(conflicts) != 23:
        raise RuntimeError("Fixed metadata/appraisal/conflict census")
    return {"rows": rows, "metadata": metadata, "appraisals": appraisals, "conflicts": conflicts, "gates": gates}

def validate_canonical(rows, gates, original=False):
    core.check_rows(rows)
    if len(rows) != 43 or len(set(r["canonical_index"] for r in rows)) != 18:
        raise RuntimeError("Complete fixed cohort census")
    expected = gates["identities"]
    if [r["id"] for r in rows] != [r["id"] for r in expected]:
        raise RuntimeError("Complete canonical row order")
    for family, count in zip(FAMILIES, (15, 16, 12)):
        if sum(r["family"] == family for r in rows) != count:
            raise RuntimeError("Family row census")
    if len(gates["input_gates"]) != 129 or len(gates["primary_output_gates"]) != 263 or len(gates["supporting_literal_gates"]) != 114:
        raise RuntimeError("Fixed target census")
    if original:
        values = input_values(rows)
        for g in gates["input_gates"]:
            if values[g["id"]] != g["typed_value"]:
                raise RuntimeError("Canonical input differs from exact fixed source")
        for row, identity in zip(rows, expected):
            if row["canonical_index"] != identity["canonical_index"] or row["study_literal"] != identity["literal_study"]:
                raise RuntimeError("Canonical identity literal mismatch")

def input_values(rows):
    return {r["id"] + "." + field: r[field] for r in rows for field in ("events", "N", "year")}

def pool_guard(rows, scale, method, guard, legacy=False):
    guard("pool_before")
    value = core.pool(rows, scale, method, guard=guard, legacy=legacy)
    RECORD("pool", value)
    guard("pool_after")
    return value

def full_diagnostics(rows, scale, method, guard, legacy=False):
    groups = {g: pool_guard([r for r in rows if r["group"] == g], scale, method, guard, legacy) for g in GROUPS if any(r["group"] == g for r in rows)}
    pooled = pool_guard(rows, scale, method, guard, legacy)
    X, cols = core.moderator_design(rows, "simultaneous")
    simultaneous = fitted_model(rows, scale, method, X, cols, guard, legacy)
    univariate = {}
    for kind in ("year", "N", "group"):
        guard("univariate_" + kind)
        X, cols = core.moderator_design(rows, kind)
        univariate[kind] = fitted_model(rows, scale, method, X, cols, guard, legacy)
    country = {}
    for convention in ("AppendixB", "Figure2"):
        guard("country_" + convention)
        X, cols, categories = core.country_design(rows, convention)
        model = fitted_model(rows, scale, method, X, cols, guard, legacy)
        model["categories"] = categories
        model["reference_category"] = categories[0]
        model["coding"] = {r["id"]: r["country_B" if convention == "AppendixB" else "country_Figure2"] for r in rows}
        country[convention] = model
    guard("Egger")
    egger = core.Egger(rows, scale, guard, legacy)
    RECORD("Egger", egger)
    between = core.between_groups(rows, groups)
    legacy_between = core.legacy_shared_between(rows, pooled, scale) if legacy else None
    RECORD("between", {"input_ids": [r["id"] for r in rows], "scale": scale, "tau_method": method, "between": between, "legacy_shared_between": legacy_between})
    funnel = {"status": "not_estimable", "input_ids": [r["id"] for r in rows]}
    if pooled["status"] == "ok":
        pairs = []
        for row in pooled["rows"]:
            se = math.sqrt(row["variance"])
            mean = pooled["random"]["effect"]
            pairs.append({"id": row["id"], "effect": row["effect"], "SE": se, "envelope95_low": mean - float(core.stats.norm.ppf(.975)) * se, "envelope95_high": mean + float(core.stats.norm.ppf(.975)) * se, "envelope99_low": mean - float(core.stats.norm.ppf(.995)) * se, "envelope99_high": mean + float(core.stats.norm.ppf(.995)) * se})
        funnel = {"status": "ok", "input_ids": pooled["input_ids"], "scale": scale, "center": pooled["random"]["effect"], "pairs": pairs, "source_target_absent": True}
    return {"pooled": pooled, "groups": groups, "between": between, "legacy_shared_between": legacy_between, "simultaneous": simultaneous, "univariate": univariate, "country": country, "Egger": egger, "funnel": funnel}

def family_pipeline(rows, scale, method, guard, legacy=False):
    out = full_diagnostics(rows, scale, method, guard, legacy)
    out["LOO"] = {}
    for excluded in rows:
        guard("LOO_" + excluded["id"])
        active = [r for r in rows if r["id"] != excluded["id"]]
        if legacy:
            view = full_diagnostics(active, scale, method, guard, legacy=True)
        else:
            view = {"pooled": pool_guard(active, scale, method, guard)}
        view["excluded_id"] = excluded["id"]
        view["remaining_input_ids"] = [r["id"] for r in active]
        out["LOO"][excluded["id"]] = view
    return out

def run_complete_suite(rows, guard):
    result = {"schema": "P133_candidate004", "pipelines": {}, "backsize_views": {}, "legacy_RAWDL001": {}, "architecture_GLMM": {"status": "source_architecture_only", "model": "PLOGIT/GLMM/ML", "individual_common_weights": None, "individual_random_weights": None, "default_prediction": False, "numeric_fit": False, "not_a_primary_rescue": True}}
    for pid, scale, method in PIPELINES:
        guard("pipeline_" + pid)
        result["pipelines"][pid] = {"scale": scale, "tau_method": method, "families": {}}
        for family in FAMILIES:
            guard(pid + "_" + family)
            active = [r for r in rows if r["family"] == family]
            result["pipelines"][pid]["families"][family] = family_pipeline(active, scale, method, guard)
            RECORD("family_completed", {"pipeline": pid, "family": family, "result": result["pipelines"][pid]["families"][family]})
    for policy in BACKSIZES:
        result["backsize_views"][policy] = {"families": {}}
        for family in FAMILIES:
            guard("backsize_" + policy + "_" + family)
            active = [r for r in rows if r["family"] == family]
            base = result["pipelines"]["PFT_REML"]["families"][family]
            view = {"pooled": core.reback_pool(base["pooled"], active, policy), "groups": {}, "LOO": {}}
            for g, pooled in base["groups"].items():
                view["groups"][g] = core.reback_pool(pooled, [r for r in active if r["group"] == g], policy)
            for excluded in active:
                key = excluded["id"]
                remaining = [r for r in active if r["id"] != key]
                view["LOO"][key] = {"excluded_id": key, "remaining_input_ids": [r["id"] for r in remaining], "pooled": core.reback_pool(base["LOO"][key]["pooled"], remaining, policy)}
            result["backsize_views"][policy]["families"][family] = view
            RECORD("backsize_family_completed", {"policy": policy, "family": family, "result": view})
    for family in FAMILIES:
        guard("legacy_RAWDL001_" + family)
        result["legacy_RAWDL001"][family] = family_pipeline([r for r in rows if r["family"] == family], "PRAW", "DL", guard, legacy=True)
        RECORD("legacy_family_completed", {"family": family, "result": result["legacy_RAWDL001"][family]})
    return result

def primary_outputs(result, gates):
    families = result["pipelines"]["PFT_REML"]["families"]
    values = {}
    for family in FAMILIES:
        full = families[family]["pooled"]
        rows = {r["id"]: r for r in full.get("rows", [])}
        for gate in gates["primary_output_gates"]:
            ident = gate["id"]
            if not ident.startswith(family + "."):
                continue
            if ".row" in ident:
                rowid, field = ident.rsplit(".", 1)
                values[ident] = rows.get(rowid, {}).get(field)
            elif full["status"] != "ok":
                values[ident] = None
            else:
                field = ident.split(".footer.", 1)[1]
                current = full
                for key in field.split("."):
                    current = current.get(key) if isinstance(current, dict) else None
                values[ident] = current
    if set(values) != {g["id"] for g in gates["primary_output_gates"]}:
        raise RuntimeError("Primary output mapping omission")
    return values

def coefficient(model, column, field):
    if model["status"] != "ok" or column not in model["columns"]:
        return None
    idx = model["columns"].index(column)
    mapping = {"estimate": "beta", "SE": "SE", "Z": "Z", "p": "p", "CI_low": "CI_low", "CI_high": "CI_high"}
    return model[mapping[field]][idx]

def supporting_outputs(result, gates):
    fams = result["pipelines"]["PFT_REML"]["families"]
    values = {}
    label_col = {"Year": "year_minus_2020", "Sample size": "N", "Nurses": "nurses", "Nursing faculty": "faculty"}
    label_group = {"Nursing students": "students", "Nurses": "nurses", "Nursing faculty": "faculty"}
    for gate in gates["supporting_literal_gates"]:
        ident = gate["id"]
        family = ident.split(".")[0]
        family_result = fams[family]
        if ".T5." in ident:
            field = ident.rsplit(".", 1)[1]
            values[ident] = coefficient(family_result["simultaneous"], label_col[gate["label"]], field)
        elif ".T6.between." in ident:
            field = ident.rsplit(".", 1)[1]
            values[ident] = family_result["between"].get("random", {}).get(field)
        elif ".T6.row" in ident:
            field = ident.rsplit(".", 1)[1]
            group = family_result["groups"][label_group[gate["label"]]]
            mapping = {"N_studies": "k", "point": ("random", "point"), "CI_low": ("random", "low"), "CI_high": ("random", "high"), "I2_percent": "I2_pct", "tau2": "tau2"}
            target = mapping[field]
            if field == "N_studies":
                value = group["k"]
            elif group["status"] != "ok":
                value = None
            elif isinstance(target, tuple):
                value = group[target[0]][target[1]]
            else:
                value = group[target]
            values[ident] = value
        elif ".Egger." in ident:
            field = ident.rsplit(".", 1)[1]
            key = "bias_SND_intercept" if field == "intercept" else "p"
            values[ident] = family_result["Egger"].get(key)
        else:
            raise RuntimeError("Unsupported fixed gate ID")
    if set(values) != {g["id"] for g in gates["supporting_literal_gates"]}:
        raise RuntimeError("Supporting output mapping omission")
    return values

def compare_gate(gate, value):
    record = {"id": gate["id"], "role": gate["role"], "source_literal": gate["literal"], "source": gate["source"], "value": value, "decimal_places": gate.get("decimal_places"), "source_star": gate.get("star"), "joint_source_contradiction": gate.get("joint_source_contradiction")}
    if gate.get("comparison_kind") == "inequality":
        good = value is not None and math.isfinite(float(value)) and 0 <= value < 0.0001
        formatted = None if value is None else str(value)
    elif gate.get("typed_value") is None:
        good = value is None
        formatted = None if value is None else str(value)
    elif value is None or not math.isfinite(float(value)):
        good, formatted = False, None
    elif gate.get("decimal_places") is None:
        good, formatted = value == gate["typed_value"], str(value)
    else:
        places = gate["decimal_places"]
        quant = Decimal(1).scaleb(-places)
        computed = Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_EVEN)
        source = Decimal(str(gate["typed_value"])).quantize(quant, rounding=ROUND_HALF_EVEN)
        good, formatted = computed == source, format(computed, "." + str(places) + "f")
    record.update(passed=bool(good),formatted=formatted)
    if gate.get("star") is not None:
        # Actual significance is additional supporting reporting, not literal-point repair.
        record["computed_significance_p_lt_05"] = value < .05 if value is not None and gate["id"].endswith(".p") else None
    return record

def compare_all_inputs_and_outputs(rows, result, gates):
    iv = input_values(rows)
    pv, sv = primary_outputs(result, gates), supporting_outputs(result, gates)
    comparisons = [compare_gate(g, iv[g["id"]]) for g in gates["input_gates"]]
    comparisons += [compare_gate(g, pv[g["id"]]) for g in gates["primary_output_gates"]]
    comparisons += [compare_gate(g, sv[g["id"]]) for g in gates["supporting_literal_gates"]]
    if len(comparisons) != 506 or len(set(x["id"] for x in comparisons)) != 506:
        raise RuntimeError("Complete fixed506 comparison census")
    return {"input_values": iv, "primary_output_values": pv, "supporting_output_values": sv, "comparisons": comparisons, "input_pass": all(x["passed"] for x in comparisons[:129]), "primary263_pass": all(x["passed"] for x in comparisons[129:392]), "supporting114_pass": all(x["passed"] for x in comparisons[392:]), "supporting_never_rescues": True}

def source_claims(result, comparisons):
    primary = result["pipelines"]["PFT_REML"]["families"]
    pools = {f: primary[f]["pooled"] for f in FAMILIES}
    valid = all(p["status"] == "ok" for p in pools.values())
    c2 = valid and all(p["heterogeneity_p"] is not None and p["heterogeneity_p"] < .05 and p["heterogeneity_p"] < .0001 for p in pools.values())
    c3 = valid and pools["attitude"]["random"]["point"] is not None and pools["awareness"]["random"]["point"] is not None and pools["attitude"]["random"]["point"] < pools["awareness"]["random"]["point"] and pools["implementation"]["I2_pct"] > pools["awareness"]["I2_pct"] and pools["implementation"]["I2_pct"] > pools["attitude"]["I2_pct"]
    return [{"id": "CL01", "role": "PRIMARY", "passed": comparisons["primary263_pass"], "source_abstract_upper80_conflict": "Canonical Figure4 upper81 remains primary, abstract80 mandatory conflictC11"}, {"id": "CL02", "role": "PRIMARY", "passed": bool(c2)}, {"id": "CL03", "role": "PRIMARY", "passed": bool(c3)}, {"id": "CL04", "role": "SUPPORTING", "report": "All10 moderator literal cells/slopes and all unprinted coefficients retain actual p/sign/NA"}, {"id": "CL05", "role": "SUPPORTING", "report": "All7 printed plus8actualgroups and both between tests; inconsistent Ns/CI preserved"}, {"id": "CL06", "role": "SUPPORTING", "report": "All3 fixed Egger bias/p, limit intercept also present; nonsignificance does not establish absence"}, {"id": "CL07", "role": "COMPLETE_CONTROL", "report": "All43LOO/country3x2/full variants/backsize5/funnels/legacy_RAWDL001 retained"}, {"id": "CL08", "role": "MANDATORY_LIMITATION", "report": "All23sourceconflicts/18source appraisals/full-paper and author-settings/event coding gaps retained"}, {"id": "CL09", "role": "EXACT_CENSUS", "report": "Canonical all43/18 plus exact129input/377output/audit/closure required"}]

def structural_census(result, rows):
    expected = {}
    for pid, scale, tau in PIPELINES:
        fams = result["pipelines"][pid]["families"]
        if set(fams) != set(FAMILIES):
            raise RuntimeError("Missing full family")
        for family in FAMILIES:
            active = [r for r in rows if r["family"] == family]
            f = fams[family]
            assert set(f["LOO"]) == {r["id"] for r in active}
            assert set(f["groups"]) == {r["group"] for r in active}
            assert set(f["univariate"]) == {"year", "N", "group"}
            assert set(f["country"]) == {"AppendixB", "Figure2"}
            for rid, loo in f["LOO"].items():
                assert loo["remaining_input_ids"] == [r["id"] for r in active if r["id"] != rid]
        expected[pid] = {"full": 3, "groups": sum(len(f["groups"]) for f in fams.values()), "LOO": sum(len(f["LOO"]) for f in fams.values()), "simultaneous": 3, "univariate": 9, "country": 6, "Egger": 3}
    assert set(result["backsize_views"]) == set(BACKSIZES)
    for policy in BACKSIZES:
        fams = result["backsize_views"][policy]["families"]
        assert set(fams) == set(FAMILIES)
        for family in FAMILIES:
            f = fams[family]
            active = [r for r in rows if r["family"] == family]
            assert set(f["LOO"]) == {r["id"] for r in active}
            assert set(f["groups"]) == {r["group"] for r in active}
    assert set(result["legacy_RAWDL001"]) == set(FAMILIES)
    for family in FAMILIES:
        f = result["legacy_RAWDL001"][family]
        active = [r for r in rows if r["family"] == family]
        assert set(f["LOO"]) == {r["id"] for r in active}
        for rid, loo in f["LOO"].items():
            remaining = [r for r in active if r["id"] != rid]
            assert set(loo["groups"]) == {r["group"] for r in remaining}
            assert set(loo["country"]) == {"AppendixB", "Figure2"}
            assert set(loo["univariate"]) == {"year", "N", "group"}
    return {"pipelines": expected, "backsize_pool_views": 270, "legacy_full": 3, "legacy_nested_LOO": 43, "scientific_pass_decided_by_audit_and_root_only": True}
