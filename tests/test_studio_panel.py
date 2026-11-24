"""The studio panel answers only its own page with its token, and only runs the fixed actions."""

import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import studio_panel  # noqa: E402


class PanelTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="panel game ")
        self.addCleanup(scratch.cleanup)
        self.game = Path(scratch.name)
        (self.game / ".gamedev-studio").write_text("", encoding="utf-8")
        reports = self.game / "qa-reports" / "run1"
        reports.mkdir(parents=True)
        (reports / "index.html").write_text("<p>report</p>", encoding="utf-8")
        (self.game / "secret.txt").write_text("private", encoding="utf-8")
        self.panel = studio_panel.Panel(self.game, "en")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), studio_panel.handler_for(self.panel))
        self.panel.server = self.server
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None, headers=None, cookie=True, host=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        sent = {"Host": host or f"127.0.0.1:{self.port}", **(headers or {})}
        if cookie:
            sent["Cookie"] = f"gds={self.panel.token}"
        data = json.dumps(body).encode() if body is not None else None
        if data is not None:
            sent["Content-Type"] = "application/json"
        connection.request(method, path, body=data, headers=sent)
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, payload, dict(response.getheaders())

    def test_token_sets_a_strict_cookie(self):
        status, _, headers = self.request("GET", f"/?t={self.panel.token}", cookie=False)
        self.assertEqual(status, 303)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.assertEqual(self.request("GET", "/?t=wrong", cookie=False)[0], 403)

    def test_requests_without_cookie_or_from_other_hosts_are_refused(self):
        self.assertEqual(self.request("GET", "/api/state", cookie=False)[0], 403)
        self.assertEqual(self.request("GET", "/api/state", host="attacker.example")[0], 421)

    def test_page_and_state(self):
        status, page, _ = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(self.panel.token.encode(), page)
        status, payload, _ = self.request("GET", "/api/state")
        state = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertEqual({tool["id"] for tool in state["tools"]},
                         {tool["id"] for tool in self.panel.catalog["tools"]})
        self.assertEqual(state["runs"], [])

    def test_actions_need_the_header_and_a_local_origin(self):
        body = {"id": "chromium", "key": "chromium_path", "value": sys.executable}
        self.assertEqual(self.request("POST", "/api/tools/config", body)[0], 403)
        headers = {"X-Studio-Token": self.panel.token, "Origin": "https://evil.example"}
        self.assertEqual(self.request("POST", "/api/tools/config", body, headers)[0], 403)
        headers["Origin"] = f"http://127.0.0.1:{self.port}"
        status, payload, _ = self.request("POST", "/api/tools/config", body, headers)
        self.assertEqual(status, 200, payload)
        self.assertEqual(self.request("POST", "/api/run-anything", {"cmd": "rm"}, headers)[0], 404)

    def test_install_without_confirmation_is_refused(self):
        headers = {"X-Studio-Token": self.panel.token}
        status, payload, _ = self.request("POST", "/api/tools/install", {"id": "ffmpeg"}, headers)
        self.assertEqual(status, 400)
        self.assertIn("yes", json.loads(payload)["error"])

    def test_files_only_from_the_reports_folder(self):
        status, payload, _ = self.request("GET", "/files/run1/index.html")
        self.assertEqual((status, payload), (200, b"<p>report</p>"))
        for path in ("/files/../secret.txt", "/files/%2e%2e/secret.txt", "/files/run1/../../secret.txt"):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)

    def test_qa_run_accepts_only_scenarios_in_the_qa_folder(self):
        headers = {"X-Studio-Token": self.panel.token}
        status, payload, _ = self.request("POST", "/api/qa/run", {"file": "secret.txt"}, headers)
        self.assertEqual(status, 400)
        status, payload, _ = self.request("POST", "/api/qa/example", {}, headers)
        self.assertEqual(status, 200, payload)
        scenarios = json.loads(self.request("GET", "/api/state")[1])["scenarios"]
        self.assertEqual([item["file"] for item in scenarios], ["qa/example.json"])
        self.assertEqual([p["name"] for p in scenarios[0]["profiles"]], ["phone", "desktop"])
        bad = {"file": "qa/example.json", "profiles": ["phone; rm -rf /"]}
        self.assertEqual(self.request("POST", "/api/qa/run", bad, headers)[0], 400)


if __name__ == "__main__":
    unittest.main()
