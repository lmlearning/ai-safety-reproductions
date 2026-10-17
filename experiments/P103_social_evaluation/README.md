# P103: Evidence of a social evaluation penalty for using AI

**Outcome: Near success.** This is a central-result reproduction; whole-paper reproduction is not claimed.

**Interpreting non-reproduction.** A failed comparison or unmatched result means that this reproduction programme did not recover that result within its stated scope and constraints, including the available inputs, methods, software and local resources. It does not establish that the paper or its conclusions are invalid. Work outside the attempted scope was not tested by this programme.

[Paper / DOI](https://doi.org/10.1073/pnas.2426766122) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### What the original authors studied

People may worry that using AI will make them seem lazy, less competent or replaceable. The authors examined that social-evaluation concern. The contribution reproduced here concerns people’s anticipated evaluations in AI-tool versus dashboard-tool situations, not a new experiment measuring how employers or colleagues actually judge AI users.

### What the reproduction programme checked

The reproduction programme reanalysed the authors’ original 500 survey records, retaining the fixed 497-person rating cohort after the original three exclusions for giving the same answer throughout. The reproduction analysis combined 21 question items into six scales, reconstructed the group comparisons and correlations, and included the separate 201-person manipulation check—a check that participants understood the intended situation. It compared every one of the 108 targets. A separately written reproduction auditor independently reconstructed the calculations; missing demographic ages did not remove anyone from the rating analysis.

### What was reproduced and what it means

This is a retrospective bounded near success. Both reproduction routes retain the programme’s original 107/108 result, and all 1,484 independent computational checks pass. Its sole strict mismatch is 0.051949 in a Welch test’s degrees of freedom, a quantity used to calculate uncertainty when groups have unequal variation. The effect estimates, intervals and statistical conclusions remain compatible. A printing explanation is plausible but unproven. The programme’s inability to match this quantity with available inputs, methods and resources does not determine the paper’s validity. The authors’ later actual-perception, hiring, mediation and other study families were outside its frozen scope and not attempted; neither whole-paper reproduction nor a universal social penalty is claimed.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** Complete primary Study 1 anticipation plus its manipulation check is a bounded near success. The programme's sole strict comparison miss is incidental degrees of freedom.

## What was reproduced

All 500 original primary records, the fixed 497-person rating cohort, 21 items/six scales and 201 manipulation-check records were retained. Both implementations evaluated every original target.

## Agreement and differences

Both routes pass 107/108; all 1,484 independent checks pass. All six effects, confidence intervals and p-value claims remain compatible.

Laziness Welch df is 492.748050824 versus 492.8: error 0.051949176 df, about 0.010542%. It is only 0.001949175 df beyond the old 0.050000001 limit. No new fitted tolerance is used.

**Limits of this reproduction:** The strict miss belongs to this programme's comparison of a displayed degrees-of-freedom value. Its historical rounding procedure is unknown, and earlier execution failures belonged to the programme. These outcomes describe what could be recovered within this setup, without establishing that the paper or its conclusions are invalid.

## Issues and omitted work

A printing/double-rounding explanation is unproven. Earlier resource and age-conversion failures in the programme remain recorded. The final source-equivalent repair omits four missing ages only from the demographic mean; all 497 rating participants remain.

No new participants, later actual-perception/hiring/mediation studies or separate norms/Pollfish work were reproduced. This result concerns anticipated evaluation, not a fresh experiment on actual evaluators’ behaviour.

Classification is retrospective. The programme's original strict comparison failure, cohort, estimator and target family are unchanged.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1073/pnas.2426766122)

- Identified public release: 2025-04-23.
- Retained selection observation: 78 citations, Semantic Scholar exact DOI batch. Exact capture time supported.
- Positive OSF public eventApril23 precedes May8 version of record; private project creation is not public findings.
- Citation values are retained selection evidence, not current counts.

The route was **released study1 participant-data reanalysis**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_p103_primary_study1_age_fix_v003.py](code/audit_p103_primary_study1_age_fix_v003.py) — primary_or_independent_scientific_entry
- [run_p103_primary_study1.py](code/run_p103_primary_study1.py) — primary_or_independent_scientific_entry
- [supervise_p103_primary_study1.py](code/supervise_p103_primary_study1.py) — Required transitive local helper, native supervisor or full original reference route
- [supervise_p103_primary_study1_age_fix_v003.py](code/supervise_p103_primary_study1_age_fix_v003.py) — Required transitive local helper, native supervisor or full original reference route



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P103_archived_complete_central_near_assessment_CPU051__ALL108_UNA__d5650336.json](results/P103_archived_complete_central_near_assessment_CPU051__ALL108_UNA__d5650336.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [P103_social_evaluation__REPORT_FINAL_AUDIT003_SUPPLEMENT_20261010.md.txt](results/P103_social_evaluation__REPORT_FINAL_AUDIT003_SUPPLEMENT_20261010.md.txt) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [audit003__AUDIT.json](results/audit003__AUDIT.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [audit003__AUDIT_MANIFEST.json](results/audit003__AUDIT_MANIFEST.json) — Archived numerical result, complete target comparison, audit or run metadata
- [audit003__audit_status.json](results/audit003__audit_status.json) — Archived numerical result, complete target comparison, audit or run metadata
- [audit003__independent_metrics.json](results/audit003__independent_metrics.json) — Archived numerical result, complete target comparison, audit or run metadata
- [run001__RESULT_MANIFEST.json](results/run001__RESULT_MANIFEST.json) — Archived numerical result, complete target comparison, audit or run metadata
- [run001__published_target_gates.json](results/run001__published_target_gates.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays

- [ADDITIVE_P103_RETAINED_ELIGIBILITY_DISTINCTNESS_AND_FROZEN_CENTRA__b1fd21ec.json](evidence/ADDITIVE_P103_RETAINED_ELIGIBILITY_DISTINCTNESS_AND_FROZEN_CENTRA__b1fd21ec.json) — Counted-scope decision, complete vector or independent review

Pass/fail labels and unmatched values in the linked historical records describe this programme's checks under its recorded constraints; they are not judgments on paper validity. Missing or unattempted components were not tested.

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
