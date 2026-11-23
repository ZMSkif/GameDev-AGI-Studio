"""Exercise the review manifest through its public CLI."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_evidence.py"


class ReviewEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.workspace = Path(temp.name)
        self.root = self.workspace / "game captures"
        self.root.mkdir()
        self.shot = self.root / "after shot.png"
        self.clip = self.root / "playback.mp4"
        self.shot.write_bytes(b"abc")
        self.clip.write_bytes(b"clip")
        self.plan = self.workspace / "plan.json"
        self.manifest = self.workspace / "manifest.json"
        self.document = {
            "issue": "https://github.com/example/game/issues/12",
            "commit": "a" * 40,
            "files": [
                {"path": self.shot.name, "role": "after"},
                {"path": self.clip.name, "role": "clip"},
            ],
        }

    def run_cli(self, action, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), action, "--root", str(self.root), *arguments],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )

    def build(self, *arguments):
        self.plan.write_text(json.dumps(self.document), encoding="utf-8")
        return self.run_cli("build", "--plan", str(self.plan), *arguments)

    def verify(self):
        return self.run_cli("verify", "--manifest", str(self.manifest))

    def test_build_and_verify_manifest(self):
        build = self.build("--out", str(self.manifest))
        self.assertEqual(build.returncode, 0, build.stderr)
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["issue"], self.document["issue"])
        self.assertEqual(manifest["commit"], self.document["commit"])
        self.assertEqual(manifest["files"][0], {
            "path": self.shot.name, "role": "after", "bytes": 3,
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        })
        verified = self.verify()
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertIn("Verified 2 evidence file(s)", verified.stdout)

    def test_verify_detects_same_size_edit_and_missing_file(self):
        result = self.build("--out", str(self.manifest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.shot.write_bytes(b"xyz")
        self.clip.unlink()
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"{self.shot.name}: bytes or SHA-256 changed", result.stderr)
        self.assertIn(f"{self.clip.name}:", result.stderr)

    def test_build_refuses_to_overwrite_existing_manifest(self):
        self.manifest.write_bytes(b"previous receipt")
        result = self.build("--out", str(self.manifest))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.manifest.read_bytes(), b"previous receipt")

    def test_build_rejects_unnormalized_and_absolute_paths(self):
        for name in ("../private.png", "/tmp/private.png", "C:/private.png", "a/./b.png"):
            with self.subTest(name=name):
                self.document["files"][0]["path"] = name
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("relative path", result.stderr)

    def test_build_rejects_escaping_symlink(self):
        outside = self.workspace / "private.png"
        outside.write_bytes(b"outside evidence root")
        link = self.root / "link.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"Cannot create a symlink: {error}")
        self.document["files"][0]["path"] = link.name
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside the evidence root", result.stderr)

    def test_build_rejects_duplicate_paths_across_case(self):
        self.document["files"][1]["path"] = self.shot.name.upper()
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate evidence path", result.stderr)


if __name__ == "__main__":
    unittest.main()
