from __future__ import annotations

import json
from pathlib import Path

from .state import initialize_workspace


UPDATE_STAGES = ("sync", "extract", "quantitative-audit", "render-note", "synthesize", "render", "audit")


def build_stage_tasks(manifest: dict, stage: str, item_keys: set[str] | None = None) -> list[dict]:
    """Create stable task descriptors for one orchestration stage."""
    rows = sorted(manifest.get("records", []), key=lambda row: row.get("zotero_item_key", ""))
    if item_keys is not None:
        rows = [row for row in rows if row.get("zotero_item_key") in item_keys]
    if stage == "update":
        tasks: list[dict] = []
        for row in rows:
            key = row.get("zotero_item_key", "")
            if row.get("duplicate_candidates") and row.get("review_status") == "needs-review":
                tasks.append({"item_key": key, "stage": "resolve-identity", "sequence": 1, "status": "needs-review"})
                continue
            if row.get("extraction_status") in {"pending", "failed"}:
                stages = UPDATE_STAGES
            elif row.get("synthesis_status") in {"pending", "stale"}:
                stages = ("synthesize", "render", "audit")
            else:
                stages = ()
            status = "needs-review" if row.get("review_status") == "needs-review" else "pending"
            for sequence, name in enumerate(stages, 1):
                tasks.append({"item_key": key, "stage": name, "sequence": sequence, "status": status})
        return tasks
    if stage == "extract":
        rows = [row for row in rows if row.get("extraction_status") in {"pending", "failed"}]
    elif stage == "synthesize":
        rows = [row for row in rows if row.get("synthesis_status") in {"pending", "stale"}]
    tasks = []
    for row in rows:
        status = "needs-review" if row.get("review_status") == "needs-review" else "pending"
        tasks.append({"item_key": row.get("zotero_item_key", ""), "stage": stage, "status": status})
    return tasks


def create_run(vault: Path, command: str, run_id: str, tasks: list[dict], batch_size: int, apply: bool) -> dict:
    """Preview or persist an auditable run descriptor."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    item_keys = sorted({task.get("item_key", "") for task in tasks if task.get("item_key")})
    batches = {key: index // batch_size + 1 for index, key in enumerate(item_keys)}
    batched_tasks = [{**task, "batch": batches.get(task.get("item_key", ""), 0)} for task in tasks]
    report = {
        "schema_version": 1,
        "run_id": run_id,
        "command": command,
        "batch_size": batch_size,
        "batch_count": max(batches.values(), default=0),
        "task_count": len(tasks),
        "mode": "apply" if apply else "dry-run",
        "run_directory": "",
    }
    if not apply:
        return report
    paths = initialize_workspace(vault)
    run_dir = paths["workspace"] / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    report["run_directory"] = str(run_dir)
    (run_dir / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "tasks.jsonl").write_text(
        "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in batched_tasks),
        encoding="utf-8",
    )
    return report
