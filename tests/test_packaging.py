from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from runtime.research_kb.packaging import SKILL_NAMES, package_skills


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_dry_run_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills"
            report = package_skills(ROOT, output, apply=False)
            self.assertFalse(output.exists())
            self.assertEqual(report["skill_count"], 9)
            self.assertEqual(report["mode"], "dry-run")

    def test_apply_publishes_clean_skills_runtime_and_release_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills"
            report = package_skills(ROOT, output, apply=True)
            self.assertEqual(report["status"], "passed")
            for name in SKILL_NAMES:
                self.assertTrue((output / name / "SKILL.md").is_file(), name)
                self.assertFalse(any((output / name).rglob("__pycache__")), name)
                self.assertFalse(any((output / name).rglob("*.pyc")), name)
            self.assertTrue((output / "social-science-empirical-kb" / "scripts" / "research-kb.py").is_file())
            self.assertTrue((output / "social-science-empirical-kb" / "scripts" / "research_kb" / "cli.py").is_file())

            release = output / "_release"
            versions = json.loads((release / "versions.json").read_text(encoding="utf-8"))
            self.assertEqual(versions["suite_version"], "0.1.0")
            self.assertEqual(versions["runtime_version"], "0.1.0")
            self.assertEqual(versions["schema_version"], "2.0.0")
            manifest = json.loads((release / "sha256-manifest.json").read_text(encoding="utf-8"))
            rel = "social-science-empirical-kb/SKILL.md"
            actual = hashlib.sha256((output / rel).read_bytes()).hexdigest()
            self.assertEqual(manifest["files"][rel], actual)
            archive = release / "social-science-empirical-kb-suite-0.1.0.zip"
            self.assertTrue(zipfile.is_zipfile(archive))
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn(rel, zipped.namelist())

    def test_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills"
            package_skills(ROOT, output, apply=True)
            before = {
                path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.rglob("*")
                if path.is_file() and path.suffix != ".zip"
            }
            package_skills(ROOT, output, apply=True)
            after = {
                path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.rglob("*")
                if path.is_file() and path.suffix != ".zip"
            }
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
