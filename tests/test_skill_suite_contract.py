from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "social-science-empirical-kb": ["references/workflow-contract.md", "references/state-and-human-gates.md", "references/third-party-skill-policy.md"],
    "social-science-literature-discovery": ["references/search-protocol.md", "references/ranking-and-screening.md", "assets/search-protocol-template.yaml"],
    "zotero-corpus-sync": ["references/identity-and-write-safety.md"],
    "social-science-paper-extraction": ["references/evidence-rules.md", "references/paper-type-routing.md", "references/extraction-contract.md", "assets/literature-note-template.md"],
    "quantitative-study-audit": ["references/design-families.md", "references/causal-language.md", "assets/audit-template.json"],
    "research-knowledge-synthesis": ["references/claim-and-relationship-rules.md", "references/synthesis-contract.md", "assets/claim-template.md", "assets/topic-review-template.md"],
    "obsidian-research-kb": ["references/managed-markdown.md", "references/vault-quality-gates.md", "assets/managed-note-template.md"],
    "research-kb-evolution": ["references/correction-and-promotion.md", "references/gold-evaluation.md"],
    "policy-citation-knowledge-base": [],
}


class SkillSuiteContractTests(unittest.TestCase):
    def test_all_skill_frontmatter_has_only_name_and_description(self):
        for name in SKILLS:
            path = ROOT / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
            self.assertIsNotNone(match, name)
            keys = [line.split(":", 1)[0] for line in match.group(1).splitlines() if ":" in line]
            self.assertEqual(keys, ["name", "description"], name)
            self.assertIn(f"name: {name}", match.group(0))
            self.assertNotIn("TODO", text)
            self.assertLess(len(text.splitlines()), 500)

    def test_required_progressive_disclosure_resources_exist(self):
        for name, resources in SKILLS.items():
            for relative in resources:
                self.assertTrue((ROOT / name / relative).is_file(), f"{name}: missing {relative}")

    def test_openai_metadata_mentions_exact_skill(self):
        for name in SKILLS:
            text = (ROOT / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn(f"${name}", text)
            self.assertIn("allow_implicit_invocation: true", text)

    def test_compatibility_skill_is_thin_adapter(self):
        path = ROOT / "policy-citation-knowledge-base" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("$social-science-empirical-kb", text)
        self.assertIn("policy-citation", text)
        self.assertLess(len(text.splitlines()), 80)


if __name__ == "__main__":
    unittest.main()
