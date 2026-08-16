from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from research_kb.orchestration import build_stage_tasks, create_run  # noqa: E402


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "records": [
                {
                    "zotero_item_key": "AAAA1111",
                    "extraction_status": "pending",
                    "review_status": "unreviewed",
                    "synthesis_status": "pending",
                },
                {
                    "zotero_item_key": "BBBB2222",
                    "extraction_status": "extracted",
                    "review_status": "verified",
                    "synthesis_status": "integrated",
                },
                {
                    "zotero_item_key": "CCCC3333",
                    "extraction_status": "failed",
                    "review_status": "needs-review",
                    "synthesis_status": "stale",
                },
            ]
        }

    def test_extract_tasks_include_pending_and_failed_only(self):
        tasks = build_stage_tasks(self.manifest, "extract")
        self.assertEqual([x["item_key"] for x in tasks], ["AAAA1111", "CCCC3333"])
        self.assertEqual(tasks[1]["status"], "needs-review")

    def test_update_tasks_preserve_stage_order(self):
        tasks = build_stage_tasks(self.manifest, "update", item_keys={"AAAA1111"})
        self.assertEqual(
            [x["stage"] for x in tasks],
            ["sync", "extract", "quantitative-audit", "render-note", "synthesize", "render", "audit"],
        )

    def test_update_is_incremental_and_identity_conflicts_stop_at_human_gate(self):
        manifest = {
            "records": [
                {"zotero_item_key": "AAAA1111", "extraction_status": "extracted", "synthesis_status": "integrated", "review_status": "verified"},
                {"zotero_item_key": "BBBB2222", "extraction_status": "pending", "synthesis_status": "pending", "review_status": "needs-review", "duplicate_candidates": ["AAAA1111"]},
                {"zotero_item_key": "CCCC3333", "extraction_status": "extracted", "synthesis_status": "stale", "review_status": "verified"},
            ]
        }

        tasks = build_stage_tasks(manifest, "update")

        self.assertNotIn("AAAA1111", {task["item_key"] for task in tasks})
        conflict = [task for task in tasks if task["item_key"] == "BBBB2222"]
        self.assertEqual([task["stage"] for task in conflict], ["resolve-identity"])
        self.assertEqual(conflict[0]["status"], "needs-review")
        stale = [task["stage"] for task in tasks if task["item_key"] == "CCCC3333"]
        self.assertEqual(stale, ["synthesize", "render", "audit"])

    def test_create_run_is_dry_by_default_and_apply_writes_descriptor(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            tasks = build_stage_tasks(self.manifest, "extract")
            preview = create_run(vault, "extract", "run-1", tasks, batch_size=10, apply=False)
            self.assertEqual(preview["task_count"], 2)
            self.assertFalse((vault / "90_Codex工作区" / "runs" / "run-1").exists())

            applied = create_run(vault, "extract", "run-1", tasks, batch_size=10, apply=True)
            self.assertTrue(Path(applied["run_directory"]).is_dir())
            self.assertTrue((Path(applied["run_directory"]) / "tasks.jsonl").is_file())

    def test_create_run_assigns_stable_paper_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            tasks = [
                {"item_key": f"KEY{i:05d}", "stage": stage, "status": "pending"}
                for i in range(12)
                for stage in ("extract", "audit")
            ]
            applied = create_run(vault, "update", "run-batches", tasks, batch_size=10, apply=True)
            rows = [__import__("json").loads(line) for line in (Path(applied["run_directory"]) / "tasks.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(applied["batch_count"], 2)
            self.assertEqual({row["batch"] for row in rows if row["item_key"] == "KEY00009"}, {1})
            self.assertEqual({row["batch"] for row in rows if row["item_key"] == "KEY00010"}, {2})


if __name__ == "__main__":
    unittest.main()
