"""Exercise HTML rendering through the review CLIs."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
COMMIT = "a" * 40


class ReviewReportTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.root = self.directory / "capture set"
        self.root.mkdir()
        self.shot = self.root / "after #é.png"
        self.shot.write_bytes(b"shot")
        (self.root / "comparison.svg").write_text("<svg></svg>", encoding="utf-8")
        (self.root / "capture deck.webm").write_bytes(b"clip")
        self.plan = self.directory / "plan.json"
        self.plan.write_text(json.dumps({
            "issue": "https://github.com/example/game/issues/21",
            "commit": COMMIT,
            "files": [
                {"path": self.shot.name, "role": "after"},
                {"path": "comparison.svg", "role": "source"},
                {"path": "capture deck.webm", "role": "clip"},
            ],
        }), encoding="utf-8")
        self.manifest = self.directory / "manifest.json"
        self.report = self.directory / "report.html"
        build = self.run_cli("review_evidence.py", "build", "--root", str(self.root),
                             "--plan", str(self.plan), "--out", str(self.manifest))
        self.assertEqual(build.returncode, 0, build.stderr)

    def run_cli(self, script, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *arguments],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )

    def render(self, *arguments):
        return self.run_cli("render_review.py", "--root", str(self.root), "--manifest",
                            str(self.manifest), "--out", str(self.report), *arguments)

    def test_render_escapes_boundaries_and_encodes_relative_media(self):
        result = self.render("--title", "Review <script>alert(1)</script>", "--verdict", "blocked")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.report.read_text(encoding="utf-8")
        self.assertIn("Review &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn('src="capture%20set/after%20%23%C3%A9.png"', html)
        self.assertIn('<video src="capture%20set/capture%20deck.webm" controls', html)
        self.assertNotIn('src="capture%20set/comparison.svg"', html)
        self.assertIn('data-status="blocked">Blocked<', html)
        self.assertIn(f'https://github.com/example/game/commit/{COMMIT}', html)
        self.assertIn('href="https://github.com/example/game/issues/21"', html)

    def test_refuses_modified_or_missing_evidence(self):
        self.shot.write_bytes(b"oops")
        changed = self.render()
        self.assertEqual(changed.returncode, 1)
        self.assertIn("bytes or SHA-256 changed", changed.stderr)
        self.shot.unlink()
        missing = self.render()
        self.assertEqual(missing.returncode, 1)
        self.assertIn(self.shot.name, missing.stderr)
        self.assertFalse(self.report.exists())

    def test_uses_requested_report_language(self):
        result = self.render("--lang", "ru", "--verdict", "confirmed")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.report.read_text(encoding="utf-8")
        self.assertIn('<html lang="ru">', html)
        self.assertIn("<h1>Материалы приёмки</h1>", html)
        self.assertIn('data-status="confirmed">Принято<', html)

    def test_refuses_invalid_manifest_and_existing_output(self):
        self.report.write_text("existing", encoding="utf-8")
        result = self.render()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.report.read_text(encoding="utf-8"), "existing")
        self.report.unlink()
        self.manifest.write_text("{}", encoding="utf-8")
        result = self.render()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.report.exists())


if __name__ == "__main__":
    unittest.main()
