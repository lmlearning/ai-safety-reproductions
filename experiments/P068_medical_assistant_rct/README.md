# P068: Reliability of LLMs as medical assistants for the general public: a randomized preregistered study

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Paper / DOI](https://doi.org/10.1038/s41591-025-04074-y) · [arXiv](https://arxiv.org/abs/2504.18919) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

# Reliability of LLMs as medical assistants for the general public: a randomized preregistered study

Strict central reproduction

**Result.** The complete selected human-trial performance analysis was reproduced from original participant answers and scoring lists.

## What was reproduced

All 2,400 responses from 1,298 participants, four randomized arms and ten scenarios remain included. Answers were independently rescored. The full condition-identification, red-flag, disposition, odds-ratio, uncertainty and acuity family was retained.

## Agreement and differences

All 12,000 scoring comparisons, 103 summary comparisons and 29,318 independent checks pass. Relevant-condition identification is 34.5%, 34.0% and 32.0% in the three LLM-assisted arms versus 47.0% in control; the source-defined corrected comparisons agree. Disposition differences remain nonsignificant.

The historical bootstrap seed is unavailable. A fixed disclosed seed was used with the original 0.02 stochastic endpoint allowance; deterministic comparisons retain separate precision limits.

## Issues and omitted work

The source fuzzy-matching and response-level assumptions were preserved, including participants with multiple responses. An initial serialization failure was repaired without changing scientific methods or targets.

No new recruitment, conversations or model inference occurred. Separate model-only, simulated-user, interaction/precision, trust/demographic and appendix analyses were omitted. This reproduces released trial statistics, not a new clinical deployment test or patient-harm estimate.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1038/s41591-025-04074-y)
- [Original paper or public release](https://arxiv.org/abs/2504.18919)

- Identified public release: 2025-04-17.
- Retained selection observation: 113 citations, Semantic Scholar. Exact capture time supported.
- April 2025 public data/code precede arXiv v1 and the later journal publication.
- Citation values are retained selection evidence, not current counts.


The route was **released trial data**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.

## Paper selection

The retained selection observation was **113 citations** from **Semantic Scholar**. The recorded substantive public date was **2025-04-17** (extended window). An exact capture time is supported in the archived selection records. Counts were not refreshed or added across providers. See the programme [selection rules](../../METHODOLOGY.md).



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p068_audit.py](code/p068_audit.py) — scientific entry
- [p068_central_serialization_corrected.py](code/p068_central_serialization_corrected.py) — scientific entry

The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P068-audit-001__audit.json](results/P068-audit-001__audit.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-audit-001__independent_scores.csv](results/P068-audit-001__independent_scores.csv) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-audit-001__manifest.json](results/P068-audit-001__manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__PREREGISTRATION.json](results/P068-central-002__PREREGISTRATION.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__PREREGISTRATION.md.txt](results/P068-central-002__PREREGISTRATION.md.txt) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__manifest.json](results/P068-central-002__manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__original_row_targets.csv](results/P068-central-002__original_row_targets.csv) — Archived numerical result, complete target comparison, audit or run metadata
- [P068-central-002__results.json](results/P068-central-002__results.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__scores.csv](results/P068-central-002__scores.csv) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__sources_manifest.json](results/P068-central-002__sources_manifest.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P068-central-002__targets.json](results/P068-central-002__targets.json) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P068-central-002.json](evidence/root_review_P068-central-002.json) — compact independent/ROOT success and closure decision

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
