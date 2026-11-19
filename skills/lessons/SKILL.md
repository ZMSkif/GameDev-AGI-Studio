---
name: lessons
description: Learning and Improvement, light (DEC-105, DEC-106) - once per release or on demand, mine the verbatim review archive for recurring failure classes, keep only lessons past the noise guard (2 independent pieces or 1 blocker), store each lesson in the studio memory bank with provenance, and propose plugin changes on a local draft branch. Use after a release, after a run of blocked reviews, or when the same kind of defect keeps coming back.
---

# Lessons

Binding: DEC-105 (#107) improvement comes from real QA failures and results; DEC-106 (#108) safe non-creative improvements may apply automatically, with a notice; DEC-100 (#101) every automatic change is notified; DEC-024 (#24) memory is never authoritative; DEC-001 (#1) changes go through a branch and PR. The contract is `contracts/v1/knowledge-policy.json` (`learning`).

`scripts/mine_lessons.py` mines the archive; `/gamedev-studio:lessons` runs the whole procedure.

## The noise guard

A failure class becomes a lesson only with **at least 2 independent occurrences** or **one severe one**. Independent means different pieces: three re-reviews of the same piece count once. Severe means the line sits under a blocker or must-fix heading. Everything below the guard is listed, not stored.

## Procedure

1. **Mine.** Run `python <plugin root>/scripts/mine_lessons.py --reviews <game>/docs/reviews --since <last run> --out <scratch>/lessons.md`. The report ends with the `--since` value for the next run. On a first run, use 0.
2. **Read the report.** Every lesson lists its pieces, its files and two example lines. Drop any class whose examples are false hits, such as "music" in a credits review, and say which you dropped and why.
3. **Store** the kept lessons in the studio bank, with provenance (review files, the review range) and the tag `lesson:<class>`. Use `--retain <base> --bank gamedev-studio::studio`, after the `memory` skill's checks. The retain step refuses secret-looking or `--forbid` text and exits 3 when anything is not stored.
4. **Propose.** For each lesson, change the plugin part the report names (a skill section, a reviewer checklist or a validator) on a local branch `lessons/<date>` in the plugin repository. Keep each change small, and cite the review files that motivate it.
5. **Classify each change:**
   - **Safe, non-creative** (DEC-106): a checklist line, a clearer instruction or a new validator test. It may be committed on the branch without asking, and the report names it (DEC-100).
   - **Creative or design-changing:** a new rule, a changed gate, balance or style. Write it as a question to the owner, with options.
6. **Ask.** Pushing the branch, opening a PR or creating an Issue always needs the owner's yes, even for safe changes (studio rule, stricter than DEC-106 allows).

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

Cat Challenge review archive (73 verdicts by 19.11.2026). A first run of the miner on it kept 10 classes and dropped 2 below the guard; the stored copy is in the coordinator's notes, not in this repository.
