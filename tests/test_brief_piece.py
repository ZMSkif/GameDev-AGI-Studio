"""Unit tests for scripts/brief_piece.py, including the four Cat Challenge failures it must prevent."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("brief_piece", REPO_ROOT / "scripts" / "brief_piece.py")
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

CARD = """# CN1 · Citizens, host and events

Piece: CN1
Goal: citizens fill the plaza with the host's events, as in render 06.
Acceptance:
1. Test: a 30-minute soak keeps every citizen within the walkable graph.
2. Shot: the plaza event at medium reads as a crowd in the render-06 camera.
Owns: src/city/citizens/**, tests/city-citizens.test.ts
Depends: CK2 merged.
Reviewer gate: soaks with and without the player; the pinned hash twice.

Merge note: keep `startShow` and re-add `runTraining` with `stepId` after the jump branch lands.
"""

DECISIONS = [
    {"number": 1, "title": "[DEC-001] Все изменения проходят через отдельную ветку и PR", "url": "u1", "body": ""},
    {"number": 40, "title": "[DEC-040] Агент не принимает собственную работу без независимого ревью", "url": "u40", "body": ""},
    {"number": 72, "title": "[DEC-071] QA checks long sessions soak saves", "url": "u72", "body": "soak citizens"},
    {"number": 99, "title": "[DEC-999] Unrelated payroll rule", "url": "u99", "body": "salary"},
]


class BriefCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.repo, self.outside = base / "game", base / "briefs"
        (self.repo / "src/city/citizens").mkdir(parents=True)
        (self.repo / "src/city/citizens/crowd.ts").write_text(
            "import { layout } from '../layout';\nexport function startShow() {}\n", encoding="utf-8")
        (self.repo / "src/city/layout.ts").write_text("export const layout = 1;\n", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests/city-citizens.test.ts").write_text("test('x', () => {})\n", encoding="utf-8")
        reviews = self.repo / "docs/reviews"
        reviews.mkdir(parents=True)
        (reviews / "2026-11-19_51_cs1_confirmed.md").write_text(
            "VERDICT: CONFIRMED\n\n- **For CN1:** the plaza ring is tight; add plaza visit spots.\n"
            "- **For CN1:** a hold margin at zone edges (about 0.3 m) would be safer.\n\n## Notes\n", encoding="utf-8")
        (reviews / "2026-11-19_57_ck2_confirmed.md").write_text(
            "VERDICT: CONFIRMED\n\n**For CN1:** play emotes only while holding; debounce emote start and stop.\n",
            encoding="utf-8")
        self.card = self.outside / "card.md"
        self.outside.mkdir()
        self.card.write_text(CARD, encoding="utf-8")
        self.decisions = self.outside / "decisions.json"
        self.decisions.write_text(json.dumps(DECISIONS), encoding="utf-8")
        self.ports = self.outside / "ports.json"
        self.ports.write_text(json.dumps({"WA-1": [5300, 5302], "CA1b": [5306, 5308]}), encoding="utf-8")

    def call(self, *extra, port_range="5303-5305"):
        out = self.outside / "brief.md"
        args = ["--card", str(self.card), "--repo-root", str(self.repo), "--out", str(out),
                "--decisions", str(self.decisions), "--ports", str(self.ports), *extra]
        if port_range:
            args += ["--port-range", port_range]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = bp.main(args)
        text = out.read_text(encoding="utf-8") if out.exists() else ""
        return code, text, stderr.getvalue()


class CatChallengeCases(BriefCase):
    def test_clashing_port_range_is_refused(self):
        code, text, err = self.call(port_range="5301-5304")
        self.assertEqual(code, 3)
        self.assertIn("overlaps WA-1 (5300-5302)", err)
        self.assertEqual(text, "")

    def test_free_port_range_is_written_into_the_rules(self):
        code, text, _ = self.call()
        self.assertEqual(code, 0)
        self.assertIn("Use only ports 5303-5305", text)

    def test_stale_merge_recipe_is_flagged(self):
        code, text, _ = self.call()
        stale = text.split("## ⚠ Stale references", 1)[1].split("##", 1)[0]
        self.assertIn("`runTraining`", stale)
        self.assertIn("`stepId`", stale)
        self.assertNotIn("`startShow`", stale)

    def test_earlier_review_notes_for_the_piece_are_pulled_in(self):
        code, text, _ = self.call()
        notes = text.split("## Notes from earlier reviews (verbatim)", 1)[1]
        self.assertIn("plaza visit spots", notes)
        self.assertIn("hold margin at zone edges", notes)
        self.assertIn("debounce emote start and stop", notes)
        self.assertIn("2026-11-19_57_ck2_confirmed.md", notes)

    def test_done_means_the_built_game_not_a_mockup(self):
        self.card.write_text(CARD.replace("2. Shot: the plaza event", "2. Shot: the mockup of the plaza event"),
                             encoding="utf-8")
        code, text, _ = self.call()
        done = text.split("## Definition of done", 1)[1].split("##", 1)[0]
        self.assertIn("A mockup, concept or plan is not done", done)
        self.assertIn("1. Test: a 30-minute soak", done)
        self.assertIn("points at a mockup or concept", done)


class BriefContentTest(BriefCase):
    def test_owned_files_reads_decisions_and_skills(self):
        code, text, _ = self.call()
        self.assertIn("`src/city/citizens/crowd.ts`", text.split("## Owns", 1)[1].split("##", 1)[0])
        self.assertIn("`src/city/layout.ts`", text.split("## Reads", 1)[1].split("##", 1)[0])
        decisions = text.split("## Decisions", 1)[1].split("##", 1)[0]
        self.assertIn("#40", decisions)
        self.assertIn("#72", decisions)
        self.assertNotIn("#99", decisions)
        self.assertIn("`studio-rules`", text.split("## Skills", 1)[1])

    def test_memories_need_provenance_and_carry_verify(self):
        memories = self.outside / "mem.json"
        memories.write_text(json.dumps({"results": [
            {"type": "world", "text": "Citizens hold one slot each.", "metadata": {"source": "review _51", "source_rev": "e13c0bd", "verified": "true"}},
            {"type": "observation", "text": "Crowds are usually fine.", "metadata": {}},
            {"type": "world", "text": "No source fact.", "metadata": {}},
        ]}), encoding="utf-8")
        code, text, _ = self.call("--memories", str(memories))
        section = text.split("## Memories (verify before use; the source wins, DEC-103)", 1)[1]
        self.assertIn("Citizens hold one slot each.", section)
        self.assertNotIn("Crowds are usually fine.", section)
        self.assertNotIn("No source fact.", section)

    def test_brief_inside_the_repository_is_refused(self):
        out = self.repo / "brief.md"
        code = bp.main(["--card", str(self.card), "--repo-root", str(self.repo), "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_card_without_acceptance_is_refused(self):
        self.card.write_text("# X\nGoal: g\nOwns: a.ts\n", encoding="utf-8")
        code, _, err = self.call()
        self.assertEqual(code, 2)
        self.assertIn("Acceptance", err)

    def test_missing_port_range_asks_for_one(self):
        code, text, _ = self.call(port_range=None)
        self.assertEqual(code, 0)
        self.assertIn("No port range given", text)

    def test_bad_port_range_is_an_error(self):
        code, _, err = self.call(port_range="53xx")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
