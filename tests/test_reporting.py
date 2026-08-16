from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.research_kb.reporting import build_upgrade_report, write_upgrade_report


class ReportingTests(unittest.TestCase):
    def test_upgrade_report_exposes_completed_and_human_gated_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            work = vault / "90_Codex工作区"
            (work / "state").mkdir(parents=True)
            (work / "evidence").mkdir()
            (vault / "01_文献笔记").mkdir()
            manifest = {
                "schema_version": 2,
                "records": [
                    {
                        "zotero_item_key": "AAAA1111",
                        "evidence_level": "fulltext",
                        "paper_type": "quantitative-empirical",
                        "extraction_status": "extracted",
                        "review_status": "verified",
                    },
                    {
                        "zotero_item_key": "BBBB2222",
                        "evidence_level": "metadata-only",
                        "extraction_status": "pending",
                        "review_status": "needs-review",
                        "duplicate_candidates": ["AAAA1111"],
                    },
                ],
            }
            (work / "state" / "corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (work / "state" / "task_queue.jsonl").write_text(
                json.dumps({"item_key": "BBBB2222", "task": "resolve-identity", "status": "needs-review"}) + "\n",
                encoding="utf-8",
            )

            report = build_upgrade_report(vault)
            output = write_upgrade_report(vault, report)

            self.assertEqual(report["corpus"]["total"], 2)
            self.assertEqual(report["queue"]["resolve-identity"], 1)
            text = output.read_text(encoding="utf-8")
            self.assertIn("总记录：2", text)
            self.assertIn("身份冲突待人工确认：1", text)
            self.assertIn("不会自动合并", text)


if __name__ == "__main__":
    unittest.main()
