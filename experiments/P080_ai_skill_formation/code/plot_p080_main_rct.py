"""Static P080 presentation from completed immutable outputs; no new inference."""
from pathlib import Path
import hashlib,json,textwrap
from datetime import datetime,timezone
from p080_resource_guard import ResourceGuard
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"papers/P080_ai_skill_formation"
OUT=P/"figures"
RUN=P/"RUN_MAIN_RCT_20261010.json"
SOURCE=P/"ORIGINAL_PUBLISHED_FIGURE_TARGETS_20261010.json"
EXPECTED_RUN="72125b6a1de180f3e486c1b998287da3e0377f3177580cd5dc95686a8332f55f"
EXPECTED_SOURCE="ef783454547a2ba7f368f039f16dfa224a8a1e52c16caeb3b42e5e30ef598347"
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(RUN)==EXPECTED_RUN and sha(SOURCE)==EXPECTED_SOURCE
guard=ResourceGuard(ROOT)
r=json.loads(RUN.read_text(encoding="utf8"))
s=json.loads(SOURCE.read_text(encoding="utf8"))
groups={tuple(g["key"]):g for g in r["groups"]}
targets={(t["metric"],t["category"],t["condition"]):t for t in s["targets"]}
COLORS={"AI":"#0173B2","No AI":"#DE8F05"}
plt.rcParams.update({"font.size":10,"axes.titlesize":12,"axes.labelsize":11,
 "figure.titlesize":16,"axes.spines.top":False,"axes.spines.right":False,
 "pdf.fonttype":42,"savefig.facecolor":"white"})
FOOTER=("Filled circles: fixed reproduction. Open diamonds: original v1 published targets. "
 "Group intervals show one fixed 1000-draw percentile-bootstrap replay. Historical source endpoints passed "
 "the prospectively fixed familywise order-rank/DKW Monte Carlo gates; acceptance envelopes are not drawn as sampling CIs.")
def finish(fig,title,extra=""):
    fig.suptitle(title,y=.98,fontweight="bold")
    handles=[
      Line2D([],[],color=COLORS["AI"],marker="o",linestyle="none",label="AI"),
      Line2D([],[],color=COLORS["No AI"],marker="o",linestyle="none",label="No AI"),
      Line2D([],[],color="#444444",marker="o",linestyle="none",label="Reproduction"),
      Line2D([],[],color="#444444",marker="D",markerfacecolor="white",
             linestyle="none",label="Original v1")]
    fig.legend(handles=handles,ncol=4,loc="lower center",bbox_to_anchor=(.5,.125),
               frameon=False,fontsize=10)
    note=FOOTER+(" "+extra if extra else "")
    wrapped="\n".join(textwrap.wrap(note,width=157))
    fig.text(.04,.035,wrapped,fontsize=8.2,ha="left",va="bottom",color="#333333")
    fig.subplots_adjust(top=.85,bottom=.27,left=.075,right=.975,wspace=.32)
def interval(ax,x,mean,ci,color,source=False):
    lo,hi=ci
    assert lo<=mean<=hi
    ax.errorbar(x,mean,yerr=[[mean-lo],[hi-mean]],fmt="D" if source else "o",
      color=color,ecolor=color,markerfacecolor="white" if source else color,
      markeredgewidth=1.3,markersize=6 if source else 6.5,
      capsize=3,linewidth=1.1 if source else 1.7,alpha=.72 if source else 1.0,zorder=3)
def group_panel(ax,metric,categories,limits,ylabel,title):
    main=metric.startswith("main_")
    for i,category in enumerate(categories):
      for j,condition in enumerate(["AI","No AI"]):
        key=(metric,category,condition)
        group,target=groups[key],targets[key]
        center=j if main else i+(-.17 if j==0 else .17)
        op_ci=group["replay_ci95"]
        orig_ci=[target["ci95_low"],target["ci95_high"]]
        if min(op_ci+orig_ci)<limits[0] or max(op_ci+orig_ci)>limits[1]:
            raise ValueError("Presentation axis would clip an original interval")
        interval(ax,center-.035,group["mean"],op_ci,COLORS[condition])
        interval(ax,center+.035,target["mean"],orig_ci,COLORS[condition],True)
    ax.set_ylim(*limits)
    if main:
        ax.set_xticks([0,1],["AI","No AI"])
        ax.set_xlim(-.5,1.5)
    else:
        labels={"CodeReading":"Code reading","Warm Up":"Warm-up",
                "Trio Task":"Trio task","Post Task Quiz":"Post-task quiz",
                "Task1":"Task 1","Task2":"Task 2"}
        ax.set_xticks(list(range(len(categories))),[labels.get(c,c) for c in categories])
        ax.set_xlim(-.5,len(categories)-.5)
    ax.set_ylabel(ylabel);ax.set_title(title,pad=12)
    ax.yaxis.grid(True,color="#e4e4e4",linewidth=.8)
    ax.set_axisbelow(True)

