from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


SKILL_NAMES = (
    "social-science-empirical-kb",
    "social-science-literature-discovery",
    "zotero-corpus-sync",
    "social-science-paper-extraction",
    "quantitative-study-audit",
    "research-knowledge-synthesis",
    "obsidian-research-kb",
    "research-kb-evolution",
    "policy-citation-knowledge-base",
)
ALLOWED_TOP_LEVEL = {"SKILL.md", "agents", "scripts", "references", "assets"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def _included_files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        yield path, relative


def _copy_skill(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path, relative in _included_files(source):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def _copy_runtime(source_root: Path, skill_target: Path) -> None:
    scripts = skill_target / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_root / "runtime" / "research-kb.py", scripts / "research-kb.py")
    package_target = scripts / "research_kb"
    package_target.mkdir(parents=True, exist_ok=True)
    for path, relative in _included_files(source_root / "runtime" / "research_kb"):
        destination = package_target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def _validate_staged(staged: Path) -> list[str]:
    errors: list[str] = []
    for name in SKILL_NAMES:
        root = staged / name
        if not (root / "SKILL.md").is_file():
            errors.append(f"{name}: missing SKILL.md")
        if not (root / "agents" / "openai.yaml").is_file():
            errors.append(f"{name}: missing agents/openai.yaml")
        for child in root.iterdir():
            if child.name not in ALLOWED_TOP_LEVEL:
                errors.append(f"{name}: unsupported top-level entry {child.name}")
        for path, _ in _included_files(root):
            if path.name.lower() in {"readme.md", "changelog.md"}:
                errors.append(f"{name}: forbidden helper file {path.name}")
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if path.suffix.lower() in {".md", ".yaml", ".yml"} and "TODO" in text:
                errors.append(f"{name}: placeholder TODO in {path.relative_to(root).as_posix()}")
    return errors


def _file_hashes(staged: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in SKILL_NAMES:
        for path, relative in _included_files(staged / name):
            key = (Path(name) / relative).as_posix()
            hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(hashes.items()))


def _deterministic_zip(staged: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in SKILL_NAMES:
            for path, relative in _included_files(staged / name):
                entry = (Path(name) / relative).as_posix()
                info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())


def package_skills(source_root: Path, output: Path, apply: bool = False) -> dict:
    """Validate and publish the canonical Skill source as a deterministic release."""
    missing = [name for name in SKILL_NAMES if not (source_root / name / "SKILL.md").is_file()]
    if missing:
        raise FileNotFoundError(f"missing Skill sources: {', '.join(missing)}")
    report = {
        "mode": "apply" if apply else "dry-run",
        "status": "passed",
        "skill_count": len(SKILL_NAMES),
        "suite_version": "0.1.0",
        "runtime_version": "0.1.0",
        "schema_version": "2.0.0",
        "output": str(output),
    }
    if not apply:
        return report

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / "skills"
        for name in SKILL_NAMES:
            _copy_skill(source_root / name, staged / name)
        _copy_runtime(source_root, staged / "social-science-empirical-kb")
        errors = _validate_staged(staged)
        if errors:
            raise ValueError("Skill validation failed: " + "; ".join(errors))

        release = staged / "_release"
        release.mkdir(parents=True, exist_ok=True)
        versions = {
            "suite_version": "0.1.0",
            "runtime_version": "0.1.0",
            "schema_version": "2.0.0",
            "skills": {name: "0.1.0" for name in SKILL_NAMES},
        }
        (release / "versions.json").write_text(
            json.dumps(versions, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        hashes = {"algorithm": "sha256", "files": _file_hashes(staged)}
        (release / "sha256-manifest.json").write_text(
            json.dumps(hashes, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        validation = {**report, "errors": []}
        (release / "validation-report.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _deterministic_zip(staged, release / "social-science-empirical-kb-suite-0.1.0.zip")

        output.mkdir(parents=True, exist_ok=True)
        for name in (*SKILL_NAMES, "_release"):
            target = output / name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(staged / name, target)
    return report
