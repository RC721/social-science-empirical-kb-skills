from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .audit import audit_workspace, plan_note_migration
from .backup import create_baseline_backup
from .evaluation import run_evaluation
from .migration import build_v2_manifest, migrate_evidence_directory
from .orchestration import build_stage_tasks, create_run
from .reporting import build_upgrade_report, write_upgrade_report
from .state import initialize_workspace


SEARCH_FILES = (
    "search_protocol.yaml",
    "queries.json",
    "candidates.jsonl",
    "deduplication.json",
    "screening_log.jsonl",
    "coverage_report.md",
    "zotero_import_plan.json",
)


def run_audit(vault: Path, run_id: str, apply: bool = False) -> dict:
    """Run structural audit and generate a read-only managed-block migration plan."""
    report = audit_workspace(vault)
    note_plan = plan_note_migration(vault)
    report["note_migration"] = {
        "mode": "dry-run",
        "notes": note_plan["notes"],
        "already_managed": note_plan["already_managed"],
        "needs_boundary_review": note_plan["needs_boundary_review"],
    }
    if apply:
        reports = vault / "90_Codex工作区" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        upgrade_path = write_upgrade_report(vault, build_upgrade_report(vault))
        report["upgrade_report"] = str(upgrade_path)
        (reports / f"{run_id}-structure.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (reports / f"{run_id}-note-migration-dry-run.json").write_text(
            json.dumps(note_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return report


def create_search_run(vault: Path, mode: str, run_id: str) -> Path:
    """Create an empty, auditable search run contract."""
    if mode not in {"exploratory", "focused", "systematic"}:
        raise ValueError(f"unsupported search mode: {mode}")
    run = vault / "90_Codex工作区" / "search_runs" / run_id
    run.mkdir(parents=True, exist_ok=False)
    content = {
        "search_protocol.yaml": f'schema_version: "1.0.0"\nrun_id: "{run_id}"\nmode: "{mode}"\nstatus: "draft"\n',
        "queries.json": "[]\n",
        "candidates.jsonl": "",
        "deduplication.json": "{\n  \"groups\": []\n}\n",
        "screening_log.jsonl": "",
        "coverage_report.md": f"# 检索覆盖报告\n\n- Run ID：`{run_id}`\n- 模式：`{mode}`\n- 状态：待执行\n",
        "zotero_import_plan.json": "{\n  \"approved\": false,\n  \"items\": []\n}\n",
    }
    for name in SEARCH_FILES:
        (run / name).write_text(content[name], encoding="utf-8")
    return run


def run_migration(vault: Path, apply: bool, source_snapshot_id: str) -> dict:
    """Dry-run or apply manifest v1 to v2 migration from the cached Zotero snapshot."""
    work = vault / "90_Codex工作区"
    old_path = work / "cache" / "corpus_manifest.json"
    snapshot_path = work / "cache" / "zotero_collection_snapshot.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    manifest, tasks = build_v2_manifest(old, snapshot, source_snapshot_id)
    source_hashes = {
        row.get("zotero_item_key", ""): row.get("pdf_sha256", "")
        for row in old.get("records", [])
        if row.get("zotero_item_key") and row.get("pdf_sha256")
    }
    extracted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence_report = migrate_evidence_directory(
        work / "evidence",
        apply=False,
        extracted_at=extracted_at,
        source_hashes=source_hashes,
    )
    task_counts: dict[str, int] = {}
    for task in tasks:
        task_counts[task["task"]] = task_counts.get(task["task"], 0) + 1
    report = {
        "schema_version": 1,
        "mode": "apply" if apply else "dry-run",
        "old_records": len(old.get("records", [])),
        "new_records": len(manifest.get("records", [])),
        "queued": len(tasks),
        "task_counts": dict(sorted(task_counts.items())),
        "missing_from_v1": [item["item_key"] for item in tasks],
        "source_snapshot_id": source_snapshot_id,
        "evidence": evidence_report,
    }
    if apply:
        backup = create_baseline_backup(vault, f"pre-v2-{source_snapshot_id}")
        paths = initialize_workspace(vault)
        manifest_path = paths["workspace"] / "state" / "corpus_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths["queue"].write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in tasks),
            encoding="utf-8",
        )
        evidence_report = migrate_evidence_directory(
            work / "evidence",
            apply=True,
            extracted_at=extracted_at,
            source_hashes=source_hashes,
        )
        report["evidence"] = evidence_report
        report["backup"] = backup
        report_path = paths["workspace"] / "reports" / "manifest-v2-migration.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_parser() -> argparse.ArgumentParser:
    """Build the public command-line contract."""
    parser = argparse.ArgumentParser(prog="research-kb")
    parser.add_argument("--vault", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--run-id", default="")
        command.add_argument("--item-key", action="append", default=[])
        command.add_argument("--collection-key", default="")
        command.add_argument("--batch-size", type=int, default=10)
        command.add_argument("--dry-run", action="store_true")

    init = sub.add_parser("init")
    add_common(init)
    init.add_argument("--domain", default="general")

    discover = sub.add_parser("discover")
    add_common(discover)
    discover.add_argument("--mode", choices=("exploratory", "focused", "systematic"), default="focused")

    migrate = sub.add_parser("migrate")
    add_common(migrate)
    migrate.add_argument("--apply", action="store_true")
    migrate.add_argument("--source-snapshot-id", default="")

    for name in ("ingest", "extract", "synthesize", "render", "audit", "eval", "update"):
        command = sub.add_parser(name)
        add_common(command)
        command.add_argument("--apply", action="store_true")
        if name == "ingest":
            command.add_argument("--plan", action="store_true")
    sync = sub.add_parser("sync")
    add_common(sync)
    sync.add_argument("--source-snapshot-id", default="")
    sync.add_argument("--apply", action="store_true")

    package = sub.add_parser("package-skills")
    add_common(package)
    package.add_argument("--output", type=Path)
    package.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    args = parser.parse_args(argv)
    vault = args.vault.resolve()
    if args.command == "init":
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "mode": "dry-run",
                        "workspace": str(vault / "90_Codex工作区"),
                        "collection_key": args.collection_key,
                        "domain": args.domain,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        result = initialize_workspace(vault, args.collection_key, args.domain)
        print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "discover":
        run_id = args.run_id or _timestamp_id()
        if args.dry_run:
            report = {"mode": "dry-run", "search_run": str(vault / "90_Codex工作区" / "search_runs" / run_id), "search_mode": args.mode}
        else:
            run = create_search_run(vault, args.mode, run_id)
            report = {"mode": "apply", "search_run": str(run), "search_mode": args.mode}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "migrate":
        report = run_migration(vault, args.apply and not args.dry_run, args.source_snapshot_id or args.run_id or _timestamp_id())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "sync":
        report = run_migration(vault, args.apply and not args.dry_run, args.source_snapshot_id or args.run_id or _timestamp_id())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "audit":
        report = run_audit(
            vault,
            run_id=args.run_id or _timestamp_id(),
            apply=args.apply and not args.dry_run,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "eval":
        report = run_evaluation(vault, apply=args.apply and not args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command in {"ingest", "extract", "synthesize", "render", "audit", "eval", "update"}:
        manifest_path = vault / "90_Codex工作区" / "state" / "corpus_manifest.json"
        if not manifest_path.exists():
            legacy = vault / "90_Codex工作区" / "cache" / "corpus_manifest.json"
            if not legacy.exists():
                parser.error("corpus manifest not found; run init and sync first")
            manifest = json.loads(legacy.read_text(encoding="utf-8"))
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tasks = build_stage_tasks(manifest, args.command, set(args.item_key) if args.item_key else None)
        report = create_run(
            vault,
            args.command,
            args.run_id or _timestamp_id(),
            tasks,
            args.batch_size,
            apply=args.apply and not args.dry_run and not getattr(args, "plan", False),
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "package-skills":
        from .packaging import package_skills

        report = package_skills(
            Path(__file__).resolve().parents[2],
            (args.output or (vault / "90_Codex工作区" / "skills")).resolve(),
            apply=args.apply and not args.dry_run,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
