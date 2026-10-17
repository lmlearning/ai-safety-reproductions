# Methodology and interpretation

The programme sought recent AI safety and adjacent papers with substantial early citation interest that could be reproduced using available local hardware and no paid services or additional API keys. Citation screening established a practical candidate set; it was not a systematic survey of all AI safety literature or a quality ranking.

## Selection

The frozen main window was 10 October 2025 through 10 October 2026, with a 10 April–9 October 2025 extension for “the last year or so.” Citation gates were 20 and 40 respectively. Retained first observations were used without provider summation or refresh. Of the final21 studies,16 use Semantic Scholar and5 OpenAlex;9 are main-window and12 extended. Exact capture timestamps are supported for8 and unknown for13. A missing capture timestamp is an evidence limitation, not an invented date. Public dates identify retained substantive-release evidence; repository creation/commit dates alone do not prove public visibility.

## What counts as a reproduction

A counted study reconstructs a complete, declared central result family. The claim may be a simulation, released-data statistical analysis or original-checkpoint evaluation. Recomputing a meta-analysis from published input effects can reproduce its central statistical result while leaving screening, constituent trials and unrounded source data unrepeated. Similarly, analysing released trial data does not recruit new participants or independently regenerate the original model responses.

Strict central success means all adopted criteria for that central scope passed. It does not imply that all scope/method decisions were prospective. P041's central scope was adopted after a failed broader attempt and confirmed with new fixed seeds. Other post-outcome corrections and source repairs are disclosed in the individual reports.

At the user's direction, small bounded discrepancies could count as near successes. Eight near studies have explicit quantitative error/precision support. Several classifications were retrospective, and the earlier strict failed comparisons remain failed. The reported bounds are practical reproduction criteria, not universal equivalence guarantees. P165 is a separately qualified central-pattern synthesis with material mean/interval exceptions; it cannot be described as an all-target small-error match. The programme has20 counted studies even when P165 is excluded.

No study claims whole-paper reproduction. Published statements outside the fixed central scope, unreleased software settings, source ambiguities, input rounding, missingness and unsupported mechanisms remain limitations. Agreement with a paper's arithmetic or figure does not independently establish the causal, clinical or policy validity of its conclusions.

## Interpreting unsuccessful or incomplete reproduction

A failed comparison, unmatched display or unrecovered result means that this programme did not reproduce that target within its stated constraints. The result depends on the inputs and source versions available, the reconstruction methods, historical software information, numerical precision and local resources. The cause of a mismatch may remain unknown. These outcomes do not establish that a paper, its methods or its conclusions are invalid.

Reports retain numerical discrepancies, documented differences between source artifacts, programme implementation errors and unresolved questions so that readers can inspect what happened. A documented source difference is reported as a difference between the retained materials, without converting an unsuccessful reconstruction into a verdict on the paper's overall validity. Missing inputs or work outside the attempted scope are untested, rather than failed scientific findings.

Historical pass/fail labels are the programme's comparison outcomes, not grades assigned to the paper. A successful numerical match likewise does not independently validate every aspect of a paper.

## Auditing and provenance

The research retained source versions, configurations, seeds, execution records, comparison outputs and independently implemented mathematical/data checks. Independent here means separately implemented computational checks within the same AI-assisted programme; it does not mean independent human-laboratory replication or blinded review. Historical platform/process evidence differs across studies and is not a universal forensic certificate.

Publication preparation selects reports, programme-authored scientific code, compact results, plans and complete-scope audit records. It leaves the original archive unchanged. PROVENANCE.json distinguishes original bytes/hashes from publication bytes/hashes. Workstation-root strings and UTF-8 formatting are normalized in publication copies; old embedded manifests continue to describe the originals. The release manifest hashes the new copies. No numerical method or success threshold is changed by this packaging.

Third-party source files, raw participant/model-response banks, checkpoints and large arrays are generally acquisition references, not bundled payloads. Selected records can identify archived upstream hashes without making those bytes available in this repository. A release integrity pass establishes that selected files match the published inventory; it does not re-execute the scientific calculations or verify every omitted archive item.
