# Reproducing P161

This directory contains the scientific code used for the reported study, compact results and audit evidence. It is an archival research release, not a claim that all legacy entry points run unchanged on every machine. Publication preparation did not repeat the original experiment or revise its numerical methods.

## Inspect and verify the release

Requires Python 3.11 or later for the publication tools; they use only the standard library. From this folder:

```console
python reproduce.py --verify
python reproduce.py --list-inputs
```

Verification checks published bytes against the release manifest. It is not a statistical audit or a fresh reproduction.

## Obtain the original inputs

[INPUTS.json](INPUTS.json) records archived asset sizes, SHA-256 values and retained source URLs, plus inventory notes for assets outside the original paper directory. Third-party papers, raw participant data, author repositories, model weights and large arrays are obtained from their original owners rather than redistributed here. A public URL alone does not establish a redistribution license.

Where an exact file URL was retained, download one explicitly selected asset with `python reproduce.py --fetch input-001` (replace the ID after inspecting INPUTS.json). Downloads are accepted only if their hashes match. No automatic download of a whole model or dataset occurs. Landing-page-only records need manual acquisition; a changed upstream file must be treated as a different version.

Bundled aggregate transcriptions / reference inputs:

No third-party source data is bundled; see the acquisition records.

## Reconstruct the original relative layout

```console
python reproduce.py --stage workspace
```

Choose a new directory. The tool copies code, included plan/input files and any verified downloads into their original relative locations. Recorded results remain separate so a new run cannot silently overwrite the old outcome. The staging receipt records that no experiment ran. Explicit workstation-root placeholders are relocated; other historical runtime/path dependencies remain visible.

## Scientific entry points and dependencies

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

Third-party Python packages identified in these files: `numpy`, `pandas`, `scipy`, `statsmodels`. [requirements.txt](requirements.txt) lists these direct dependencies for inspection, without claiming a newly validated lockfile. Read the recorded configuration/runtime files for the actual versions and seeds used in the reported experiment. Any R packages, author code, hardware-specific PyTorch builds and non-Python dependencies require their original setup.

Historical command / invocation records:

```console
python -I -S -B -X utf8 papers/P161_ai_grading/review/secondary_independent001/p161_complete_direct_supervisor003.py --control papers/P161_ai_grading/ROOT_SAME349_REPAIR_TRUE_CONTROL353.json
```

source_control_derived_historical_schema_not_new_authority

Known constraints:

- Historical outputs must remain exclusive; use fresh checkout/output configuration.

- Hardcoded {{USER_HOME}} roots, local package-site paths and frozen source/control refs require explicit configuration; never silently remove guards.

- Pure estimator modules are definitions; Windows supervisor also requires P157common/P160allocation/P092resource helpers listed.

- Original exact91-case source-schema/mask can contain individual grades: regenerate locally, do not copy that whole schema blindly.

Original frozen guards, root authorizations and software/code hashes are retained as scientific provenance. They have not been disabled by the publication tools. Some legacy runs therefore need an explicitly documented new execution plan/environment and revised provenance bindings before a new run can start. Never report a hash-only verification, a staged workspace, a source inspection or a partial diagnostic as a fresh successful experiment. Use the original reported scope, retain every comparison and disclose any changes made for a new environment.

## Read the recorded outcome

[README.md](README.md) states the result and limitations. [PROVENANCE.json](PROVENANCE.json) inventories every selected source file with original and publication hashes. The scientific outcome is historical evidence; checking its bytes does not independently recompute it.
