"""Predeclared engineering-only checks. Written prospectively, never run in preparation."""
from decimal import Decimal, ROUND_HALF_EVEN
import math

def engineering_checks(core, pipeline, rows, result, guard):
    checks = []
    def record(ident, good, observed=None, expected=None):
        checks.append({"id": ident, "passed": bool(good), "observed": observed, "expected": expected, "scientific_credit": False})
    for value, expected in [("1.245","1.24"),("1.255","1.26"),("-1.245","-1.24"),("-1.255","-1.26")]:
        got = format(Decimal(value).quantize(Decimal(".01"),rounding=ROUND_HALF_EVEN),".2f")
        record("half_even_"+value,got==expected,got,expected)
    for value, expected in [(0.0,True),(.00009999,True),(.0001,False),(-.0001,False)]:
        got = 0 <= value < .0001
        record("strict_inequality_"+str(value),got==expected,got,expected)
    fake = {"id":"edge.singleton","canonical_index":1,"events":11,"N":37,"year":2013,"family":"awareness","forest_row":1,"group":"students","country_B":"FAKE_A","country_Figure2":"FAKE_A"}
    singleton = core.pool([fake],"PFT","REML",guard=guard)
    record("singleton_no_deletion",singleton["status"]=="ok" and singleton["input_ids"]==[fake["id"]])
    record("singleton_heterogeneity_NA",singleton.get("tau2") is None and singleton.get("I2_pct") is None and singleton.get("heterogeneity_p") is None and singleton.get("Q")==0 and singleton.get("Q_df")==0)
    record("singleton_PI_NA",singleton.get("prediction",{}).get("low") is None and singleton.get("prediction",{}).get("high") is None)
    legacy = core.pool([fake],"PRAW","DL",guard=guard,legacy=True)
    cp = core.cp_interval(11,37)
    record("legacy_singleton_CP",legacy["status"]=="ok" and legacy["random"]["low"]==cp[0] and legacy["random"]["high"]==cp[1] and legacy["Q"] is None)
    homogeneous = [dict(fake,id="edge.homogeneous."+str(i),canonical_index=i+1) for i in range(4)]
    for scale in ("PFT","PAS","PLOGIT","PRAW"):
        for tau in ("REML","DL"):
            out = core.pool(homogeneous,scale,tau,guard=guard)
            record("homogeneous_"+scale+"_"+tau,out["status"]=="ok" and out["Q"]==0 and out["tau2"]==0 and out["I2_pct"]==0,out.get("tau2"),0)
    boundaries = [dict(fake,id="edge.zero",events=0),dict(fake,id="edge.all",events=37,canonical_index=2)]
    for index,row in enumerate(boundaries):
        cp = core.cp_interval(row["events"],row["N"])
        record("CP_boundary_"+str(index),cp[index]==float(index),cp[index],index)
        for scale in ("PFT","PAS","PLOGIT"):
            y,v,inc=core.effects([row],scale)
            record("finite_boundary_"+str(index)+"_"+scale,math.isfinite(float(y[0])) and float(v[0])>0)
        raw=core.pool([row],"PRAW","DL",guard=guard,legacy=True)
        record("legacy_boundary_explicit_failure_"+str(index),raw["status"]=="not_estimable" and raw["input_ids"]==[row["id"]])
    duplicate = core.fit_model(homogeneous,"PFT","REML",[[1,1] for r in homogeneous],["intercept","duplicate"],guard)
    record("fixed_rank_failure",duplicate["status"]=="not_estimable" and duplicate["columns"]==["intercept","duplicate"] and len(duplicate["input_ids"])==4)
    saturated = core.fit_model(homogeneous,"PFT","REML",core.np.eye(4),["one","two","three","four"],guard)
    record("saturated_failure",saturated["status"]=="not_estimable" and len(saturated["input_ids"])==4)
    size=37.0
    low=.5*math.asin(math.sqrt(1/(size+1)))
    high=.5*(math.asin(math.sqrt(size/(size+1)))+math.pi/2)
    record("Miller_below_min",core.inverse_effect(low-1e-6,"PFT",size)==0)
    record("Miller_above_max",core.inverse_effect(high+1e-6,"PFT",size)==1)
    census=pipeline.structural_census(result,rows)
    record("complete_six_pipeline_census",len(census["pipelines"])==6)
    for pid in census["pipelines"]:
        f=census["pipelines"][pid]
        record("pipeline_census_"+pid,f=={"full":3,"groups":8,"LOO":43,"simultaneous":3,"univariate":9,"country":6,"Egger":3},f)
    record("all_backsize_views",census["backsize_pool_views"]==270)
    record("all_legacy_nested_LOO",census["legacy_nested_LOO"]==43)
    return {"checks":checks,"all_pass":all(x["passed"] for x in checks),"strict_failures_retained":True,"scope":"Unrelated engineering fixture; final complete independent comparison required; no original target matching/scientific credit"}
