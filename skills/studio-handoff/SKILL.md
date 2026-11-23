---
name: studio-handoff
description: Transfer an in-progress GameDev Studio piece to a fresh Claude Code or Codex session using a compact, revision-linked GitHub checkpoint. Use near a context or usage limit, before a pause, or when ownership changes.
---

# Studio handoff

Apply the `studio-rules`, `orchestration-playbook` and `context-brief` skills. Work from the existing piece Issue or PR. The checkpoint carries enough detail to resume. Binding decisions still come from their approved sources (DEC-002, DEC-102, DEC-103).

1. **Record the exact state.** Include the Issue or PR URL, worktree or branch, last available commit, current ownership, next unfinished acceptance line, last checks and their results, and the single next step. Explicitly say which work is uncommitted and where it lives. Include runtime constraints or approved decisions only when needed to resume.
2. **Use one checkpoint.** When a comment is authorized, place it on the corresponding Issue or PR. When pausing before that action is authorized, prepare the checkpoint locally and give the owner or next session its path. Keep private transcripts, account details and credentials out of comments, handoffs and commits.
3. **Resume from current evidence.** In a new session, reopen the Issue, confirm the branch and `git status`, read the relevant decisions and rebuild the worker brief when inputs changed. If local changes are unavailable, recover from the known worktree or commit before continuing. The paused agent or its coordinator should confirm the transfer so two sessions do not edit the same piece.
4. **Keep review separate.** An independent reviewer opens a fresh session on the exact commit or archive and uses the `review-evidence` skill for the result. Existing approval and publishing boundaries apply after a handoff.

Optional external workflow and mobile setup: [Mr. Mak with GameDev Studio](../../reference/mr-mak-workspace.md). Source for the fresh-chat convention: [Mr. Mak handoff](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/desktop/service/handoff.mjs).
