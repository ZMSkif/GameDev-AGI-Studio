"""Unit tests for scripts/mine_lessons.py.

The invariants: every pattern hit is counted and shown with its file and line; text rules only annotate
doubts; reviews whose titles share a piece code are one piece; nothing is stored unless named with --keep;
storing stops at the first failure; the run marker waits for every kept lesson; no document_id is sent.
"""
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

    def review(self, number, title, body, verdict="blocked"):
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        name = f"2026-11-19_{number:02d}_agent-{slug}-finished_{verdict}.md"
        (self.dir / name).write_text(HEADER.format(title=title, v=verdict.upper()) + body, encoding="utf-8")

    def clear(self):
        for f in self.dir.glob("*.md"):
            f.unlink()

    def where(self, report, cid):
        """Which list a class landed in: lessons, doubtful, below or None."""
        for key in ("lessons", "doubtful", "below"):
            for entry in report[key]:
                if entry["class"] == cid:
                    return key, entry
        return None, None


class PieceTest(unittest.TestCase):
    def test_one_group_per_piece_on_real_titles(self):
        titles = {5: "Review WP0 wearable pipeline pilot", 9: "Re-review WP0 wearables fix round",
                  21: "Review WA-0 asset pipeline stage", 37: "Review city CA1a + WA-0 fixes",
                  64: "Review CN1 citizens, host and events", 70: "Review CA1b buildings and kiosks",
                  16: "Second review of fix round r16", 36: "Review zero-click start and r17b",
                  7: "Review joystick, jump and run carry", 10: "Review joystick, jump and run carry",
                  26: "Review jump teaching piece"}
        g = ml.piece_groups(titles)
        self.assertEqual(g[5], g[9])
        self.assertEqual(g[21], g[37])          # CA1a + WA-0 share WA-0: one piece, the safe direction
        self.assertEqual(g[7], g[10])
        self.assertEqual(len({g[64], g[70], g[16], g[36], g[26], g[5], g[21], g[7]}), 8)

    def test_review_item_ids_and_versions_never_split_a_piece(self):
        same = ["Review CN1 citizens", "Re-check B1 fix for CN1", "Review CN1 fix of B1", "R2 re-review of CN1",
                "Review CN1 after integration of CK2", "Re-review v2 of CN1", "Review B1 fix in CN1",
                "Re-review CN1: fix for B2 regression"]
        g = ml.piece_groups(dict(enumerate(same)))
        self.assertEqual(len(set(g.values())), 1, g)

    def test_titles_without_a_code_use_their_words(self):
        g = ml.piece_groups({1: "Re-review jump teaching, round 3", 2: "Review jump teaching piece",
                             3: "Review credits screen rework"})
        self.assertEqual(g[1], g[2])
        self.assertNotEqual(g[1], g[3])
        self.assertEqual(ml.piece_key("Review v2 of the menu"), "menu")


