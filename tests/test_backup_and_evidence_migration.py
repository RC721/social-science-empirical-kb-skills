from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.research_kb.backup import create_baseline_backup
from runtime.research_kb.migration import migrate_evidence_directory


class BackupAndEvidenceMigrationTests(unittest.TestCase):
    def test_backup_copies_exact_targets_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            (vault / "01_文献笔记").mkdir(parents=True)
            (vault / "90_Codex工作区" / "evidence").mkdir(parents=True)
            note = vault / "01_文献笔记" / "Paper.md"
            evidence = vault / "90_Codex工作区" / "evidence" / "AAAA1111.json"
            note.write_text("人工内容\n", encoding="utf-8")
            evidence.write_text('{"schema_version": 1}\n', encoding="utf-8")

            result = create_baseline_backup(
                vault,
                "baseline-test",
                targets=("01_文献笔记", "90_Codex工作区/evidence"),
            )

            backup = vault / "90_Codex工作区" / "backups" / "baseline-test"
            self.assertEqual(result["file_count"], 2)
            self.assertEqual((backup / "01_文献笔记" / "Paper.md").read_text(encoding="utf-8"), "人工内容\n")
            hashes = json.loads((backup / "sha256-manifest.json").read_text(encoding="utf-8"))["files"]
            self.assertEqual(hashes["01_文献笔记/Paper.md"], hashlib.sha256(note.read_bytes()).hexdigest())

    def test_evidence_migration_dry_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "evidence"
            source.mkdir()
            path = source / "AAAA1111.json"
            original = {
                "schema_version": 1,
                "zotero_item_key": "AAAA1111",
                "evidence": [{"evidence_id": "AAAA1111-E001", "quote": "Result", "section": "results"}],
            }
            path.write_text(json.dumps(original), encoding="utf-8")

            report = migrate_evidence_directory(source, apply=False, extracted_at="2026-08-16T00:00:00Z")

            self.assertEqual(report["migratable"], 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_evidence_migration_applies_independently_and_reports_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "evidence"
            source.mkdir()
            good = source / "AAAA1111.json"
            bad = source / "broken.json"
            good.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "zotero_item_key": "AAAA1111",
                        "evidence": [{"evidence_id": "AAAA1111-E001", "quote": "Result", "section": "results"}],
                    }
                ),
                encoding="utf-8",
            )
            bad.write_text("{not json", encoding="utf-8")

            report = migrate_evidence_directory(
                source,
                apply=True,
                extracted_at="2026-08-16T00:00:00Z",
                source_hashes={"AAAA1111": "pdfhash"},
            )

            migrated = json.loads(good.read_text(encoding="utf-8"))
            self.assertEqual(report["migrated"], 1)
            self.assertEqual(report["failed"], 1)
            self.assertEqual(migrated["evidence"][0]["original_text"], "Result")
            self.assertEqual(migrated["evidence"][0]["source_hash"], "pdfhash")
            self.assertEqual(bad.read_text(encoding="utf-8"), "{not json")


if __name__ == "__main__":
    unittest.main()
