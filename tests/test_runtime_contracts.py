from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from research_kb.contracts import causal_language_gate, migrate_evidence_v1  # noqa: E402
from research_kb.migration import build_v2_manifest  # noqa: E402
from research_kb.notes import merge_managed_content  # noqa: E402


class RuntimeContractTests(unittest.TestCase):
    def test_manifest_v2_queues_snapshot_items_missing_from_v1(self):
        old = {
            "schema_version": 1,
            "collection_name": "Test",
            "collection_key": "COLL",
            "records": [
                {
                    "zotero_item_key": "AAAA1111",
                    "title": "Existing",
                    "filename": "Existing.md",
                    "evidence_level": "fulltext",
                    "extraction_status": "audited",
                }
            ],
        }
        snapshot = {
            "collection_name": "Test",
            "collection_key": "COLL",
            "records": [
                {
                    "item": {"key": "AAAA1111", "version": 4, "data": {"title": "Existing", "dateModified": "2026-08-15T00:00:00Z"}},
                    "attachments": [{"item": {"data": {"contentType": "application/pdf"}}, "fulltext": {"content": "paper"}}],
                },
                {
                    "item": {
                        "key": "BBBB2222",
                        "version": 1,
                        "data": {"title": "New", "DOI": "10.1000/TEST", "abstractNote": "Abstract", "dateModified": "2026-08-16T00:00:00Z"},
                    },
                    "attachments": [],
                },
            ],
        }

        manifest, tasks = build_v2_manifest(old, snapshot, source_snapshot_id="snapshot-1")

        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(len(manifest["records"]), 2)
        existing = next(x for x in manifest["records"] if x["zotero_item_key"] == "AAAA1111")
        new = next(x for x in manifest["records"] if x["zotero_item_key"] == "BBBB2222")
        self.assertEqual(existing["ingestion_status"], "pdf-ready")
        self.assertEqual(existing["extraction_status"], "extracted")
        self.assertEqual(new["ingestion_status"], "imported")
        self.assertEqual(new["extraction_status"], "pending")
        self.assertEqual(new["evidence_level"], "abstract-only")
        self.assertEqual(new["doi"], "10.1000/test")
        self.assertEqual(existing["last_changed"], "2026-08-15T00:00:00Z")
        self.assertIn("last_processed", existing)
        self.assertIn("version_relation", existing)
        self.assertEqual([x["item_key"] for x in tasks], ["BBBB2222"])

    def test_manifest_queues_probable_duplicate_for_human_identity_review(self):
        old = {
            "schema_version": 1,
            "records": [
                {"zotero_item_key": "AAAA1111", "title": "A Study of Policy Evidence", "doi": "10.1000/test", "evidence_level": "fulltext"}
            ],
        }
        snapshot = {
            "records": [
                {"item": {"key": "AAAA1111", "version": 1, "data": {"title": "A Study of Policy Evidence", "DOI": "10.1000/test"}}, "attachments": []},
                {"item": {"key": "BBBB2222", "version": 1, "data": {"title": "A Study of Policy Evidence", "DOI": "10.1000/test"}}, "attachments": []},
            ]
        }

        manifest, tasks = build_v2_manifest(old, snapshot, source_snapshot_id="snapshot-2")

        duplicate = next(row for row in manifest["records"] if row["zotero_item_key"] == "BBBB2222")
        self.assertEqual(tasks[0]["task"], "resolve-identity")
        self.assertEqual(tasks[0]["status"], "needs-review")
        self.assertEqual(duplicate["review_status"], "needs-review")
        self.assertEqual(duplicate["duplicate_candidates"], ["AAAA1111"])

    def test_evidence_v1_migration_preserves_original_quote(self):
        old = {
            "schema_version": 1,
            "zotero_item_key": "AAAA1111",
            "evidence": [
                {
                    "evidence_id": "AAAA1111-E001",
                    "quote": "The estimate was 0.42.",
                    "section": "results",
                    "pdf_page": 8,
                    "locator_quality": "exact-page",
                }
            ],
        }

        migrated = migrate_evidence_v1(old, source_hash="abc123", extracted_at="2026-08-16T00:00:00Z")

        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["evidence"][0]["original_text"], "The estimate was 0.42.")
        self.assertNotIn("quote", migrated["evidence"][0])
        self.assertEqual(migrated["evidence"][0]["source_hash"], "abc123")

    def test_managed_merge_preserves_researcher_section(self):
        existing = """---\ntype: literature-note\n---\n\n# Title\n\n## 研究者笔记\n\n这段人工内容必须保留。\n"""
        managed = "## 一句话结论\n\n这是新的自动内容。"

        merged = merge_managed_content(existing, managed)
        replaced = merge_managed_content(merged, "## 一句话结论\n\n第二版自动内容。")

        self.assertIn("这段人工内容必须保留。", replaced)
        self.assertIn("第二版自动内容。", replaced)
        self.assertNotIn("这是新的自动内容。", replaced)
        self.assertEqual(replaced.count("research-kb:managed:start"), 1)

    def test_causal_language_gate_uses_design_not_author_wording(self):
        self.assertEqual(causal_language_gate("causal", "observational"), "prohibited")
        self.assertEqual(causal_language_gate("causal", "quasi-experimental"), "qualified-only")
        self.assertEqual(causal_language_gate("causal", "experimental"), "allowed")
        self.assertEqual(causal_language_gate("associational", "observational"), "qualified-only")


if __name__ == "__main__":
    unittest.main()