class GuardTest(MineCase):
    def test_two_pieces_make_a_lesson(self):
        self.review(1, "Review CK2 npc", "## Should-fix\n- The stale assertion catches nothing.\n", "confirmed")
        self.review(2, "Review CS1 scene", "## Should-fix\n- Mutant M8 survived the suite.\n", "confirmed")
        key, entry = self.where(ml.mine(self.dir), "check-that-cannot-fail")
        self.assertEqual(key, "lessons")
        self.assertEqual(entry["solid_pieces"], ["ck2", "cs1"])

    def test_re_reviews_of_one_piece_count_once(self):
        for n, title in ((1, "Review WP0 wearable pipeline pilot"), (2, "Re-review WP0 wearables fix round"),
                         (3, "Review B1 fix in WP0")):
            self.review(n, title, "## Notes\n- A soak longer than 30-minute windows.\n", "confirmed")
        self.assertEqual(self.where(ml.mine(self.dir), "long-run-only-failure")[0], "below")

    def test_a_single_blocker_is_a_lesson(self):
        self.review(1, "Review CN1", "VERDICT: BLOCKED\n\n## BLOCKER\n**B1.** The music volume stuck at 0.\n")
        key, entry = self.where(ml.mine(self.dir), "audio-lifecycle")
        self.assertEqual(key, "lessons")
        self.assertTrue(entry["severe"])

    def test_severity_ends_at_the_next_heading(self):
        self.review(1, "Review CN1", "## BLOCKER\nThe pause freeze.\n## Should-fix\n- The music fades late.\n")
        self.assertEqual(self.where(ml.mine(self.dir), "audio-lifecycle")[0], "below")

    def test_a_blocker_section_that_says_none_is_not_severe(self):
        # The real _41 shape.
        for none in ("None.", "None. All the validators and the tests pass."):
            with self.subTest(none=none):
                self.clear()
                self.review(41, "Review city CA1a + WA-0 fixes", f"## BLOCKER\n{none}\n\n**B1 is fixed.**\n"
                            "- **Awning crest:** the blue shards and white slivers are gone.\n", "confirmed")
                key, entry = self.where(ml.mine(self.dir), "primitive-or-mangled-asset")
                self.assertEqual(key, "below")
                self.assertIn("the section says None", entry["hits"][0]["doubts"])

    def test_none_starting_a_sentence_keeps_the_blocker(self):
        for line in ("None of the music buttons work.", "Nothing plays after the ad: the music is stuck."):
            with self.subTest(line=line):
                self.clear()
                self.review(1, "Review CN1", f"## BLOCKER\n{line}\n")
                key, entry = self.where(ml.mine(self.dir), "audio-lifecycle")
                self.assertEqual(key, "lessons")
                self.assertTrue(entry["severe"])

    def test_heading_forms(self):
        for heading, severe in (("## No blockers", False), ("## Blockers: none", False),
                                ("### Zero must-fix items", False), ("## Must-fix list: none.", False),
                                ("## Must-fix: no music after resume", True)):
            with self.subTest(heading=heading):
                self.clear()
                self.review(1, "Review CN1", f"{heading}\n- The music stops after the ad.\n")
                self.assertEqual(self.where(ml.mine(self.dir), "audio-lifecycle")[1]["hits"][0]["severe"], severe)


class DoubtTest(MineCase):
    """Doubts annotate; they never remove a hit. Paired cases from both reviewers."""

    def hit(self, line, heading="## Notes"):
        self.clear()
        self.review(1, "Review CN1", f"{heading}\n{line}\n")
        report = ml.mine(self.dir)
        hits = [h for key in ("lessons", "doubtful", "below") for e in report[key] for h in e["hits"]]
        self.assertTrue(hits, line)
        return hits[0]

    def test_pass_and_absent_defect_wording_is_marked(self):
        self.assertIn("the line reports a pass", self.hit("- Music playback passed all checks.")["doubts"])
        self.assertIn("the line says a defect is absent", self.hit("- Music is not stuck; all checks pass.")["doubts"])

    def test_real_defects_with_pass_or_negation_words_are_not_marked(self):
        for line in ("- The bonnet in the `pass` slot is a lumpy, melted blob.",
                     "- The licence rows for three tracks are gone, and the licence test still passes.",
                     "- Players keep passing through the collider.",
                     "- Music is not only stuck but also silent.",
                     "- Music passed on desktop but is stuck at 0 on iOS."):
            with self.subTest(line=line):
                self.assertEqual(self.hit(line)["doubts"], [])

    def test_a_doubtful_hit_still_counts_and_is_shown(self):
        self.review(1, "Review CN1", "## BLOCKER\n- Music playback passed all checks.\n")
        report = ml.mine(self.dir)
        key, entry = self.where(report, "audio-lifecycle")
        self.assertEqual(key, "doubtful")
        self.assertIn("doubt: the line reports a pass", ml.render(report))

    def test_every_hit_is_listed_with_file_and_line(self):
        self.review(1, "Review CN1", "VERDICT: BLOCKED\n\n## BLOCKER\n- The music stops.\n- The music never resumes.\n")
        report = ml.mine(self.dir)
        text = ml.render(report)
        name = next(self.dir.glob("*.md")).name
        self.assertIn(f"`{name}:10` [cn1] (severe): - The music stops.", text)
        self.assertIn(f"`{name}:11` [cn1] (severe): - The music never resumes.", text)


