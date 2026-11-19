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

A failure class becomes a lesson only with **at least 2 independent occurrences** or **one severe one**. Everything below the guard is listed, not stored.
- **Independent** means different pieces. The piece is the code in the review's title (CN1, WP0, WA-0). A title without a code counts as its words, minus review words such as "re-review" and "fix round". So a piece and its re-reviews count once.
- **Severe** means a defect line under a blocker or must-fix heading. A heading such as "No blockers" is not severe. A line that only reports a pass ("music passed all checks") is not an occurrence.
- **The whole archive is always counted**, so repeats spread over several runs add up. `--since N` only limits the report to lessons with a file numbered above N.

## Procedure

1. **Mine.** Run `python <plugin root>/scripts/mine_lessons.py --reviews <game>/docs/reviews --since <last run> --out <scratch>/lessons.md`. The out file must be outside the game repository.
   - The last run is the highest `archive_last` on the studio bank's `lessons-run` memories for this repository (the command shows the recall); with none, use 0.
   - The report ends with the `--since` value for the next run.
2. **Read the report.** Every lesson lists its pieces, its files and two example lines. Drop each class whose examples are false hits, such as "music" in a credits review: run again with `--drop <class>` and say which you dropped and why. A dropped class is neither reported as a lesson nor stored.
3. **Store** the kept lessons in the studio bank, after the `memory` skill's checks: the same command plus `--retain <base> --bank gamedev-studio::studio --repository <owner/name>`.
   - Each lesson carries provenance (the repository, the review files, the review range) and the tags `lesson`, `lesson:<class>` and `repo:<owner/name>`. A `lessons-run` memory records where the run stopped.
   - Every document id is new for each run, so a run never replaces an earlier one (DEC-138).
   - The whole payload (text, metadata, tags and id) is checked for secret-looking or `--forbid` text first. The script exits 3 when anything is not stored.
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
