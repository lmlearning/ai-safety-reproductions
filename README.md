# AI safety and adjacent research: 21 reproduction studies

This repository documents a local reproduction programme examining recent, well-cited papers in and around AI safety. It contains **21 counted central-result studies: 12 strict reproductions and 9 near successes**. Each paper has an individual report, the scientific code and audit tools used, selected recorded results, and input/provenance records.

The reproduced scopes concern AI evaluation, model reliability, emergent misalignment, human–AI interaction, persuasion, education, health and agent transparency. Most are reanalyses of released observations or published effect estimates. They test whether a paper's central analysis can be recovered; they do not independently repeat participant recruitment, original model training or every experiment in a paper.

## Results at a glance

- **12 strict central reproductions:** all adopted central comparison criteria passed.
- **8 near successes with quantitative error/precision support:** small discrepancies are disclosed alongside the original strict decisions.
- **1 qualified near success (P165):** the central patterns reproduced, with material local mean/interval exceptions. This is not a uniform small-error match. Excluding this case still leaves **20** counted studies.
- **0 whole-paper reproductions.** A central-result success is not a claim that every result or causal interpretation in the paper was independently validated.

The computational routes were **19 released-data/published-effect reanalyses, 1 fresh CPU simulation, and 1 original-checkpoint inference study**. P028 additionally fitted fresh CPU probes to released activations. Computation used local resources, including an AMD Ryzen AI Max+ 395 system, without paid services or additional API keys. Assistant and subagent reasoning supported the work; no private OpenAI research infrastructure or unexposed internal models are claimed.

## The 21 studies

Click a paper title for what was done, the issues encountered, the exact reproduced result and the limits. Citation counts are the programme's **retained initial selection observations**, not current totals. S2 = Semantic Scholar; OA = OpenAlex.

| ID | Paper and individual report | Outcome | Central experiment / analysis | Initial citations | Recorded public date |
|---|---|---|---|---:|---|
| P041 | [How to Correctly Report LLM-as-a-Judge Evaluations](experiments/P041_judge_reporting/README.md) | Strict central | Main Figure 4: 84 simulated coverage/length points and 42 scalar comparisons | 31 (S2) | 2025-11-26 |
| P065 | [AI chatbots versus human healthcare professionals: a systematic review and meta-analysis of empathy in patient care](experiments/P065_empathy_meta_analysis/README.md) | Strict central | Figure 2 pooling of all 13 empathy effect/SE inputs | 79 (S2) | 2025-06-09 |
| P066 | [Human-large language model collaboration in clinical medicine: a systematic review and meta-analysis](experiments/P066_clinical_collaboration_meta/README.md) | Strict central | All seven Figure 2 clinician–LLM collaboration contrasts | 34 (S2) | 2025-11-15 |
| P068 | [Reliability of LLMs as medical assistants for the general public: a randomized preregistered study](experiments/P068_medical_assistant_rct/README.md) | Strict central | 2,400 trial responses, four arms, ten scenarios | 113 (S2) | 2025-04-17 |
| P072 | [The Levers of Political Persuasion with Conversational AI](experiments/P072_levers_persuasion/README.md) | Strict central | Primary policy-attitude analyses across all three studies | 90 (S2) | 2025-07-18 |
| P080 | [How AI Impacts Skill Formation](experiments/P080_ai_skill_formation/README.md) | Strict central | Complete main randomized skill-formation trial analysis | 42 (S2) | 2026-01-28 |
| P120 | [Large language models provide unsafe answers to patient-posed medical questions](experiments/P120_patient_question_safety/README.md) | Strict central | Complete released medical-answer safety analysis | 68 (S2) | 2025-07-25 |
| P134 | [The Effectiveness of AI Chatbots in Alleviating Mental Distress and Promoting Health Behaviors Among Adolescents and Young Adults: Systematic Review and Meta-Analysis](experiments/P134_young_adult_chatbot_meta/README.md) | Strict central | Complete central mental-distress/health-behaviour synthesis | 44 (OA) | 2025-06-30 |
| P132 | [Effectiveness of generative artificial intelligence-based teaching versus traditional teaching methods in medical education: a meta-analysis of randomized controlled trials](experiments/P132_medical_teaching_rct_meta/README.md) | Strict central | Complete central medical-teaching trial meta-analysis | 47 (OA) | 2025-08-19 |
| P135 | [Chatbot-Delivered Interventions for Improving Mental Health Among Young People: A Systematic Review and Meta-Analysis](experiments/P135_young_people_chatbot_meta/README.md) | Strict central | Complete central young-people chatbot meta-analysis | 54 (OA) | 2025-07-15 |
| P133 | [AI literacy and competency in nursing education: preparing students and faculty members for an AI-enabled future-a systematic review and meta-analysis](experiments/P133_nursing_ai_meta/README.md) | Strict central | Complete central nursing AI-literacy synthesis | 56 (OA) | 2025-11-26 |
| P150 | [Racial bias in AI-mediated psychiatric diagnosis and treatment: a qualitative comparison of four large language models](experiments/P150_psychiatric_bias/README.md) | Strict central | Complete central psychiatric diagnosis/treatment bias analysis | 53 (S2) | 2025-06-04 |
| P069 | [The Ideation-Execution Gap: Execution Outcomes of LLM-Generated versus Human Research Ideas](experiments/P069_ideation_execution/README.md) | Near success | 181 reviews, 43 projects, both arms, seven metrics | 62 (S2) | 2025-06-25 |
| P079 | [Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](experiments/P079_developer_productivity/README.md) | Near success | 246 tasks, 16 developers, complete issue-time analysis | 213 (S2) | 2025-07-10 |
| P028 | [Convergent Linear Representations of Emergent Misalignment](experiments/P028_convergent_em/README.md) | Near success | Released-activation probe analysis: nine layers, four contrasts | 71 (S2) | 2025-06-13 |
| P161 | [Can AI Grade Like a Human? Validity, Reliability, and Fairness in University Coursework Assessment](experiments/P161_ai_grading/README.md) | Near success | All 86 central inter-rater agreement targets | 31 (OA) | December 2025 (day unknown) |
| P156 | [The 2025 AI Agent Index](experiments/P156_ai_agent_index/README.md) | Near success | All 30 agents, 45 fields, eight transparency targets | 38 (S2) | 2026-02-19 |
| P165 | [When Can We Trust LLMs in Mental Health? Large-Scale Benchmarks for Reliable LLM Evaluation](experiments/P165_mentalbench/README.md) | Qualified near† | All released central validation data; material local exceptions | 31 (S2) | 2025-10-21 |
| P157 | [Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers](experiments/P157_loop_think_generalize/README.md) | Near success | All nine checkpoints and complete Figure 5 evaluation | 37 (S2) | 2026-04-08 |
| P103 | [Evidence of a social evaluation penalty for using AI](experiments/P103_social_evaluation/README.md) | Near success | Complete primary Study 1 anticipation and manipulation check | 78 (S2) | 2025-04-23 |
| P109 | [Does Generative Artificial Intelligence Improve Students’ Higher-Order Thinking? A Meta-Analysis Based on 29 Experiments and Quasi-Experiments](experiments/P109_higher_order_thinking/README.md) | Near success | All 59 effects and 16 overall synthesis targets | 47 (S2) | 2025-12-05 |

