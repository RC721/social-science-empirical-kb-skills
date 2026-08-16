from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


KEY_PATTERN = re.compile(r"(?m)^zotero_item_key:\s*[\"']?([^\s\"']+)")
EVIDENCE_ID_PATTERN = re.compile(r"^[A-Z0-9]+-E[0-9A-F]{10}$")
START = "<!-- research-kb:managed:start -->"
END = "<!-- research-kb:managed:end -->"
ACTIVE_MARKDOWN_DIRS = ("00_首页", "01_文献笔记", "02_主题综述", "03_概念知识", "04_研究问题", "05_研究地图", "06_学术论断", "07_主题比较矩阵")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _note_key(text: str) -> str:
    match = KEY_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def audit_workspace(vault: Path) -> dict:
    """Run read-only structural and evidence checks on the active knowledge base."""
    work = vault / "90_Codex工作区"
    manifest_path = work / "state" / "corpus_manifest.json"
    notes_dir = vault / "01_文献笔记"
    evidence_dir = work / "evidence"
    errors: list[str] = []
    warnings: list[str] = []
    manifest = _read_json(manifest_path) if manifest_path.exists() else {"records": []}
    if manifest.get("schema_version") != 2:
        errors.append("corpus manifest is not schema v2")
    records = manifest.get("records", [])
    manifest_keys = {row.get("zotero_item_key", "") for row in records if row.get("zotero_item_key")}

    note_paths = sorted(notes_dir.glob("*.md")) if notes_dir.exists() else []
    note_keys: list[str] = []
    managed_notes = 0
    for path in note_paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"invalid UTF-8 note: {path.name}")
            continue
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"invalid or missing YAML frontmatter: {path.name}")
        key = _note_key(text)
        if not key:
            errors.append(f"missing zotero_item_key: {path.name}")
        else:
            note_keys.append(key)
        starts = text.count(START)
        ends = text.count(END)
        if starts == 1 and ends == 1 and text.index(START) < text.index(END):
            managed_notes += 1
        elif starts or ends:
            errors.append(f"unbalanced managed markers: {path.name}")

    duplicates = sorted(key for key, count in Counter(note_keys).items() if count > 1)
    for key in duplicates:
        errors.append(f"duplicate zotero_item_key: {key}")

    evidence_v2 = 0
    evidence_keys: set[str] = set()
    evidence_ids: set[str] = set()
    if evidence_dir.exists():
        for path in sorted(evidence_dir.glob("*.json")):
            try:
                artifact = _read_json(path)
            except (json.JSONDecodeError, UnicodeDecodeError):
                errors.append(f"invalid evidence JSON: {path.name}")
                continue
            if artifact.get("schema_version") != 2:
                errors.append(f"evidence is not schema v2: {path.name}")
                continue
            evidence_v2 += 1
            key = artifact.get("zotero_item_key", "")
            if key:
                evidence_keys.add(key)
            for item in artifact.get("evidence", []):
                value = item.get("evidence_id", "")
                if not value:
                    errors.append(f"missing evidence_id: {path.name}")
                elif value in evidence_ids:
                    errors.append(f"duplicate evidence_id: {value}")
                else:
                    evidence_ids.add(value)
                if value and not (EVIDENCE_ID_PATTERN.match(value) or re.match(r"^[A-Z0-9]+-E\d{3}$", value)):
                    warnings.append(f"legacy evidence_id format: {value}")

    missing_note_keys = sorted(manifest_keys - set(note_keys))
    identity_review_keys = sorted(
        row["zotero_item_key"]
        for row in records
        if row.get("zotero_item_key") in missing_note_keys and row.get("duplicate_candidates")
    )
    note_generation_keys = sorted(set(missing_note_keys) - set(identity_review_keys))
    missing_evidence_keys = sorted(
        row["zotero_item_key"]
        for row in records
        if row.get("evidence_level") == "fulltext"
        and row.get("extraction_status") in {"parsed", "extracted", "limited"}
        and row.get("zotero_item_key") not in evidence_keys
    )
    pending_evidence_keys = sorted(
        row["zotero_item_key"]
        for row in records
        if row.get("evidence_level") == "fulltext"
        and row.get("extraction_status") == "pending"
        and row.get("zotero_item_key") not in evidence_keys
    )
    if identity_review_keys:
        warnings.append(f"probable duplicate/version records awaiting identity review: {len(identity_review_keys)}")
    if note_generation_keys:
        warnings.append(f"new records awaiting Literature Notes: {len(note_generation_keys)}")
    if missing_evidence_keys:
        errors.append(f"fulltext records missing Evidence artifacts: {len(missing_evidence_keys)}")
    if pending_evidence_keys:
        warnings.append(f"fulltext records queued for first extraction: {len(pending_evidence_keys)}")
    unmanaged = len(note_paths) - managed_notes
    if unmanaged:
        warnings.append(f"legacy notes awaiting managed-boundary review: {unmanaged}")

    active_markdown: list[Path] = []
    for directory in ACTIVE_MARKDOWN_DIRS:
        root = vault / directory
        if root.exists():
            active_markdown.extend(sorted(root.rglob("*.md")))
    stems: dict[str, list[Path]] = defaultdict(list)
    for path in active_markdown:
        stems[path.stem.casefold()].append(path)
    duplicate_stems = {
        stem: [path.relative_to(vault).as_posix() for path in paths]
        for stem, paths in sorted(stems.items())
        if len(paths) > 1
    }
    excluded_target_parts = {"backups", ".git", ".obsidian", ".tools", "skill-development", "skills"}
    target_stems = {
        path.stem.casefold()
        for path in vault.rglob("*.md")
        if not any(part in excluded_target_parts for part in path.parts)
    }
    broken_links: list[dict] = []
    for path in active_markdown:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in WIKILINK_PATTERN.findall(text):
            name = target.strip().replace("\\", "/").rsplit("/", 1)[-1]
            stem = (name[:-3] if name.lower().endswith(".md") else name).casefold()
            if stem not in target_stems:
                broken_links.append({"source": path.relative_to(vault).as_posix(), "target": target})
    if duplicate_stems:
        errors.append(f"duplicate active Markdown stems: {len(duplicate_stems)}")
    if broken_links:
        errors.append(f"broken Wikilinks in active knowledge directories: {len(broken_links)}")

    return {
        "schema_version": 1,
        "status": "failed" if errors else "passed-with-warnings" if warnings else "passed",
        "counts": {
            "manifest_records": len(records),
            "literature_notes": len(note_paths),
            "managed_notes": managed_notes,
            "evidence_v2": evidence_v2,
            "evidence_ids": len(evidence_ids),
            "active_markdown": len(active_markdown),
        },
        "missing_note_keys": missing_note_keys,
        "identity_review_keys": identity_review_keys,
        "note_generation_keys": note_generation_keys,
        "missing_evidence_keys": missing_evidence_keys,
        "pending_evidence_keys": pending_evidence_keys,
        "duplicate_stems": duplicate_stems,
        "broken_links": broken_links,
        "errors": errors,
        "warnings": warnings,
    }


def plan_note_migration(vault: Path) -> dict:
    """Describe safe managed-block migration without modifying any note bytes."""
    notes_dir = vault / "01_文献笔记"
    items: list[dict] = []
    for path in sorted(notes_dir.glob("*.md")) if notes_dir.exists() else []:
        payload = path.read_bytes()
        try:
            text = payload.decode("utf-8")
            key = _note_key(text)
            starts = text.count(START)
            ends = text.count(END)
            if starts == 1 and ends == 1 and text.index(START) < text.index(END):
                action = "already-managed"
            elif starts or ends:
                action = "invalid-markers-needs-review"
            else:
                action = "manual-boundary-required"
        except UnicodeDecodeError:
            key = ""
            action = "invalid-utf8-needs-review"
        items.append(
            {
                "file": path.name,
                "item_key": key,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "action": action,
            }
        )
    return {
        "schema_version": 1,
        "mode": "dry-run",
        "notes": len(items),
        "already_managed": sum(item["action"] == "already-managed" for item in items),
        "needs_boundary_review": sum(item["action"] != "already-managed" for item in items),
        "items": items,
    }
