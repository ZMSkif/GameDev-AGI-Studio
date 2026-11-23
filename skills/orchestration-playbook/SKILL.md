---
name: orchestration-playbook
description: The coordinator's playbook for running a game with many agents in Claude Code or Codex - piece cards with file ownership, one independent reviewer per piece with mutants and soaks, a verbatim review archive, a visual progress board, resume notes on the tracking Issue for usage limits and restarts, port ranges, commit as you go, a separate pre-publish check, three-way decisions with Codex and the advisor, and owner questions with options. Use when you coordinate agents or sessions, split work, assign reviewers, recover after a limit or restart, or prepare an owner checkpoint.
---

# Orchestration playbook

Binding: DEC-040 (#40) nobody accepts own work; DEC-051 (#51) parallel agents in isolated branches and worktrees; DEC-052 (#52) semantic conflicts go to an independent integrator; DEC-039 (#39) bounded retries, then diagnosis, then escalation; DEC-085 (#86) on subscription limits pause, never switch to a paid API; DEC-002 (#2) GitHub Issues and Projects are the record, never Markdown trackers; DEC-003 (#3) owner decisions bind; DEC-143 (#146) the self-hosted coordinator stays deferred: this playbook uses the agent runtime's own tools.

## 1. Orchestrate, do not do the workers' jobs

The coordinator writes briefs, splits the work, keeps file ownership disjoint, integrates and checks results. Building features, writing tests and running QA suites go to agents (studio roles in `agents/`). Small glue, such as one wiring line or an owner-authorised MCP call, may stay with the coordinator. Cat Challenge owner, 17.11.2026: «Ты должен оркестрировать а не делать за них и проверять результат».

## 2. Piece cards

Every piece of work gets a card, and the card is its GitHub Issue (DEC-002, #2); a design document may explain the plan, but tasks, status and acceptance live in Issues:
- **Goal**, an effort size (S ≤ ½ day, M 1–2 days, L 3–5, XL > 5);
- **Acceptance**, numbered; each line says `Test:` (a script or test checks it) or `Shot:` (a screenshot checks it);
- **Owns:** every file the piece may change ("new" = it creates the file); reading is free; one owner per file per wave;
- **Depends** and **Reviewer gate:** the piece-specific checks on top of the general review.

Rules that kept parallel work clean: a scaffold piece first that fixes the lockfile and package skeletons so nobody reopens them; shared seams (the game's main file, save schema wiring, licence merge parts) belong to the coordinator and change only at a gate; strings go through one localisation piece; tests and harnesses are new files only.

A brief has nine parts: context (3–5 lines), read first, owns only, do not touch, contracts (unchangeable without the coordinator), rules (determinism, ports, no pushes, no secrets, questions in one message), checks that must pass, the report (the first 400 characters say what was done and where), the shared notes folder.

## 3. One independent reviewer per piece

- A separate agent reviews each piece before merge; the builder never reviews itself. Playing two roles in one session is not independent review; say so and ask for a separate reviewer.
- The reviewer works read-only in a scratch copy (`git archive` or its own worktree), never in the implementer's worktree, and stops its servers afterwards.
- It checks: the diff touches only the card's files (`git diff --name-only`); the branch merges cleanly into the current main (`git merge-tree`) and re-runs on the new head if main moved; the full suite and typecheck; every acceptance line with its own probes and captures; numbers re-measured from the shipped files.
- **Mutants:** it breaks the code on purpose (a guard removed, a margin ×10, a flag forced false) and expects tests to fail. A surviving mutant is a missing test. A known-bad input must fail the gate. A new regression test must fail on the old commit. A loop over an empty list proves nothing.
- **Soaks** run longer than the tests' own windows; **determinism** hashes are computed twice.
- The verdict is `VERDICT: CONFIRMED` or `VERDICT: BLOCKED`, with must-fix, should-fix and notes, evidence paths, and a "could not check" list. The same reviewer re-checks the fix round. Unrequested changes in a fix round are a regression risk; Cat Challenge's audio watchdog doubled the music.
- Bars that worked: the art tiers of the `art-acceptance` skill; the 10-point screen checklist (mockup match; no primitive; 0 layout issues; controls ≥ 44 px; contrast 4.5:1 text and 3:1 graphics; reduced motion and press sounds; no dark patterns; platform rules; full suite and no start-up regression over 5 %; only owned files).

## 4. Verbatim review archive

Save every verdict as it arrived, numbered, in the game repository (Cat Challenge: 69 files in `docs/reviews/` by the evening of 19.11.2026). Use `/gamedev-studio:archive-reviews` or `python <plugin root>/scripts/archive_reviews.py --transcript <session.jsonl> --out docs/reviews`. It finds task notifications whose result holds a `VERDICT:` line, dedupes by content, numbers after the highest file and refuses secret-looking bodies. The archive is evidence; it is not a task tracker.

## 5. A visual progress board

The Cat Challenge owner asked to see who did what and who reviewed it. Use the `review-evidence` skill to record acceptance evidence on the piece's Issue or PR. Keep a board page (an Artifact) with one card per piece: status, area, title, bullets, builder, reviewer, verdict, before and after images and next step in the owner's language. Update the view after each report or verdict; GitHub Issues and PRs stay the record (DEC-002).

## 6. Resume notes for usage limits and restarts

Agents stop on weekly limits (HTTP 429) or when the coordinator process restarts. Before a pause, write one resume comment on the game's tracking Issue (or its PR): per stream the branch and commit, its ports and the next step. Agent ids, which only the running coordinator can use, stay in the coordinator's own memory and are never committed. On resume, continue each agent with `SendMessage` ("continue from where you stopped"), never start duplicates, and first tell every agent to commit what it has. Cat Challenge kept a resume file in its repository (that project used Markdown plans); in a studio game the record is GitHub (DEC-002). On a limit, pause (DEC-085).

When a piece needs a fresh session because its original agent cannot resume or ownership changes, use the `studio-handoff` skill. Record a single checkpoint for the piece and verify ownership and the current revision before editing.

## 7. Ports, commits and machine hygiene

- Give each agent its own port range (Cat Challenge: 3 ports per agent, 5300–5310) and list reserved ports nobody may take.
- **Commit as you go** in the agent's own worktree: a restart loses uncommitted work (four agents were cut off on 19.11.2026; one had no commits).
- Note other heavy processes that add timing noise (a GPU-heavy process ran during reviews); report them, touch nothing.
- Name flaky-under-load tests and run release suites with other agents idle.

## 8. A separate pre-publish check

Before any publish, a fresh agent (the `pre-publish-reviewer` role) checks the exact archive: plays the production build through every level, compares memory, warnings and movement with the previous release, and re-checks what the release QA could not reach. Publishing itself needs the owner's yes (`playgama-release` skill).

## 9. Three-way decisions

For big choices (engine, stack, architecture, a contested gate): Claude, Codex (read-only) and the advisor.
- Codex answers blind first; then cross-review; at most 3–4 rounds; the verbatim exchange goes to a log the owner can read before work starts.
- Codex in Claude Code: the `codex` plugin's companion `task --background --fresh` (or `--resume-last`), with "read-only" in the prompt and long briefs passed as a file path; never pass unknown flags (they become a prompt); run `status` and `result` from the project root.
- Record disagreements honestly. A three-way majority never overrides an owner decision; anything that touches a binding decision goes to the owner. (Cat Challenge used majority rule only because its owner decided so for that project.)

## 10. Questions to the owner

Only with options, in the owner's language and plain words, the recommended option first, each option a real choice with a one-line example; batch non-blocking questions at a checkpoint so autonomous work goes on. A permission the owner gave is per game and per action; record it in GitHub and never stretch it to another game, build or action (DEC-009, #9).

## Source

Cat Challenge: `docs/city/CITY_PLAN.md` §11 (piece cards), `docs/design/MASTER_PLAN.md` §6.1 (reviewer protocol), `docs/status/RESUME_2026-11-23.md`, the 68 verdicts in `docs/reviews/`, `docs/stack-plugin/PLUGIN_PLAN.md` §7, and the coordinator's memory notes (orchestration, reviewers, board, limits, questions with options), 16–19.11.2026.
