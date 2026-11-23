---
description: Run the release gate of one build for one platform (Playgama by default) with an independent Release QA Engineer, then a separate pre-publish review. Reports every requirement by number; publishes nothing.
argument-hint: "[platform, default playgama] [build or archive path]"
---

Run the release gate for: `$ARGUMENTS` (platform first, default `playgama`; then the build or archive, default the current production build).

1. Apply the `studio-rules` and `playgama-release` skills. Re-read the live platform rules (Playgama MCP `get_game_checklist`, `get_bridge_sdk_docs`) and date them; mark them `UNVERIFIED` if the MCP is not connected.
2. Fix the exact build: version, commit and, for an archive, its SHA-256 (`/gamedev-studio:package-playgama` makes one).
   For an existing local ZIP, use the [pre-release report](../reference/browser-visual-qa.md#local-pre-release-report) to record archive size and any measured browser QA observations.
3. Delegate the gate to the `gamedev-studio:release-qa-engineer` subagent with the build, the platform's QA matrix and the previous release's report. In Codex, play that role from `agents/release-qa-engineer.md` in a fresh session.
4. When it reports, delegate the archive to the `gamedev-studio:pre-publish-reviewer` subagent, a different agent from the one that ran the gate (DEC-040, #40).
5. Archive both verdicts verbatim (`/gamedev-studio:archive-reviews`).
6. Report to the owner: a table by requirement number with pass, fail or not run, the blockers, what only a human can check (feel, sound, visual, real devices), and the question whether to publish, with options. Publishing is a separate step and needs the owner's yes (DEC-009, #9; DEC-077, #78).
