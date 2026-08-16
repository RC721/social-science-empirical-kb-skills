from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


DEFAULT_BASELINE_TARGETS = (
    "01_文献笔记",
    "02_主题综述",
    "03_概念知识",
    "04_研究问题",
    "05_研究地图",
    "06_学术论断",
    "07_主题比较矩阵",
    "90_Codex工作区/skills",
    "90_Codex工作区/evidence",
    "90_Codex工作区/cache/corpus_manifest.json",
    "90_Codex工作区/cache/zotero_collection_snapshot.json",
)


def create_baseline_backup(vault: Path, backup_id: str, targets: tuple[str, ...] = DEFAULT_BASELINE_TARGETS) -> dict:
    """Copy exact migration inputs and write a SHA-256 manifest without changing sources."""
    destination = vault / "90_Codex工作区" / "backups" / backup_id
    if destination.exists():
        raise FileExistsError(f"backup already exists: {destination}")
    destination.mkdir(parents=True)
    hashes: dict[str, str] = {}
    sizes: dict[str, int] = {}
    missing: list[str] = []
    for relative_text in targets:
        relative = Path(relative_text)
        source = vault / relative
        if not source.exists():
            missing.append(relative.as_posix())
            continue
        files = [source] if source.is_file() else sorted(path for path in source.rglob("*") if path.is_file())
        for path in files:
            file_relative = relative if source.is_file() else relative / path.relative_to(source)
            target = destination / file_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            key = file_relative.as_posix()
            payload = path.read_bytes()
            hashes[key] = hashlib.sha256(payload).hexdigest()
            sizes[key] = len(payload)
    manifest = {
        "schema_version": 1,
        "backup_id": backup_id,
        "algorithm": "sha256",
        "files": dict(sorted(hashes.items())),
        "sizes": dict(sorted(sizes.items())),
        "missing_targets": sorted(missing),
    }
    (destination / "sha256-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "backup_id": backup_id,
        "path": str(destination),
        "file_count": len(hashes),
        "missing_targets": sorted(missing),
    }
