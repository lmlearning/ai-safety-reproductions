# P028: Convergent Linear Representations of Emergent Misalignment

**Outcome: Near success.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

# Convergent Linear Representations of Emergent Misalignment

Bounded near success

**Result.** The complete saved-activation probe study is a bounded near success, with all original failed flags preserved.

## What was reproduced

All 897 responses, 55,386 tokens, nine layers, four classifier contrasts, 20 Table 1 metrics, 36 graphical coefficient medians and eight claims remain. The computation includes 800 original-scope fits and 400 prespecified diagnostics.

## Agreement and differences

Maximum metric error is 0.007592365 on the 0–1 scale, within 0.010. All 36 graphical medians meet the unchanged 0.020 bound; maximum error is 0.014542980. All eight claims and 6,083 independent checks pass. The original strict result remains 59/64.

## Issues and omitted work

Two of five old failures were our previously documented graph-transcription errors: medical-panel layers 27/28 are approximately -0.06/-0.03. Correction used the original page; graphical tolerance was not widened. Token-level leakage/dependence and missing response-level independence information remain limitations.

Base-model training, new generation, causal steering/interventions and fresh external model judging were not reproduced. Probe agreement is not proof of a causal misalignment mechanism.

The near classification is retrospective. No data, labels, estimator, seeds or fits were changed for reclassification.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2506.11618)

- Identified public release: 2025-06-13.
- Retained selection observation: 71 citations, Semantic Scholar. Exact capture time unknown.
- Original June 13 v1; related source history retained without a later-version date reset.
- Citation values are retained selection evidence, not current counts.


The route was **released activations + fresh probes**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.

## Paper selection

The retained selection observation was **71 citations** from **Semantic Scholar**. The recorded substantive public date was **2025-06-13** (extended window). The exact citation-capture time is unknown in the retained evidence; the count is not presented as a current observation. Counts were not refreshed or added across providers. See the programme [selection rules](../../METHODOLOGY.md).



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_probe.py](code/audit_probe.py) — primary_or_independent_scientific_entry
- [run_probe.py](code/run_probe.py) — primary_or_independent_scientific_entry

The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P028_near_success_adoption933__ROOT_WHOLE64_NEAR_VECTOR933.json](results/P028_near_success_adoption933__ROOT_WHOLE64_NEAR_VECTOR933.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [P028-central-001__comparison.json](results/P028-central-001__comparison.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [P028-central-001__manifest.json](results/P028-central-001__manifest.json) — Archived numerical result, complete target comparison, audit or run metadata

- [INDEPENDENT_COMPLETE_P028_ARCHIVED_WHOLE_CENTRAL_NEAR_SUPPORT_RSTAT001.json](evidence/INDEPENDENT_COMPLETE_P028_ARCHIVED_WHOLE_CENTRAL_NEAR_SUPPORT_RSTAT001.json) — Final pinned execution/configuration/audit record
- [ROOT_ADOPTED_P028_ARCHIVED_COMPLETE_CENTRAL_NEAR_RULE930.json](evidence/ROOT_ADOPTED_P028_ARCHIVED_COMPLETE_CENTRAL_NEAR_RULE930.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
