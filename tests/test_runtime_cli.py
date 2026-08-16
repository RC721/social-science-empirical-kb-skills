from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from research_kb.cli import build_parser, create_search_run, run_audit, run_migration  # noqa: E402


class RuntimeCliTests(unittest.TestCase):
    def test_cli_exposes_full_planned_command_surface(self):
        parser = build_parser()
        subparsers = next(action for action in parser._actions if action.dest == "command")
        self.assertEqual(
            set(subparsers.choices),
            {"init", "discover", "ingest", "sync", "migrate", "extract", "synthesize", "render", "audit", "eval", "update", "package-skills"},
        )

    def test_every_command_accepts_common_runtime_options_and_ingest_plan(self):
        parser = build_parser()
        for command in ("init", "discover", "ingest", "sync", "migrate", "extract", "synthesize", "render", "audit", "eval", "update", "package-skills"):
            arguments = [
                "--vault",
                ".",
                command,
                "--run-id",
                "run-1",
                "--item-key",
                "AAAA1111",
                "--collection-key",
                "COLL",
                "--batch-size",
                "8",
                "--dry-run",
            ]
            if command == "ingest":
                arguments.append("--plan")
            parsed = parser.parse_args(arguments)
            self.assertEqual(parsed.run_id, "run-1", command)
            self.assertEqual(parsed.item_key, ["AAAA1111"], command)
            self.assertEqual(parsed.collection_key, "COLL", command)
            self.assertEqual(parsed.batch_size, 8, command)
            self.assertTrue(parsed.dry_run, command)
        ingest = parser.parse_args(["ingest", "--plan"])
        self.assertTrue(ingest.plan)

    def test_search_run_creates_all_reproducibility_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = create_search_run(Path(tmp), mode="systematic", run_id="run-1")
            expected = {
                "search_protocol.yaml",
                "queries.json",
                "candidates.jsonl",
                "deduplication.json",
                "screening_log.jsonl",
                "coverage_report.md",
                "zotero_import_plan.json",
            }
            self.assertEqual({p.name for p in run.iterdir()}, expected)
            self.assertIn('mode: "systematic"', (run / "search_protocol.yaml").read_text(encoding="utf-8"))

    def test_migration_dry_run_reports_delta_without_writing_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            work = vault / "90_Codex工作区"
            (work / "cache").mkdir(parents=True)
            old = {"schema_version": 1, "records": [{"zotero_item_key": "AAAA1111", "evidence_level": "metadata-only"}]}
            snapshot = {
                "records": [
                    {"item": {"key": "AAAA1111", "version": 1, "data": {"title": "Old"}}, "attachments": []},
                    {"item": {"key": "BBBB2222", "version": 1, "data": {"title": "New"}}, "attachments": []},
                ]
            }
            (work / "cache" / "corpus_manifest.json").write_text(json.dumps(old), encoding="utf-8")
            (work / "cache" / "zotero_collection_snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")

            report = run_migration(vault, apply=False, source_snapshot_id="test-snapshot")

            self.assertEqual(report["old_records"], 1)
            self.assertEqual(report["new_records"], 2)
            self.assertEqual(report["queued"], 1)
            self.assertFalse((work / "state" / "corpus_manifest.json").exists())

    def test_migration_apply_writes_manifest_and_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            work = vault / "90_Codex工作区"
            (work / "cache").mkdir(parents=True)
            (work / "cache" / "corpus_manifest.json").write_text(json.dumps({"schema_version": 1, "records": []}), encoding="utf-8")
            (work / "cache" / "zotero_collection_snapshot.json").write_text(
                json.dumps({"records": [{"item": {"key": "AAAA1111", "version": 1, "data": {"title": "New"}}, "attachments": []}]}),
                encoding="utf-8",
            )
            (work / "evidence").mkdir()
            (work / "evidence" / "AAAA1111.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "zotero_item_key": "AAAA1111",
                        "evidence": [{"evidence_id": "AAAA1111-E001", "quote": "Text"}],
                    }
                ),
                encoding="utf-8",
            )

            report = run_migration(vault, apply=True, source_snapshot_id="test-snapshot")

            manifest = json.loads((work / "state" / "corpus_manifest.json").read_text(encoding="utf-8"))
            queue = (work / "state" / "task_queue.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(manifest["schema_version"], 2)
            self.assertEqual(len(queue), 1)
            evidence = json.loads((work / "evidence" / "AAAA1111.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["schema_version"], 2)
            self.assertEqual(report["evidence"]["migrated"], 1)
            backup = work / "backups" / "pre-v2-test-snapshot"
            self.assertTrue((backup / "90_Codex工作区" / "evidence" / "AAAA1111.json").is_file())

    def test_audit_apply_writes_audit_and_read_only_note_migration_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            work = vault / "90_Codex工作区"
            (work / "state").mkdir(parents=True)
            (work / "evidence").mkdir()
            (vault / "01_文献笔记").mkdir()
            (work / "state" / "corpus_manifest.json").write_text(
                json.dumps({"schema_version": 2, "records": []}), encoding="utf-8"
            )

            report = run_audit(vault, run_id="audit-1", apply=True)

            self.assertEqual(report["status"], "passed")
            self.assertTrue((work / "reports" / "audit-1-structure.json").is_file())
            self.assertTrue((work / "reports" / "audit-1-note-migration-dry-run.json").is_file())


if __name__ == "__main__":
    unittest.main()
