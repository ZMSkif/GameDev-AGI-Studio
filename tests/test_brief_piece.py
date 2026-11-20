"""Unit tests for scripts/brief_piece.py, including the four Cat Challenge failures it must prevent."""
import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

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

    def test_a_string_that_looks_like_a_definition_does_not_count(self):
        (self.repo / "src/city/citizens/recipe.ts").write_text(
            'const recipe = "function runTraining() {}";\nconst tpl = `export const stepId = 1`;\n'
            "const url = 'http://example.com'; export function startShow2() {}\n", encoding="utf-8")
        (self.repo / "tool.py").write_text('DOC = """def runTraining(): pass"""\n', encoding="utf-8")
        self.card.write_text(CARD + "\nAlso `startShow2`.\n", encoding="utf-8")
        _, text, _ = self.call()
        stale = self.section(text, "## ⚠ Stale references")
        self.assertIn("`runTraining`", stale)
        self.assertIn("`stepId`", stale)
        self.assertNotIn("`startShow2`", stale)  # defined after a string holding "//"

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

    def test_a_plain_for_line_ends_the_block(self):
        (self.reviews / "2026-11-19_50_agent-review-city-cs2-finished_confirmed.md").write_text(
            '# Review: Agent "Review city CS2" finished\n\n---\n\n'
            "For CN1: keep the hold slots,\none per hold.\nFor CK2: rename the lane.\n",
            encoding="utf-8")
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("one per hold.", notes)
        self.assertNotIn("rename the lane", notes)

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
        self.assertRegex(built, r"quoted: `2026-11-19_49_agent-review-city-cs1-finished_confirmed.md` sha256 `[0-9a-f]{16}`")
        first = built
        (self.repo / "src/city/citizens/crowd.ts").write_text("export function startShow() { /* v2 */ }\n", encoding="utf-8")
        _, text, _ = self.call("--card-source", "issue #42 updated 2026-11-19T10:00Z")
        self.assertNotEqual(self.section(text, "## Built from"), first)  # new content, new hash
        (self.reviews / "2026-11-19_49_agent-review-city-cs1-finished_confirmed.md").write_text(
            CS1_REVIEW + "\n- one more line\n", encoding="utf-8")
        _, again, _ = self.call("--card-source", "issue #42 updated 2026-11-19T10:00Z")
        self.assertNotEqual(self.section(again, "## Built from"), self.section(text, "## Built from"))
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



