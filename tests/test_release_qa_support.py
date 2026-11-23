"""Exercise generic preflight and reference evidence through the CLI."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ISSUE = "https://github.com/example/project/issues/30"
DECISION = "https://github.com/example/project/issues/42#issuecomment-61"
COMMIT = "a" * 40


class ReleaseQaSupportTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.archive = self.root / "build.zip"
        with ZipFile(self.archive, "w", ZIP_DEFLATED) as archive:
            archive.writestr("assets/", b"")
            archive.writestr("index.html", b"123")
            archive.writestr("assets/app.wasm", b"abc" * 80)
        self.out = self.root / "report.json"

    def run_cli(self, script, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )

    def release(self, *args):
        return self.run_cli("build_release_report.py", "--archive", self.archive, "--out", self.out, *args)

    def test_local_inventory_without_platform_or_browser_claims(self):
        result = self.release("--platform", "playgama", "--platform", "youtube-playables",
                              "--max-archive-bytes", "20")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.out.read_text())
        self.assertEqual(report["archive"]["archive_bytes"], self.archive.stat().st_size)
        self.assertEqual(report["archive"]["sha256"], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertEqual(report["archive"]["file_count"], 2)
        self.assertEqual(report["archive"]["uncompressed_bytes"], 243)
        self.assertEqual(report["archive"]["files"][0]["path"], "index.html")
        self.assertEqual(report["archive_budget"]["status"], "failed")
        self.assertIsNone(report["candidate_browser_qa"])
        self.assertEqual(report["archive_browser_match"], {"status": "not_run"})
        self.assertEqual(report["pause"], {"status": "not_run"})
        self.assertEqual(report["save"], {"status": "not_run"})
        self.assertEqual([target["status"] for target in report["platforms"]], ["unverified", "unverified"])

    def test_candidate_measurements_and_partial_named_checks(self):
        pause = {"name": "still paused", "type": "step", "passed": True, "detail": "text matched"}
        save = {"name": "load after refresh", "type": "step", "passed": False, "detail": "old value"}
        qa = self.root / "summary.json"
        qa.write_text(json.dumps({
            "version": 1,
            "issue": ISSUE,
            "builds": {"after": {"commit": COMMIT}},
            "viewports": [
                {"name": "wide", "builds": {"after": {
                    "ready_ms": 13.2, "scenario_passed": False, "checks": [pause, save], "errors": [],
                }}},
                {"name": "square", "builds": {"after": {
                    "ready_ms": None, "scenario_passed": False, "checks": [], "errors": ["not ready"],
                }}},
            ],
        }))
        result = self.release("--qa-result", qa, "--pause-check", pause["name"], "--save-check", save["name"])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.out.read_text())
        self.assertEqual(report["candidate_browser_qa"]["candidate_commit"], COMMIT)
        self.assertEqual(report["archive_browser_match"], {"status": "unverified"})
        self.assertEqual([v["ready_ms"] for v in report["candidate_browser_qa"]["viewports"]], [13.2, None])
        self.assertEqual(report["pause"]["status"], "incomplete")
        self.assertEqual(report["save"]["status"], "failed")
        self.assertEqual(report["pause"]["observations"][0], {"viewport": "wide", "status": "passed"})
        self.assertEqual(report["pause"]["observations"][1], {"viewport": "square", "status": "not_run"})

        self.out.unlink()
        page = self.root / "release.html"
        result = self.release("--qa-result", qa, "--pause-check", pause["name"], "--save-check", save["name"],
                              "--platform", "playgama", "--html", page, "--lang", "ru")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = page.read_text(encoding="utf-8")
        self.assertIn("Не полностью", html)
        self.assertIn("Не подтверждено", html)
        self.assertIn("assets/app.wasm", html)
        self.assertIn("готова 13.2 мс", html)
        self.assertIn("Есть проваленная проверка", html)

    def test_invalid_zip_or_qa_does_not_create_report(self):
        qa = self.root / "summary.json"
        qa.write_text("{}")
        self.assertNotEqual(self.release("--qa-result", qa).returncode, 0)
        self.assertFalse(self.out.exists())
        self.archive.write_bytes(b"not zip")
        self.assertNotEqual(self.release().returncode, 0)
        self.assertFalse(self.out.exists())

    def reference_plan(self, url):
        (self.root / "before.png").write_bytes(b"capture")
        (self.root / "approved reference.png").write_bytes(b"reference")
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({
            "issue": ISSUE, "commit": COMMIT,
            "files": [
                {"path": "before.png", "role": "before"},
                {"path": "approved reference.png", "role": "reference", "decision_url": url},
            ],
        }))
        return plan

    def test_reference_keeps_approval_and_uses_a_distinct_gallery_role(self):
        manifest = self.root / "manifest.json"
        result = self.run_cli("review_evidence.py", "build", "--root", self.root, "--out", manifest,
                              "--plan", self.reference_plan(DECISION))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli("review_evidence.py", "verify", "--root", self.root, "--manifest", manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(manifest.read_text())["files"][1]["decision_url"], DECISION)
        report = self.root / "review.html"
        result = self.run_cli("render_review.py", "--root", self.root, "--manifest", manifest, "--out", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        html = report.read_text(encoding="utf-8")
        self.assertIn('data-role="reference"><div class="media">', html)
        self.assertIn('<img src="approved%20reference.png"', html)
        self.assertIn(f'<a class="spacer" href="{DECISION}">Approval record</a>', html)

    def test_reference_rejects_a_non_github_decision_url(self):
        result = self.run_cli("review_evidence.py", "build", "--root", self.root,
                              "--plan", self.reference_plan("javascript:alert(1)"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("decision_url", result.stderr)


if __name__ == "__main__":
    unittest.main()
