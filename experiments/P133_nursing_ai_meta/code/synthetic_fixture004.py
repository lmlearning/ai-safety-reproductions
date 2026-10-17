"""Unrelated synthetic fixture recipe. No original outcome execution authorized."""
import copy

def synthetic_bundle(source_bundle):
    """Preserve only source schema/identity topology; replace every numeric input."""
    bundle = copy.deepcopy(source_bundle)
    rows = []
    family_index = {"awareness": 0, "attitude": 1, "implementation": 2}
    for old in source_bundle["rows"]:
        r = copy.deepcopy(old)
        j, f = r["canonical_index"], family_index[r["family"]]
        n = 103 + 7 * j + 3 * f
        e = 17 + (29 * j + 13 * f) % (n - 33)
        r.update(N=n, events=e, year=2011 + j % 7, study_literal="UNRELATED_FAKE_" + str(j))
        rows.append(r)
    bundle["rows"] = rows
    bundle["fixture"] = {"unrelated": True, "recipe": "N=103+7*canonical_index+3*family_index;events=17+(29*index+13*family_index)mod(N-33);year=2011+indexmod7", "RNG": "none", "original_numeric_fields_used": False, "not_scientific_credit": True}
    return bundle

def expected_edge_cases():
    return [
        {"id": "CP_zero", "row": {"id": "fake.boundary.zero", "events": 0, "N": 37, "year": 2013, "canonical_index": 1}, "expect": "CP lower0; PFT/PAS transforms finite; canonical PLOGIT only0 correction .5; legacy raw no variance ->explicitnot_estimable"},
        {"id": "CP_all", "row": {"id": "fake.boundary.all", "events": 37, "N": 37, "year": 2013, "canonical_index": 2}, "expect": "CP upper1; PFT/PAS transforms finite; canonical PLOGIT only0 correction .5; legacy raw no variance ->explicitnot_estimable"},
        {"id": "round_ties", "values": ["1.245", "1.255", "-1.245", "-1.255"], "places": 2, "expected": ["1.24", "1.26", "-1.24", "-1.26"]},
        {"id": "inequality", "values": [0.0, 0.00009999, 0.0001, -0.0001], "expected": [True, True, False, False]},
        {"id": "singleton", "expect": "PFT pool common/random normalCI; tau2/I2/p/PI NA, tau2_calc0; legacy CP pooledCI; both never omitted"},
        {"id": "rank_deficient", "expect": "Fixed duplicate-column model explicit not_estimable, all identities and requestedcolumns retained; no removed coefficient, source-port limitation disclosed"},
        {"id": "saturated_country", "expect": "k=p ->not enough residual observations/tau not estimable, no metadata deletion/relabeling"},
        {"id": "Miller_outside", "expect": "Below exact source minimum0/above maximum1; negative interior radicand NA without empirical epsilon clipping"},
        {"id": "nonconvergence", "expect": "Original REML iteration101 causesfailure with retainedtrace; no replacement solver"}
    ]
