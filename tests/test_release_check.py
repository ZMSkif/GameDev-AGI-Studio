"""Unit tests for scripts/release_check.py, plus the real CHANGELOG against the current version."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("release_check", REPO_ROOT / "scripts" / "release_check.py")
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

CHANGELOG = """# Changelog

## [1.2.0] - 2026-12-01

### Added
- New thing.

## [1.1.0] - 2026-11-01

### Fixed
- Old thing.
"""


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        for rel in rc.MANIFESTS:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(json.dumps({"name": "demo", "version": "1.2.0"}), encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rc.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()


class ReleaseCheckTest(FixtureCase):
    def test_matching_tag_writes_only_its_section(self):
        notes = self.root / "notes.md"
        code, _, _ = self.call("--tag", "v1.2.0", "--notes-out", str(notes))
        self.assertEqual(code, 0)
        text = notes.read_text(encoding="utf-8")
        self.assertIn("New thing.", text)
        self.assertNotIn("Old thing.", text)
        self.assertNotIn("## [1.2.0]", text)

    def test_last_section_runs_to_the_end(self):
        self.assertEqual(rc.section(CHANGELOG, "1.1.0"), "### Fixed\n- Old thing.")

    def test_tag_not_matching_a_manifest_fails(self):
        (self.root / ".codex-plugin/plugin.json").write_text(json.dumps({"version": "1.1.0"}), encoding="utf-8")
        code, _, err = self.call("--tag", "v1.2.0")
        self.assertEqual(code, 1)
        self.assertIn(".codex-plugin/plugin.json: version '1.1.0' does not match tag v1.2.0", err)

    def test_missing_or_empty_section_fails(self):
        code, _, err = self.call("--tag", "v9.9.9")
        self.assertEqual(code, 1)
        self.assertIn("no non-empty '## [9.9.9]", err)
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## [1.2.0] - 2026-12-01\n\n## [1.1.0] - 2026-11-01\nx\n",
                                                encoding="utf-8")
        code, _, err = self.call("--tag", "v1.2.0")
        self.assertEqual(code, 1)

    def test_bad_tag_and_missing_argument(self):
        self.assertEqual(self.call("--tag", "1.2.0")[0], 1)
        self.assertEqual(self.call("--tag", "v1.2")[0], 1)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(rc.main([]), 2)

    def test_heading_needs_a_date(self):
        (self.root / "CHANGELOG.md").write_text("## [1.2.0]\n- x\n", encoding="utf-8")
        self.assertEqual(self.call("--tag", "v1.2.0")[0], 1)


class RealRepositoryTest(unittest.TestCase):
    def test_current_version_has_a_changelog_section(self):
        version = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        errors, notes = rc.check(REPO_ROOT, f"v{version}")
        self.assertEqual(errors, [])
        self.assertTrue(notes)


if __name__ == "__main__":
    unittest.main()
