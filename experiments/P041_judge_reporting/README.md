# P041: How to Correctly Report LLM-as-a-Judge Evaluations

**Outcome: Strict central reproduction.** This is a central-result reproduction; whole-paper reproduction is not claimed.

[arXiv](https://arxiv.org/abs/2511.21140) · [Source and acquisition records](INPUTS.json) · [Programme overview](../../README.md)

## Study in plain language

### The question

An AI model is often evaluated by asking another model to mark its answers as correct or incorrect. That judge can make mistakes too. This paper studies how to estimate the first model's true accuracy, and the uncertainty around it, when the judge is imperfect. It also asks how a limited budget of trusted calibration labels should be allocated.

### What we actually did

We generated artificial correct/incorrect answers and judge decisions with known error rates. Because the true accuracy is known in a simulation, we can check whether a reported uncertainty interval actually contains it across repeated trials. We varied true accuracy across all 21 published settings, recalculated the main figure's coverage and interval-width curves, and checked the authors' original-seed example. We compared the uncorrected judge estimate with the paper's corrections and calibration-allocation rules.

### What the result tells us

The main figure's numerical behaviour reproduced within the fixed error bounds. This supports the recoverability of that simulation, rather than demonstrating that a real language-model judge works reliably. The broader appendix did not fully reproduce: eight smaller-budget reference figures duplicate larger-budget figures. The central-only scope was adopted after that failure and then checked with new fixed random seeds. Those limitations remain in the detailed results below.

The sections below give the detailed comparisons and caveats. For common statistical and model terms, see the [reading guide](../../READING_GUIDE.md).

**Result.** The main Figure 4 simulation was reproduced. The full empirical attempt did not pass.

## What was reproduced

Fresh CPU simulations covered all 21 true-accuracy values, all 84 central coverage/interval-length points and all 42 original-seed single-trial comparisons. Each fresh confirmation retained 10,080,000 simulated trials plus 210,000 original scalar trials. Analytic and deterministic calculations were also checked.

## Agreement and differences

Maximum coverage errors were 0.0052334 and 0.0039334, within the fixed 0.020 bound. Maximum interval-length errors were 0.0006102 and 0.0005166, within 0.005. All 42 single-trial comparisons passed their 0.00001 bound.

The full experiment still fails 336/1,344 plotted comparisons: all eight m=200 interval-length references duplicate their m=500 counterparts. Those failures are retained.

## Issues and omitted work

The central-only scope was adopted after the full failure, then confirmed with three fresh fixed seeds. This is a disclosed post-result scope amendment. Source algorithm/code differences and clipping were preserved. Adaptive intervals are not shorter at every accuracy level.

No real LLM judge inference or machine-checked proof was performed. The result recovers an imperfect-judge simulation, not real-world judge reliability or the full appendix.

## Paper and selection

- [Original paper or public release](https://arxiv.org/abs/2511.21140)

- Identified public release: 2025-11-26.
- Retained selection observation: 31 citations, Semantic Scholar. Exact capture time unknown.
- Original v1; precise citation capture time remains unknown.
- Citation values are retained selection evidence, not current counts.

The route was **fresh simulation**, using local computation without paid services or additional API keys. The code below is the programme's implementation and independent audit tooling for this scope.



## Code and rerunning

Start with [REPRODUCE.md](REPRODUCE.md). It identifies the scientific entry points, dependencies, historical commands and known execution constraints. The following code is included in this folder:

- [audit_reporting.py](code/audit_reporting.py) — scientific entry
- [run_judge_reporting.py](code/run_judge_reporting.py) — scientific entry



The folder also provides [a local artifact tool](reproduce.py), [input acquisition records](INPUTS.json), and [source-to-publication hashes](PROVENANCE.json). The artifact tool can check file integrity or reconstruct the original relative layout; it does not rerun the scientific experiment.

## Results and audit trail

- [P041-central-002__central_amendment.md.txt](results/P041-central-002__central_amendment.md.txt) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__configuration.json](results/P041-central-002__configuration.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__figure2.png](results/P041-central-002__figure2.png) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__figure2_numeric.npz](results/P041-central-002__figure2_numeric.npz) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__figure3.png](results/P041-central-002__figure3.png) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__figure3_numeric.npz](results/P041-central-002__figure3_numeric.npz) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__fixed_formula_checks.json](results/P041-central-002__fixed_formula_checks.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__hashes.json](results/P041-central-002__hashes.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__log.txt](results/P041-central-002__log.txt) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__metrics.json](results/P041-central-002__metrics.json) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__n1000_m200_q0-70_q1-70.png](results/P041-central-002__n1000_m200_q0-70_q1-70.png) — successful original run/audit product, target comparison, figure or hash manifest
- [P041-central-002__n1000_m200_q0-70_q1-90.png](results/P041-central-002__n1000_m200_q0-70_q1-90.png) — successful original run/audit product, target comparison, figure or hash manifest

- [audit_P041-central-002.json](evidence/audit_P041-central-002.json) — compact independent/ROOT success and closure decision

The full included-file index is [PROVENANCE.json](PROVENANCE.json). The [historical report](evidence/HISTORICAL_REPORT.txt) preserves the counted report's original qualifications; old warehouse paths there are historical references rather than public download links. Published copies normalize workstation paths and UTF-8 encoding. Their hashes are recorded separately from the original archive hashes.
