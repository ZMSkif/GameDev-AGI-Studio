"""Frame sampling for video references: what is chosen, what is written, what is refused."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import video_watch  # noqa: E402

FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


class PlanTests(unittest.TestCase):
    info = {"duration": 6.0, "fps": 30.0}

    def test_scene_even_and_dense_moments_keep_their_reason(self):
        moments = video_watch.plan(self.info, [2.0, 4.0], 1.0, (2.5, 3.0, 4), 60)
        reasons = dict(moments)
        self.assertEqual(moments[0], (0.0, "scene"))
        self.assertEqual(reasons[4.0], "scene")
        self.assertEqual(reasons[1.0], "uniform")
        self.assertEqual([t for t, reason in moments if reason == "dense"], [2.5, 2.75, 3.0])
        self.assertEqual(moments, sorted(moments))

    def test_moments_closer_than_a_frame_are_merged(self):
        moments = video_watch.plan(self.info, [1.0, 1.01], 1.0, None, 60)
        self.assertEqual(sum(1 for t, _ in moments if 0.99 <= t <= 1.02), 1)

    def test_cap_keeps_dense_range(self):
        moments = video_watch.plan(self.info, [], 0.1, (1.0, 2.0, 10), 15)
        self.assertLessEqual(len(moments), 15)
        self.assertEqual(sum(1 for _, reason in moments if reason == "dense"), 11)

    def test_range_outside_the_clip_is_refused(self):
        with self.assertRaises(ValueError):
            video_watch.plan(self.info, [], 1.0, (7.0, 8.0, 10), 60)


@unittest.skipUnless(FFMPEG, "FFmpeg and ffprobe are needed for an end-to-end run")
class EndToEndTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory(prefix="video watch ")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.clip = self.root / "clip one.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=3",
                        "-pix_fmt", "yuv420p", str(self.clip)], check=True)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "video_watch.py"), *map(str, args)],
                              capture_output=True, text=True, encoding="utf-8", timeout=120)

    def test_writes_frames_metadata_and_report(self):
        out = self.root / "frames out"
        result = self.run_cli(self.clip, "--out", out, "--range", "1", "1.5", "--dense-fps", "8",
                              "--copy-source", "--lang", "ru")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((out / "frames.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source"]["width"], 320)
        self.assertAlmostEqual(data["source"]["duration"], 3.0, places=1)
        self.assertEqual(len(data["source"]["sha256"]), 64)
        self.assertTrue(any(frame["reason"] == "dense" for frame in data["frames"]))
        for frame in data["frames"]:
            self.assertGreater((out / frame["file"]).stat().st_size, 0)
        report = (out / "report.html").read_text(encoding="utf-8")
        self.assertIn('src="source.mp4"', report)
        self.assertIn('data-seek="1.000"', report)
        self.assertIn("Смотреть отсюда", report)
        self.assertTrue((out / "source.mp4").is_file())

    def test_refuses_existing_output_and_non_video(self):
        out = self.root / "exists"
        out.mkdir()
        result = self.run_cli(self.clip, "--out", out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("already exists", result.stderr)
        text = self.root / "notes.txt"
        text.write_text("not a video", encoding="utf-8")
        result = self.run_cli(text, "--out", self.root / "fresh")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "fresh").exists())


if __name__ == "__main__":
    unittest.main()
