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

## [Unreleased]

### Added
- Not yet released.

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
            self.manifest(rel, {"name": "demo", "version": "1.2.0"})
        self.changelog(CHANGELOG)

    def manifest(self, rel, obj):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(json.dumps(obj), encoding="utf-8")

    def changelog(self, text):
        (self.root / "CHANGELOG.md").write_text(text, encoding="utf-8")

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
        self.assertEqual(notes.read_text(encoding="utf-8"), "### Added\n- New thing.\n")

    def test_last_section_runs_to_the_end(self):
        self.assertEqual(rc.section(CHANGELOG, "1.1.0"), "### Fixed\n- Old thing.")

    def test_each_manifest_must_match(self):
        for rel in rc.MANIFESTS:
            with self.subTest(manifest=rel):
                self.setUp()
                self.manifest(rel, {"version": "1.1.0"})
                code, _, err = self.call("--tag", "v1.2.0")
                self.assertEqual(code, 1)
                self.assertIn(f"{rel}: version '1.1.0' does not match tag v1.2.0", err)

    def test_unreadable_manifests_fail_without_a_traceback(self):
        for content in ("[1, 2]", "{not json", b"\xff\xfe\x00bad"):
            with self.subTest(content=content):
                path = self.root / rc.MANIFESTS[0]
                (path.write_bytes if isinstance(content, bytes) else lambda c: path.write_text(c, encoding="utf-8"))(content)
                code, _, err = self.call("--tag", "v1.2.0")
                self.assertEqual(code, 1)
                self.assertIn(rc.MANIFESTS[0], err)
        (self.root / rc.MANIFESTS[1]).unlink()
        self.assertIn("cannot read", self.call("--tag", "v1.2.0")[2])

    def test_missing_or_unreadable_changelog_fails(self):
        (self.root / "CHANGELOG.md").unlink()
        code, _, err = self.call("--tag", "v1.2.0")
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: cannot read", err)
        (self.root / "CHANGELOG.md").write_bytes(b"## [1.2.0] - 2026-12-01\n\xff\n")
        self.assertEqual(self.call("--tag", "v1.2.0")[0], 1)

    def test_missing_empty_or_heading_only_section_fails(self):
        code, _, err = self.call("--tag", "v9.9.9")
        self.assertEqual(code, 1)
        self.assertIn("no '## [9.9.9]", err)
        for body in ("", "### Added\n"):
            with self.subTest(body=body):
                self.changelog(f"# Changelog\n\n## [1.2.0] - 2026-12-01\n{body}\n## [1.1.0] - 2026-11-01\nx\n")
                self.assertEqual(self.call("--tag", "v1.2.0")[0], 1)

    def test_tag_shape(self):
        for tag in ("1.2.0", "v1.2", "v1.2.0.1", "v1.2.0x", "v1.2.0\n", "v1.2.0-rc.1", "v1.2.0+build", "v١.٢.٠"):
            with self.subTest(tag=tag):
                self.assertEqual(self.call("--tag", tag)[0], 1)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(rc.main([]), 2)

    def test_tag_shape_alone_rejects_pre_release_and_build_versions(self):
        # The manifests and the heading match the tag, so only the tag rule can refuse it.
        for version in ("1.2.0-rc.1", "1.2.0+build.5", "١.٢.٠"):
            with self.subTest(version=version):
                for rel in rc.MANIFESTS:
                    self.manifest(rel, {"version": version})
                self.changelog(f"## [{version}] - 2026-12-01\n- x\n")
                code, _, err = self.call("--tag", f"v{version}")
                self.assertEqual(code, 1)
                self.assertIn("is not v<major>.<minor>.<patch>", err)

    def test_heading_needs_exactly_version_and_a_real_date(self):
        for text in ("## [1.2.0]\n- x\n", "## [1.2.0] - 2026-12-01 extra\n- x\n", "## [1.2.0] - 2026-13-45\n- x\n",
                     "## [1x2x0] - 2026-12-01\n- x\n"):
            with self.subTest(text=text):
                self.changelog(text)
                self.assertEqual(self.call("--tag", "v1.2.0")[0], 1)

    def test_duplicate_section_fails(self):
        self.changelog("## [1.2.0] - 2026-12-01\n- a\n\n## [1.2.0] - 2026-12-02\n- b\n")
        code, _, err = self.call("--tag", "v1.2.0")
        self.assertEqual(code, 1)
        self.assertIn("2 sections for 1.2.0", err)

    def test_notes_out_that_cannot_be_written_fails(self):
        code, _, err = self.call("--tag", "v1.2.0", "--notes-out", str(self.root / "missing" / "notes.md"))
        self.assertEqual(code, 1)
        self.assertIn("--notes-out: cannot write", err)


class RealRepositoryTest(unittest.TestCase):
    def test_current_version_has_a_changelog_section(self):
        version = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        errors, notes = rc.check(REPO_ROOT, f"v{version}")
        self.assertEqual(errors, [])
        self.assertTrue(notes)

    def test_release_workflow_checks_main_and_splits_permissions(self):
        text = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn('git merge-base --is-ancestor "$GITHUB_SHA" origin/main', text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("needs: check", text)
        self.assertEqual(text.count("contents: write"), 1)


if __name__ == "__main__":
    unittest.main()
