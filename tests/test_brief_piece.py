"""Unit tests for scripts/brief_piece.py, including the four Cat Challenge failures it must prevent."""
import contextlib
import importlib.util
import io
import json
import subprocess
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

# The shape of the real CN1 card in the game's plan (bullets, bold fields, "new" paths, two fields on a line).
REAL_CARD = """#### CN1 · Citizens, host schedule and events — **M**
- **Goal:**
  - the populations of §1.4;
  - one host actor on a schedule (door ↔ plaza);
- **Acceptance:**
  1. Test (fake clock): the call fires at :00; the countdown comes from `meta/showOfDay.ts`.
  2. Test: there are never two hosts; the determinism hash holds.
  3. Shot: plaza event frames, like render 06, on high and medium.
- **Owns:** new `src/city/citizens/**`, new `src/city/events/**`, new `tests/city-events.test.ts`.
- **Depends:** CK2, CS1. **Reviewer gate:** the fake-clock tests; an event video on medium; per-tier counts.
"""

# The shape of the real CS1 review that addressed CN1: a block with sub-bullets, then unrelated bullets.
CS1_REVIEW = """# Review: Agent "Review city CS1 scene module" finished

- Verdict: CONFIRMED

---

VERDICT: CONFIRMED

## NOTES
- **For CN1:**
  - every hold has one slot (r 0.4);
  - the nodes `avDoor`, `ewN` and `ppE` lie inside place zones,
    so don't use them as visit spots;
  - visit periods must cover the walking time.
- The velvet ropes have no collider, so players and citizens walk through them.
- **The player ring costs a little at the door:** CP1 should measure it.
"""

CK2_REVIEW = """# Review: Agent "Review city CK2 NPC package" finished

---

**Must-fix list: none.** Three open points are worth doing before CN1 relies on this code.
   - The risk is emotes: if CN1 plays `target.emote` whenever `holding` is true, a fan dances while sliding.
- Unrelated: the CK2 tests are fine.
- The fix in `crowd.ts` must keep the debounce.
"""

OWN_REVIEW = """# Review: Agent "Review CN1 citizens, host and events" finished

---

VERDICT: BLOCKED
CN1 acceptance 3 fails on medium.
"""

DECISIONS = [
    {"number": 1, "title": "[DEC-001] Все изменения проходят через отдельную ветку и PR", "url": "u1", "body": ""},
    {"number": 40, "title": "[DEC-040] Агент не принимает собственную работу без независимого ревью", "url": "u40", "body": ""},
    {"number": 72, "title": "[DEC-071] QA checks long sessions soak saves", "url": "u72", "body": "soak citizens"},
    {"number": 99, "title": "[DEC-999] Unrelated payroll rule", "url": "u99", "body": "salary"},
]

FULL_META = {"source_type": "review", "source": "review _51", "source_rev": "e13c0bd", "recorded_by": "reviewer",
             "verified": "true"}


class BriefCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.repo, self.outside = base / "game", base / "briefs"
        (self.repo / "src/city/citizens").mkdir(parents=True)
        (self.repo / "src/city/citizens/crowd.ts").write_text(
            "import { layout } from '../layout';\nimport { useState } from 'react';\n"
            "// runTraining was removed in the jump branch\n/* export function stepId() {} was the old API */\n"
            "export function startShow() {}\n",
            encoding="utf-8")
        (self.repo / "src/city/layout.ts").write_text("export const layout = 1;\n", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests/city-citizens.test.ts").write_text("test('x', () => {})\n", encoding="utf-8")
        self.reviews = self.repo / "docs/reviews"
        self.reviews.mkdir(parents=True)
        (self.reviews / "2026-11-19_49_agent-review-city-cs1-finished_confirmed.md").write_text(CS1_REVIEW, encoding="utf-8")
        (self.reviews / "2026-11-19_57_agent-review-city-ck2-finished_confirmed.md").write_text(CK2_REVIEW, encoding="utf-8")
        (self.reviews / "2026-11-19_64_agent-review-cn1-finished_blocked.md").write_text(OWN_REVIEW, encoding="utf-8")
        self.card = self.outside / "card.md"
        self.outside.mkdir()
        self.card.write_text(CARD, encoding="utf-8")
        self.decisions = self.outside / "decisions.json"
        self.decisions.write_text(json.dumps(DECISIONS), encoding="utf-8")
        self.ports = self.outside / "ports.json"
        self.ports.write_text(json.dumps({"WA-1": [5300, 5302], "CA1b": [5306, 5308], "CN1": [5304, 5304]}),
                              encoding="utf-8")

    def call(self, *extra, port_range="5303-5305"):
        out = self.outside / "brief.md"
        if out.exists():
            out.unlink()
        args = ["--card", str(self.card), "--repo-root", str(self.repo), "--out", str(out),
                "--decisions", str(self.decisions), "--ports", str(self.ports), *extra]
        if port_range:
            args += ["--port-range", port_range]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = bp.main(args)
        text = out.read_text(encoding="utf-8") if out.exists() else ""
        return code, text, stderr.getvalue()

    @staticmethod
    def section(text, heading):
        return text.split(heading, 1)[1].split("\n## ", 1)[0]


class CatChallengeCases(BriefCase):
    def test_clashing_port_range_is_refused(self):
        code, text, err = self.call(port_range="5301-5304")
        self.assertEqual(code, 3)
        self.assertIn("overlaps WA-1 (5300-5302)", err)
        self.assertEqual(text, "")

    def test_a_range_sharing_one_edge_port_is_refused(self):
        code, _, err = self.call(port_range="5302-5303")
        self.assertEqual(code, 3)
        self.assertIn("WA-1", err)
        self.assertEqual(self.call(port_range="5305-5306")[0], 3)

    def test_the_pieces_own_range_is_not_a_clash(self):
        code, text, _ = self.call()
        self.assertEqual(code, 0)
        self.assertIn("Use only ports 5303-5305", text)

    def test_stale_merge_recipe_is_flagged(self):
        _, text, _ = self.call()
        stale = self.section(text, "## ⚠ Stale references")
        self.assertIn("`runTraining`", stale)   # only a comment names it
        self.assertIn("`stepId`", stale)        # nothing names it
        self.assertNotIn("`startShow`", stale)  # defined

    def test_definitions_exports_and_imports_count(self):
        (self.repo / "src/city/citizens/steps.ts").write_text(
            "export const stepId = 3;\nclass Coach {\n  runTraining(level: number): void {\n  }\n}\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertNotIn("## ⚠ Stale references", text)
        self.card.write_text(CARD + "\nAlso call `useState` and `startShowtime`.\n", encoding="utf-8")
        _, text, _ = self.call()
        stale = self.section(text, "## ⚠ Stale references")
        self.assertNotIn("`useState`", stale)   # imported from a package
        self.assertIn("`startShowtime`", stale)  # startShow is not startShowtime

    def test_earlier_review_notes_for_the_piece_are_pulled_in_whole(self):
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("  - every hold has one slot (r 0.4);", notes)
        self.assertIn("    so don't use them as visit spots;", notes)   # a continuation line, verbatim
        self.assertIn("  - visit periods must cover the walking time.", notes)
        self.assertNotIn("velvet ropes", notes)                      # the next bullet is not CN1's
        self.assertNotIn("CP1 should measure", notes)

    def test_lines_in_other_pieces_reviews_that_name_the_piece_are_pulled_in(self):
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("worth doing before CN1 relies on this code", notes)
        self.assertIn("if CN1 plays `target.emote`", notes)
        self.assertNotIn("the CK2 tests are fine", notes)
        self.assertNotIn("acceptance 3 fails on medium", notes)  # the piece's own review is not a note

    def test_must_or_fix_lines_about_owned_files_are_pulled_in(self):
        self.card.write_text(CARD.replace("Owns: src/city/citizens/**", "Owns: src/city/citizens/crowd.ts"),
                             encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("The fix in `crowd.ts` must keep the debounce.", self.section(text, "## Notes from earlier"))

    def test_done_means_the_built_game_not_a_mockup(self):
        self.card.write_text(CARD.replace("2. Shot: the plaza event", "2. Shot: the mockup of the plaza event"),
                             encoding="utf-8")
        _, text, _ = self.call()
        done = self.section(text, "## Definition of done")
        self.assertIn("A mockup, concept or plan is not done", done)
        self.assertIn("1. Test: a 30-minute soak", done)
        self.assertIn("points at a mockup or concept", done)

    def test_a_line_without_evidence_is_flagged(self):
        self.card.write_text(CARD.replace("1. Test: a 30-minute soak", "1. A 30-minute soak"), encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("1. A 30-minute soak keeps every citizen within the walkable graph.  ⚠ no Test:/Shot:",
                      self.section(text, "## Definition of done"))


class RealCardShapeTest(BriefCase):
    def test_real_card_fields(self):
        card = bp.parse_card(REAL_CARD)
        self.assertEqual(card["piece"], "CN1")
        self.assertEqual(card["owns"], ["src/city/citizens/**", "src/city/events/**", "tests/city-events.test.ts"])
        self.assertEqual(card["new"], card["owns"])
        self.assertEqual(card["depends"], ["CK2, CS1."])
        self.assertEqual(card["reviewer_gate"], ["the fake-clock tests; an event video on medium; per-tier counts."])
        self.assertEqual(card["goal"], ["  - the populations of §1.4;", "  - one host actor on a schedule (door ↔ plaza);"])
        self.assertEqual(len(card["acceptance"]), 3)

    def test_real_card_brief(self):
        self.card.write_text(REAL_CARD, encoding="utf-8")
        _, text, _ = self.call()
        owns = self.section(text, "## Owns (change only these)")
        self.assertIn("- `src/city/citizens/crowd.ts`", owns)
        self.assertIn("- `src/city/events/**` (new: it does not exist yet)", owns)
        self.assertNotIn("new `", owns)
        self.assertNotIn("⚠ no Test:/Shot:", self.section(text, "## Definition of done"))  # "Test (fake clock):"
        self.assertIn("the fake-clock tests", self.section(text, "## Reviewer gate"))
        self.assertNotIn("Reviewer gate", self.section(text, "## Depends"))


class BriefContentTest(BriefCase):
    def test_owned_files_reads_decisions_and_skills(self):
        _, text, _ = self.call()
        self.assertIn("`src/city/citizens/crowd.ts`", self.section(text, "## Owns"))
        self.assertIn("`src/city/layout.ts`", self.section(text, "## Reads"))
        decisions = self.section(text, "## Decisions")
        self.assertIn("#40", decisions)
        self.assertIn("#72", decisions)
        self.assertNotIn("#99", decisions)
        self.assertIn("`studio-rules`", text.split("## Skills", 1)[1])

    def test_memories_need_every_provenance_field(self):
        memories = self.outside / "mem.json"
        missing_rev = dict(FULL_META, source_rev="")
        no_recorder = {k: v for k, v in FULL_META.items() if k != "recorded_by"}
        memories.write_text(json.dumps({"results": [
            {"type": "world", "text": "Citizens hold one slot each.", "metadata": FULL_META},
            {"type": "observation", "text": "Crowds are usually fine.", "metadata": FULL_META},
            {"type": "world", "text": "No source fact.", "metadata": {}},
            {"type": "world", "text": "Empty revision fact.", "metadata": missing_rev},
            {"type": "experience", "text": "No recorder fact.", "metadata": no_recorder},
        ]}), encoding="utf-8")
        _, text, _ = self.call("--memories", str(memories))
        section = self.section(text, "## Memories (verify before use; the source wins, DEC-103)")
        self.assertIn("Citizens hold one slot each.", section)
        for dropped in ("Crowds are usually fine.", "No source fact.", "Empty revision fact.", "No recorder fact."):
            self.assertNotIn(dropped, section)

    def test_built_from_records_the_revisions(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       check=True)
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
        (self.repo / "src/city/citizens/crowd.ts").write_text("export function startShow() { }\n", encoding="utf-8")
        _, text, _ = self.call("--card-source", "issue #42 updated 2026-11-19T10:00Z")
        built = self.section(text, "## Built from")
        self.assertIn(f"`{head}`", built)
        self.assertIn("uncommitted changes in `src/city/citizens/crowd.ts`", built)
        self.assertIn("from issue #42 updated 2026-11-19T10:00Z", built)
        self.assertIn("Review archive: 3 files, last `2026-11-19_64_agent-review-cn1-finished_blocked.md`", built)
        self.assertRegex(built, r"Card: sha256 `[0-9a-f]{16}`")

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
        self.assertEqual(self.call(port_range="53xx")[0], 2)
        self.assertEqual(self.call(port_range="5310-5300")[0], 2)

    def test_in_a_git_repository_only_tracked_files_count(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        other = self.repo / ".claude/worktrees/agent-x/src"
        other.mkdir(parents=True)
        (other / "steps.ts").write_text("export const stepId = 1;\n", encoding="utf-8")   # another worktree
        (self.repo / "bundle.js").write_text("function stepId(){}\n" + "x" * bp.MAX_SOURCE_BYTES, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "bundle.js"], check=True)       # tracked but huge
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.section(text, "## ⚠ Stale references"))
        (self.repo / "src/city/citizens/steps.ts").write_text("export const stepId = 1;\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "src/city/citizens/steps.ts"], check=True)
        _, text, _ = self.call()
        self.assertNotIn("`stepId`", text.split("## ⚠ Stale references", 1)[-1].split("\n## ", 1)[0]
                         if "## ⚠ Stale references" in text else "")

    def test_node_modules_are_not_read(self):
        lib = self.repo / "node_modules/pkg"
        lib.mkdir(parents=True)
        (lib / "index.js").write_text("export function stepId() {}\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.section(text, "## ⚠ Stale references"))


if __name__ == "__main__":
    unittest.main()
