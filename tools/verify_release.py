"""Verify the published artifact inventory without running an experiment."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def verify(root: Path, selected: str | None = None) -> dict:
    root = root.resolve()
    manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    failures, checked = [], 0
    for row in manifest["files"]:
        if selected and not row["path"].startswith("experiments/" + selected + "/"):
            continue
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root):
            failures.append({"path": row["path"], "error": "outside release"})
            continue
        if not path.is_file():
            failures.append({"path": row["path"], "error": "missing"})
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != row["sha256"] or path.stat().st_size != row["bytes"]:
            failures.append({"path": row["path"], "error": "content differs"})
        checked += 1
    return {"checked_files": checked, "failures": failures, "ok": checked > 0 and not failures,
            "experiment_executed": False,
            "meaning": "Inventory integrity only; this does not independently reproduce a scientific result."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", help="Folder name in experiments/, for example P065_empathy_meta_analysis")
    args = parser.parse_args()
    result = verify(Path(__file__).resolve().parents[1], args.study)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
