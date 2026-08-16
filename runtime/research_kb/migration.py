from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from .contracts import migrate_evidence_v1


def _normalized_doi(value: str) -> str:
    doi = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :]
    return doi.strip()


def _creator_name(creator: dict) -> str:
    return creator.get("name") or " ".join(part for part in (creator.get("firstName", ""), creator.get("lastName", "")) if part).strip()


def _citekey(data: dict) -> str:
    direct = data.get("citationKey") or data.get("citekey")
    if direct:
        return str(direct).strip()
    for line in (data.get("extra") or "").splitlines():
        if line.lower().startswith("citation key:"):
            return line.split(":", 1)[1].strip()
    return ""


def _normalized_title(value: str) -> str:
    return "".join(character for character in (value or "").casefold() if character.isalnum())


def _snapshot_item(record: dict) -> tuple[str, dict, bool]:
    item = record.get("item", {})
    key = item.get("key") or item.get("data", {}).get("key", "")
    data = item.get("data", {})
    has_pdf = any(
        (attachment.get("fulltext") or {}).get("content")
        or (attachment.get("item") or {}).get("data", {}).get("contentType") == "application/pdf"
        for attachment in record.get("attachments", [])
    )
    return key, data, has_pdf


def build_v2_manifest(old: dict, snapshot: dict, source_snapshot_id: str) -> tuple[dict, list[dict]]:
    """Merge a v1 manifest with a current Zotero snapshot and queue new items."""
    old_by_key = {row["zotero_item_key"]: row for row in old.get("records", [])}
    doi_index: dict[str, set[str]] = {}
    title_index: dict[str, set[str]] = {}
    for old_key, old_row in old_by_key.items():
        old_doi = _normalized_doi(old_row.get("doi", ""))
        old_title = _normalized_title(old_row.get("title", ""))
        if old_doi:
            doi_index.setdefault(old_doi, set()).add(old_key)
        if old_title:
            title_index.setdefault(old_title, set()).add(old_key)
    rows: list[dict] = []
    tasks: list[dict] = []
    for record in sorted(snapshot.get("records", []), key=lambda x: (x.get("item", {}).get("key") or "")):
        key, data, has_pdf = _snapshot_item(record)
        previous = deepcopy(old_by_key.get(key, {}))
        current_doi = _normalized_doi(previous.get("doi") or data.get("DOI", ""))
        current_title = previous.get("title") or data.get("title", "")
        current_title_normalized = _normalized_title(current_title)
        duplicate_candidates = sorted(
            (
                (doi_index.get(current_doi, set()) if current_doi else set())
                | (title_index.get(current_title_normalized, set()) if current_title_normalized else set())
            )
            - {key}
        )
        level = previous.get("evidence_level") or ("fulltext" if has_pdf else "abstract-only" if data.get("abstractNote") else "metadata-only")
        if previous:
            ingestion = "pdf-ready" if has_pdf else "imported"
            extraction = "extracted" if previous.get("extraction_status") == "audited" or level == "fulltext" else "limited"
        else:
            ingestion = "pdf-ready" if has_pdf else "imported"
            extraction = "pending"
            if duplicate_candidates:
                tasks.append(
                    {
                        "item_key": key,
                        "task": "resolve-identity",
                        "status": "needs-review",
                        "reason": "probable-duplicate-or-version",
                        "candidates": duplicate_candidates,
                    }
                )
            else:
                tasks.append({"item_key": key, "task": "extract", "status": "pending", "reason": "new-zotero-item"})
        row = {
            **previous,
            "schema_version": 2,
            "zotero_item_key": key,
            "title": current_title,
            "authors": previous.get("authors") or [name for creator in data.get("creators", []) if (name := _creator_name(creator))],
            "year": previous.get("year") or str(data.get("date", ""))[:4],
            "journal": previous.get("journal") or data.get("publicationTitle", ""),
            "doi": current_doi,
            "citekey": previous.get("citekey") or _citekey(data),
            "evidence_level": level,
            "ingestion_status": ingestion,
            "extraction_status": extraction,
            "review_status": "needs-review" if not previous and duplicate_candidates else "verified" if previous.get("extraction_status") == "audited" else "unreviewed",
            "synthesis_status": "integrated" if previous else "pending",
            "zotero_item_version": record.get("item", {}).get("version", 0),
            "source_snapshot_id": source_snapshot_id,
            "last_changed": data.get("dateModified", ""),
            "last_processed": previous.get("last_processed") or previous.get("last_verified", ""),
            "pdf_sha256": previous.get("pdf_sha256", ""),
            "skill_version": previous.get("skill_version", "0.1.0"),
            "extractor_version": previous.get("extractor_version", "0.1.0"),
            "failure_code": previous.get("failure_code", ""),
            "duplicate_of": previous.get("duplicate_of", ""),
            "duplicate_candidates": duplicate_candidates,
            "version_relation": previous.get("version_relation", ""),
        }
        rows.append(row)
        if current_doi:
            doi_index.setdefault(current_doi, set()).add(key)
        if current_title_normalized:
            title_index.setdefault(current_title_normalized, set()).add(key)
    manifest = {
        "schema_version": 2,
        "collection_name": snapshot.get("collection_name", old.get("collection_name", "")),
        "collection_key": snapshot.get("collection_key", old.get("collection_key", "")),
        "source_snapshot_id": source_snapshot_id,
        "records": rows,
    }
    return manifest, tasks


def migrate_evidence_directory(
    directory: Path,
    apply: bool,
    extracted_at: str,
    source_hashes: dict[str, str] | None = None,
) -> dict:
    """Migrate independent v1 evidence JSON files while leaving failures untouched."""
    source_hashes = source_hashes or {}
    report = {"mode": "apply" if apply else "dry-run", "files": 0, "migratable": 0, "migrated": 0, "already_v2": 0, "failed": 0, "failures": []}
    if not directory.exists():
        return report
    for path in sorted(directory.glob("*.json")):
        report["files"] += 1
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
            if artifact.get("schema_version") == 2:
                report["already_v2"] += 1
                continue
            if artifact.get("schema_version") != 1 or not artifact.get("zotero_item_key"):
                raise ValueError("not a valid Evidence v1 artifact")
            item_key = artifact["zotero_item_key"]
            migrated = migrate_evidence_v1(
                artifact,
                source_hash=source_hashes.get(item_key, "legacy-source-hash-unavailable"),
                extracted_at=extracted_at,
            )
            report["migratable"] += 1
            if apply:
                path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                report["migrated"] += 1
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            report["failed"] += 1
            report["failures"].append({"file": path.name, "error": str(error)})
    return report
