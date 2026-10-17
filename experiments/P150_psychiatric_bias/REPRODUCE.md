# Reproducing P150

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

- [P150_independent_auditor003.py](code/P150_independent_auditor003.py) — scientific entry
- [P150_complete_primary002.py](code/P150_complete_primary002.py) — scientific entry

Third-party Python packages identified in these files: none; the included Python files use the standard library. [requirements.txt](requirements.txt) lists these direct dependencies for inspection, without claiming a newly validated lockfile. Read the recorded configuration/runtime files for the actual versions and seeds used in the reported experiment. Any R packages, author code, hardware-specific PyTorch builds and non-Python dependencies require their original setup.

Historical command / invocation records:

```console
python papers/P150_psychiatric_bias/scripts/P150_complete_primary002.py --config <fixed-original-config.json> --authorization <new-exact-authorization.json>
```

```console
python papers/P150_psychiatric_bias/review/independent_audit_preparation001/P150_independent_auditor003.py --config <fixed-audit-config.json> --authority <new-exact-authority.json> --mode original
```

Known constraints:

- Keep repository-relative layout for __file__-based roots. Preserve input bytes and pinned hashes. Install stated scientific dependencies separately; do not copy original runtime.

- New output namespaces are required. Historical immutable run directories must not be overwritten.

- Authorization/freeze/runtime source checks remain active in immutable runners. Later guarded studies need an explicitly documented portable launch/config adapter; none was implemented or tested by this inventory.

Original frozen guards, root authorizations and software/code hashes are retained as scientific provenance. They have not been disabled by the publication tools. Some legacy runs therefore need an explicitly documented new execution plan/environment and revised provenance bindings before a new run can start. Never report a hash-only verification, a staged workspace, a source inspection or a partial diagnostic as a fresh successful experiment. Use the original reported scope, retain every comparison and disclose any changes made for a new environment.

## Read the recorded outcome

[README.md](README.md) states the result and limitations. [PROVENANCE.json](PROVENANCE.json) inventories every selected source file with original and publication hashes. The scientific outcome is historical evidence; checking its bytes does not independently recompute it. Failed or unmatched results in these records mean that this programme did not recover a target under its stated constraints; they do not establish that the paper or its conclusions are invalid. Unattempted components remain untested.
