# P080: How AI Impacts Skill Formation

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[arXiv](https://arxiv.org/abs/2601.20245) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

# How AI Impacts Skill Formation

Strict central reproduction

**Result.** The complete main randomized-trial quantitative contribution was reproduced, including its bootstrap uncertainty.

## What was reproduced

All 52 participants, 26 per arm, and the original 50-person adjusted cohort were retained. Sections 5.2.1–5.2.2/Figures 6–10 cover task time, learning, subareas, experience groups, self-reports and difficulty, including all 36 bootstrap groups and exact regression effects.

## Agreement and differences

All 141 original comparisons and 796 independent checks pass. Means/effects meet the fixed 0.0001 displayed-unit limit; all 72 historical bootstrap endpoints pass the planned Monte Carlo comparison.

Mean quiz scores are 50.000000% with AI versus 65.384615% without AI. The adjusted control-minus-AI gap is 15.322629 percentage points, 95% CI [2.954153, 27.691105]. Task-time differences remain nonsignificant.

## Issues and omitted work

The literal 17% prose is inconsistent with the source numbers: the unadjusted gap is 15.384615 points. Original grade truncation, overlapping subareas and the N=50 adjustment were preserved. A fractional-grade diagnostic changes one exploratory p-value but does not replace the source analysis.

The historical bootstrap seed, qualitative persona/adoption bridge and complete pilot cohorts are unavailable. No new participants or AI assistance were generated. The result does not reproduce the separate qualitative contribution or establish a universal learning effect.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2601.20245)

- Identified public release: 2026-01-28.
- Retained selection observation: 42 citations, Semantic Scholar. Exact capture time supported.
- January 2026 v1 is positive; August 2025 repository public visibility remains unknown. Retained42 also clears the extended threshold40.
- Citation values are retained selection evidence, not current counts.


The route was **released trial data**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.

## Paper selection

The retained selection observation was **42 citations** from **Semantic Scholar**. The recorded substantive public date was **2026-01-28** (main window). An exact capture time is supported in the archived selection records. Counts were not refreshed or added across providers. See the programme [selection rules](../../METHODOLOGY.md).



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_p080_main_rct.py](code/audit_p080_main_rct.py) — scientific entry
- [p080_resource_guard.py](code/p080_resource_guard.py) — statically imported runner/auditor helper
- [plot_p080_main_rct.py](code/plot_p080_main_rct.py) — scientific entry
- [run_p080_main_rct.py](code/run_p080_main_rct.py) — scientific entry

The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [figures__P080_Figure10_difficulty.png](results/figures__P080_Figure10_difficulty.png) — successful original run/audit product, target comparison, figure or hash manifest
- [figures__P080_Figure6_primary_RCT.png](results/figures__P080_Figure6_primary_RCT.png) — successful original run/audit product, target comparison, figure or hash manifest
- [figures__P080_Figure7_experience.png](results/figures__P080_Figure7_experience.png) — successful original run/audit product, target comparison, figure or hash manifest
- [figures__P080_Figure8_subareas.png](results/figures__P080_Figure8_subareas.png) — successful original run/audit product, target comparison, figure or hash manifest
- [figures__P080_Figure9_self_reports.png](results/figures__P080_Figure9_self_reports.png) — successful original run/audit product, target comparison, figure or hash manifest
- [figures__P080_all_five_original_figure_groups.pdf](results/figures__P080_all_five_original_figure_groups.pdf) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P080-central-001.json](evidence/root_review_P080-central-001.json) — compact independent/ROOT success and closure decision
- [ELIGIBILITY_REVIEW_20261010.json](evidence/ELIGIBILITY_REVIEW_20261010.json) — Final pinned execution/configuration/audit record
- [FINAL_FREEZE_MANIFEST_20261010.json](evidence/FINAL_FREEZE_MANIFEST_20261010.json) — frozen successful run/config/input provenance
- [FROZEN_INPUT_MANIFEST_20261010.json](evidence/FROZEN_INPUT_MANIFEST_20261010.json) — frozen successful run/config/input provenance
- [RESULTS_PROVENANCE_20261010.json](evidence/RESULTS_PROVENANCE_20261010.json) — frozen successful run/config/input provenance

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
