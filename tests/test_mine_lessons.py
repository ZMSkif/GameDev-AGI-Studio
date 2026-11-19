"""Unit tests for scripts/mine_lessons.py: classes, the noise guard, --since and the retain guard."""
import contextlib
import importlib.util
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("mine_lessons", REPO_ROOT / "scripts" / "mine_lessons.py")
ml = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ml)

HEADER = "# Review: x\n\n- Verdict: {v}\n\n---\n\n"


class MineCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def review(self, number, piece, body, verdict="blocked"):
        name = f"2026-11-19_{number:02d}_{piece}_{verdict}.md"
        (self.dir / name).write_text(HEADER.format(v=verdict.upper()) + body, encoding="utf-8")

    def classes(self, report):
        return {lesson["class"]: lesson for lesson in report["lessons"]}


class NoiseGuardTest(MineCase):
    def test_a_severe_single_occurrence_is_a_lesson(self):
        self.review(1, "review-audio", "VERDICT: BLOCKED\n\n## BLOCKER\n**B1.** The music volume stuck at 0.\n")
        lesson = self.classes(ml.mine(self.dir))["audio-lifecycle"]
        self.assertTrue(lesson["severe"])
        self.assertEqual(lesson["independent_occurrences"], 1)

    def test_one_plain_occurrence_is_below_the_guard(self):
        self.review(1, "review-ui", "VERDICT: CONFIRMED\n\n## Notes\n- One name runs off the tile edge.\n", "confirmed")
        report = ml.mine(self.dir)
        self.assertNotIn("text-clipping", self.classes(report))
        self.assertEqual([d["class"] for d in report["dropped"]], ["text-clipping"])

    def test_two_pieces_make_a_lesson(self):
        self.review(1, "review-npc", "VERDICT: CONFIRMED\n\n## Should-fix\n- The stale assertion catches nothing.\n", "confirmed")
        self.review(2, "review-city", "VERDICT: CONFIRMED\n\n## Should-fix\n- Mutant M8 survived the suite.\n", "confirmed")
        lesson = self.classes(ml.mine(self.dir))["check-that-cannot-fail"]
        self.assertEqual(lesson["independent_occurrences"], 2)
        self.assertFalse(lesson["severe"])

    def test_re_reviews_of_one_piece_count_once(self):
        for n in (1, 2, 3):
            self.review(n, "review-npc", "VERDICT: CONFIRMED\n\n## Notes\n- A soak longer than 30-minute windows.\n", "confirmed")
        report = ml.mine(self.dir)
        self.assertNotIn("long-run-only-failure", self.classes(report))
        self.assertEqual(report["dropped"][0]["class"], "long-run-only-failure")

    def test_severity_ends_at_the_next_heading(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nThe pause freeze.\n## Should-fix\n- The music fades late.\n")
        report = ml.mine(self.dir)
        self.assertNotIn("audio-lifecycle", self.classes(report))


class ScopeTest(MineCase):
    def test_since_skips_older_files_and_reports_the_next_start(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
        self.review(5, "review-b", "VERDICT: BLOCKED\n\n## Must-fix\n1. The collider overhang is 0.9 m.\n")
        report = ml.mine(self.dir, since=1)
        self.assertEqual(report["files"], 1)
        self.assertEqual(set(self.classes(report)), {"collider-mismatch"})
        self.assertIn("Next run: --since 5", ml.render(report))

    def test_real_archive_shape_still_parses(self):
        self.review(66, "agent-review-ca1b-buildings-and-kiosks-finished",
                    "VERDICT: BLOCKED\n\n## Must-fix, per asset\n1. **`stage_truck_v1`, tier A.** a lumpy, melted blob\n")
        self.assertIn("primitive-or-mangled-asset", self.classes(ml.mine(self.dir)))


class RetainTest(MineCase):
    def report(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck at volume 0\n")
        return ml.mine(self.dir)

    def test_lessons_go_to_the_bank_with_provenance(self):
        sent = []

        class Resp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def fake(req, timeout=0):
            sent.append(json.loads(req.data.decode("utf-8")))
            return Resp()

        with mock.patch.object(ml.urllib.request, "urlopen", side_effect=fake):
            refused = ml.retain(self.report(), "http://127.0.0.1:8888", "gamedev-studio::studio", [])
        self.assertEqual(refused, [])
        item = sent[0]["items"][0]
        self.assertEqual(set(item["metadata"]), {"source_type", "source", "source_rev", "recorded_by", "verified"})
        self.assertIn("lesson:audio-lifecycle", item["tags"])
        self.assertEqual(item["metadata"]["verified"], "false")

    def test_forbidden_text_is_not_retained(self):
        with mock.patch.object(ml.urllib.request, "urlopen") as urlopen:
            refused = ml.retain(self.report(), "http://x", "b", [re.compile("audio-lifecycle")])
        urlopen.assert_not_called()
        self.assertEqual(refused[0][0], "audio-lifecycle")

    def test_cli_exit_codes(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(ml.main(["--reviews", str(self.dir / "missing")]), 2)
            self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
            self.assertEqual(ml.main(["--reviews", str(self.dir), "--json"]), 0)
            self.assertEqual(ml.main(["--reviews", str(self.dir), "--forbid", "("]), 2)
        self.assertIn('"audio-lifecycle"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
