# P120: Large language models provide unsafe answers to patient-posed medical questions

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

**Interpreting non-reproduction.** A failed comparison or unmatched result means that this reproduction programme did not recover that result within its stated scope and constraints, including the available inputs, methods, software and local resources. It does not establish that the paper or its conclusions are invalid. Work outside the attempted scope was not tested by this programme.

[Paper / DOI](https://doi.org/10.1038/s41746-026-02428-5) · [arXiv](https://arxiv.org/abs/2507.18905) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### What the original authors studied

The original authors asked how often answers to patient-written medical questions were judged problematic, and whether those judgments differed between four model groups. Their evidence is a saved collection of responses and human ratings, not observations of what happened to patients. Their central analysis counts problematic answers, summarizes quality ratings and examines which kinds of problems and agreements occur across models.

### What the reproduction programme checked

The reproduction programme reanalysed all 888 responses to 222 questions. The reproduction code read the authors’ ratings, reproduced the authors’ label-processing rules, counted problems, calculated means and variation in quality scores, and recomputed every original overall and pairwise comparison. The reproduction passed all 141 published comparisons, with 20,073 independent checks. The reproduced problematic-response rates ranged from about 21.6% for Claude to 43.2% for the pooled Llama group. The programme also retained all issue categories, correlations and questions that received unanimous judgments.

### What was reproduced and what it means

The programme reconstructed the comparison while preserving observable source differences: parts of the authors’ code handle capitalization and trailing spaces differently, and the Llama group mixes two versions. It did not silently change those rules. New responses and physician judgments were outside its scope, not failed collection attempts. The percentages describe archived ratings, not current performance or a probability of patient harm. This limited reconstruction does not independently validate the rating process or determine the paper’s validity.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete four-model comparative analysis of patient-question responses was reproduced from released ratings.

## What was reproduced

All 888 responses to 222 questions and four cohorts were included: problematic-response counts, rating means/SDs, all original omnibus/pairwise tests, 20 issue percentages, correlations and unanimous-question identities.

## Agreement and differences

All 141 original comparisons and 20,073 independent checks pass. Problematic-response rates are 21.621622% for Claude, 27.477477% for Gemini, 31.531532% for GPT-4o and 43.243243% for the pooled Llama cohort. Original quality-rating and between-model tests also reproduce.

**Limits of this reproduction:** All selected comparisons passed. The repaired export issue belonged to the programme, and alternative diagnostic results were not substitutes for the authors' analysis. Unavailable generation details and unattempted fresh ratings limit this reproduction's scope, without determining the validity of the paper.

## Issues and omitted work

The main parser normalizes labels, but correlation/agreement code uses exact spellings. Both were retained; normalization changes unanimous acceptable counts from 80 to 83 in a separate diagnostic. The Llama cohort contains 15 Llama 3.0 and 207 Llama 3.1 responses, without complete historical generation metadata.

An optional-comment null/empty export issue in the programme was repaired without changing scientific output. Paired-test diagnostics can differ from the source’s independent-cohort inference and were not substituted.

No new model responses, physician judgments or question collection occurred. These are reproduced judgments of cached responses, not current model testing or a direct clinical harm rate.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1038/s41746-026-02428-5)
- [Original paper or public release](https://arxiv.org/abs/2507.18905)

- Identified public release: 2025-07-25.
- Retained selection observation: 68 citations, Semantic Scholar. Exact capture time supported.
- Use the July 2025 original preprint, not the later journal date.
- Citation values are retained selection evidence, not current counts.

The route was **released judged responses**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_p120_raw_xml_independent_v004.py](code/audit_p120_raw_xml_independent_v004.py) — scientific entry
- [run_p120_original_quantitative_v004.py](code/run_p120_original_quantitative_v004.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [audit002__AUDIT_MANIFEST.json](results/audit002__AUDIT_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [audit002__AUDIT_SUMMARY.json](results/audit002__AUDIT_SUMMARY.json) — successful original run/audit product, target comparison, figure or hash manifest
- [audit002__independent_all_fixed_diagnostics.json](results/audit002__independent_all_fixed_diagnostics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [audit002__independent_all_original_metrics.json](results/audit002__independent_all_original_metrics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [audit002__independent_mandatory_target_checks.json](results/audit002__independent_mandatory_target_checks.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__RAW_SERIALIZATION_REPAIR_VALIDATION.json](results/run004__RAW_SERIALIZATION_REPAIR_VALIDATION.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__RUN_MANIFEST.json](results/run004__RUN_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__RUN_SUMMARY.json](results/run004__RUN_SUMMARY.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__all_fixed_supporting_diagnostics.json](results/run004__all_fixed_supporting_diagnostics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__all_original_method_details.json](results/run004__all_original_method_details.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__all_original_method_metrics.json](results/run004__all_original_method_metrics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [run004__mandatory_target_checks.json](results/run004__mandatory_target_checks.json) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P120-final-central-success001.json](evidence/root_review_P120-final-central-success001.json) — compact independent/ROOT success and closure decision

Pass/fail labels and unmatched values in the linked historical records describe this programme's checks under its recorded constraints; they are not judgments on paper validity. Missing or unattempted components were not tested.

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