OUT.mkdir(parents=True,exist_ok=True)
paths=[]
combined=OUT/"P080_all_five_original_figure_groups.pdf"
if combined.exists():raise ValueError("Refuse overwriting an existing presentation")
with PdfPages(combined,metadata={"Title":"P080 complete primary RCT reproduction",
                               "Author":"Independent source-faithful reproduction"}) as pdf:
    figures=[]
    fig,axes=plt.subplots(1,3,figsize=(13,5.4))
    group_panel(axes[0],"main_TaskTime",["all"],(0,35),"Minutes","Task completion time")
    group_panel(axes[1],"main_QuizScorePercent",["all"],(0,100),"Quiz score (%)","Quiz performance")
    ax=axes[2]
    for i,metric in enumerate(["TaskTime","QuizScore"]):
      fitted=r["regressions"]["standardized_"+metric]
      target=targets["main_effect_total_SD",metric,"No AI minus AI"]
      interval(ax,i-.035,fitted["coef"][1],fitted["ci95"][1],"#444444")
      interval(ax,i+.035,target["mean"],[target["ci95_low"],target["ci95_high"]],"#444444",True)
    ax.axhline(0,color="#777777",linestyle="--",linewidth=1)
    ax.set_xticks([0,1],["Task time","Quiz score"]);ax.set_xlim(-.5,1.5);ax.set_ylim(-.5,1.5)
    ax.set_ylabel("Effect / total-sample SD");ax.set_title("No AI minus AI",pad=12)
    ax.yaxis.grid(True,color="#e4e4e4",linewidth=.8);ax.set_axisbelow(True)
    finish(fig,"P080 / original Figure 6: complete primary RCT (N=52)",
           "The effect panel uses exact conventional OLS confidence intervals; total-sample SD differs from pooled Cohen d.")
    figures.append(("P080_Figure6_primary_RCT",fig))
    fig,axes=plt.subplots(1,2,figsize=(12,5.4))
    years=["1-3 years","4-6 years","7+ years"]
    group_panel(axes[0],"experience_TaskTime",years,(0,35),"Minutes","Task time by coding experience")
    group_panel(axes[1],"experience_QuizScorePercent",years,(0,100),"Quiz score (%)","Quiz score by coding experience")
    finish(fig,"P080 / original Figure 7: all experience strata",
           "Original AI / No-AI stratum sizes: 2/2, 10/9 and14/15. No strata excluded.")
    figures.append(("P080_Figure7_experience",fig))
    fig,ax=plt.subplots(figsize=(12,5.4))
    group_panel(ax,"subarea_percent",["Task1","Task2","Conceptual","Debugging","CodeReading"],
                (0,100),"Subarea score (%)","All original task and question subareas")
    finish(fig,"P080 / original Figure 8: all five original subareas",
           "Original integer truncation and overlapping Q3 assignment are preserved; fractional diagnostics remain supporting only.")
    figures.append(("P080_Figure8_subareas",fig))
    fig,ax=plt.subplots(figsize=(10,5.4))
    group_panel(ax,"self_report",["Learning","Enjoyment"],(1,7),"Rating (1 to 7)",
                "Learning and enjoyment")
    finish(fig,"P080 / original Figure 9: all self-reported outcomes")
    figures.append(("P080_Figure9_self_reports",fig))
    fig,ax=plt.subplots(figsize=(11,5.4))
    group_panel(ax,"difficulty",["Warm Up","Trio Task","Post Task Quiz"],(1,5),
                "Effort rating (1 to 5)","All original task-stage effort ratings")
    finish(fig,"P080 / original Figure 10: all task-stage difficulty outcomes",
           "The original effort mapping and actual released CSV aliases were fixed before outcomes.")
    figures.append(("P080_Figure10_difficulty",fig))
    for name,fig in figures:
      guard.check()
      path=OUT/(name+".png")
      if path.exists():raise ValueError("Refuse overwriting an existing presentation")
      fig.savefig(path,dpi=220)
      pdf.savefig(fig)
      paths.append(path)
      plt.close(fig)
      print(str(path),flush=True)
paths.append(combined)
guard.check()
assert sha(RUN)==EXPECTED_RUN and sha(SOURCE)==EXPECTED_SOURCE
record={"paper_id":"P080","created_UTC":datetime.now(timezone.utc).isoformat(),
 "purpose":"Presentation from completed immutable outputs only; no statistical rerun or gate change.",
 "input_hashes":{"run":EXPECTED_RUN,"original_source_targets":EXPECTED_SOURCE},
 "CIs":"Fixed1000-draw replay intervals alongside original published endpoints; exact regression intervals for effect panel. Monte Carlo acceptance envelopes not plotted as recreated publication CIs.",
 "resource":guard.summary(),"files":[
 {"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)}
 for p in paths+[Path(__file__)] ]}
(P/"PLOT_PRESENTATION_PROVENANCE_20261010.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf8")
provenance_path=P/"RESULTS_PROVENANCE_20261010.json"
provenance=json.loads(provenance_path.read_text(encoding="utf8"))
for entry in record["files"]:
    provenance["files"].append(entry)
plot_record=P/"PLOT_PRESENTATION_PROVENANCE_20261010.json"
provenance["files"].append({"path":plot_record.relative_to(ROOT).as_posix(),
                           "bytes":plot_record.stat().st_size,"sha256":sha(plot_record)})
provenance["presentation_generated_after_completed_statistics"]=True
provenance_path.write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf8")
print("plot_code_sha256",sha(__file__))
print("plot_presentation_provenance_sha256",sha(plot_record))
print("results_provenance_sha256",sha(provenance_path))
