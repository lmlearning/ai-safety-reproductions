"""Validate navigation, study coverage and scientific-source syntax offline."""
from __future__ import annotations
import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def validate(root: Path) -> dict:
    root = root.resolve()
    listing = json.loads((root / "STUDIES.json").read_text(encoding="utf-8"))
    expected = {r["paper_id"] for r in listing["studies"]}
    failures, syntax_count, local_links, code_count = [], 0, 0, 0
    folders = [p for p in (root / "experiments").iterdir() if p.is_dir()]
    actual = {p.name.split("_", 1)[0] for p in folders}
    if actual != expected or len(folders) != 21:
        failures.append("The study folders do not match the21 distinct listed papers")
    per_study = []
    for folder in folders:
        for name in ["README.md", "REPRODUCE.md", "reproduce.py", "requirements.txt", "STUDY.json", "INPUTS.json", "PROVENANCE.json"]:
            if not (folder / name).is_file():
                failures.append(str((folder / name).relative_to(root)) + " is missing")
        sources = [p for p in (folder / "code").rglob("*") if p.is_file()]
        if not sources:
            failures.append(folder.name + " has no scientific code")
        code_count += len(sources)
        provenance = json.loads((folder / "PROVENANCE.json").read_text(encoding="utf-8"))
        for row in provenance["files"]:
            target = (folder / row["published_path"]).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                failures.append(folder.name + " has an absent or unsafe provenance path")
        per_study.append({"paper_id": folder.name.split("_",1)[0], "scientific_code_files":len(sources),
                          "selected_archive_files":len(provenance["files"])})
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.stat().st_size >= 100_000_000:
            failures.append(str(path.relative_to(root)) + " exceeds this release's100MB per-file packaging bound")
        if len(path.relative_to(root).as_posix()) > 160:
            failures.append(str(path.relative_to(root)) + " exceeds the160-character relative path packaging bound")
        if path.suffix.lower() == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(root)))
                syntax_count += 1
            except (SyntaxError, UnicodeError) as error:
                failures.append(str(path.relative_to(root)) + ": " + str(error))
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^\n)]+)\)", text):
            target = target.strip().split(' "',1)[0].strip('<>')
            if urlsplit(target).scheme or target.startswith("#"):
                continue
            target = unquote(target.split("#",1)[0])
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            local_links += 1
            if not resolved.is_relative_to(root) or not resolved.exists():
                failures.append(str(path.relative_to(root)) + " -> " + target)
    return {"ok":not failures, "distinct_studies":len(expected), "scientific_code_files":code_count,
            "python_files_parsed":syntax_count, "local_markdown_links_checked":local_links,
            "per_study":sorted(per_study,key=lambda r:r["paper_id"]), "failures":failures,
            "scientific_programs_executed":False,
            "limits":"Static syntax and selected navigation/coverage checks, not runtime portability, external URL availability, license adjudication or scientific recomputation."}


if __name__ == "__main__":
    result=validate(Path(__file__).resolve().parents[1])
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["ok"] else 1)
