---
name: studio-handoff
description: Transfer an in-progress GameDev Studio piece to a fresh Claude Code or Codex session, another agent or a developer using a compact, revision-linked GitHub checkpoint. Use near a context or usage limit, before a pause, when ownership changes, or to hand a finished change to review.
---

# Studio handoff

Apply the `studio-rules`, `orchestration-playbook` and `context-brief` skills. Work from the existing piece Issue or PR. The checkpoint carries enough detail to resume; binding decisions still come from their approved sources (DEC-002, DEC-102, DEC-103).

Read the current project files and the relevant terminal output or report before writing a handoff. Use the evidence on disk now, not an earlier progress message.

## 1. Record the exact state

- The Issue or PR URL, worktree or branch, last commit and the expected base revision.
- The intended behaviour, affected files, useful starting points, the exact skills to load and the known constraints.
- What is implemented, what remains, the next unfinished acceptance line, the last checks with their actual results, and the single next step.
- Which work is uncommitted and where it lives, and any running process (dev server, editor, long build, paid job) that must not be interrupted.
- For assets: stable IDs, hashes, local dependency paths, actual event markers, the receiving scene or system, and how to check it at normal gameplay speed.
- Carry forward accepted choices and unresolved questions. Leave missing values unresolved instead of turning an example's timing, names or taste into requirements.

## 2. Make ownership clear

State who owns which shared files and which files must not be overwritten. The receiving side re-reads shared state before applying the handoff and reconciles changed inputs instead of overwriting another agent's work. The paused agent or its coordinator confirms the transfer so two sessions never edit the same piece. Do not assign the owner work the receiving agent can do itself.

## 3. Keep the states apart

Separate the source baseline, the selected proposal, the implemented behaviour, agent verification and owner acceptance. A selected mockup is not a shipped feature; a submitted generation job is not a reviewed asset; a prepared build is not an installed update. Keep the current specification current and put chronological details in the development log.

## 4. Use one checkpoint

When a comment is authorized, place it on the Issue or PR. When pausing before that is authorized, prepare the checkpoint locally and give the owner or the next session its path. Keep private transcripts, account details, credentials and signed links out of comments, handoffs and commits.

## 5. Resume from current evidence

In the new session, reopen the Issue, confirm the branch and `git status`, read the relevant decisions and rebuild the worker brief when inputs changed. If local changes are unavailable, recover them from the known worktree or commit before continuing.

## 6. Hand a finished change to review

Lead with the practical result, then summarize the change and the verification, with links to the report or artifacts. An independent reviewer opens a fresh session on the exact commit or archive and uses `review-evidence`. Existing approval and publishing boundaries apply after a handoff.

Optional desktop and phone setup: [Mr. Mak with GameDev Studio](../../reference/mr-mak-workspace.md). Sources: [Mr. Mak feature handoff](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/feature-handoff/SKILL.md) and [handoff.mjs](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/desktop/service/handoff.mjs) (MIT, see `reference/mr-mak-notices.md`).
