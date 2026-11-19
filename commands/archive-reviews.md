---
description: Archive every independent reviewer verdict of this session verbatim into the game's review folder.
argument-hint: "[archive folder, default docs/reviews]"
---

Archive the reviewer verdicts of this session verbatim, as the `orchestration-playbook` skill of the gamedev-studio plugin describes (section "Verbatim review archive").

Steps:
1. The archive folder is `$ARGUMENTS`; if it is empty, use `docs/reviews` in the current game repository.
2. Find this session's transcript: the newest `*.jsonl` in `~/.claude/projects/<this project's folder name>/`. Do not guess a path; list the folder first.
3. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/archive_reviews.py" --transcript <transcript> --out <archive folder> --dry-run` and show the list of files it would write.
4. Run it again without `--dry-run`. Pass `--forbid` with a pattern for anything private you must not commit, such as a local user folder path.
5. If the script reports `SKIPPED`, open those verdicts yourself, remove the secret or private text in a copy, and tell the user what was left out. Never commit a skipped body unchanged.
6. Commit the new files in the game repository on its working branch. Do not push.