class ScopeTest(MineCase):
    def test_since_reports_only_classes_with_a_new_hit(self):
        self.review(1, "Review CN1", "## BLOCKER\nmusic stuck\n")
        self.review(5, "Review CK2", "## Must-fix\n1. The collider overhang is 0.9 m.\n")
        report = ml.mine(self.dir, since=1)
        self.assertEqual((report["files"], report["new_files"]), (2, 1))
        self.assertEqual([e["class"] for e in report["lessons"]], ["collider-mismatch"])
        self.assertIn("Next run: --since 5", ml.render(report))

    def test_repeats_across_runs_add_up(self):
        self.review(1, "Review CK2", "## Notes\n- The stale assertion catches nothing.\n", "confirmed")
        self.assertEqual(self.where(ml.mine(self.dir, since=0), "check-that-cannot-fail")[0], "below")
        self.review(2, "Review CS1", "## Notes\n- Mutant M3 survived.\n", "confirmed")
        self.assertEqual(self.where(ml.mine(self.dir, since=1), "check-that-cannot-fail")[0], "lessons")


class FakeHindsight:
    """Stands in for urlopen: records each payload and answers like Hindsight 1.2.2."""

    def __init__(self, answers=None):
        self.sent, self.answers = [], list(answers or [])

    def __call__(self, req, timeout=0):
        self.sent.append(json.loads(req.data.decode("utf-8")))
        answer = self.answers.pop(0) if self.answers else {"success": True, "bank_id": "b", "items_count": 1}
        if isinstance(answer, Exception):
            raise answer
        body = json.dumps(answer).encode("utf-8")

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return body

        return Resp()


class RetainTest(MineCase):
    REPO = "owner/game"

    def setUp(self):
        super().setUp()
        self.review(1, "Review CN1", "## BLOCKER\nmusic stuck at volume 0\n")
        self.review(2, "Review CK2", "## BLOCKER\n- The collider overhang is 0.9 m.\n")
        self.report = ml.mine(self.dir)

    def retain(self, fake, keep=("audio-lifecycle", "collider-mismatch"), forbid=(), token="t1"):
        with mock.patch.object(ml.urllib.request, "urlopen", side_effect=fake):
            return ml.retain(self.report, list(keep), "http://127.0.0.1:8888", "gamedev-studio::studio", self.REPO,
                             list(forbid), token=token)

    def items(self, fake):
        return [s["items"][0] for s in fake.sent]

    def test_only_kept_classes_and_then_the_marker_are_stored(self):
        fake = FakeHindsight()
        stored, refused = self.retain(fake, keep=("collider-mismatch",))
        self.assertEqual(refused, [])
        self.assertEqual(stored, ["lesson:collider-mismatch", "lessons-run"])
        lesson, marker = self.items(fake)
        self.assertTrue(all(lesson["metadata"][k] for k in ("source_type", "source", "source_rev", "recorded_by")))
        self.assertIn(self.REPO, lesson["metadata"]["source"])
        self.assertEqual(lesson["tags"], ["lesson", "lesson:collider-mismatch", "repo:owner/game"])
        self.assertEqual((lesson["metadata"]["verified"], marker["metadata"]["verified"]), ("false", "false"))
        self.assertEqual(marker["metadata"]["archive_last"], "2")
        for item in (lesson, marker):
            self.assertNotIn("document_id", item)
            self.assertNotIn("update_mode", item)
            self.assertEqual(item["metadata"]["lessons_run"], "t1")

    def test_storing_stops_at_the_first_failure(self):
        fake = FakeHindsight(answers=[{"success": False}])
        stored, refused = self.retain(fake)
        self.assertEqual(stored, [])
        self.assertEqual(len(fake.sent), 1)                  # nothing after the failure, so a re-run stores nothing twice
        self.assertEqual([r[0] for r in refused], ["lesson:collider-mismatch", "lesson:audio-lifecycle", "lessons-run"])
        fake = FakeHindsight(answers=[{"success": True, "items_count": 1}, urllib.error.URLError("refused")])
        stored, refused = self.retain(fake)
        self.assertEqual(stored, ["lesson:collider-mismatch"])
        self.assertEqual([r[0] for r in refused], ["lesson:audio-lifecycle", "lessons-run"])

    def test_the_guard_checks_the_whole_payload(self):
        for pattern in ("audio-lifecycle", "owner/game", "gamedev-studio:lessons", "review archive"):
            with self.subTest(pattern=pattern):
                fake = FakeHindsight()
                stored, refused = self.retain(fake, keep=("audio-lifecycle",), forbid=[re.compile(pattern)])
                self.assertEqual(fake.sent, [])
                self.assertEqual(stored, [])
                self.assertIn("--forbid", refused[0][1])

    def test_a_secret_in_a_source_file_name_is_refused(self):
        next(e for e in self.report["lessons"] if e["class"] == "audio-lifecycle")["hits"][0]["file"] = "2026-11-19_01_agent-ghp_" + "a" * 36 + "-finished.md"
        fake = FakeHindsight()
        stored, refused = self.retain(fake, keep=("audio-lifecycle",))
        self.assertEqual(fake.sent, [])
        self.assertIn("secret", refused[0][1])

    def test_failed_answers_are_reported(self):
        for answer in ({"success": False}, {"success": True, "items_count": 0},
                       urllib.error.HTTPError("u", 500, "err", {}, None), urllib.error.URLError("refused")):
            with self.subTest(answer=answer):
                stored, refused = self.retain(FakeHindsight(answers=[answer]), keep=("audio-lifecycle",))
                self.assertEqual(stored, [])
                self.assertEqual(len(refused), 2)

    def test_default_token_is_random(self):
        a, b = FakeHindsight(), FakeHindsight()
        self.retain(a, keep=("audio-lifecycle",), token=None)
        self.retain(b, keep=("audio-lifecycle",), token=None)
        self.assertNotEqual(self.items(a)[0]["metadata"]["lessons_run"], self.items(b)[0]["metadata"]["lessons_run"])


