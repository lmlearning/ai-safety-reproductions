"""Independent scalar 80-digit audit, without importing the experiment implementation."""
import csv, datetime as dt, decimal, hashlib, json, math, pathlib
from decimal import Decimal as D
decimal.getcontext().prec = 80
ROOT=pathlib.Path(__file__).resolve().parents[1]
PAPER=ROOT/"papers/P065_empathy_meta_analysis"
RUN=PAPER/"runs/P065-central-001"
OUT=PAPER/"audits/P065-audit-001"
OUT.mkdir(parents=True,exist_ok=False)
START=dt.datetime.now(dt.timezone.utc).isoformat()
original=[
 ("Ayers 2023","GPT-3.5","1.9143","0.1225"),
 ("Maida 2024","GPT-3.5","0.15","0.041"),
 ("Reynolds 2024","GPT-3.5","-0.9874","0.27"),
 ("Wan 2024","GPT-3.5","0.7858","0.0446"),
 ("Armbruster 2024","GPT-4","1.4445","0.1591"),
 ("Guo 2024","GPT-4","1.421","0.291"),
 ("He 2024","GPT-4","0.8048","0.0951"),
 ("Meyer 2024","GPT-4","1.4363","0.1589"),
 ("Small 2024","GPT-4","0.48","0.1633"),
 ("Soroudi 2024","GPT-4","0.8297","0.4706"),
 ("Xu 2024","GPT-4","0.2291","0.1456"),
 ("Yonatan-Leus 2024","GPT-4","0.9727","0.1222"),
 ("Yong 2024","GPT-4","2.0757","0.4105")]