† P165's qualified classification and numerical exceptions are prominent in its report. Near-success classifications do not rewrite the original strict failures.

## How the programme selected and judged papers

The main selection window was **10 October 2025–10 October 2026**, with an explicit “or so” extension **10 April–9 October 2025**. The adopted citation gates were 20 in the main window and 40 in the extension. The final set has 9 main-window and 12 extended-window papers; retained counts range from 31 to 213. Counts from different providers were not combined. Exact citation-capture times are supported for 8 papers and unknown for 13. The dates reflect retained substantive-release evidence with stated limits, rather than an exhaustive proof of the first-ever public appearance.

Plans, inputs, seeds, comparison criteria, complete target families, outcomes and independent computational checks were retained during the programme. Strict and near outcomes refer to each report's declared central scope. Some scopes, methods or near-success decisions were amended after outcomes; those changes and the earlier failures are disclosed. See [methodology and interpretation](METHODOLOGY.md).

## Explore or rerun a study

Each `experiments/Pxxx_.../` folder contains:

- `README.md`: the scientific report, with scope, agreement, issues and omissions.
- `code/`: the original programme-authored scientific runner, auditor and relevant helpers.
- `results/`, `evidence/` and `plans/`: selected numerical records, independent checks and frozen decisions.
- `INPUTS.json` and `PROVENANCE.json`: source acquisition records and original-to-publication file hashes.
- `REPRODUCE.md`, `requirements.txt` and `reproduce.py`: execution notes, dependency information and a small artifact inspection/staging tool.

The scientific code includes historical Windows/runtime/hash guards. The release does not claim every legacy entry point is a newly tested, cross-platform one-command rerun. Source data, third-party author code, model weights and large arrays are acquired from upstream sources; compact aggregate transcriptions are bundled where identified. Consult the individual execution notes before attempting a computation.

To check the integrity of all published files with Python 3.11 or later:

```console
python tools/verify_release.py
```

This command checks file hashes. It does **not** execute or independently reproduce the experiments. See [reproducing and verifying](REPRODUCING.md), [third-party material and licensing](THIRD_PARTY_NOTICES.md), the [machine-readable study list](STUDIES.json), and the [publication validation record](PUBLICATION_CHECKS.json).

## Scope of this release

This is a curated release of the 21 counted studies. It excludes unrelated unsuccessful candidate studies and machine-management records. Within these 21 studies, failed comparisons, repairs, scope amendments and unresolved source discrepancies remain part of the scientific account. The original research archive remains separate and unchanged; this release includes selected evidence rather than every raw array or every operational log.
