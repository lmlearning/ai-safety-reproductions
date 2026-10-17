# P132: Effectiveness of generative artificial intelligence-based teaching versus traditional teaching methods in medical education: a meta-analysis of randomized controlled trials

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Paper / DOI](https://doi.org/10.1186/s12909-025-07750-2) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### The question

The paper combines randomized teaching studies to ask whether generative-AI approaches change medical learners’ knowledge, practical skills or satisfaction. Different studies use different tests, so their results are converted to a common standardized difference before combination. The pooled estimate summarizes the reported differences; its confidence interval expresses their statistical uncertainty. A wide interval can leave both improvement and no improvement compatible with the evidence.

### What we actually did

We started with every published mean, standard deviation and sample size in the 17 comparisons. We recalculated the standardized effects, eleven pooled summaries, uncertainty, variation between studies and four comparisons between subgroups. All 141 primary comparisons, 79 supporting comparisons and 141 stricter display-precision checks passed. The independent calculation passed 6,859,667 comparisons. The reproduced standardized differences were about 0.27 for knowledge, 0.63 for skills and 1.18 for satisfaction; the knowledge interval includes zero.

### What the result tells us

The published central synthesis is recoverable, not independently confirmed by new teaching experiments. We retained source choices that complicate interpretation: analytic counts differ from initial allocations, some participants appear in both immediate and delayed analyses, and a figure’s direction labels are reversed. We did not reconstruct participant records, screening decisions or the original unrounded analysis project. Reproducing the arithmetic does not establish that AI improves every learning outcome or that overlapping comparisons are independent.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete declared quantitative synthesis of generative-AI teaching versus traditional teaching was reproduced.

## What was reproduced

All 17 mean/SD/N comparisons, three main outcomes, eight subgroups in four families, eleven pools and four between-group tests were retained, with uncertainty, heterogeneity, weights and analytic counts.

## Agreement and differences

All 141 primary comparisons, 79 supporting comparisons and 141 stricter display-precision checks pass; the independent checker passes 6,859,667 comparisons.

Knowledge is g=0.269870, 95% CI [-0.307288, 0.847028]; skill is 0.629524 [0.097532, 1.161517]; satisfaction is 1.183459 [0.497341, 1.869577].

## Issues and omitted work

Allocation counts differ from analytic forest counts. One delayed-cohort count is inferred from published subgroup totals, not participant records. Original geography/duration assignments, a reversed favours axis and reused immediate/delayed participants were retained. The subgroup-independence assumption remains questionable.

Finite rounding sensitivity samples are not rigorous bounds over every unrounded dataset. Original trials, recruitment, teaching interventions, search/screening, GRADE and the unrounded analysis project were not reproduced. This recovers the source synthesis under disclosed assumptions, not universal teaching efficacy. All criteria were fixed before results.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1186/s12909-025-07750-2)

- Identified public release: 2025-08-19.
- Retained selection observation: 47 citations, OpenAlex. Exact capture time unknown.
- The earlier protocol is methods-only, not an earlier empirical findings release.
- Citation values are retained selection evidence, not current counts.

The route was **released synthesis**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_p132_complete007.py](code/audit_p132_complete007.py) — scientific entry
- [run_p132_complete002.py](code/run_p132_complete002.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [original001__ALL_INDEPENDENT_FAILED_COMPARISONS.jsonl](results/original001__ALL_INDEPENDENT_FAILED_COMPARISONS.jsonl) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__AUDIT_STATUS.json](results/original001__AUDIT_STATUS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_COMPLETE_FIXED_LOO_TIMING_CONTROLS.json](results/original001__INDEPENDENT_COMPLETE_FIXED_LOO_TIMING_CONTROLS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_COMPLETE_KNOWLEDGE_FUNNEL_POINTS.json](results/original001__INDEPENDENT_COMPLETE_KNOWLEDGE_FUNNEL_POINTS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_NOMINAL_COMPLETE_ANALYSIS.json](results/original001__INDEPENDENT_NOMINAL_COMPLETE_ANALYSIS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_PRIMARY_GATES.json](results/original001__INDEPENDENT_PRIMARY_GATES.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_SAMPLED_PRECISION_RANGE_SUMMARY.json](results/original001__INDEPENDENT_SAMPLED_PRECISION_RANGE_SUMMARY.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_STRICT_FINAL_GATES.json](results/original001__INDEPENDENT_STRICT_FINAL_GATES.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_SUPPORTING_INTERMEDIATES.json](results/original001__INDEPENDENT_SUPPORTING_INTERMEDIATES.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__OUTPUT_MANIFEST.json](results/original001__OUTPUT_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report001__OUTPUT_MANIFEST.json](results/final_report001__OUTPUT_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report001__SUMMARY_REPORT.md.txt](results/final_report001__SUMMARY_REPORT.md.txt) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P132-final-central-success001.json](evidence/root_review_P132-final-central-success001.json) — compact independent/ROOT success and closure decision
- [ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json](evidence/ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
