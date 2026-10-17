# P066: Human-large language model collaboration in clinical medicine: a systematic review and meta-analysis

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

**Interpreting non-reproduction.** A failed comparison or unmatched result means that this reproduction programme did not recover that result within its stated scope and constraints, including the available inputs, methods, software and local resources. It does not establish that the paper or its conclusions are invalid. Work outside the attempted scope was not tested by this programme.

[Paper / DOI](https://doi.org/10.1038/s41746-026-02382-2) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### What the original authors studied

The original authors asked whether clinicians working with a language model perform differently from clinicians working without one. Their central figure combines earlier comparisons of accuracy, broader performance scores and time taken. A combined, or pooled, result is a weighted summary across studies. The surrounding uncertainty interval matters: a positive average alone does not establish a dependable improvement, especially when only a few comparisons are available.

### What the reproduction programme checked

The reproduction programme used all seven comparisons in the authors’ released analysis code. The reproduction analysis independently recalculated study effects, pooled results, confidence and prediction intervals, weights, variation between studies and statistical tests for all three panels. All 63 numerical comparisons and six stated claims passed, as did 290 independent checks. The programme’s initial implementation missed one comparison; applying the source solver convention across every panel resolved it without changing the limits.

### What was reproduced and what it means

The programme reproduced the figure but could not reconcile the available source methods. Following the authors’ code gives a composite improvement of about 4.88 percentage points, interval 0.65 to 9.12. Applying the interval method stated in their prose gives roughly −22.54 to 32.31, including no improvement. Both results remain recorded. This unresolved reconstruction does not determine the paper’s validity. Repeating the trials or review was outside the programme’s scope; the reconstruction neither resolves this gap nor independently demonstrates clinical benefit.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** All three panels of the original Figure 2 clinician–LLM collaboration synthesis were reproduced, with material source-method conflicts disclosed.

## What was reproduced

All seven contrasts, study effects, pooled results, intervals, prediction intervals, weights, heterogeneity, tests and six qualitative claims were recomputed. The target was the original released code and figure, fixed before results.

## Agreement and differences

All 63 numerical comparisons, six claims and 290 independent checks pass after a documented source-defined solver correction. The composite-score estimate is 4.884471 percentage points, 95% CI [0.653519, 9.115423]. Accuracy/time confidence intervals and all three prediction intervals cross their nulls.

**Limits of this reproduction:** The initial mismatch belonged to this programme's implementation and was resolved. The retained code, prose and interval conventions still do not fully identify the authors' historical setup. Those limits describe what the programme could reconstruct; they do not establish that the paper or its conclusions are invalid.

## Issues and omitted work

The code uses a normal composite interval while the prose says HKSJ; HKSJ gives [-22.54430, 32.31324] and changes significance. Accuracy common-effect code also differs from the prose’s Mantel–Haenszel description.

The programme's initial 68/69 comparison result used a different numerical root-solving convention from the source software. Reproducing the documented solver convention across every panel resolved this without changing targets or tolerances. The authors’ exact dependency version remains unknown; a separate audit line-ending repair changed no statistics.

Trials, screening, risk-of-bias/GRADE and unavailable sensitivities were not repeated. Recovering the figure does not resolve its conflict with the Methods section or establish clinical benefit.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1038/s41746-026-02382-2)
- [Original paper or public release](https://zenodo.org/records/17611904)

- Identified public release: 2025-11-15.
- Retained selection observation: 34 citations, Semantic Scholar. Exact capture time supported.
- November 2025 public empirical-code deposit precedes the January 2026 article. Creation time alone is not public-release proof.
- Citation values are retained selection evidence, not current counts.

The route was **released synthesis**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p066_audit_windows_newlines.py](code/p066_audit_windows_newlines.py) — scientific entry
- [p066_central_solver_corrected.py](code/p066_central_solver_corrected.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P066-audit-002__audit.json](results/P066-audit-002__audit.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-audit-002__audit_manifest.json](results/P066-audit-002__audit_manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-audit-002__original_prereg_request_log_snapshot.json](results/P066-audit-002__original_prereg_request_log_snapshot.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__configuration.json](results/P066-central-002__configuration.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__execution.json](results/P066-central-002__execution.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__raw_per_study.json](results/P066-central-002__raw_per_study.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__results.json](results/P066-central-002__results.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__run_manifest.json](results/P066-central-002__run_manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P066-central-002__solver_traces.json](results/P066-central-002__solver_traces.json) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P066-central-002.json](evidence/root_review_P066-central-002.json) — compact independent/ROOT success and closure decision
- [ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json](evidence/ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json) — Final pinned execution/configuration/audit record

Pass/fail labels and unmatched values in the linked historical records describe this programme's checks under its recorded constraints; they are not judgments on paper validity. Missing or unattempted components were not tested.

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
