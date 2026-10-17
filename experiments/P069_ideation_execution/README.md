# P069: The Ideation-Execution Gap: Execution Outcomes of LLM-Generated versus Human Research Ideas

**Outcome: Near success.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

# The Ideation-Execution Gap: Execution Outcomes of LLM-Generated versus Human Research Ideas

Bounded near success

**Result.** The complete execution-study review analysis is a bounded near success; the original strict result remains 152/155.

## What was reproduced

All 181 reviews, 43 executed projects, both human/LLM-idea arms, seven metrics, original correlations and exclusion-robustness analyses were retained. Every original target was assessed.

## Agreement and differences

All 21 count targets and 27 qualitative claims agree. The largest error across 107 scalar targets is 0.005, within the adopted 0.010 natural-unit bound. All 1,127 independent checks pass. The same three published mean-gap summaries still fail the old precision rule.

## Issues and omitted work

The producer arithmetic for the mean-gap discrepancies is unresolved. Missing stable reviewer identifiers limit reconstruction of reviewer-level dependence. Canonical text-encoded counts/Boolean flags were decoded without altering statistics.

Fresh idea generation, project execution, recruitment and reviewing were not repeated; unsupported reviewer-level inference was not added. The central comparison and conclusions reproduce within a small numerical error.

This is a retrospective application of the user’s later bounded-error instruction, not an original preregistered strict success or a new experiment. The earlier ideation-only study is distinct from this execution study.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2506.20803)

- Identified public release: 2025-06-25.
- Retained selection observation: 62 citations, Semantic Scholar. Exact capture time unknown.
- Distinct June 2025 execution study, not its 2024 idea-only predecessor or planning registration.
- Citation values are retained selection evidence, not current counts.


The route was **released review data**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.

## Paper selection

The retained selection observation was **62 citations** from **Semantic Scholar**. The recorded substantive public date was **2025-06-25** (extended window). The exact citation-capture time is unknown in the retained evidence; the count is not presented as a current observation. Counts were not refreshed or added across providers. See the programme [selection rules](../../METHODOLOGY.md).



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p069_audit_setup_corrected.py](code/p069_audit_setup_corrected.py) — primary_or_independent_scientific_entry
- [p069_central.py](code/p069_central.py) — primary_or_independent_scientific_entry

The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [environment__ROOT_INDEPENDENT_ARCHIVED_P069_ALL155_BOUND_CHECK917.json](results/environment__ROOT_INDEPENDENT_ARCHIVED_P069_ALL155_BOUND_CHECK917.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [github_publication_prep__CPU_NEAR9_P069_PRIMARY_COMPACT_AGGREGATE_RESULTS.json](results/github_publication_prep__CPU_NEAR9_P069_PRIMARY_COMPACT_AGGREGATE_RESULTS.json) — Exact primary aggregate-only complete target projection; no underlying participant rows

- [INDEPENDENT_COMPLETE_P069_ARCHIVED_NEAR_SUPPORT_REVIEW_RSTAT001.json](evidence/INDEPENDENT_COMPLETE_P069_ARCHIVED_NEAR_SUPPORT_REVIEW_RSTAT001.json) — Final pinned execution/configuration/audit record
- [ROOT_ADOPTED_ARCHIVED_P069_NEAR_SUCCESS_REVIEW_RULE916.json](evidence/ROOT_ADOPTED_ARCHIVED_P069_NEAR_SUCCESS_REVIEW_RULE916.json) — Final pinned execution/configuration/audit record
- [INDEPENDENT_COMPLETE_P069_ARCHIVED_NEAR_SUPPORTED916_CPU001.json](evidence/INDEPENDENT_COMPLETE_P069_ARCHIVED_NEAR_SUPPORTED916_CPU001.json) — Final pinned execution/configuration/audit record
- [REPORT.md.txt](evidence/REPORT.md.txt) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
