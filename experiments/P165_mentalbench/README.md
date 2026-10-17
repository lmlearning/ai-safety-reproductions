# P165: When Can We Trust LLMs in Mental Health? Large-Scale Benchmarks for Reliable LLM Evaluation

**Outcome: Qualified near success — material exceptions.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[arXiv](https://arxiv.org/abs/2510.19032) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

# When Can We Trust LLMs in Mental Health? Large-Scale Benchmarks for Reliable LLM Evaluation

Qualified near success — material exceptions

**Result.** MentalBench is a qualified near success with material local exceptions. It is not uniformly small-error or an all-table success.

## What was reproduced

All 1,000 conversations, ten response sources, seven attributes and four judges remain. All 28 judge/attribute analyses, original model exclusions, means, paired masks, agreement/bias/MSE statistics and the 1,000-draw conditional bootstrap were recomputed. All 1,150 published diagnostics remain represented, including 254 with unresolved auxiliary producer/label bindings.

## Agreement and differences

All 56 ICC point estimates are within 0.0005; all 112 Table 4 values are within 0.001. All 23 fixed central contrasts agree and the independent implementation passes 69,502 comparisons.

Only 315/324 original central numerical targets pass. Qwen3 Guidance is 2.761953 versus 3.07: error 0.308047 on the 1–5 scale. Eight confidence-limit/width targets have errors up to 0.152486. These are material, not roundoff. Original seeds, inputs, targets and limits were not changed to hide them.

## Issues and omitted work

Human context text has seven duplicate groups and 21 cross-source conflicts. Explicit conversation IDs, not scores or guessed row order, establish joins. Ten valid Human workbook cells are blank in each original analysis CSV; the paper’s CSV missingness was preserved, without filling from workbooks.

The released human reference is aggregated; three individual expert arrays and their aggregation/preprocessing producer were not recovered. No new responses, human judgments or recruitment occurred, and not every auxiliary table producer is established.

## Interpretation

This retrospective paper-level classification reflects close central agreement estimates and 23 scientific contrasts while retaining substantial mean/interval exceptions. The original 315/324 conjunction remains failed. It is separate from the eight bounded near cases; excluding it still leaves 20 counted papers.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2510.19032)

- Identified public release: 2025-10-21.
- Retained selection observation: 31 citations, Semantic Scholar. Exact capture time unknown.
- Exact firstS2 capture time unknown. Known-by later retention is not proof of capture as ofOctober10. Earlier repository visibility/title-alias limitations and separate retrospective selection remain explicit.
- Citation values are retained selection evidence, not current counts.


The route was **released mentalbench ratings**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.

## Paper selection

The retained selection observation was **31 citations** from **Semantic Scholar**. The recorded substantive public date was **2025-10-21** (main window). The exact citation-capture time is unknown in the retained evidence; the count is not presented as a current observation. Counts were not refreshed or added across providers. See the programme [selection rules](../../METHODOLOGY.md).

Selection used a separately disclosed retrospective retained-record method. Its exact first Semantic Scholar capture time is unknown; later verified retention does not establish that 31 citations were observed on 10 October 2026. Earlier repository public visibility and title-alias provenance remain unresolved.

## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [mentalbench_core001.py](code/mentalbench_core001.py) — primary_or_independent_scientific_entry
- [mentalbench_entry001.py](code/mentalbench_entry001.py) — primary_or_independent_scientific_entry
- [mentalbench_original_csv001.py](code/mentalbench_original_csv001.py) — local_helper_or_native_execution_support
- [mentalbench_structure001.py](code/mentalbench_structure001.py) — local_helper_or_native_execution_support
- [mentalbench_targets001.py](code/mentalbench_targets001.py) — local_helper_or_native_execution_support
- [audit_entry005.py](code/audit_entry005.py) — local_helper_or_native_execution_support
- [original_reader005.py](code/original_reader005.py) — local_helper_or_native_execution_support
- [semantic_bridge005.py](code/semantic_bridge005.py) — local_helper_or_native_execution_support
- [independent_mentalbench_core001.py](code/independent_mentalbench_core001.py) — local_helper_or_native_execution_support

The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P165_reviewed_source_ROOT929__ROOT_COMPLETE_CLOSED_P165_ANALYSIS___1d0cc830.json](results/P165_reviewed_source_ROOT929__ROOT_COMPLETE_CLOSED_P165_ANALYSIS___1d0cc830.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [independent_audit956__INDEPENDENT_CENTRAL_CONTRASTS005.json](results/independent_audit956__INDEPENDENT_CENTRAL_CONTRASTS005.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays
- [primary955__COMPLETE_ALL1150_DIAGNOSTICS001.json](results/primary955__COMPLETE_ALL1150_DIAGNOSTICS001.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays

- [ROOT_ADOPTED_P165_MENTALBENCH_SOURCE_METHOD_NEAR921.json](evidence/ROOT_ADOPTED_P165_MENTALBENCH_SOURCE_METHOD_NEAR921.json) — Final pinned execution/configuration/audit record
- [COMPLETE_MENTALBENCH_CENTRAL_SOURCE_MAP_AND_PROSPECTIVE_NEAR_PLAN_P092018.json](evidence/COMPLETE_MENTALBENCH_CENTRAL_SOURCE_MAP_AND_PROSPECTIVE_NEAR_PLAN_P092018.json) — Final pinned execution/configuration/audit record
- [ROOT_RETROSPECTIVE_P165_CENTRAL_NEAR_DECISION958.json](evidence/ROOT_RETROSPECTIVE_P165_CENTRAL_NEAR_DECISION958.json) — Final pinned execution/configuration/audit record
- [INDEPENDENT_COMPLETE_P165_WHOLE_CENTRAL_NEAR_RECOMMENDATION_CPU006.json](evidence/INDEPENDENT_COMPLETE_P165_WHOLE_CENTRAL_NEAR_RECOMMENDATION_CPU006.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
