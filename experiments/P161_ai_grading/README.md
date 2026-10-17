# P161: Can AI Grade Like a Human? Validity, Reliability, and Fairness in University Coursework Assessment

**Outcome: Near success.** This is a central-result reproduction; whole-paper reproduction is not claimed.

**Interpreting non-reproduction.** A failed comparison or unmatched result means that this reproduction programme did not recover that result within its stated scope and constraints, including the available inputs, methods, software and local resources. It does not establish that the paper or its conclusions are invalid. Work outside the attempted scope was not tested by this programme.

[Paper / DOI](https://doi.org/10.22521/edupij.2025.19.591) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### What the original authors studied

If an AI and a lecturer both grade an essay, how close are their actual marks? The authors compared ChatGPT-4o with two faculty graders on teacher-education essays about designing a preschool science activity with ScratchJr. Each essay received scores on nine criteria and a total mark.

### What the reproduction programme checked

The reproduction programme used the released 91 grading records from two campuses. For every criterion and the total, its analysis compared all three grader pairs: the two humans with each other, and each human with the AI. The analysis recalculated the paper's intraclass correlation coefficients, or ICCs, which assess agreement in the marks themselves. This is stronger than merely asking whether graders rank students in a similar order. The reproduction retained the original missing-score rule: one criterion uses 90 common records; the other criteria and totals use 91. It checked all 86 selected published agreement values, including duplicates reported in different places.

### What was reproduced and what it means

Every selected value was within 0.010 of the publication, making this a near success; the reproduction programme could not match five values under its older, tighter criteria. Those misses, within the released records and available methods, do not establish that the paper or its findings are invalid. The reported pattern of higher human–human than human–AI agreement also held. The reproduction programme did not have the AI or faculty grade new essays. These results do not show that AI marks are interchangeable with lecturers' marks or reproduce the paper's broader fairness claims.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete central grading-agreement family is a bounded near success, preserving the original 81/86 strict result.

## What was reproduced

All 91 records from both campuses, nine criteria plus totals, three rater pairs and single/average ICCs were retained: 60 Table 5 entries, 20 Table 2 duplicates and six Abstract values. The common-rater cohort is N=90 for criterion 6 and N=91 elsewhere.

## Agreement and differences

All 86 ICC targets are within 0.010; maximum error is 0.005791159. All 20 ordering claims, 135 integrity checks per route and 42,785 independent comparisons pass. Human–human agreement remains higher than human–AI agreement at the tested endpoints. The programme still could not match five targets under its strict criteria.

**Limits of this reproduction:** The strict misses and unmatched supporting results describe this programme's recovery from released grading records, with incomplete producer information for some supporting outputs. Fresh grading was not attempted. These limits do not establish that the paper or its grading-agreement findings are invalid.

## Issues and omitted work

The programme could not establish producers or matching results for all supporting tables/extra records and five conditional figures within the available material. Original cached totals, formulas and missingness masks were retained; alternatives did not replace them. The exact December publication day is unknown in selected metadata.

Fresh grading/recruitment, all noncentral results, causal fairness and grading interchangeability were not reproduced.

The 0.010 near bound was adopted retrospectively from archived results, not presented as original preregistration.

## Paper and selection

- [Original paper or public release](https://doi.org/10.22521/edupij.2025.19.591)

- Identified public release: 2025-12 (exact day UNKNOWN in selected metadata).
- Retained selection observation: 31 citations, OpenAlex. Exact capture time unknown.
- December 2025 supported; exact day unknown. Earlier raw ratings/instruments are not confirmed aggregate findings.
- Citation values are retained selection evidence, not current counts.

The route was **released assessment data**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p092_lean087_resources.py](code/p092_lean087_resources.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_common001.py](code/p157_common001.py) — Required transitive local helper, native supervisor or full original reference route
- [p160_common002.py](code/p160_common002.py) — Required transitive local helper, native supervisor or full original reference route
- [p161_complete_primary005.py](code/p161_complete_primary005.py) — primary_or_independent_scientific_entry
- [p161_render_numeric_svg001.py](code/p161_render_numeric_svg001.py) — Required transitive local helper, native supervisor or full original reference route
- [p161_complete_auditor002.py](code/p161_complete_auditor002.py) — local_helper_or_native_execution_support
- [p161_complete_direct_supervisor003.py](code/p161_complete_direct_supervisor003.py) — local_helper_or_native_execution_support
- [p161_joint_resources002.py](code/p161_joint_resources002.py) — local_helper_or_native_execution_support
- [p161_secondary_entry002.py](code/p161_secondary_entry002.py) — primary_or_independent_scientific_entry
- [p161_secondary_primitives001.py](code/p161_secondary_primitives001.py) — local_helper_or_native_execution_support
- [p161_secondary_xlsx001.py](code/p161_secondary_xlsx001.py) — local_helper_or_native_execution_support



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [environment__ROOT_P161_ARCHIVED_ALL86_BOTH_ROUTES_NEAR_CHECK937.json](results/environment__ROOT_P161_ARCHIVED_ALL86_BOTH_ROUTES_NEAR_CHECK937.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [github_publication_prep__CPU_NEAR9_P161_PRIMARY_COMPACT_AGGREGATE_RESULTS.json](results/github_publication_prep__CPU_NEAR9_P161_PRIMARY_COMPACT_AGGREGATE_RESULTS.json) — Exact primary aggregate-only complete target projection; no underlying participant rows
- [P161_ai_grading__RESULT_REPORT_CURRENT355.txt](results/P161_ai_grading__RESULT_REPORT_CURRENT355.txt) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays

- [INDEPENDENT_COMPLETE_P161_ARCHIVED_ALL86_NEAR_SUPPORT_RSTAT001.json](evidence/INDEPENDENT_COMPLETE_P161_ARCHIVED_ALL86_NEAR_SUPPORT_RSTAT001.json) — Final pinned execution/configuration/audit record
- [ROOT_ADOPTED_P161_ARCHIVED_ALL86_ICC_NEAR_RULE935.json](evidence/ROOT_ADOPTED_P161_ARCHIVED_ALL86_ICC_NEAR_RULE935.json) — Final pinned execution/configuration/audit record

Pass/fail labels and unmatched values in the linked historical records describe this programme's checks under its recorded constraints; they are not judgments on paper validity. Missing or unattempted components were not tested.

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
