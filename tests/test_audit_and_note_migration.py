from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.research_kb.audit import audit_workspace, plan_note_migration


class AuditAndNoteMigrationTests(unittest.TestCase):
    def _vault(self, tmp: str) -> Path:
        vault = Path(tmp)
        work = vault / "90_Codex工作区"
        (work / "state").mkdir(parents=True)
        (work / "evidence").mkdir()
        (vault / "01_文献笔记").mkdir()
        manifest = {
            "schema_version": 2,
            "records": [
                {"zotero_item_key": "AAAA1111", "filename": "Paper.md", "evidence_level": "fulltext"},
                {"zotero_item_key": "BBBB2222", "filename": "Missing.md", "evidence_level": "metadata-only"},
            ],
        }
        (work / "state" / "corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        evidence = {
            "schema_version": 2,
            "zotero_item_key": "AAAA1111",
            "evidence_level": "fulltext",
            "evidence": [{"evidence_id": "AAAA1111-E1234567890", "original_text": "text"}],
        }
        (work / "evidence" / "AAAA1111.json").write_text(json.dumps(evidence), encoding="utf-8")
        return vault

    def test_audit_reports_structural_status_and_missing_note_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._vault(tmp)
            note = vault / "01_文献笔记" / "Paper.md"
            note.write_text(
                "---\ntype: literature-note\nzotero_item_key: AAAA1111\n---\n\n"
                "<!-- research-kb:managed:start -->\n内容\n<!-- research-kb:managed:end -->\n\n"
                "## 研究者笔记\n人工\n",
                encoding="utf-8",
            )
            before = note.read_bytes()

            report = audit_workspace(vault)

            self.assertEqual(note.read_bytes(), before)
            self.assertEqual(report["counts"]["manifest_records"], 2)
            self.assertEqual(report["counts"]["literature_notes"], 1)
            self.assertEqual(report["counts"]["evidence_v2"], 1)
            self.assertEqual(report["missing_note_keys"], ["BBBB2222"])
            self.assertEqual(report["errors"], [])

    def test_audit_detects_duplicate_keys_and_unbalanced_managed_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._vault(tmp)
            first = vault / "01_文献笔记" / "Paper.md"
            second = vault / "01_文献笔记" / "Duplicate.md"
            first.write_text("---\nzotero_item_key: AAAA1111\n---\n<!-- research-kb:managed:start -->\n", encoding="utf-8")
            second.write_text("---\nzotero_item_key: AAAA1111\n---\n", encoding="utf-8")

            report = audit_workspace(vault)

            self.assertTrue(any("duplicate zotero_item_key" in value for value in report["errors"]))
            self.assertTrue(any("unbalanced managed markers" in value for value in report["errors"]))

    def test_note_migration_plan_preserves_legacy_bytes_and_requires_boundary_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._vault(tmp)
            note = vault / "01_文献笔记" / "Paper.md"
            note.write_text("---\nzotero_item_key: AAAA1111\n---\n\n高质量旧笔记\n", encoding="utf-8")
            before = note.read_bytes()

            report = plan_note_migration(vault)

            self.assertEqual(note.read_bytes(), before)
            self.assertEqual(report["notes"], 1)
            self.assertEqual(report["needs_boundary_review"], 1)
            self.assertEqual(report["items"][0]["action"], "manual-boundary-required")

    def test_audit_checks_wikilinks_only_in_active_knowledge_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = self._vault(tmp)
            (vault / "03_概念知识").mkdir()
            (vault / "90_Codex工作区" / "internal").mkdir()
            (vault / "03_概念知识" / "Concept.md").write_text("# Concept\n", encoding="utf-8")
            (vault / "90_Codex工作区" / "internal" / "Concept.md").write_text("# Internal duplicate\n", encoding="utf-8")
            (vault / "01_文献笔记" / "Paper.md").write_text(
                "---\nzotero_item_key: AAAA1111\n---\n\n[[Concept]]\n[[Missing]]\n", encoding="utf-8"
            )

            report = audit_workspace(vault)

            self.assertEqual(len(report["broken_links"]), 1)
            self.assertEqual(report["broken_links"][0]["target"], "Missing")
            self.assertEqual(report["duplicate_stems"], {})
            self.assertTrue(any("broken Wikilinks" in value for value in report["errors"]))


if __name__ == "__main__":
    unittest.main()
