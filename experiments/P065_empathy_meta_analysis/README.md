# P065: AI chatbots versus human healthcare professionals: a systematic review and meta-analysis of empathy in patient care

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Paper / DOI](https://doi.org/10.1093/bmb/ldaf017) · [arXiv](https://arxiv.org/abs/2602.05628) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### The question

The paper asks whether people rate chatbot responses as more empathetic than responses from healthcare professionals. It brings together results from earlier studies rather than running one new comparison. This is a meta-analysis: each study contributes an estimated difference and a measure of how precisely it was estimated. Combining them can reveal an overall pattern, while also showing how much the studies disagree.

### What we actually did

We started with all 13 published effect estimates and standard errors behind Figure 2. Our code recomputed the weighted overall result, the GPT-3.5 and GPT-4 groups, confidence intervals, study weights, differences between groups and variation between studies. More precise results contribute more weight, while the model also allows studies to differ. We compared every planned value and claim with the publication: all 97 comparisons passed. A separately written calculation passed 189 checks. The overall difference was 0.872 standardized units, matching the reported 0.87.

### What the result tells us

The published central calculation is recoverable from its public inputs. Its confidence interval, about 0.54 to 1.20 standardized units, remains positive, but results vary greatly between studies. This concerns perceived empathy in the studied responses, not better medical decisions or patient outcomes. We did not repeat the literature search, assess the trials afresh or collect new responses and ratings.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete Figure 2 empathy meta-analysis was independently recomputed.

## What was reproduced

All 13 published effect/standard-error inputs, overall and GPT-3.5/GPT-4 subgroup pooling, intervals, heterogeneity, weights, subgroup comparison and four statistical claims were included.

## Agreement and differences

All 97 original comparisons and 189 independent checks pass. Overall standardized mean difference is 0.871882, 95% CI [0.539217, 1.204548], matching 0.87 [0.54, 1.20]. GPT-3.5 is 0.509224 [-0.139022, 1.157470]; GPT-4 is 1.027394 [0.709252, 1.345535]. The between-subgroup difference remains nonsignificant.

## Issues and omitted work

The June 2025 medRxiv release, rather than a later journal date, determines the extended-window selection. Bibliographic author-list differences are documented. Inputs are rounded summaries; overall heterogeneity is approximately 96.9%.

Database searches, study selection, risk-of-bias judgments, constituent experiments and fresh chatbot/human ratings were not repeated. This verifies pooling arithmetic for perceived empathy, not clinical benefit or the validity of the underlying empathy measures. All original comparisons passed without a post-result scope or numerical change.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1093/bmb/ldaf017)
- [Original paper or public release](https://arxiv.org/abs/2602.05628)
- [Original paper or public release](https://doi.org/10.1101/2025.06.09.25329258)

- Identified public release: 2025-06-09.
- Retained selection observation: 79 citations, Semantic Scholar. Exact capture time unknown.
- The June 2025 medRxiv report predates the later journal/arXiv release; no date reset.
- Citation values are retained selection evidence, not current counts.

The route was **released synthesis**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_empathy_meta_analysis.py](code/audit_empathy_meta_analysis.py) — scientific entry
- [run_empathy_meta_analysis.py](code/run_empathy_meta_analysis.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P065-audit-001__audit.json](results/P065-audit-001__audit.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__configuration.json](results/P065-central-001__configuration.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__environment.json](results/P065-central-001__environment.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__execution.json](results/P065-central-001__execution.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__raw_per_study.json](results/P065-central-001__raw_per_study.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__results.json](results/P065-central-001__results.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__run_manifest.json](results/P065-central-001__run_manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P065-central-001__source_manifest.json](results/P065-central-001__source_manifest.json) — successful original run/audit product, target comparison, figure or hash manifest

- [ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json](evidence/ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
