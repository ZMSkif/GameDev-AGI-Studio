"""Reference boards render local takes with hashes and refuse paths or links that do not belong."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


class ReferenceBoardTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="board ")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        (self.root / "take a.png").write_bytes(PNG)
        (self.root / "b.png").write_bytes(PNG + b"x")
        self.board = {
            "title": "Robot <round 2>",
            "issue": "https://github.com/example/game/issues/3",
            "groups": [{"title": "A", "variants": [
                {"image": "take a.png", "label": "A1", "verdict": "selected", "prompt": "brass <robot>",
                 "provider": "fal.ai", "model": "example/model"},
                {"image": "b.png", "label": "A2", "verdict": "rejected", "reason": "feet merge"},
            ]}],
        }

    def run_cli(self, out="board.html"):
        path = self.root / "board.json"
        path.write_text(json.dumps(self.board), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPTS / "reference_board.py"), "--board", str(path),
                               "--out", str(self.root / out), "--lang", "ru"],
                              capture_output=True, text=True, encoding="utf-8", timeout=60)

    def test_renders_takes_with_verdicts_hashes_and_escaped_text(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        html = (self.root / "board.html").read_text(encoding="utf-8")
        self.assertIn('src="take%20a.png"', html)
        self.assertIn('data-verdict="selected"', html)
        self.assertIn("Отклонён", html)
        self.assertIn("brass &lt;robot&gt;", html)
        self.assertIn("Robot &lt;round 2&gt;", html)
        self.assertIn("sha256 ", html)
        self.assertIn("issues/3", html)

    def test_refuses_images_outside_the_folder_and_remote_images(self):
        for image in ("../outside.png", "/etc/passwd.png", "https://example.com/a.png", "notes.txt"):
            with self.subTest(image=image):
                self.board["groups"][0]["variants"][0]["image"] = image
                result = self.run_cli(out=f"refused-{abs(hash(image))}.html")
                self.assertEqual(result.returncode, 1)
                self.assertFalse((self.root / f"refused-{abs(hash(image))}.html").exists())

    def test_refuses_signed_links_and_unknown_verdicts(self):
        self.board["groups"][0]["variants"][0]["reason"] = "https://cdn.example.com/a.png?token=abc"
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("signed URL", result.stderr)
        self.board["groups"][0]["variants"][0]["reason"] = "ok"
        self.board["groups"][0]["variants"][0]["verdict"] = "great"
        self.assertEqual(self.run_cli().returncode, 1)

    def test_does_not_overwrite(self):
        (self.root / "board.html").write_text("keep", encoding="utf-8")
        self.assertEqual(self.run_cli().returncode, 1)
        self.assertEqual((self.root / "board.html").read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
