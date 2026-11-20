---
description: Mine the verbatim review archive for recurring failure classes, store the kept lessons in studio memory with provenance, and propose plugin changes on a local draft branch. Nothing is pushed.
argument-hint: "[--since N] [review folder, default docs/reviews]"
---

Run the lessons procedure of the `lessons` skill for `$ARGUMENTS`.

1. The review folder is the argument that is not `--since`; the default is `docs/reviews` in the current game repository. The game repository's `owner/name` comes from `git remote get-url origin`.
2. Without `--since`, find the last run in the studio memory bank. Use `recall` with the query `lessons run <owner/name>`, tags `["lessons-run", "repo:<owner/name>"]`, `tags_match: "all_strict"` and `types: ["world", "experience"]`. Take the highest `archive_last` in the results' metadata. With no result, use 0.
3. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/mine_lessons.py" --reviews <folder> --since <N> --out <scratch folder>/lessons.md` and show the report. The out file must be outside the game repository.
4. Read every hit in the report: its file and line, piece, "severe" mark and doubts. Decide for each class in "Lessons" and "Doubtful" whether it is a real recurring failure, and say why for each class you keep or leave out.
5. If the studio bank is wired (`memory` skill), store only the kept classes: the same command plus `--retain <base> --bank gamedev-studio::studio --repository <owner/name> --keep <class>` for each one. Add a `--forbid` pattern for local user paths. Exit code 3 means something was not stored. Show what was stored and follow the printed line: a refusal gives the retry (`--run-token <token>` with `--keep` for the rest, or `--mark-run` when only the marker is missing); an UNKNOWN item may already be in the bank, so recall it by its `lessons_run` token before storing anything again.
6. Make the proposed changes in a worktree of `ZMSkif/GameDev-AGI-Studio` on a local branch `lessons/<date>`. Never edit the installed plugin copy or a marketplace clone.
   - Commit a safe, non-creative change only after `python scripts/validate_contracts.py`, `python scripts/validate_plugin.py` and `python -m unittest discover -s tests` pass. List it as an automatic change (DEC-106, DEC-100).
   - Write each creative change as an owner question with options instead.
7. Never push the branch or open a PR without the owner's yes.
