from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from research_kb.state import (  # noqa: E402
    build_task_queue,
    evidence_id,
    initialize_workspace,
    mark_dependents_stale,
    validate_extraction,
)


class RuntimeStateTests(unittest.TestCase):
    def test_initialize_workspace_creates_contract_files_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            paths = initialize_workspace(vault, collection_key="COLL", domain="policy-citation")
            config = paths["config"].read_text(encoding="utf-8")
            paths["config"].write_text(config + "# researcher override\n", encoding="utf-8")
            initialize_workspace(vault, collection_key="OTHER", domain="different")

            self.assertIn('collection_key: "COLL"', paths["config"].read_text(encoding="utf-8"))
            self.assertIn("# researcher override", paths["config"].read_text(encoding="utf-8"))
            self.assertTrue(paths["skills_lock"].is_file())
            self.assertTrue(paths["manifest_schema"].is_file())
            self.assertTrue(paths["evidence_schema"].is_file())
            self.assertTrue(paths["audit_schema"].is_file())
            self.assertTrue(paths["correction_schema"].is_file())
            self.assertTrue((vault / "90_Codex工作区" / "config" / "domains" / "policy-citation.yaml").is_file())
            self.assertTrue((vault / "90_Codex工作区" / "feedback" / "corrections.jsonl").is_file())

            lock = paths["skills_lock"].read_text(encoding="utf-8")
            for skill_id in (
                "zotero:Zotero",
                "openalex-database",
                "paper-lookup",
                "citation-management",
                "pdf:pdf",
                "scientific-critical-thinking",
                "scholar-evaluation",
                "statistical-analysis",
                "statsmodels",
                "everyday-causal-skills",
                "SLR-Engine",
                "paper-search-pro",
                "obsidian-ontology-sync",
                "verification-before-completion",
            ):
                self.assertIn(f'skill_id: "{skill_id}"', lock)
            self.assertNotIn('commit: "installed-snapshot"', lock)
            self.assertNotIn("UNPINNED-CANDIDATE", lock)

    def test_task_queue_is_stable_and_deduplicated(self):
        records = [
            {"zotero_item_key": "BBBB2222", "extraction_status": "pending", "review_status": "unreviewed"},
            {"zotero_item_key": "AAAA1111", "extraction_status": "failed", "review_status": "needs-review"},
            {"zotero_item_key": "BBBB2222", "extraction_status": "pending", "review_status": "unreviewed"},
        ]
        queue = build_task_queue(records)
        self.assertEqual([x["item_key"] for x in queue], ["AAAA1111", "BBBB2222"])
        self.assertEqual(queue[0]["status"], "needs-review")

    def test_dependency_changes_mark_only_downstream_artifacts_stale(self):
        graph = {
            "paper:AAAA1111": ["claim:c1", "concept:x"],
            "claim:c1": ["review:r1"],
            "concept:x": ["review:r2"],
            "paper:BBBB2222": ["claim:c2"],
        }
        self.assertEqual(
            mark_dependents_stale(graph, ["paper:AAAA1111"]),
            ["claim:c1", "concept:x", "review:r1", "review:r2"],
        )

    def test_evidence_id_is_stable_for_same_source_location(self):
        first = evidence_id("AAAA1111", "finding", "results", 8, "Table 3", "The effect was positive.")
        second = evidence_id("AAAA1111", "finding", "results", 8, "Table 3", "The effect was positive.")
        changed = evidence_id("AAAA1111", "finding", "results", 9, "Table 3", "The effect was positive.")
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertRegex(first, r"^AAAA1111-E[0-9A-F]{10}$")

    def test_validate_extraction_rejects_unsupported_objective_values(self):
        extraction = {
            "schema_version": 2,
            "zotero_item_key": "AAAA1111",
            "evidence_level": "fulltext",
            "study_design": {"sample_size": "1,000", "evidence_ids": []},
            "variables": [],
            "models": [],
            "findings": [],
        }
        errors = validate_extraction(extraction, evidence_ids={"AAAA1111-E0000000001"})
        self.assertIn("study_design.sample_size requires evidence_ids", errors)

        extraction["study_design"]["evidence_ids"] = ["AAAA1111-E0000000001"]
        self.assertEqual(validate_extraction(extraction, evidence_ids={"AAAA1111-E0000000001"}), [])


if __name__ == "__main__":
    unittest.main()