class CliTest(MineCase):
    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ml.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.call("--reviews", str(self.dir / "missing"))[0], 2)
        self.review(1, "Review CN1", "## BLOCKER\nmusic stuck\n")
        code, out, _ = self.call("--reviews", str(self.dir), "--json")
        self.assertEqual(code, 0)
        self.assertIn('"audio-lifecycle"', out)
        d = str(self.dir)
        for args in (("--forbid", "("), ("--keep", "no-such-class", "--retain", "http://x", "--repository", "o/g"),
                     ("--keep", "audio-lifecycle"), ("--retain", "http://x", "--repository", "o/g"),
                     ("--retain", "http://x", "--keep", "audio-lifecycle"),
                     ("--retain", "http://x", "--repository", "bad", "--keep", "audio-lifecycle"),
                     ("--retain", "http://x", "--repository", "o/g", "--keep", "collider-mismatch")):
            with self.subTest(args=args):
                self.assertEqual(self.call("--reviews", d, *args)[0], 2)

    def test_retain_without_keep_stores_nothing(self):
        self.review(1, "Review CN1", "## BLOCKER\nmusic stuck\n")
        with mock.patch.object(ml.urllib.request, "urlopen") as urlopen:
            code, _, err = self.call("--reviews", str(self.dir), "--retain", "http://x", "--repository", "o/g")
        self.assertEqual(code, 2)
        self.assertIn("--keep", err)
        urlopen.assert_not_called()

    def test_out_inside_the_game_repository_is_refused(self):
        for folder in (self.dir / "game", self.dir / "игры" / "game"):   # git prints the path in UTF-8
            with self.subTest(folder=folder.name):
                reviews = folder / "docs" / "reviews"
                reviews.mkdir(parents=True)
                subprocess.run(["git", "init", "-q", str(folder)], check=True)
                (reviews / "2026-11-19_01_agent-review-a-finished_blocked.md").write_text(
                    HEADER.format(title="Review CN1", v="BLOCKED") + "## BLOCKER\nmusic stuck\n", encoding="utf-8")
                code, _, err = self.call("--reviews", str(reviews), "--out", str(folder / "docs" / "lessons.md"))
                self.assertEqual(code, 2, err)
                self.assertFalse((folder / "docs" / "lessons.md").exists())
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(self.call("--reviews", str(self.dir / "game" / "docs" / "reviews"),
                                       "--out", str(Path(other) / "r.md"))[0], 0)


if __name__ == "__main__":
    unittest.main()
