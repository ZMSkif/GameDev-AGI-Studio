---
name: context-brief
description: Context Intelligence, light (DEC-102) - turn a piece card (Goal, Acceptance with Test/Shot lines, Owns, Depends, Reviewer gate) into one brief for a worker agent with the relevant decision issues, plugin skills, owned files and the files they read, earlier review notes for that piece, Hindsight memories with provenance, a free port range and the commit-as-you-go rule. Use before delegating any piece, when writing a worker brief, or when an agent needs exactly the context for one task.
---

# Context brief

Binding: DEC-102 (#103) give an agent only relevant sources, with revision and provenance; DEC-103 (#104) the source of truth wins over memory; DEC-002 (#2) tasks and status live in GitHub, so the brief is a working file outside the repository; DEC-051 (#51) one worktree per agent; DEC-040 (#40) a separate reviewer.

`scripts/brief_piece.py` builds the brief; `/gamedev-studio:brief-piece <issue>` runs it. It only reads, and it writes one file outside the game repository. It never changes code.

## What goes in, and why

| Section | From | Prevents |
|---|---|---|
| Goal, Definition of done | the card; every acceptance line, each with `Test:` or `Shot:` evidence | Cat Challenge marked a board card done when only the mockup existed. Done now means the built game, and a line that points at a mockup is flagged |
| Owns / Reads | the card's Owns (a path marked "new" may not exist yet), expanded in the repository, plus the files they import | edits outside the piece; missing context |
| Decisions | decision issues ranked by the card's words, always with DEC-001, DEC-016, DEC-040 | re-deciding what the owner decided |
| Skills | plugin skills ranked by the card's words, always `studio-rules` | reinventing a solved procedure |
| Stale references | backticked names in the card that no tracked source file defines, exports or imports; a comment that names a removed function does not count | a stale merge recipe (`runTraining`, `stepId`) that would have broken the typecheck |
| Notes from earlier reviews | verbatim: whole "For <piece>:" blocks, every line or block in another piece's review that names the piece, and must / block / fix lines about owned files | notes for CN1 that the coordinator had to paste by hand |
| Memories | project-bank facts with provenance only, marked "verify before use" | memory treated as truth |
| Rules | ports, commit as you go, no push | two agents given clashing port ranges; a range that shares even one port is refused, exit 3 |
| Built from | the game repository's HEAD and its uncommitted changes, the card's hash and source, the decisions and memories files' hashes, the review archive's last file, the plugin version | a brief that silently mixes revisions (DEC-102) |

## Procedure

1. Read the piece's GitHub Issue: `gh issue view <n> --json title,body,updatedAt` into a file outside the repository. A card without numbered acceptance lines or an Owns list goes back to the coordinator.
2. Fetch the decisions once: `gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --state open --limit 1000 --json number,title,url,body`.
3. If a project memory bank is wired (`memory` skill), recall facts for the piece: `types: ["world", "experience"]`, query = the card's title and goal, saved as JSON. A memory without all five provenance fields is left out.
4. Take a free port range from the coordinator's registry (a JSON map of stream → `[first, last]`).
5. Run `python <plugin root>/scripts/brief_piece.py --card <card> --card-source "issue #<n> updated <updatedAt>" --repo-root <game repo> --decisions <json> [--memories <json>] --ports <registry> --port-range <a-b> --out <file outside the repo>`.
6. Read the brief before sending it. Fix the card, not the brief, when the brief flags a stale name or a mockup line. Add the piece's range to the port registry.

## Limits

- It ranks by shared words, so check the decision list. Add any decision the coordinator knows applies.
- Imports are found for relative JS/TS imports and Godot `res://` loads only.
- Definitions are found by pattern for JS/TS, Python, GDScript, C# and JSON keys. A name defined some other way, for example by a code generator, is reported as stale: check it before you change the card.
- Notes come from the archive's wording. A note that never names the piece or an owned file is not found, so read the reviews of the pieces it depends on.
- It is a brief, not a record: status stays on the Issue and the PR.

## Source

Cat Challenge:
- `docs/city/CITY_PLAN.md` §11 (piece cards);
- `docs/status/RESUME_2026-11-23.md` (CN1 notes, ports, the `runTraining` warning);
- the owner's board rule (a card shows who built and who reviewed).

`tests/test_brief_piece.py` tests these four failures, with the real card's shape and the real archive's note shapes.

A run on the real CN1 card and the 76-file archive (19.11.2026, read only) found:
- the three "For CN1:" notes in the CS1 review;
- the four prose notes in the CS1 and CK2 reviews (plaza visit spots, `holding`, emotes, debounce);
- other lines in the CK2 and CS1 reviews that name CN1.

It flagged `stepId` and not `runTraining`, in 11 s.
