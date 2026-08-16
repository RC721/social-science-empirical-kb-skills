from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.research_kb.evaluation import build_gold_candidate_set, run_evaluation


class EvaluationTests(unittest.TestCase):
    def test_candidate_gold_set_is_deterministic_and_stratified(self):
        records = [
            {
                "zotero_item_key": f"KEY{i:05d}",
                "paper_type": "quantitative-empirical" if i % 2 else "bibliometric",
                "evidence_level": "fulltext" if i % 3 else "abstract-only",
                "title": f"Paper {i}",
            }
            for i in range(40)
        ]
        first = build_gold_candidate_set({"records": records}, size=30)
        second = build_gold_candidate_set({"records": list(reversed(records))}, size=30)
        self.assertEqual(first, second)
        self.assertEqual(len(first["items"]), 30)
        self.assertEqual(first["review_status"], "candidate-needs-human-verification")
        self.assertGreater(len({item["stratum"] for item in first["items"]}), 1)

    def test_evaluation_apply_writes_candidate_and_does_not_claim_human_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            state = vault / "90_Codex工作区" / "state"
            state.mkdir(parents=True)
            records = [
                {"zotero_item_key": f"KEY{i:05d}", "paper_type": "quantitative-empirical", "evidence_level": "fulltext"}
                for i in range(35)
            ]
            (state / "corpus_manifest.json").write_text(json.dumps({"records": records}), encoding="utf-8")

            report = run_evaluation(vault, apply=True)

            self.assertEqual(report["candidate_count"], 30)
            self.assertEqual(report["human_verified_count"], 0)
            self.assertEqual(report["status"], "needs-human-verification")
            self.assertTrue((vault / "90_Codex工作区" / "evals" / "gold" / "candidate-gold-set.json").is_file())


if __name__ == "__main__":
    unittest.main()
