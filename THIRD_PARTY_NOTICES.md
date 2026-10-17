# Sources, attribution and licensing

The repository's original reproduction code and associated documentation are offered under the [MIT License](LICENSE), copyright © 2026 Lars Malmqvist, except for the GPL-covered P133 primary program described below and material carrying its own notice. The MIT grant does not replace third-party licences or grant rights in the underlying papers, datasets, model weights or dependency packages.

## P133: retained GPL component and combined primary program

The [P133 statistical core](experiments/P133_nursing_ai_meta/code/candidate_core007.py) declares that its method sources are GPL (>=2) and that the port is distributed under **GPL-3.0-or-later**. That declaration is preserved. The P133 primary program that incorporates this port is distributed under GPL-3.0-or-later; it must not be treated as MIT-only. The included source files in that primary program are:

- [candidate_core007.py](experiments/P133_nursing_ai_meta/code/candidate_core007.py)
- [candidate_pipeline007.py](experiments/P133_nursing_ai_meta/code/candidate_pipeline007.py)
- [candidate_worker009.py](experiments/P133_nursing_ai_meta/code/candidate_worker009.py)
- [synthetic_fixture004.py](experiments/P133_nursing_ai_meta/code/synthetic_fixture004.py)
- [engineering_checks004.py](experiments/P133_nursing_ai_meta/code/engineering_checks004.py)

The separately implemented [P133 auditor](experiments/P133_nursing_ai_meta/code/audit_p133_complete003.py) does not import that primary program and is covered by this repository's MIT licence. A copy of the [GNU GPL version 3](LICENSES/GPL-3.0-or-later.txt) is included for the GPL-covered program. The original source and publication hashes remain in the study's [provenance record](experiments/P133_nursing_ai_meta/PROVENANCE.json).

The port draws on `metafor` (Wolfgang Viechtbauer; retained version 4.8-0) and `meta` (Guido Schwarzer and contributors; retained version 8.2-1). Their retained package declarations specify GPL (>=2). Source references: [pinned metafor package description](https://raw.githubusercontent.com/wviechtb/metafor/82030a0b3b12947066b94bb1d4b45eefd325731a/DESCRIPTION), [archived meta source package](https://cran.r-project.org/src/contrib/Archive/meta/meta_8.2-1.tar.gz). See [P133's licensing note](experiments/P133_nursing_ai_meta/LICENSING.md) for the file scope.

## Papers, inputs and external dependencies

Every study identifies the paper being reproduced and records the source locations and hashes used. The paper authors are not presented as authors or endorsers of this reproduction programme.

Third-party papers, author code, raw participant/model-response datasets, model weights, package binaries and large arrays are generally obtained from their owners rather than bundled. Each study's `INPUTS.json` supplies acquisition records. Those materials retain their own terms; public availability alone is not a licence. For example, P157's required author model source is an external Apache-2.0 dependency, not code relicensed by this repository's MIT grant.

Two retained metadata records also contain third-party text that is explicitly excluded from MIT:

- [P150's source inventory](experiments/P150_psychiatric_bias/plans/PSYCHIATRIC_ALL_PRIMARY_SECTIONS_AND_HISTORY001.json) contains attributed passages from the original article and its CC BY-NC-ND 4.0 notice. The MIT licence does not apply to those passages or override that notice.
- [P157's paper metadata](experiments/P157_loop_think_generalize/evidence/01_grokking.json) contains the original abstract and provider/author licence information. The abstract and provider-supplied material retain those terms.

Dependency names in `requirements.txt` are installation references; the libraries are not vendored here. Scientific titles, quotations and published reference values remain attributed to the cited work. Licence texts and their sources are indexed in [LICENSES/README.md](LICENSES/README.md).
