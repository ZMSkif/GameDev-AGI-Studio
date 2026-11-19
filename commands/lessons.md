---
description: Mine the verbatim review archive since the last run for recurring failure classes, store the lessons in studio memory with provenance, and propose plugin changes on a local draft branch. Nothing is pushed.
argument-hint: "[--since N] [review folder, default docs/reviews]"
---

Run the lessons procedure of the `lessons` skill for `$ARGUMENTS`.

1. The review folder is the argument that is not `--since`; the default is `docs/reviews` in the current game repository. Without `--since`, find the last run's value in the studio memory bank (recall "lessons last run", tag `lesson:*`, `types: ["world", "experience"]`), or use 0.
2. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/mine_lessons.py" --reviews <folder> --since <N> --out <scratch folder>/lessons.md` and show the report.
3. Remove false hits, saying which you removed and why. If the studio bank is wired (`memory` skill), store the rest with `--retain <base> --bank gamedev-studio::studio`, adding a `--forbid` pattern for local user paths.
4. In the plugin repository, create a local branch `lessons/<date>` and make the changes the report proposes. Commit the safe, non-creative ones and list them as automatic changes (DEC-106, DEC-100). Write each creative change as an owner question with options instead.
5. Never push, open a PR or create an Issue without the owner's yes.
