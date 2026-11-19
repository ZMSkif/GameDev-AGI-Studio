"""Unit tests for scripts/mine_lessons.py: classes, the noise guard, --since, --drop and the retain guard."""
import contextlib
import importlib.util
import io
import json
import re
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("mine_lessons", REPO_ROOT / "scripts" / "mine_lessons.py")
ml = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ml)

HEADER = '# Review: Agent "{title}" finished\n\n- Verdict: {v}\n\n---\n\n'


class MineCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def review(self, number, slug, body, verdict="blocked", title=None):
        """A file named like the archiver names them; the header title defaults to the slug in words."""
        name = f"2026-11-19_{number:02d}_agent-{slug}-finished_{verdict}.md"
        title = title or slug.replace("-", " ").capitalize()
        (self.dir / name).write_text(HEADER.format(title=title, v=verdict.upper()) + body, encoding="utf-8")

    def classes(self, report):
        return {lesson["class"]: lesson for lesson in report["lessons"]}


class PieceKeyTest(unittest.TestCase):
    def test_real_titles_share_one_key_per_piece(self):
        same = [
            ("Review WP0 wearable pipeline pilot", "Re-review WP0 wearables fix round"),
            ("Review CN1 citizens, host and events", "Review cn1 round 2"),
            ("Review city WA-0 asset pipeline stage", "Review wa0 fixes"),
            ("Review joystick jump and run carry", "Review joystick jump and run carry"),
            ("Review pause freeze fix and overlay", "Re-review pause freeze fix and overlay again"),
        ]
        for a, b in same:
            self.assertEqual(ml.piece_key(a), ml.piece_key(b), (a, b))

    def test_different_pieces_get_different_keys(self):
        keys = {ml.piece_key(t) for t in ("Review CN1 citizens", "Review CA1B buildings", "Review city CK2 NPC package",
                                          "Review credits screen rework", "Review audio loading and sounds")}
        self.assertEqual(keys, {"cn1", "ca1b", "ck2", "credits-screen-rework", "audio-loading-and-sounds"})

    def test_review_words_are_not_piece_codes(self):
        self.assertEqual(ml.piece_key("Second review of fix round r16"), "r16")
        self.assertEqual(ml.piece_key("Review pass 2 of the menu"), "menu")


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

    def test_a_re_review_with_another_file_name_is_the_same_piece(self):
        # The real archive: the first review and the fix-round re-review of WP0 have different names.
        self.review(5, "review-wp0-wearable-pipeline-pilot", "## Notes\n- One label is cut off at 360 px.\n",
                    title="Review WP0 wearable pipeline pilot")
        self.review(9, "re-review-wp0-wearables-fix-round", "## Notes\n- The label is still cut off.\n",
                    title="Re-review WP0 wearables fix round")
        report = ml.mine(self.dir)
        self.assertNotIn("text-clipping", self.classes(report))
        self.assertEqual(report["dropped"][0]["files"][0][:13], "2026-11-19_05")

    def test_severity_ends_at_the_next_heading(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nThe pause freeze.\n## Should-fix\n- The music fades late.\n")
        self.assertNotIn("audio-lifecycle", self.classes(ml.mine(self.dir)))

    def test_no_blockers_heading_is_not_severe(self):
        for heading in ("## No blockers", "## Blockers: none", "### Zero must-fix items"):
            with self.subTest(heading=heading):
                for f in self.dir.glob("*.md"):
                    f.unlink()
                self.review(1, "review-a", f"VERDICT: CONFIRMED\n\n{heading}\n- The music fades late on iOS.\n",
                            "confirmed")
                self.assertNotIn("audio-lifecycle", self.classes(ml.mine(self.dir)))

    def test_a_pass_line_is_not_an_occurrence(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\n- Music playback passed all checks.\n")
        report = ml.mine(self.dir)
        self.assertNotIn("audio-lifecycle", self.classes(report))
        self.assertEqual(report["dropped"], [])

    def test_a_pass_line_that_names_a_defect_still_counts(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\n- Music passed on desktop but is stuck at 0 on iOS.\n")
        self.assertTrue(self.classes(ml.mine(self.dir))["audio-lifecycle"]["severe"])
        cases = {"check-that-cannot-fail": "- The suite passes, but mutant M3 survived.",
                 "text-clipping": "- The layout check passes, yet the German label is clipped at 360 px."}
        for cid, line in cases.items():
            with self.subTest(cls=cid):
                for f in self.dir.glob("*.md"):
                    f.unlink()
                self.review(1, "review-a", f"VERDICT: BLOCKED\n\n## BLOCKER\n{line}\n")
                self.assertTrue(self.classes(ml.mine(self.dir))[cid]["severe"])


class ScopeTest(MineCase):
    def test_since_reports_only_lessons_with_a_new_occurrence(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
        self.review(5, "review-b", "VERDICT: BLOCKED\n\n## Must-fix\n1. The collider overhang is 0.9 m.\n")
        report = ml.mine(self.dir, since=1)
        self.assertEqual((report["files"], report["new_files"]), (2, 1))
        self.assertEqual(set(self.classes(report)), {"collider-mismatch"})
        self.assertIn("Next run: --since 5", ml.render(report))

    def test_repeats_across_runs_add_up(self):
        # Run 1 sees one piece (below the guard); run 2 sees a second piece and must keep the lesson.
        self.review(1, "review-npc", "## Notes\n- The stale assertion catches nothing.\n", "confirmed")
        self.assertNotIn("check-that-cannot-fail", self.classes(ml.mine(self.dir, since=0)))
        self.review(2, "review-city", "## Notes\n- Mutant M3 survived.\n", "confirmed")
        lesson = self.classes(ml.mine(self.dir, since=1))["check-that-cannot-fail"]
        self.assertEqual(lesson["independent_occurrences"], 2)
        self.assertEqual(len(lesson["new_files"]), 1)

    def test_real_archive_shape_still_parses(self):
        self.review(66, "review-ca1b-buildings-and-kiosks",
                    "VERDICT: BLOCKED\n\n## Must-fix, per asset\n1. **`stage_truck_v1`, tier A.** a lumpy, melted blob\n")
        self.assertIn("primitive-or-mangled-asset", self.classes(ml.mine(self.dir)))

    def test_drop_leaves_a_class_out(self):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
        report = ml.mine(self.dir, drop=("audio-lifecycle",))
        self.assertEqual(report["lessons"], [])
        self.assertEqual(report["removed"][0]["class"], "audio-lifecycle")
        self.assertIn("Dropped as false hits", ml.render(report))


class FakeHindsight:
    """Stands in for urlopen: records each payload and answers like Hindsight 1.2.2."""

    def __init__(self, answer=None, error=None):
        self.sent, self.answer, self.error = [], answer, error

    def __call__(self, req, timeout=0):
        self.sent.append(json.loads(req.data.decode("utf-8")))
        if self.error:
            raise self.error
        body = json.dumps(self.answer if self.answer is not None else
                          {"success": True, "bank_id": "b", "items_count": 1, "async": False}).encode("utf-8")

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return body

        return Resp()


class RetainTest(MineCase):
    REPO = "owner/game"

    def report(self, **kw):
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck at volume 0\n")
        return ml.mine(self.dir, **kw)

    def retain(self, fake, report=None, forbid=(), token="t1"):
        with mock.patch.object(ml.urllib.request, "urlopen", side_effect=fake):
            return ml.retain(report or self.report(), "http://127.0.0.1:8888", "gamedev-studio::studio", self.REPO,
                             list(forbid), token=token)

    def test_lessons_and_the_run_marker_go_to_the_bank_with_provenance(self):
        fake = FakeHindsight()
        self.assertEqual(self.retain(fake), [])
        lesson, marker = (s["items"][0] for s in fake.sent)
        self.assertTrue({"source_type", "source", "source_rev", "recorded_by", "verified"} <= set(lesson["metadata"]))
        self.assertTrue(all(lesson["metadata"].values()))
        self.assertIn(self.REPO, lesson["metadata"]["source"])
        self.assertEqual(lesson["tags"], ["lesson", "lesson:audio-lifecycle", "repo:owner/game"])
        self.assertEqual(lesson["metadata"]["verified"], "false")
        self.assertEqual(marker["tags"], ["lessons-run", "repo:owner/game"])
        self.assertEqual(marker["metadata"]["archive_last"], "1")
        for item in (lesson, marker):
            self.assertNotIn("update_mode", item)

    def test_document_ids_differ_between_runs_and_games(self):
        ids = set()
        for repo, token in (("owner/game", "a"), ("owner/game", "b"), ("owner/other", "a")):
            fake = FakeHindsight()
            self.REPO = repo
            for f in self.dir.glob("*.md"):
                f.unlink()
            self.retain(fake, token=token)
            ids |= {s["items"][0]["document_id"] for s in fake.sent}
        self.assertEqual(len(ids), 6)
        self.assertTrue(all("::" in i for i in ids))

    def test_default_token_is_random(self):
        a, b = FakeHindsight(), FakeHindsight()
        report = self.report()
        self.retain(a, report, token=None)
        self.retain(b, report, token=None)
        self.assertNotEqual(a.sent[0]["items"][0]["document_id"], b.sent[0]["items"][0]["document_id"])

    def test_forbidden_text_in_content_is_not_retained(self):
        fake = FakeHindsight()
        refused = self.retain(fake, forbid=[re.compile("audio-lifecycle")])
        self.assertEqual(len(fake.sent), 1)  # only the run marker, which does not name the class
        self.assertIn("audio-lifecycle", refused[0][0])

    def test_forbidden_text_in_metadata_tags_or_id_is_not_retained(self):
        for pattern in ("owner/game", "gamedev-studio:lessons", "review archive"):  # metadata, tags, id
            with self.subTest(pattern=pattern):
                fake = FakeHindsight()
                refused = self.retain(fake, forbid=[re.compile(pattern)])
                self.assertEqual(fake.sent, [])
                self.assertEqual(len(refused), 2)

    def test_secret_in_source_file_name_is_not_retained(self):
        report = self.report()
        report["lessons"][0]["files"] = ["2026-11-19_01_agent-ghp_" + "a" * 36 + "-finished_blocked.md"]
        fake = FakeHindsight()
        refused = self.retain(fake, report)
        self.assertEqual(len(fake.sent), 1)
        self.assertEqual(len(refused), 1)

    def test_dropped_class_is_not_sent(self):
        fake = FakeHindsight()
        self.assertEqual(self.retain(fake, self.report(drop=("audio-lifecycle",))), [])
        self.assertEqual([s["items"][0]["tags"][0] for s in fake.sent], ["lessons-run"])

    def test_failed_answers_are_reported(self):
        cases = [FakeHindsight(answer={"success": False}), FakeHindsight(answer={"success": True, "items_count": 0}),
                 FakeHindsight(error=urllib.error.HTTPError("u", 500, "err", {}, None)),
                 FakeHindsight(error=urllib.error.URLError("refused"))]
        for fake in cases:
            with self.subTest(answer=fake.answer, error=fake.error):
                refused = self.retain(fake)
                self.assertEqual(len(refused), 2)


class CliTest(MineCase):
    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ml.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.call("--reviews", str(self.dir / "missing"))[0], 2)
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
        code, out, _ = self.call("--reviews", str(self.dir), "--json")
        self.assertEqual(code, 0)
        self.assertIn('"audio-lifecycle"', out)
        self.assertEqual(self.call("--reviews", str(self.dir), "--forbid", "(")[0], 2)
        self.assertEqual(self.call("--reviews", str(self.dir), "--drop", "no-such-class")[0], 2)
        self.assertEqual(self.call("--reviews", str(self.dir), "--retain", "http://x")[0], 2)
        self.assertEqual(self.call("--reviews", str(self.dir), "--retain", "http://x", "--repository", "bad")[0], 2)

    def test_out_inside_the_game_repository_is_refused(self):
        subprocess.run(["git", "init", "-q", str(self.dir)], check=True)
        self.review(1, "review-a", "VERDICT: BLOCKED\n\n## BLOCKER\nmusic stuck\n")
        code, _, err = self.call("--reviews", str(self.dir), "--out", str(self.dir / "report.md"))
        self.assertEqual(code, 2)
        self.assertIn("outside the game repository", err)
        self.assertFalse((self.dir / "report.md").exists())
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(self.call("--reviews", str(self.dir), "--out", str(Path(other) / "r.md"))[0], 0)


if __name__ == "__main__":
    unittest.main()
