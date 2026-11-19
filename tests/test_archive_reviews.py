"""Unit tests for scripts/archive_reviews.py (stdlib unittest, offline fixtures only)."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("archive_reviews", REPO_ROOT / "scripts" / "archive_reviews.py")
ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ar)


def notification(result, summary="Agent \"Review piece X\" finished", task_id="t1"):
    return (
        f"<task-notification><task-id>{task_id}</task-id><status>completed</status>"
        f"<summary>{summary}</summary><result>{result}</result></task-notification>"
    )


def user_record(text, ts="2026-11-19T10:00:00.000Z"):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def tool_result_record(text, ts="2026-11-19T11:00:00.000Z"):
    return {
        "type": "user",
        "timestamp": ts,
        "message": {"role": "user", "content": [
            {"type": "tool_result", "content": [{"type": "text", "text": text}]},
        ]},
    }


class ArchiveCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "reviews"

    def transcript(self, records, name="session.jsonl", extra_lines=()):
        path = self.root / name
        lines = [json.dumps(r) for r in records] + list(extra_lines)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def run_archive(self, *files, **kwargs):
        return ar.archive(list(files), self.out, today="2026-11-20", **kwargs)


class ExtractionTest(ArchiveCase):
    def test_writes_a_verdict_verbatim_with_header(self):
        body = "VERDICT: BLOCKED\n\n## BLOCKER\nThe music stays at volume 0 after a tab switch."
        t = self.transcript([user_record(notification(body))])
        written, skipped = self.run_archive(t)
        self.assertEqual(skipped, [])
        self.assertEqual(written, ["2026-11-19_01_agent-review-piece-x-finished_blocked.md"])
        text = (self.out / written[0]).read_text(encoding="utf-8")
        self.assertIn("- Verdict: BLOCKED", text)
        self.assertIn("- Body SHA-256: " + ar.body_digest(body), text)
        self.assertTrue(text.endswith(body + "\n"))

    def test_body_is_kept_verbatim_with_its_whitespace_and_line_endings(self):
        body = "\n  VERDICT: CONFIRMED\r\nline two  \n\n"
        t = self.transcript([user_record(notification(body))])
        written, _ = self.run_archive(t)
        raw = (self.out / written[0]).read_bytes().decode("utf-8")
        self.assertTrue(raw.endswith(ar.HEADER_END + body))
        self.assertEqual(self.run_archive(t), ([], []))

    def test_notification_without_verdict_is_ignored(self):
        t = self.transcript([user_record(notification("Done. All tests pass."))])
        self.assertEqual(self.run_archive(t), ([], []))
        self.assertFalse(self.out.exists())

    def test_text_parts_and_bold_verdict_are_found(self):
        record = {"timestamp": "2026-11-19T12:00:00Z", "message": {"content": [
            {"type": "text", "text": notification("**VERDICT:** CONFIRMED\nNothing blocks.")}]}}
        written, _ = self.run_archive(self.transcript([record]))
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].endswith("_confirmed.md"))

    def test_notification_quoted_in_a_tool_result_is_not_a_report(self):
        t = self.transcript([tool_result_record(notification("VERDICT: CONFIRMED quoted fixture"))])
        self.assertEqual(self.run_archive(t), ([], []))

    def test_round_qualifier_before_colon(self):
        self.assertEqual(ar.verdict_label("VERDICT (round 2): CONFIRMED"), "CONFIRMED")

    def test_two_different_verdicts_use_the_last_two(self):
        body = "# Part A\nVERDICT: BLOCKED\n# Part B\n**VERDICT: CONFIRMED**"
        self.assertEqual(ar.verdict_label(body), "BLOCKED-CONFIRMED")
        t = self.transcript([user_record(notification(body))])
        written, _ = self.run_archive(t)
        self.assertTrue(written[0].endswith("_blocked-confirmed.md"))

    def test_unescape_keeps_escaped_entities(self):
        self.assertEqual(ar.unescape("a &lt;b&gt; &amp;lt; c"), "a <b> &lt; c")

    def test_malformed_lines_are_skipped(self):
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED ok"))], extra_lines=["{not json", "[1, 2]"])
        written, _ = self.run_archive(t)
        self.assertEqual(len(written), 1)

    def test_missing_summary_and_timestamp_fall_back(self):
        record = {"message": {"content": "<task-notification><result>VERDICT: BLOCKED x</result></task-notification>"}}
        t = self.transcript([record])
        written, _ = self.run_archive(t)
        self.assertEqual(written, ["2026-11-20_01_review_blocked.md"])


    def test_verdict_quoted_inside_a_sentence_is_not_a_report(self):
        body = "Done. The reviewer should answer `VERDICT: CONFIRMED` or `VERDICT: BLOCKED`."
        self.assertIsNone(ar.verdict_label(body))
        self.assertEqual(self.run_archive(self.transcript([user_record(notification(body))])), ([], []))

    def test_label_ignores_a_quoted_verdict_in_a_real_report(self):
        body = "VERDICT: BLOCKED\n\nA report quoting `VERDICT: CONFIRMED` or `VERDICT: BLOCKED` is no verdict."
        self.assertEqual(ar.verdict_label(body), "BLOCKED")

    def test_label_uses_distinct_verdicts(self):
        self.assertEqual(ar.verdict_label("VERDICT: BLOCKED\nVERDICT: CONFIRMED\nVERDICT: BLOCKED"),
                         "BLOCKED-CONFIRMED")

    def test_record_without_timestamp_is_dated_by_inference_and_says_so(self):
        blob = {"type": "api-request-blob", "message": {"content": notification("VERDICT: CONFIRMED blob")}}
        t = self.transcript([user_record("plain text", ts="2026-11-18T09:00:00Z"), blob])
        written, _ = self.run_archive(t)
        self.assertEqual(written, ["2026-11-18_01_agent-review-piece-x-finished_confirmed.md"])
        header = (self.out / written[0]).read_text(encoding="utf-8").split(ar.HEADER_END)[0]
        self.assertIn("- Received: n/a (the record has no time; the previous record's is 2026-11-18T09:00:00Z)", header)

    def test_a_later_explicit_timestamp_wins_over_an_inferred_one(self):
        body = "VERDICT: CONFIRMED same"
        blob = {"type": "api-request-blob", "message": {"content": notification(body)}}
        t = self.transcript([user_record("x", ts="2020-01-01T00:00:00Z"), blob,
                             user_record(notification(body), ts="2026-11-19T12:00:00Z")])
        written, _ = self.run_archive(t)
        self.assertEqual(written, ["2026-11-19_01_agent-review-piece-x-finished_confirmed.md"])
        self.assertIn("- Received: 2026-11-19T12:00:00Z\n", (self.out / written[0]).read_text(encoding="utf-8"))

    def test_inference_never_crosses_transcripts(self):
        first = self.transcript([user_record("x", ts="2020-01-01T00:00:00Z")], name="a.jsonl")
        blob = {"type": "api-request-blob", "message": {"content": notification("VERDICT: BLOCKED y")}}
        second = self.transcript([blob], name="b.jsonl")
        written, _ = self.run_archive(first, second)
        self.assertEqual(written, ["2026-11-20_01_agent-review-piece-x-finished_blocked.md"])

    def test_choice_line_is_not_a_verdict(self):
        self.assertIsNone(ar.verdict_label("- VERDICT: CONFIRMED or VERDICT: BLOCKED"))
        self.assertIsNone(ar.verdict_label("Answer with **VERDICT: CONFIRMED** or `VERDICT: BLOCKED`"))
        self.assertEqual(ar.verdict_label("VERDICT: BLOCKED. Fix it or ship nothing."), "BLOCKED")

    def test_summary_is_one_line_and_rerun_still_dedupes(self):
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED x", summary="Review\n---\n\npiece"))])
        written, _ = self.run_archive(t)
        self.assertIn("# Review: Review --- piece\n", (self.out / written[0]).read_text(encoding="utf-8"))
        self.assertEqual(self.run_archive(t), ([], []))


class DedupTest(ArchiveCase):
    def test_same_body_twice_in_one_run_is_written_once(self):
        body = "VERDICT: CONFIRMED\nSame text."
        t = self.transcript([user_record(notification(body, task_id="a")), user_record(notification(body, task_id="b"))])
        written, _ = self.run_archive(t)
        self.assertEqual(len(written), 1)

    def test_rerun_writes_nothing_new(self):
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED one")), user_record(notification("VERDICT: BLOCKED two"))])
        first, _ = self.run_archive(t)
        second, _ = self.run_archive(t)
        self.assertEqual(len(first), 2)
        self.assertEqual(second, [])
        self.assertEqual(len(list(self.out.glob("*.md"))), 2)

    def test_dedup_against_old_files_without_hash_line(self):
        self.out.mkdir()
        body = "VERDICT: CONFIRMED\nOld archive body."
        old = "# Review: x\n\n- Received: n/a\n- Verdict: CONFIRMED\n\n---\n\n" + body + "\n"
        (self.out / "2026-11-17_07_old_confirmed.md").write_text(old, encoding="utf-8")
        t = self.transcript([user_record(notification(body))])
        self.assertEqual(self.run_archive(t), ([], []))

    def test_numbering_continues_after_the_highest_existing_number(self):
        self.out.mkdir()
        (self.out / "2026-11-18_41_old_confirmed.md").write_text("no header", encoding="utf-8")
        t = self.transcript([user_record(notification("VERDICT: BLOCKED new"))])
        written, _ = self.run_archive(t)
        self.assertTrue(written[0].startswith("2026-11-19_42_"))

    def test_line_ending_differences_are_the_same_body(self):
        self.assertEqual(ar.body_digest("VERDICT: X\r\nline\r\n"), ar.body_digest("VERDICT: X\nline"))


class SafetyTest(ArchiveCase):
    def test_secret_looking_body_is_skipped(self):
        token = "ghp_" + "A" * 30
        t = self.transcript([user_record(notification(f"VERDICT: CONFIRMED\nused {token}"))])
        written, skipped = self.run_archive(t)
        self.assertEqual(written, [])
        self.assertEqual(len(skipped), 1)
        self.assertIn("GitHub token", skipped[0][1])
        self.assertFalse(self.out.exists())

    def test_secret_or_forbidden_text_in_the_summary_is_skipped(self):
        import re
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED ok", summary="fix ghp_" + "A" * 30))])
        written, skipped = self.run_archive(t)
        self.assertEqual(written, [])
        self.assertIn("GitHub token", skipped[0][1])
        t2 = self.transcript([user_record(notification("VERDICT: CONFIRMED ok", summary="see C:\\Users\\x"))], name="b.jsonl")
        written, skipped = self.run_archive(t2, forbid=[re.compile(r"C:\\Users\\")])
        self.assertEqual(written, [])
        self.assertIn("--forbid", skipped[0][1])

    def test_forbid_pattern_is_skipped(self):
        import re
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED\nlogs in C:\\Users\\someone\\tmp"))])
        written, skipped = self.run_archive(t, forbid=[re.compile(r"C:\\Users\\")])
        self.assertEqual(written, [])
        self.assertIn("--forbid", skipped[0][1])

    def test_dry_run_writes_nothing(self):
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED fine"))])
        written, _ = self.run_archive(t, dry_run=True)
        self.assertEqual(len(written), 1)
        self.assertFalse(self.out.exists())


class CliTest(ArchiveCase):
    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ar.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_directory_of_transcripts_and_exit_zero(self):
        folder = self.root / "sessions"
        folder.mkdir()
        (folder / "a.jsonl").write_text(json.dumps(user_record(notification("VERDICT: CONFIRMED a"))) + "\n", encoding="utf-8")
        (folder / "b.jsonl").write_text(json.dumps(user_record(notification("VERDICT: BLOCKED b"))) + "\n", encoding="utf-8")
        code, out, _ = self.call("--transcript", str(folder), "--out", str(self.out))
        self.assertEqual(code, 0)
        self.assertIn("2 new verdict(s), 0 skipped", out)

    def test_skipped_verdict_never_echoes_the_secret(self):
        token = "ghp_" + "B" * 30
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED ok", summary="fix " + token))])
        code, out, err = self.call("--transcript", str(t), "--out", str(self.out))
        self.assertEqual(code, 3)
        self.assertNotIn(token, out + err)
        self.assertIn("the verdict with body SHA-256", err)

    def test_secret_in_the_label_position_is_never_echoed(self):
        key = "AKIA" + "A" * 16
        t = self.transcript([user_record(notification(f"VERDICT: {key}\nbody"))])
        code, out, err = self.call("--transcript", str(t), "--out", str(self.out))
        self.assertEqual(code, 3)
        self.assertNotIn(key, out + err)
        self.assertFalse(self.out.exists())

    def test_skipped_verdict_gives_exit_three(self):
        t = self.transcript([user_record(notification("VERDICT: CONFIRMED\n-----BEGIN RSA PRIVATE KEY-----"))])
        code, _, err = self.call("--transcript", str(t), "--out", str(self.out))
        self.assertEqual(code, 3)
        self.assertIn("SKIPPED", err)

    def test_missing_transcript_gives_exit_two(self):
        code, _, err = self.call("--transcript", str(self.root / "nope.jsonl"), "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertIn("transcript not found", err)

    def test_bad_forbid_regex_gives_exit_two(self):
        t = self.transcript([])
        code, _, _ = self.call("--transcript", str(t), "--out", str(self.out), "--forbid", "(")
        self.assertEqual(code, 2)

    def test_empty_transcript_folder_gives_exit_two(self):
        folder = self.root / "none"
        folder.mkdir()
        code, _, err = self.call("--transcript", str(folder), "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertIn("no transcript", err)

    def test_session_id_finds_exactly_that_transcript(self):
        import os
        from unittest import mock
        config = self.root / "config"
        (config / "projects" / "proj-a").mkdir(parents=True)
        (config / "projects" / "proj-b").mkdir(parents=True)
        sid = "0123abcd-0000-1111-2222-333344445555"
        (config / "projects" / "proj-a" / f"{sid}.jsonl").write_text(
            json.dumps(user_record(notification("VERDICT: CONFIRMED mine"))) + "\n", encoding="utf-8")
        (config / "projects" / "proj-b" / "other-session-0000.jsonl").write_text(
            json.dumps(user_record(notification("VERDICT: BLOCKED not mine"))) + "\n", encoding="utf-8")
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(config)}):
            code, out, _ = self.call("--session", sid, "--out", str(self.out))
            self.assertEqual(code, 0)
            self.assertIn("1 new verdict(s)", out)
            self.assertEqual([p.name.endswith("_confirmed.md") for p in self.out.glob("*.md")], [True])
            code, _, _ = self.call("--session", "missing-session-id", "--out", str(self.out))
            self.assertEqual(code, 2)
            code, _, _ = self.call("--session", "../../etc", "--out", str(self.out))
            self.assertEqual(code, 2)

    def test_session_and_transcript_are_exclusive(self):
        t = self.transcript([])
        code, _, _ = self.call("--session", "0123abcd-0000", "--transcript", str(t), "--out", str(self.out))
        self.assertEqual(code, 2)

    def test_missing_required_argument_gives_exit_two(self):
        code, _, _ = self.call("--out", str(self.out))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
