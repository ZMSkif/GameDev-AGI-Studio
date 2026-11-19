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
        body = "Part A VERDICT: BLOCKED\nPart B VERDICT: CONFIRMED"
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

    def test_missing_required_argument_gives_exit_two(self):
        code, _, _ = self.call("--out", str(self.out))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
