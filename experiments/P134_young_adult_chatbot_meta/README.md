# P134: The Effectiveness of AI Chatbots in Alleviating Mental Distress and Promoting Health Behaviors Among Adolescents and Young Adults: Systematic Review and Meta-Analysis

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Paper / DOI](https://doi.org/10.2196/79850) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### What the original authors studied

The original authors asked what earlier studies suggest about chatbot interventions for adolescents and young adults, including distress, emotions, wellbeing and health behaviours. They combined multiple studies because any one study may be small or measure a different outcome. Most included chatbots are rule-based or retrieve prepared material; only three use generative AI. The findings should therefore not be read as a test of every modern language-model chatbot.

### What the reproduction programme checked

The reproduction programme used all 145 released effect rows, including 88 comparisons described by means, standard deviations and sample sizes. Rows can recur across outcomes, so they are not 145 independent trials. The reproduction code recomputed all eleven central outcome summaries, their confidence intervals, study counts and statistical directions. All 337 central comparisons and 51,910 independent checks passed. Overall mental distress reproduced as a standardized difference of about −0.35, with an interval from −0.46 to −0.24; negative values indicate lower distress under the source’s coding.

### What was reproduced and what it means

The complete declared central synthesis is recoverable from public summaries. Eight supporting numerical displays still disagree, and some subgroup assignments, correlations within trials and auxiliary methods are unavailable. The programme documented its source-transcription corrections before calculation. The programme did not repeat recruitment, intervention delivery, study selection or risk-of-bias assessment. Statistical agreement is not an independent demonstration that these interventions are effective, safe or suitable for an individual.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** All eleven central outcome syntheses were reproduced from released summaries.

## What was reproduced

All 145 effect rows, 88 mean/SD/N contrasts and 31 trial-metadata records were retained, including every central pooled estimate, interval, count and significance direction. Repeated outcome rows are not 145 independent trials.

## Agreement and differences

All 337 central comparisons and 51,910 independent checks pass. Overall mental distress is g=-0.350394, 95% CI [-0.456007, -0.244781]; the other ten central families also meet their precision limits.

Eight supporting numerical/display comparisons fail; 324/332 such comparisons agree. Those discrepancies remain failures.

## Issues and omitted work

Ten documented source-transcription corrections were made before calculation; three proposed corrections were rejected. Supporting weights, Q and Z displays do not all reproduce. Exact subgroup assignments, within-trial covariance and trim-and-fill implementation are unavailable.

Most included systems are rule-based or retrieval chatbots; only three use generative AI. Human trials, searching/screening, risk-of-bias/GRADE and unavailable ancillary analyses were not repeated. The statistical reconstruction does not independently confirm treatment efficacy or establish the same result for all modern generative models. No post-result method, scope or tolerance change was made.

## Paper and selection

- [Original paper or public release](https://doi.org/10.2196/79850)

- Identified public release: 2025-06-30.
- Retained selection observation: 44 citations, OpenAlex. Exact capture time unknown.
- Publisher public preprintJune30 predates its later version of record.
- Citation values are retained selection evidence, not current counts.

The route was **released synthesis**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_independent_source_formula_local004.py](code/audit_independent_source_formula_local004.py) — scientific entry
- [run_complete_central003.py](code/run_complete_central003.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [original001__INDEPENDENT_ALL337_PRIMARY_CHECKS.json](results/original001__INDEPENDENT_ALL337_PRIMARY_CHECKS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_ALL_ORIGINAL_COMPUTATIONS.json](results/original001__INDEPENDENT_ALL_ORIGINAL_COMPUTATIONS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__INDEPENDENT_ALL_SUPPORTING_SOURCE_COMPARISONS.json](results/original001__INDEPENDENT_ALL_SUPPORTING_SOURCE_COMPARISONS.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__OUTPUT_MANIFEST.json](results/original001__OUTPUT_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [original001__SUMMARY.json](results/original001__SUMMARY.json) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__ALL336_SUPPORTING_COMPARISONS.csv](results/final_report002__ALL336_SUPPORTING_COMPARISONS.csv) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__ALL337_CENTRAL_GATES.csv](results/final_report002__ALL337_CENTRAL_GATES.csv) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__FINAL_READABILITY_AND_FAILURE_HISTORY_SUPPLEMENT003.json](results/final_report002__FINAL_READABILITY_AND_FAILURE_HISTORY_SUPPLEMENT003.json) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__REPORT.json](results/final_report002__REPORT.json) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__REPORT.md.txt](results/final_report002__REPORT.md.txt) — successful original run/audit product, target comparison, figure or hash manifest
- [final_report002__SUMMARY_REPORT.md.txt](results/final_report002__SUMMARY_REPORT.md.txt) — successful original run/audit product, target comparison, figure or hash manifest
- [original002__ALL337_PRIMARY_CHECKS.json](results/original002__ALL337_PRIMARY_CHECKS.json) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P134-final-central-success001.json](evidence/root_review_P134-final-central-success001.json) — compact independent/ROOT success and closure decision
- [ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json](evidence/ALL_SIX_EARLIEST_RELEASE_PROPOSED_DISPOSITIONS001.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
