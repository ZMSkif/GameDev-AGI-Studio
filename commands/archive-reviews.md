---
description: Archive every independent reviewer verdict of this session verbatim into the game's review folder.
argument-hint: "[archive folder, default docs/reviews]"
---

Archive the reviewer verdicts of this session verbatim, as the `orchestration-playbook` skill of the gamedev-studio plugin describes (section "Verbatim review archive").

Steps:
1. The archive folder is `$ARGUMENTS`; if it is empty, use `docs/reviews` in the current game repository.
2. This session is `${CLAUDE_SESSION_ID}`. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/archive_reviews.py" --session ${CLAUDE_SESSION_ID} --out <archive folder> --dry-run`. The script finds exactly this session's transcript and fails if it cannot; never pick a transcript by its date, because parallel sessions write to the same folder. Show the list of files it would write.
3. Run it again without `--dry-run`. Pass `--forbid` with a pattern for anything private you must not commit, such as a local user folder path.
4. If the script reports `SKIPPED`, open those verdicts yourself, remove the secret or private text in a copy, and tell the user what was left out. Never commit a skipped verdict unchanged.
5. Commit the new files in the game repository on its working branch. Do not push.
