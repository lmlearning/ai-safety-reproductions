# P072: The Levers of Political Persuasion with Conversational AI

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Paper / DOI](https://doi.org/10.1126/science.aea3884) · [arXiv](https://arxiv.org/abs/2507.13919) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### The question

What makes an AI conversation persuasive? The original experiments measured people's agreement with policy positions before and after exposure to persuasive material. They varied features such as having a dialogue instead of reading a static argument, personalisation, prompting and how the model had been trained.

### What we actually did

We used the released participant records from all three studies to rebuild the complete selected policy-attitude analysis. For each comparison, the code recreated the original group assignments and exclusions, calculated the changes in reported attitudes, and fitted the same statistical designs used by the source scripts. We then checked the published estimates, uncertainty intervals, tests and participant counts across the selected 93 tables. This included follow-up and robustness analyses; it did not involve generating new persuasive messages or recruiting another sample.

### What the result tells us

All 2,470 selected comparisons reproduced after a documented correction to which source script defined two designs. For example, dialogue-versus-static differences reproduced at about 2.94 and 3.60 percentage points in studies 1 and 3. These are changes in the study's attitude measure, not evidence that the arguments were true, that people changed their real-world behaviour, or that every kind of AI persuasion has the same effect. The paper's separate factual-accuracy and scaling analyses were outside this reproduction.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete declared primary policy-attitude contribution across all three studies was reproduced.

## What was reproduced

Released participant data were used for all 93 selected supplementary tables, 643 rows and 2,470 comparisons: randomized-arm effects, follow-up, dialogue/static contrasts, post-training, personalization, prompts, interactions, attrition and counts. Original missing-outcome filters and robustness estimators were retained.

## Agreement and differences

All 2,470 comparisons and 14,552 independent checks pass. Dialogue-versus-static effects are 2.93890 and 3.60093 percentage points in studies 1 and 3; the pooled information-prompt effect is 2.29300 points. Selected uncertainty, tests and counts also match their fixed precision.

## Issues and omitted work

An intermediate 2,449/2,470 result mapped two study-2 designs to the wrong original script. The source-defined mapping was corrected without changing data, targets or tolerances; earlier serialization failures remain. Original duplicated controls, unclustered inference and code/caption filters were preserved.

New conversations, recruitment and model training were not repeated. Separate Bayesian scale/claim analyses, other scaling-curve syntheses, factual extraction, secondary statistics and private dialogue text are outside this scope. This is the complete selected policy-attitude family, not the full paper or a general claim about all AI persuasion.

## Paper and selection

- [Original paper or public release](https://doi.org/10.1126/science.aea3884)
- [Original paper or public release](https://arxiv.org/abs/2507.13919)

- Identified public release: 2025-07-18.
- Retained selection observation: 90 citations, Semantic Scholar. Exact capture time unknown.
- July 18 is a confirmed public report. Earlier July repository public-push timing remains unknown; located dates remain in the extension.
- Citation values are retained selection evidence, not current counts.

The route was **released experiment data**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p072_audit.py](code/p072_audit.py) — scientific entry
- [p072_central.py](code/p072_central.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P072-audit-001__AUDIT_MANIFEST.json](results/P072-audit-001__AUDIT_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-audit-001__AUDIT_RESULT.json](results/P072-audit-001__AUDIT_RESULT.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-audit-001__audit_checks.json](results/P072-audit-001__audit_checks.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-audit-001__independent_computed_tables.json](results/P072-audit-001__independent_computed_tables.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-audit-001__independent_model_statistics.json](results/P072-audit-001__independent_model_statistics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-audit-001__independent_target_decisions.json](results/P072-audit-001__independent_target_decisions.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__RUN_MANIFEST.json](results/P072-central-003__RUN_MANIFEST.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__analysis_designs.json](results/P072-central-003__analysis_designs.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__attrition_details.json](results/P072-central-003__attrition_details.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__computed_tables.json](results/P072-central-003__computed_tables.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__metrics.json](results/P072-central-003__metrics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P072-central-003__model_statistics.json](results/P072-central-003__model_statistics.json) — successful original run/audit product, target comparison, figure or hash manifest

- [root_review_P072-central-003.json](evidence/root_review_P072-central-003.json) — compact independent/ROOT success and closure decision

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
