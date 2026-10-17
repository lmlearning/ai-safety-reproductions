# Reproducing and verifying

Start with a study's README.md and REPRODUCE.md. The reported results were completed in the original programme; packaging this release is not a new scientific run.

## Inspect the supplied evidence

Use Python3.11 or later and run `python tools/verify_release.py` from the repository root. It verifies published file sizes/hashes using only the standard library. A study's `python reproduce.py --verify` selects that folder. Neither command repeats an experiment. PUBLICATION_CHECKS.json records structural, syntax, inventory and link validation of the prepared package.

## Acquire inputs

Each INPUTS.json records upstream URLs and archived hashes where retained. No credentials are supplied or required by the publication tools. Some records provide landing pages rather than exact immutable download URLs; these require source-specific manual acquisition. Public accessibility is not treated as permission to redistribute. Source files that change upstream will fail the recorded hash check and must be versioned explicitly rather than silently substituted.

For one explicitly chosen asset with an exact URL, use the study tool's `--fetch INPUT_ID`. It leaves mismatching or incomplete bytes as a .part file and never silently overwrites an existing asset. Large checkpoint/activation downloads are opt-in, not automatic installation steps.

## Stage and execute separately

`python reproduce.py --stage workspace` reconstructs the original relative code/plan/input layout in a new directory and relocates explicit workstation-root placeholders. It does not execute code, fetch missing inputs automatically, copy old result directories into the new run, or disable scientific integrity checks. Read the historical command records and inspect the scientific entry points before execution.

The original programmes include immutable run identifiers, code/input/software hash bindings, Windows resource/affinity measurements, local Python/R package layouts and accelerator assumptions. Some require an explicitly documented new plan/environment to bind a new run. requirements.txt files identify direct Python imports; they are not freshly validated lockfiles. Matching historical Python, R and package versions can matter numerically. The package retains these limitations instead of presenting an untested universal launch command.

Keep a fresh output directory, original source hashes, exact versions, seeds, all target comparisons, errors and exit status for any new run. Report environmental or methodological adaptations explicitly. A partial diagnostic or a hash verification must not be labelled a fresh reproduction of the entire declared central result.
