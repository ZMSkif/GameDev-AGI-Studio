---
name: lessons
description: Learning and Improvement, light (DEC-105, DEC-106) - once per release or on demand, mine the verbatim review archive for recurring failure classes, keep only lessons past the noise guard (2 independent pieces or 1 blocker), store each lesson in the studio memory bank with provenance, and propose plugin changes on a local draft branch. Use after a release, after a run of blocked reviews, or when the same kind of defect keeps coming back.
---

# Lessons

Binding:
- DEC-105 (#107): improvement comes from real QA failures and results.
- DEC-106 (#108): safe, verified, non-creative improvements may apply automatically, with a notice.
- DEC-100 (#101): every automatic change is notified.
- DEC-024 (#24): memory is never authoritative.
- DEC-138 (#140): only the owner deletes memory.
- DEC-001 (#1): changes go through a branch and a PR.

The contract is `contracts/v1/knowledge-policy.json` (`learning`).

`scripts/mine_lessons.py` mines the archive. `/gamedev-studio:mine-lessons` runs the whole procedure.

## The noise guard

A failure class is a candidate lesson only with **at least 2 independent occurrences** or **one severe one**. The script proposes; the agent decides. Nothing is stored unless the agent names the class with `--keep` after reading its hits, because only the owner can remove a stored memory (DEC-138).
- **Independent** means different pieces. Reviews whose titles share a piece code in any case (CN1, cn1, WP0, WA-0, CA1b) are one piece, even through a third review. A review item (B1, M3, R2) or a fix round (r17) counts only when the title names no other code; a version (v2) never does. A title without a code counts as its words, minus review words such as "re-review", "fix round" and "piece". Titles that share no code stay apart, so check the printed groups.
- **Severe** means a line under a blocker or must-fix heading. A section is not severe when its heading says there is none ("No blockers", "Must-fix list: none") or its first line is "None." on its own, as the archive writes it.
- **Doubts annotate, never remove.** A hit whose line only reports a pass ("music passed all checks") or only says a defect is absent ("music is not stuck") is marked doubtful in the report and does not count toward the guard. A class that passes the guard only with doubtful hits is listed under "Doubtful".
- **The whole archive is always counted**, so repeats spread over several runs add up. `--since N` only limits the report to classes with a hit in a file numbered above N.

## Procedure

1. **Mine.** Run `python <plugin root>/scripts/mine_lessons.py --reviews <game>/docs/reviews --since <last run> --out <scratch>/lessons.md`. The out file must be outside the game repository.
   - The last run is the highest `archive_last` on the studio bank's `lessons-run` memories for this repository (the command shows the recall); with none, use 0.
   - The report ends with the `--since` value for the next run.
2. **Read every hit.** The report lists every hit, headings included, with its file, line, piece, "severe" and any doubt. Decide per class whether it is a real recurring failure, such as a broken audio life cycle, or a false hit, such as "music" in a credits review. Say which classes you keep and why.
3. **Store** only the kept classes in the studio bank, after the `memory` skill's checks: the same command plus `--retain <base> --bank gamedev-studio::studio --repository <owner/name> --keep <class>` for each kept class. Without `--keep`, `--retain` stores nothing and exits 2. A class must be in "Lessons" or "Doubtful" to be kept.
   - Each lesson carries provenance (the repository, the review files, the review range) and the tags `lesson`, `lesson:<class>` and `repo:<owner/name>`. A `lessons-run` memory records where the run stopped.
   - No item names a `document_id`, so Hindsight makes a new document for each and a run never replaces an earlier one (DEC-138).
   - Storing stops at the first item that is not stored for sure. A refusal (the server said no, or could not be reached) prints how to finish, with the run's `--run-token`: `--keep` with only the classes not yet stored, or `--mark-run` when only the run marker is missing. `--mark-run` without the token of an unfinished run is refused. A lost answer (a timeout or dropped connection after sending) is UNKNOWN: the item may be in the bank, so do not store again until a recall with its tags finds, or does not find, metadata `lessons_run` = the printed run token.
   - The `lessons-run` marker (`verified: "false"`, like every lesson) is stored only after every kept lesson was. If one is not stored, the marker is not stored, and the next run uses the same `--since`.
   - The whole payload (text, metadata and tags) is checked for secret-looking or `--forbid` text first. The script exits 3 when anything is not stored.
4. **Propose.** For each lesson, change the plugin part the report names: a skill section, a reviewer checklist or a validator.
   - Work in a worktree of `ZMSkif/GameDev-AGI-Studio` on a local branch `lessons/<date>`. Never edit the installed plugin copy or a marketplace clone.
   - Keep each change small, and cite the review files that motivate it.
5. **Classify each change:**
   - **Safe, verified, non-creative** (DEC-106): a checklist line, a clearer instruction or a new validator test. Commit it on the branch without asking only after the validators and the tests pass, and name it in the report (DEC-100).
   - **Creative or design-changing:** a new rule, a changed gate, balance or style. Write it as a question to the owner, with options.
6. **Ask.** Pushing the branch or opening a PR always needs the owner's yes, even for safe changes. This is the owner's rule for the memory round (19.11.2026, relayed by the coordinator), and it is stricter than DEC-106. It is recorded as `learning.push_or_pr_requires_owner_yes`. Creating an engineering task follows DEC-008 (#8).

## Classes the miner knows

They come from the Cat Challenge reviews. Add a class only when a review shows it twice:
- primitive or mangled assets at the close-up;
- colliders that do not match the mesh;
- gate rules that step;
- checks that cannot fail: stale assertions, surviving mutants, loops over nothing;
- the audio life cycle;
- text clipping;
- licence registry gaps;
- WebGL context loss;
- platform pause and mute;
- unrequested changes;
- failures that only long soaks show;
- passability per control scheme.

## Source

The Cat Challenge review archive (76 verdicts by 19.11.2026). A run of the miner on it kept 10 classes and dropped 2 below the guard. The stored copy is in the coordinator's notes, not in this repository.
