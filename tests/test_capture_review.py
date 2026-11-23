"""Regression coverage for game-independent browser evidence capture."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CHROMIUM = os.environ.get("GAMEDEV_TEST_CHROMIUM")
WEB_FIXTURE = """<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  button, output { display: block; position: absolute; width: 110px; height: 40px; }
  button { left: 20px; top: 20px; } output { left: 20px; top: 80px; overflow: hidden; }
  .regressed output { left: 90px; top: 35px; width: 900px; }
</style></head><body class="{variant}">
<button id="advance">Continue</button><output id="status"></output>
<a id="navigate" href="{next}">Go to another screen</a>
<script>
  const status = document.getElementById('status');
  status.textContent = localStorage.getItem('acted') ? 'Complete' : 'Ready';
  document.getElementById('advance').onclick = () => {{
    localStorage.setItem('acted', 'yes');
    status.textContent = 'Complete';
  }};
  if (document.body.className === 'regressed') throw Error('Intentional fixture regression');
</script></body></html>"""


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/same-redirect", "/cross-redirect"}:
            target = "/healthy" if self.path == "/same-redirect" else self.server.cross_target
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return
        variant = "regressed" if self.path == "/regressed" else "healthy"
        next_path = "/cross-redirect" if self.path == "/cross-build" else "/same-redirect"
        html = (WEB_FIXTURE.replace("{variant}", variant).replace("{next}", next_path)
                .replace("{{", "{").replace("}}", "}").encode())
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *_args):
        pass


class CaptureReviewTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="visual qa ")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.config_path = self.root / "scenario.json"
        self.config = {
            "issue": "https://github.com/example/web-fixture/issues/42",
            "before": {"url": "http://127.0.0.1:8888", "commit": "a" * 40},
            "after": {"url": "http://localhost:8890", "commit": "b" * 40},
            "ready_selector": "#status",
            "steps": [
                {"action": "text", "selector": "#status", "text": "Ready"},
                {"action": "tap", "selector": "#advance"},
                {"action": "text", "selector": "#status", "text": "Complete", "label": "Interaction"},
                {"action": "reload"},
                {"action": "text", "selector": "#status", "text": "Complete", "label": "Persistence"},
            ],
            "layout": {"within": ["#advance", "#status"], "no_overlap": [["#advance", "#status"]]},
            "timeout_ms": 1500,
        }

    def run_cli(self, out, *args):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "capture_review.py"), "--config", str(self.config_path),
             "--out", str(out), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
        )

    def start_fixture(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        return server, f"http://127.0.0.1:{server.server_port}"

    def test_rejects_remote_urls_credentials_and_file_urls(self):
        for url in ("https://example.com", "http://name@localhost", "file:///build/index.html",
                    "http://127.0.0.1:0", "http://localhost.example.org"):
            with self.subTest(url=url):
                self.config["after"]["url"] = url
                out = self.root / "result"
                result = self.run_cli(out)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("loopback HTTP(S) URL", result.stderr)
                self.assertFalse(out.exists())

    def test_rejects_actions_outside_the_declarative_scenario(self):
        self.config["steps"] = [{"action": "evaluate", "selector": "#status", "code": "alert(1)"}]
        result = self.run_cli(self.root / "result")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unsupported action", result.stderr)

    def test_reload_does_not_accept_a_selector(self):
        self.config["steps"] = [{"action": "reload", "selector": "#status"}]
        result = self.run_cli(self.root / "result")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("may also use", result.stderr)

    def test_refuses_existing_result(self):
        self.config["before"]["url"] = "http://[::1]:8888"
        result = self.run_cli(self.root)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("already exists", result.stderr)

    @unittest.skipUnless(CHROMIUM, "set GAMEDEV_TEST_CHROMIUM to exercise browser capture")
    def test_records_both_passing_and_regressing_builds(self):
        _, origin = self.start_fixture()
        self.config["before"]["url"] = f"{origin}/healthy"
        self.config["after"]["url"] = f"{origin}/regressed"
        out = self.root / "regressed"
        failed = self.run_cli(out, "--executable-path", CHROMIUM)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        data = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertFalse(data["passed"])
        self.assertEqual([item["name"] for item in data["viewports"]], ["portrait", "landscape", "square"])
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("Intentional fixture regression", index)
        self.assertIn('data-failed="true"', index)
        self.assertIn('class="stats"', index)
        for viewport in data["viewports"]:
            actual = viewport["builds"]
            self.assertTrue(actual["before"]["scenario_passed"], actual["before"])
            self.assertFalse(actual["after"]["scenario_passed"])
            self.assertGreaterEqual(actual["after"]["ready_ms"], 0)
            self.assertTrue(any(not check["passed"] for check in actual["after"]["checks"]
                                if check["type"] == "no_overlap"))
            self.assertTrue(any(not check["passed"] for check in actual["after"]["checks"]
                                if check["type"] == "within"))
            overlap = next(check for check in actual["after"]["checks"]
                           if check["type"] == "no_overlap" and not check["passed"])
            self.assertEqual([region["role"] for region in overlap["regions"]], ["element", "element", "overlap"])
            self.assertIn("expected", overlap)
            self.assertIn("actual", overlap)
            self.assertTrue(all(isinstance(check.get("at_ms"), int) for check in actual["after"]["checks"]))
            review = (out / viewport["report"]).read_text(encoding="utf-8")
            self.assertIn('data-show-region="r-after-', review)
            self.assertIn('class="marker"', review)
            self.assertTrue((out / viewport["report"]).is_file())
            directory = out / viewport["name"]
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["commit"], "b" * 40)
            for image in ("before.png", "after.png"):
                self.assertGreater((directory / image).stat().st_size, 0)
        self.config["after"]["url"] = f"{origin}/healthy"
        self.config["viewports"] = ["square"]
        video = ["--record-video"] if os.environ.get("GAMEDEV_TEST_VIDEO") == "1" else []
        fixed = self.run_cli(self.root / "fixed", "--executable-path", CHROMIUM, "--lang", "ru", *video)
        self.assertEqual(fixed.returncode, 0, fixed.stderr)
        self.assertIn("Пройдено", (self.root / "fixed" / "index.html").read_text(encoding="utf-8"))
        if video:
            report = (self.root / "fixed" / "square" / "review.html").read_text(encoding="utf-8")
            self.assertIn('href="../index.html"', report)
            self.assertLess(report.index('src="after.png"'), report.index('src="before.webm"'))
            for clip in ("before.webm", "after.webm"):
                self.assertGreater((self.root / "fixed" / "square" / clip).stat().st_size, 0)

    @unittest.skipUnless(CHROMIUM, "set GAMEDEV_TEST_CHROMIUM to exercise browser capture")
    def test_cross_origin_redirect_is_a_failure_and_is_not_captured(self):
        server, origin = self.start_fixture()
        _, another_origin = self.start_fixture()
        server.cross_target = f"{another_origin}/healthy"
        self.config["before"]["url"] = f"{origin}/same-build"
        self.config["after"]["url"] = f"{origin}/cross-build"
        self.config["viewports"] = ["square"]
        self.config["steps"] = [
            {"action": "click", "selector": "#navigate"},
            {"action": "visible", "selector": "#status", "label": "On destination"},
        ]
        out = self.root / "redirect"
        video = ["--record-video"] if os.environ.get("GAMEDEV_TEST_VIDEO") == "1" else []
        failed = self.run_cli(out, "--executable-path", CHROMIUM, *video)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        viewport, = json.loads((out / "summary.json").read_text(encoding="utf-8"))["viewports"]
        before, after = (viewport["builds"][side] for side in ("before", "after"))
        self.assertTrue(before["scenario_passed"], before)
        self.assertFalse(after["scenario_passed"])
        issue = "Main frame left its configured origin"
        self.assertIn(issue, after["errors"])
        self.assertIn(issue, (out / "index.html").read_text(encoding="utf-8"))
        self.assertNotIn("On destination", [check["name"] for check in after["checks"]])
        self.assertTrue((out / viewport["report"]).is_file())
        directory = out / "square"
        self.assertTrue((directory / "before.png").is_file())
        self.assertFalse((directory / "after.png").exists())
        if video:
            self.assertTrue((directory / "before.webm").is_file())
            self.assertFalse((directory / "after.webm").exists())


if __name__ == "__main__":
    unittest.main()