critical=D("1.959963984540054235524594430520551527955550077869548398476952647")
def chisq_sf(q,df):
    x=float(q)/2
    if df==1:return math.erfc(math.sqrt(x))
    if df==3:return math.erfc(math.sqrt(x))+2*math.sqrt(x)*math.exp(-x)/math.sqrt(math.pi)
    assert df%2==0
    return math.exp(-x)*sum(x**j/math.factorial(j) for j in range(df//2))
def scalar_fit(records):
    y=[D(r[2]) for r in records]; variances=[D(r[3])**2 for r in records]
    w=[1/v for v in variances]; sumw=sum(w); fixed=sum(a*b for a,b in zip(w,y))/sumw
    # Expanded quadratic form deliberately differs from the runner's residual sum.
    q=sum(a*b*b for a,b in zip(w,y))-(sum(a*b for a,b in zip(w,y))**2)/sumw
    df=len(y)-1; c=sumw-sum(a*a for a in w)/sumw
    tau=max((q-D(df))/c,D(0)); rw=[1/(v+tau) for v in variances]
    mu=sum(a*b for a,b in zip(rw,y))/sum(rw); se=(1/sum(rw)).sqrt(); z=mu/se
    return {"k":len(y),"df":df,"mu":mu,"se":se,"ci_low":mu-critical*se,"ci_high":mu+critical*se,
            "Q":q,"tau2":tau,"C":c,"fixed_mean":fixed,"I2":max((q-D(df))/q,D(0))*100,"Z":z,
            "p":math.erfc(abs(float(z))/math.sqrt(2)),"heterogeneity_p":chisq_sf(q,df)},rw
checks=[]
manifest=json.loads((RUN/"run_manifest.json").read_text(encoding="utf8"))
for name,expected in manifest.items():
    path=RUN/name
    checks.append({"label":"run_integrity."+name,"pass":path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==expected["sha256"]})
source_manifest=json.loads((RUN/"source_manifest.json").read_text(encoding="utf8"))
for name,expected in source_manifest.items():
    path=ROOT/name
    checks.append({"label":"source_integrity."+name,"pass":path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==expected["sha256"]})
with (RUN/"frozen/original_data.csv").open(encoding="utf8",newline="") as f:entered=list(csv.DictReader(f))
checks.append({"label":"input_count_13","pass":len(entered)==len(original)==13})
for r,o in zip(entered,original):
    checks.append({"label":"independent_transcription."+o[0],"pass":tuple(r[k] for k in ["study","model","smd","se"])==o})
fits,weights={},{}
fits["overall"],weights["overall"]=scalar_fit(original)
for group in ["GPT-3.5","GPT-4"]:
    fits[group],weights[group]=scalar_fit([r for r in original if r[1]==group])
fits["overall"]["weight_percent"]=D(100)
for group in ["GPT-3.5","GPT-4"]:
    fits[group]["weight_percent"]=sum(w for r,w in zip(original,weights["overall"]) if r[1]==group)/sum(weights["overall"])*100
# Closed-form two-group interaction statistic, independent of runner's weighted residual form.
q=(fits["GPT-3.5"]["mu"]-fits["GPT-4"]["mu"])**2/(fits["GPT-3.5"]["se"]**2+fits["GPT-4"]["se"]**2)
sub={"Q":q,"df":1,"I2":max((q-1)/q,D(0))*100,"p":chisq_sf(q,1)}
result=json.loads((RUN/"results.json").read_text(encoding="utf8"))
for group,fit in fits.items():
    for key,value in fit.items():
        actual=result["fits"][group][key]; expected=float(value)
        tolerance=1e-14+1e-10*abs(expected)
        checks.append({"label":f"independent_arithmetic.{group}.{key}","actual":actual,"independent":expected,
                       "tolerance":tolerance,"pass":abs(actual-expected)<=tolerance})
for key,value in sub.items():
    expected=float(value);actual=result["subgroup_difference"][key]; tolerance=1e-14+1e-10*abs(expected)
    checks.append({"label":"independent_subgroup."+key,"actual":actual,"independent":expected,"tolerance":tolerance,"pass":abs(actual-expected)<=tolerance})
# Re-evaluate every recorded criterion using the frozen targets, not the experiment's pass fields.
target=json.loads((RUN/"frozen/targets.json").read_text(encoding="utf8"))
rechecked=[]
for group,reference in target["fits"].items():
    for field,published in reference.items():
        if field.endswith("_less_than"):
            ok=float(fits[group][field.removesuffix("_less_than")])<published
        else:ok=abs(float(fits[group][field])-published)<=target["tolerances"].get(field,0)+1e-12
        rechecked.append({"label":f"{group}.{field}","pass":ok})
for field,published in target["subgroup_difference"].items():
    tol=target["tolerances"].get("subgroup_I2" if field=="I2" else field,0)
    rechecked.append({"label":"subgroup_difference."+field,"pass":abs(float(sub[field])-published)<=tol+1e-12})
for r,o,w in zip(entered,original,weights["overall"]):
    vals={"smd":D(o[2]),"individual_ci_low":D(o[2])-critical*D(o[3]),"individual_ci_high":D(o[2])+critical*D(o[3]),
          "normalized_weight_percent":100*w/sum(weights["overall"])}
    for key,col,tol in [("smd","printed_smd","mu"),("individual_ci_low","printed_ci_low","ci_low"),
                        ("individual_ci_high","printed_ci_high","ci_high"),("normalized_weight_percent","printed_weight_percent","weight_percent")]:
        rechecked.append({"label":o[0]+"."+key,"pass":abs(float(vals[key])-float(r[col]))<=target["tolerances"][tol]+1e-12})
claims={"overall_positive_significant":fits["overall"]["ci_low"]>0,"gpt4_positive_significant":fits["GPT-4"]["ci_low"]>0,
        "gpt35_not_significant":fits["GPT-3.5"]["p"]>=.05,"subgroup_difference_not_significant":sub["p"]>=.05}
for label,expected in target["qualitative_claims"].items():rechecked.append({"label":label,"pass":claims[label]==expected})
prob=.5*(1+math.erf(float(fits["overall"]["mu"])/2))
rechecked.append({"label":"probability_superiority","pass":abs(prob-target["probability_superiority"])<=target["tolerances"]["probability_superiority"]})
checks.append({"label":"recorded_check_count","pass":len(rechecked)==result["check_count"]})
for independent,recorded in zip(rechecked,result["comparison_checks"]):
    checks.append({"label":"criterion_rechecked."+independent["label"],"pass":independent["label"]==recorded["label"] and independent["pass"]==recorded["pass"]})
audit={"start_utc":START,"end_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"implementation":"80-digit Decimal scalar; independent literal transcription; standard-library normal and finite chi-square tails",
       "audit_code_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
       "run_manifest_sha256":hashlib.sha256((RUN/"run_manifest.json").read_bytes()).hexdigest(),
       "checks":checks,"all_audit_checks_pass":all(c["pass"] for c in checks),
       "all_original_comparisons_pass":all(c["pass"] for c in rechecked),"failed_audit_checks":[c for c in checks if not c["pass"]],
       "failed_original_comparisons":[c for c in rechecked if not c["pass"]],
       "independent_80_digit_fits":{g:{k:str(v) for k,v in vals.items()} for g,vals in fits.items()},
       "independent_subgroup":{k:str(v) for k,v in sub.items()}}
(OUT/"audit.json").write_text(json.dumps(audit,indent=2),encoding="utf8")
print(json.dumps({"audit_checks":len(checks),"all_audit_checks_pass":audit["all_audit_checks_pass"],
                  "all_original_comparisons_pass":audit["all_original_comparisons_pass"],
                  "failed_audit_checks":audit["failed_audit_checks"],"failed_original_comparisons":audit["failed_original_comparisons"]},indent=2))
