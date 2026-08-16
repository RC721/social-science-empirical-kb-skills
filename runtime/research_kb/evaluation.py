from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path


def build_gold_candidate_set(manifest: dict, size: int = 30) -> dict:
    """Select a deterministic, paper-type and evidence-level stratified candidate set."""
    groups: dict[str, deque[dict]] = defaultdict(deque)
    records = sorted(manifest.get("records", []), key=lambda row: row.get("zotero_item_key", ""))
    for row in records:
        key = row.get("zotero_item_key", "")
        if not key:
            continue
        stratum = f"{row.get('paper_type') or 'unclassified'}|{row.get('evidence_level') or 'metadata-only'}"
        groups[stratum].append(row)
    selected: list[dict] = []
    strata = sorted(groups)
    while len(selected) < min(size, len(records)) and any(groups.values()):
        for stratum in strata:
            if len(selected) >= min(size, len(records)):
                break
            if not groups[stratum]:
                continue
            row = groups[stratum].popleft()
            selected.append(
                {
                    "item_key": row["zotero_item_key"],
                    "title": row.get("title", ""),
                    "paper_type": row.get("paper_type", ""),
                    "evidence_level": row.get("evidence_level", "metadata-only"),
                    "stratum": stratum,
                    "verification_status": "candidate",
                }
            )
    return {
        "schema_version": 1,
        "target_size": size,
        "review_status": "candidate-needs-human-verification",
        "selection_rule": "deterministic round-robin by paper_type and evidence_level",
        "items": selected,
    }


def run_evaluation(vault: Path, apply: bool = False, size: int = 30) -> dict:
    """Prepare or inspect the human-gated gold evaluation set."""
    work = vault / "90_Codex工作区"
    manifest_path = work / "state" / "corpus_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate = build_gold_candidate_set(manifest, size=size)
    gold = work / "evals" / "gold"
    verified = 0
    if gold.exists():
        for path in gold.glob("*.json"):
            if path.name == "candidate-gold-set.json":
                continue
            try:
                artifact = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if artifact.get("verification_status") == "human-verified":
                verified += 1
    if apply:
        gold.mkdir(parents=True, exist_ok=True)
        (gold / "candidate-gold-set.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return {
        "status": "ready" if verified >= size else "needs-human-verification",
        "candidate_count": len(candidate["items"]),
        "human_verified_count": verified,
        "required_human_verified": size,
        "mode": "apply" if apply else "dry-run",
    }
