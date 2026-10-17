# P157: Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers

**Outcome: Near success.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[arXiv](https://arxiv.org/abs/2604.07822) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### The question

Can a model solve harder reasoning problems by repeating its internal computation, and can extra repetition sometimes hurt? This paper studies recurrent-depth transformers. A recurrence is another pass through a repeated computation block; a checkpoint is a saved trained model. The reproduced benchmark tests reasoning that requires linking multiple facts.

### What we actually did

We evaluated the authors’ nine final checkpoints across all 29,250 held-out examples, up to 40 fixed recurrences, and both original adaptive stopping policies, rules that choose when to stop repeating. Verified completed CPU results for seven checkpoints were retained; the remaining models and adaptive evaluations were completed on GPU. We compared all 3,279 Figure 5 cells. Because a plotted curve does not always reveal an exact number, comparisons retained the ranges supported by the source figure. The whole audit checked predictions, counters, saved outputs and adaptive rules.

### What the result tells us

This is a bounded near success under limits fixed before the final outcome audit. The strict figure-interval rule remains 3,278/3,279: one cell lies 0.015625 percentage points outside its compatible range. All panel and cell near bounds pass, and the published claim interpretations remain compatible. The audit did not independently repeat every pass through the neural network. We did not retrain models or reproduce other seeds and figures; the result does not claim that more computation always helps or establish a universally optimal stopping depth.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The complete Figure 5 checkpoint evaluation is a bounded near success with one tiny source-figure discrepancy.

## What was reproduced

All nine original final checkpoints, 29,250 held-out examples, 40 fixed recurrences and both adaptive policies were evaluated. Retained fixed outputs include 10,530,000 predictions, 14,040 accuracy counters and 2,285,010,000 FP32 logits. All 3,279 figure cells remain.

## Agreement and differences

The old strict interval rule passes 3,278/3,279. The sole miss lies 0.015625 percentage points outside its source-compatible interval union. All panel means meet the prospective two-point bound, every cell the five-point maximum, and all four source-claim interpretations remain compatible.

The conservative difference to any compatible source ordinate is at most 0.745833333 percentage points. This describes figure uncertainty; it is distinct from the 0.015625-point distance outside the interval. Unreleased author accuracies were not recovered.

## Issues and omitted work

Seven verified complete CPU products were reused; full r8/r_dyn and both adaptive policies were completed on GPU. Partial r8 was excluded. Earlier stops/repairs remain archived. The whole audit checks predictions, logits, counters and adaptive rules but does not repeat every neural forward pass.

Training, other seeds/figures and broad language-model claims are outside scope. No universal monotonicity or optimal-depth claim is added. Near bounds were fixed before these outcomes; the original strict conjunction remains false.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2604.07822)

- Identified public release: 2026-04-08 substantive README; 2026-04-09 paper v1.
- Retained selection observation: 37 citations, Semantic Scholar. Exact capture time unknown.
- Substantive READMEApril8 and paper v1April9; finite earlier-source review is not a global absence proof.
- Citation values are retained selection evidence, not current counts.

The route was **original checkpoint inference**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [p157_closed_near_classifier001.py](code/p157_closed_near_classifier001.py) — Required transitive local helper, native supervisor or full original reference route
- [p092_lean087_resources.py](code/p092_lean087_resources.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_common001.py](code/p157_common001.py) — local_helper_or_native_execution_support
- [p157_audit002.py](code/p157_audit002.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_data002.py](code/p157_data002.py) — local_helper_or_native_execution_support
- [p157_models002.py](code/p157_models002.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_phase002.py](code/p157_phase002.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_science002.py](code/p157_science002.py) — Required transitive local helper, native supervisor or full original reference route
- [p157_gpu_audit006.py](code/p157_gpu_audit006.py) — local_helper_or_native_execution_support
- [p157_gpu_contract006.py](code/p157_gpu_contract006.py) — local_helper_or_native_execution_support
- [p157_gpu_models006.py](code/p157_gpu_models006.py) — primary_or_independent_scientific_entry
- [p157_gpu_phase006.py](code/p157_gpu_phase006.py) — local_helper_or_native_execution_support
- [p157_gpu_science006.py](code/p157_gpu_science006.py) — primary_or_independent_scientific_entry
- [p157_gpu_audit006__dffbe654.py](code/p157_gpu_audit006__dffbe654.py) — local_helper_or_native_execution_support
- [p157_gpu_contract007.py](code/p157_gpu_contract007.py) — local_helper_or_native_execution_support
- [p157_gpu_models006__36b96fd2.py](code/p157_gpu_models006__36b96fd2.py) — local_helper_or_native_execution_support
- [p157_gpu_phase007.py](code/p157_gpu_phase007.py) — local_helper_or_native_execution_support
- [p157_gpu_science007.py](code/p157_gpu_science007.py) — local_helper_or_native_execution_support



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [near915002__COMPLETE_ALL3279_ALL14040_NEAR_BOUND_CANDIDATE001.json](results/near915002__COMPLETE_ALL3279_ALL14040_NEAR_BOUND_CANDIDATE001.json) — Complete aggregate target/error/audit ledger; exclude underlying participant rows, predictions, logits and bootstrap arrays

- [EXACT_PLOT_VERSION_AND_PUBLIC_CHRONOLOGY_SOURCES009.json](evidence/EXACT_PLOT_VERSION_AND_PUBLIC_CHRONOLOGY_SOURCES009.json) — Final pinned execution/configuration/audit record
- [01_grokking.json](evidence/01_grokking.json) — Final pinned execution/configuration/audit record
- [INDEPENDENT_COMPLETE_CLOSED_P157_C1_C4_COMPATIBILITY_RSTAT001.json](evidence/INDEPENDENT_COMPLETE_CLOSED_P157_C1_C4_COMPATIBILITY_RSTAT001.json) — Final pinned execution/configuration/audit record
- [ROOT_COMPLETE_CURRENT_GPU006_FULL_NATIVE_AND_PRODUCTS_ACCEPTANCE997.json](evidence/ROOT_COMPLETE_CURRENT_GPU006_FULL_NATIVE_AND_PRODUCTS_ACCEPTANCE997.json) — Final pinned execution/configuration/audit record
- [INDEPENDENT_COMPLETE_CLOSED_P157_AUDIT007_SCOPE_NATIVE_PRODUCTS_P092042.json](evidence/INDEPENDENT_COMPLETE_CLOSED_P157_AUDIT007_SCOPE_NATIVE_PRODUCTS_P092042.json) — Final pinned execution/configuration/audit record
- [ROOT_CLOSED_ALL9_FIXED_AND_BOTH_ADAPTIVE_WHOLE_INPUT_QUALIFICATION1011.json](evidence/ROOT_CLOSED_ALL9_FIXED_AND_BOTH_ADAPTIVE_WHOLE_INPUT_QUALIFICATION1011.json) — Final pinned execution/configuration/audit record
- [ROOT_ACCEPTED_COMPLETE_C1_C4_SOURCE_BOUND_COMPATIBILITY1012.json](evidence/ROOT_ACCEPTED_COMPLETE_C1_C4_SOURCE_BOUND_COMPATIBILITY1012.json) — Final pinned execution/configuration/audit record
- [ROOT_ACTUAL_P157_AUDIT007_EXTERNAL_TOOL_NATIVE_AND_PRODUCTS_CLOSURE1010.json](evidence/ROOT_ACTUAL_P157_AUDIT007_EXTERNAL_TOOL_NATIVE_AND_PRODUCTS_CLOSURE1010.json) — Final pinned execution/configuration/audit record

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
