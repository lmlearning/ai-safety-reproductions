"""Inspect, verify, fetch, or stage this study's published reproduction artifacts.

This tool never executes legacy scientific programs or disables their guards.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def within(base: Path, name: str) -> Path:
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Path leaves the chosen directory: " + name)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true", help="Check the published file hashes; no scientific run")
    modes.add_argument("--list-inputs", action="store_true", help="Show source and acquisition records")
    modes.add_argument("--fetch", metavar="INPUT_ID", help="Download one explicitly selected source asset")
    modes.add_argument("--stage", type=Path, metavar="NEW_DIRECTORY", help="Reconstruct the original relative layout in a new directory")
    parser.add_argument("--downloads", type=Path, default=HERE / "downloads")
    args = parser.parse_args()
    info = json.loads((HERE / "STUDY.json").read_text(encoding="utf-8"))
    provenance = json.loads((HERE / "PROVENANCE.json").read_text(encoding="utf-8"))
    inputs = json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))
    if args.verify:
        sys.path.insert(0, str(ROOT / "tools"))
        from verify_release import verify
        result = verify(ROOT, HERE.name)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["ok"] else 1)
    if args.list_inputs:
        print(json.dumps(inputs, indent=2))
    elif args.fetch:
        row = next((r for r in inputs["assets"] if r["id"] == args.fetch), None)
        if not row:
            raise SystemExit("Unknown input ID; use --list-inputs.")
        urls = row.get("download_urls", [])
        if not urls:
            raise SystemExit("No exact file URL retained. See the source landing pages and INPUTS.json.")
        target = within(args.downloads, row["original_relative_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise SystemExit("Refusing to replace an existing input: " + str(target))
        temporary = target.with_name(target.name + ".part")
        if temporary.exists():
            raise SystemExit("An unfinished download already exists: " + str(temporary))
        request = urllib.request.Request(urls[0], headers={"User-Agent": "AI-safety-reproductions-artifact/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=90) as response, temporary.open("xb") as output:
                shutil.copyfileobj(response, output)
            if digest(temporary) != row["sha256"]:
                raise SystemExit("Downloaded bytes differ from the archived SHA-256. The .part file is retained for inspection.")
            temporary.rename(target)
        except BaseException:
            # Preserve partial bytes; never silently accept a changed upstream asset.
            raise
        print("Verified download: " + str(target))
    elif args.stage:
        destination = args.stage.resolve()
        if destination.exists():
            raise SystemExit("Choose a new directory; existing runs are never overwritten.")
        destination.mkdir(parents=True)
        count = 0
        for row in provenance["files"]:
            if row["role"] not in {"code", "input", "plan"}:
                continue
            source = within(HERE, row["published_path"])
            target = within(destination, row["original_relative_path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            # Publication copies remove workstation paths. Relocation is explicit,
            # logged, and does not change scientific methods or frozen thresholds.
            if row.get("text"):
                text = raw.decode("utf-8")
                text = text.replace("{{REPRODUCTION_ROOT}}", destination.as_posix())
                raw = text.encode("utf-8")
            target.write_bytes(raw)
            count += 1
        for row in inputs["assets"]:
            source = within(args.downloads, row["original_relative_path"])
            target = within(destination, row["original_relative_path"])
            if source.is_file() and not target.exists():
                if digest(source) != row["sha256"]:
                    raise SystemExit("Changed downloaded input: " + str(source))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                count += 1
        receipt = {"paper_id": info["paper_id"], "files_staged": count,
                   "experiment_executed": False, "legacy_guards_disabled": False,
                   "warning": "Follow REPRODUCE.md. Missing source assets, original runtime versions, frozen hash checks and platform-specific guards can still prevent execution."}
        (destination / "PUBLICATION_STAGE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))
    else:
        print(json.dumps({"paper_id": info["paper_id"], "classification": info["classification"],
                          "scope": info["result_and_scope"], "experiment_executed": False,
                          "next": "Read README.md and REPRODUCE.md; use --verify or --list-inputs."}, indent=2))


if __name__ == "__main__":
    main()