class RoundTwoCases(BriefCase):
    """The second review round's findings: definitions, note context, card prose, non-ASCII paths."""

    def stale(self, text):
        return self.section(text, "## ⚠ Stale references") if "## ⚠ Stale references" in text else ""

    def test_a_call_is_not_a_definition(self):
        (self.repo / "src/city/citizens/use.ts").write_text("runTraining();\nconst x = stepId + 1;\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))
        self.assertIn("`stepId`", self.stale(text))

    def test_more_definition_shapes_count(self):
        (self.repo / "src/city/citizens/more.ts").write_text(
            "import React, { useMemo } from 'react';\n"
            "const glob = 'assets/*.glb';\n"
            "class Coach {\n  runTraining<T>(level: T): void {\n  }\n}\n", encoding="utf-8")
        (self.repo / "src/city/citizens/Step.cs").write_text("class S {\n  public int stepId { get; set; }\n}\n",
                                                             encoding="utf-8")
        self.card.write_text(CARD + "\nAlso `useMemo`.\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertEqual(self.stale(text), "")

    def test_import_and_export_lists_count(self):
        (self.repo / "src/city/citizens/index.ts").write_text(
            "import { stepId } from './steps';\nexport { runTraining } from './coach';\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertEqual(self.stale(text), "")

    def test_tests_and_fixtures_do_not_keep_a_name_alive(self):
        for rel in ("tests/fixtures/steps.ts", "e2e/flow.mjs", "src/city/coach.test.ts"):
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text("export const stepId = 3;\nexport function runTraining() {}\n",
                                         encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.stale(text))
        self.assertIn("`runTraining`", self.stale(text))
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)   # the same through git's file list
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.stale(text))
        self.assertIn("`runTraining`", self.stale(text))

    def test_an_unclosed_export_list_stays_fast(self):
        (self.repo / "src/city/citizens/big.ts").write_text(("export { stepId, " * 3000) + "\n", encoding="utf-8")
        self.card.write_text(CARD + "\nAlso `missingName`.\n", encoding="utf-8")
        started = time.monotonic()
        _, text, _ = self.call()
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("`missingName`", self.stale(text))

    def test_a_for_block_in_the_pieces_own_review_is_pulled_in(self):
        (self.reviews / "2026-11-19_65_agent-review-cn1-finished_blocked.md").write_text(
            OWN_REVIEW + "\n- **For CN1:** re-run the soak on medium.\n", encoding="utf-8")
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("re-run the soak on medium", notes)
        self.assertNotIn("acceptance 3 fails on medium", notes)

    def test_a_blank_line_ends_a_block(self):
        (self.reviews / "2026-11-19_50_agent-review-city-cs2-finished_confirmed.md").write_text(
            '# Review: Agent "Review city CS2" finished\n\n---\n\n'
            "- **For CN1:** keep the hold slots.\n\n  - an unrelated indented line.\n", encoding="utf-8")
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("keep the hold slots", notes)
        self.assertNotIn("an unrelated indented line", notes)

    def test_a_mention_in_a_sub_item_brings_its_parent_and_a_line_number(self):
        (self.reviews / "2026-11-19_58_agent-review-city-ck2-finished_confirmed.md").write_text(
            '# Review: Agent "Review city CK2 NPC package" finished\n\n---\n\n'
            "4. **`holding: true` carrying motion.**\n"
            "   - Either expose the flag or document it.\n"
            "   - A CN1 that follows the contract would start the emote too often.\n", encoding="utf-8")
        _, text, _ = self.call()
        notes = self.section(text, "## Notes from earlier reviews (verbatim)")
        self.assertIn("From `2026-11-19_58_agent-review-city-ck2-finished_confirmed.md`, line 5:", notes)
        self.assertIn("4. **`holding: true` carrying motion.**", notes)
        self.assertIn("   - Either expose the flag or document it.", notes)

    def test_prose_after_the_last_field_is_not_part_of_it(self):
        _, text, _ = self.call()
        self.assertNotIn("Merge note", self.section(text, "## Reviewer gate"))

    def test_non_ascii_paths_in_git(self):
        base = Path(self._tmp.name) / "игры"
        repo = base / "game"
        (repo / "src").mkdir(parents=True)
        (repo / "src/Карта.ts").write_text("export function runTraining() {}\nexport const stepId = 1;\n",
                                          encoding="utf-8")
        (repo / "src/Игра.ts").write_text("export function startShow() {}\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       check=True)
        (repo / "src/Игра.ts").write_text("export function startShow() { }\n", encoding="utf-8")
        out = self.outside / "brief-ru.md"
        args = ["--card", str(self.card), "--repo-root", str(repo), "--out", str(out),
                "--port-range", "5303-5305"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = bp.main(args)
        self.assertEqual(code, 0, stderr.getvalue())
        text = out.read_text(encoding="utf-8")
        self.assertNotIn("## ⚠ Stale references", text)
        self.assertIn("uncommitted changes", self.section(text, "## Built from"))


class RoundThreeCases(BriefCase):
    """One fail direction: a misread may flag a name as stale, it must never hide a stale one."""

    def stale(self, text):
        return self.section(text, "## ⚠ Stale references") if "## ⚠ Stale references" in text else ""

    def test_json_values_never_define_a_name_but_keys_do(self):
        (self.repo / "src/city/citizens/recipe.json").write_text(
            '{"recipe": "function runTraining() {}", "note": "export const stepId = 1"}', encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))
        self.assertIn("`stepId`", self.stale(text))
        (self.repo / "src/city/citizens/keys.json").write_text('{"stepId": 3}', encoding="utf-8")
        _, text, _ = self.call()
        self.assertNotIn("`stepId`", self.stale(text))

    def test_comments_and_odd_strings(self):
        (self.repo / "src/city/citizens/odd.ts").write_text(
            "function/* old name */runTraining() {}\nconst glob = '/*.glb';\nexport const stepId = 1;\n",
            encoding="utf-8")
        _, text, _ = self.call()
        self.assertEqual(self.stale(text), "")

    def test_python_comments_and_csharp_verbatim_strings(self):
        (self.repo / "tool.py").write_text("# def runTraining(): was removed\n", encoding="utf-8")
        (self.repo / "Paths.cs").write_text('var dir = @"C:\\dir\\";\nclass P { public int stepId { get; set; } }\n',
                                            encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))
        self.assertNotIn("`stepId`", self.stale(text))

    def test_an_unclosed_block_comment_stays_fast(self):
        (self.repo / "src/city/citizens/open.ts").write_text("/* " + "stepId runTraining " * 20000, encoding="utf-8")
        started = time.monotonic()
        _, text, _ = self.call()
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("`stepId`", self.stale(text))

    def test_python_test_files_do_not_count(self):
        (self.repo / "test_training.py").write_text("def runTraining():\n    pass\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))

    def test_renamed_and_non_ascii_uncommitted_files_are_found(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       check=True)
        subprocess.run(["git", "-C", str(self.repo), "mv", "src/city/citizens/crowd.ts", "src/city/citizens/Толпа.ts"],
                       check=True)
        self.assertIn("src/city/citizens/Толпа.ts", bp.uncommitted(self.repo))
        self.assertNotIn("src/city/citizens/crowd.ts", bp.uncommitted(self.repo))
        _, first, _ = self.call()
        self.assertIn("uncommitted changes in `src/city/citizens/Толпа.ts` (sha256", self.section(first, "## Built from"))
        (self.repo / "src/city/citizens/Толпа.ts").write_text("export function startShow() { /* v2 */ }\n",
                                                             encoding="utf-8")
        _, second, _ = self.call()
        self.assertNotEqual(self.section(first, "## Built from"), self.section(second, "## Built from"))

    def test_card_fields_with_blank_lines(self):
        card = bp.parse_card("# CN1 · x\n- **Goal:**\n\nthe plaza fills up.\n\nThe host walks the plaza.\n"
                             "- **Acceptance:**\n  1. Test: a.\n- **Owns:** `src/a.ts`\n"
                             "- **Depends:**\n\nCK2.\n- **Reviewer gate:**\n\nthe video.\n\nMerge note: keep `x`.\n")
        self.assertEqual(card["goal"], ["the plaza fills up.", "The host walks the plaza."])
        self.assertEqual(card["depends"], ["CK2."])
        self.assertEqual(card["reviewer_gate"], ["the video."])

    def test_a_for_note_starts_at_its_own_line(self):
        _, text, _ = self.call()
        self.assertIn("From `2026-11-19_49_agent-review-city-cs1-finished_confirmed.md`, line 10:\n\n- **For CN1:**",
                      text)

    def test_the_archive_digest_follows_every_file(self):
        _, first, _ = self.call()
        (self.reviews / "2026-11-19_70_agent-review-city-ck9-finished_confirmed.md").write_text(
            '# Review: Agent "Review city CK9" finished\n\n---\n\nNothing about this piece.\n', encoding="utf-8")
        _, second, _ = self.call()
        digest = lambda text: [l for l in self.section(text, "## Built from").splitlines() if "Review archive" in l]
        self.assertNotEqual(digest(first), digest(second))


class RoundFourCases(BriefCase):
    def stale(self, text):
        return self.section(text, "## ⚠ Stale references") if "## ⚠ Stale references" in text else ""

    def test_json_needs_the_exact_key(self):
        (self.repo / "src/city/citizens/k.json").write_text('{"function runTraining() {}": true, "x": 1}',
                                                         encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))

    def test_a_string_continued_over_a_backslash_is_still_a_string(self):
        (self.repo / "src/city/citizens/c.js").write_text('const s = "one \\\nfunction runTraining() {}";\n',
                                                        encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`runTraining`", self.stale(text))

    def test_every_found_name_shows_where(self):
        (self.repo / "src/city/citizens/re.js").write_text("// header\nconst re = /function runTraining()/;\n",
                                                         encoding="utf-8")
        _, text, _ = self.call()
        found = self.section(text, "## Names the card uses, and where they were found")
        self.assertIn("- `runTraining`: `src/city/citizens/re.js:2`: const re = /function runTraining()/;", found)
        self.assertIn("- `startShow`: `src/city/citizens/crowd.ts:5`: export function startShow() {}", found)

    def test_built_from_changes_when_any_used_byte_changes(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                       check=True)
        fresh = self.repo / "src/city/citizens/new/main.ts"          # untracked, in a new folder
        fresh.parent.mkdir()
        fresh.write_text("export const a = 1;\n", encoding="utf-8")
        used = [fresh, self.repo / "src/city/citizens/crowd.ts", self.repo / "src/city/layout.ts"]   # owned, owned, read
        _, base, _ = self.call()
        for path in used:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original[:-1] + (b"X" if original[-1:] != b"X" else b"Y"))
                _, changed, _ = self.call()
                path.write_bytes(original)
                self.assertNotEqual(self.section(base, "## Built from"), self.section(changed, "## Built from"))


class RoundFourClaudeCases(BriefCase):
    def stale(self, text):
        return self.section(text, "## ⚠ Stale references") if "## ⚠ Stale references" in text else ""

    def old_worktree(self):
        wt = self.repo / ".claude/worktrees/agent-old"
        (wt / "src").mkdir(parents=True)
        (wt / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (wt / "src/old.ts").write_text("export const stepId = 1;\nexport function runTraining() {}\n", encoding="utf-8")

    def test_a_repository_git_refuses_is_not_walked(self):
        self.old_worktree()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "src", "tests", "docs"], check=True)
        with mock.patch.object(bp, "git", return_value=None):   # git refuses the repository (e.g. dubious ownership)
            code, text, _ = self.call()
        self.assertEqual(code, 0)
        unchecked = self.section(text, "## ⚠ Names not checked")
        for name in ("runTraining", "stepId", "startShow"):
            self.assertIn(f"`{name}`", unchecked)
        self.assertNotIn("## Names the card uses, and where they were found", text)
        built = self.section(text, "## Built from")
        self.assertIn("git would not read it", built)
        self.assertNotIn("clean", built)

    def test_a_walk_skips_claude_folders_and_nested_repositories(self):
        self.old_worktree()
        nested = self.repo / "vendor/other"
        (nested / ".git").mkdir(parents=True)
        (nested / "x.ts").write_text("export const stepId = 1;\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.stale(text))
        self.assertIn("`runTraining`", self.stale(text))

    def test_csharp_brace_on_the_next_line_and_raw_strings(self):
        (self.repo / "Coach.cs").write_text(
            'class Coach\n{\n    public void runTraining()\n    {\n    }\n'
            '    string raw = """export const stepId = 1""";\n}\n', encoding="utf-8")
        _, text, _ = self.call()
        self.assertNotIn("`runTraining`", self.stale(text))
        self.assertIn("`stepId`", self.stale(text))

    def test_an_unclosed_comment_hides_nothing(self):
        (self.repo / "src/city/citizens/open2.ts").write_text("/* export const stepId = 1;\n", encoding="utf-8")
        (self.repo / "Paths.cs").write_text('var dir = @"C:\\dir\\"; var s = "export const runTraining = 1";\n',
                                            encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("`stepId`", self.stale(text))
        self.assertIn("`runTraining`", self.stale(text))

    def test_a_plain_word_label_after_a_blank_line_stays_in_the_field(self):
        card = bp.parse_card("# CN1 · x\n- **Goal:**\n\nNote: the plaza fills up.\n- **Acceptance:**\n  1. Test: a.\n"
                             "- **Owns:** `src/a.ts`\n- **Reviewer gate:** the video.\n\nSoaks: 30 minutes on medium.\n"
                             "\nMerge note: keep `x`.\n")
        self.assertEqual(card["goal"], ["Note: the plaza fills up."])
        self.assertEqual(card["reviewer_gate"], ["the video.", "Soaks: 30 minutes on medium."])


class RoundFiveCases(BriefCase):
    def test_calls_with_arguments_and_short_names_are_never_silently_skipped(self):
        self.card.write_text(CARD + "\nCall `runTraining(level)`, `go()` and `go2(x)`; the `fx` package.\n",
                             encoding="utf-8")
        _, text, _ = self.call()
        stale = self.section(text, "## ⚠ Stale references")
        for name in ("runTraining", "go", "go2"):
            self.assertIn(f"`{name}`", stale)
        self.assertIn("`fx`", self.section(text, "## ⚠ Names not checked"))
        checked, short = bp.card_names("`go()` `fx` `id` `abc` `a.b` `src/x.ts`")
        self.assertEqual((checked, short), ({"go", "abc"}, {"fx", "id"}))


class RoundFiveClaudeCases(BriefCase):
    def test_import_meta_and_dynamic_import_blocks_define_nothing(self):
        (self.repo / "src/city/citizens/dyn.ts").write_text(
            "if (import.meta.env.DEV) { stepId(); }\nimport('./x').then((m) => { runTraining(); });\n",
            encoding="utf-8")
        _, text, _ = self.call()
        stale = self.section(text, "## ⚠ Stale references")
        self.assertIn("`stepId`", stale)
        self.assertIn("`runTraining`", stale)

    def test_found_line_numbers_survive_multi_line_comments_and_strings(self):
        (self.repo / "src/city/citizens/lines.ts").write_text(
            "/* one\ntwo\nthree */\nconst s = `a\nb`;\nexport const stepId = 1;\n", encoding="utf-8")
        _, text, _ = self.call()
        self.assertIn("- `stepId`: `src/city/citizens/lines.ts:6`: export const stepId = 1;",
                      self.section(text, "## Names the card uses, and where they were found"))


class ClosedCheckCases(BriefCase):
    def test_a_refused_repository_lists_every_card_name_as_not_checked(self):
        self.card.write_text(CARD + "\nAlso `go(level)` and the `id` field.\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        with mock.patch.object(bp, "git", return_value=None):   # git refuses the repository (e.g. dubious ownership)
            _, text, _ = self.call()
        unchecked = self.section(text, "## ⚠ Names not checked")
        for name in ("go", "id", "runTraining", "stepId", "startShow"):
            self.assertIn(f"`{name}`", unchecked)


class EncodingCases(BriefCase):
    def test_decisions_written_by_windows_powershell_are_read(self):
        # PowerShell 5.1 `>` writes UTF-16LE with a BOM; Out-File -Encoding utf8 writes UTF-8 with a BOM.
        for encoding, bom in (("utf-16-le", b"\xff\xfe"), ("utf-8", b"\xef\xbb\xbf"), ("utf-8", b"")):
            with self.subTest(encoding=encoding, bom=bom):
                self.decisions.write_bytes(bom + json.dumps(DECISIONS, ensure_ascii=False).encode(encoding))
                code, text, err = self.call()
                self.assertEqual(code, 0, err)
                self.assertIn("#40", self.section(text, "## Decisions"))

if __name__ == "__main__":
    unittest.main()
