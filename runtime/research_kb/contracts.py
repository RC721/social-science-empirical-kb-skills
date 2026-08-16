from __future__ import annotations

from copy import deepcopy


def causal_language_gate(author_claim_type: str, design_status: str) -> str:
    """Return the strongest causal wording allowed by the audited design."""
    if author_claim_type != "causal":
        return "qualified-only" if author_claim_type == "associational" else "prohibited"
    if design_status == "experimental":
        return "allowed"
    if design_status == "quasi-experimental":
        return "qualified-only"
    return "prohibited"


def migrate_evidence_v1(artifact: dict, source_hash: str, extracted_at: str) -> dict:
    """Migrate stored original evidence to v2 without consulting Markdown notes."""
    migrated = deepcopy(artifact)
    migrated["schema_version"] = 2
    for item in migrated.get("evidence", []):
        item["original_text"] = item.pop("quote", item.get("original_text", ""))
        item.setdefault("source_channel", "unknown")
        item.setdefault("table_or_figure", "")
        item["source_hash"] = source_hash
        item["extracted_at"] = extracted_at
    return migrated
