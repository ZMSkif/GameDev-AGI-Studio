---
name: studio-team
description: Index of the nine base GameDev Studio roles (Studio Director, Producer, Game Designer, Art Director, Technical Director, Gameplay Engineer, Asset Pipeline Artist, QA Engineer, Publishing and Analytics Agent) and the on-demand specialists (Release QA Engineer, Pre-publish Reviewer, Art Reviewer, i18n Language Reviewer, Crowd and NPC Soak Reviewer), and how to use them. Use when a task needs a specific studio role or reviewer, when assigning or reviewing work between roles, or in Codex, where the roles are played one after another from the role files.
---

# GameDev Studio team

The base team is fixed at nine roles; specialists may be added on demand but the nine are never reduced (DEC-142, #144; DEC-032, #32). The authoritative list is `contracts/v1/agent-team-policy.json` (`minimum_roles`). Each role is defined once, in `agents/<file>` at the plugin root.

| Role | Role file |
| --- | --- |
| Studio Director | `agents/studio-director.md` |
| Producer | `agents/producer.md` |
| Game Designer | `agents/game-designer.md` |
| Art Director | `agents/art-director.md` |
| Technical Director | `agents/technical-director.md` |
| Gameplay Engineer | `agents/gameplay-engineer.md` |
| Asset Pipeline Artist | `agents/asset-pipeline-artist.md` |
| QA Engineer | `agents/qa-engineer.md` |
| Publishing & Analytics Agent | `agents/publishing-analytics-agent.md` |

## On-demand specialists

Added on demand, never instead of a base role (DEC-032, #32; DEC-142, #144). Most are read-only reviewers that return `VERDICT: CONFIRMED` or `VERDICT: BLOCKED`; the coordinator archives each verdict verbatim (`orchestration-playbook` skill).

| Specialist | Role file | Use for |
| --- | --- | --- |
| Release QA Engineer | `agents/release-qa-engineer.md` | the full release gate of one build for one platform, by requirement number |
| Pre-publish Reviewer | `agents/pre-publish-reviewer.md` | the last independent check of the exact archive before any publish |
| Art Reviewer | `agents/art-reviewer.md` | a strict art review: no primitives, tiers A/B/C, posed fit |
| i18n Language Reviewer | `agents/i18n-native-reviewer.md` | an AI language review of every language; not a human native read |
| Crowd and NPC Soak Reviewer | `agents/crowd-soak-reviewer.md` | long soaks, mutants and determinism hashes for crowds, NPCs and bots |

## In Claude Code

The roles are plugin subagents named `gamedev-studio:<file name without .md>`, for example `gamedev-studio:qa-engineer`. Delegate the task to the subagent; do not play the role inline.

## In Codex

Codex 0.169.0 did not discover custom agents shipped inside a plugin, so the roles are played one after another in the same session:

1. Apply the `studio-rules` skill first.
2. Find the plugin root: the directory two levels above this `SKILL.md` (it contains `agents/`). Read the role file for the role you are about to play, and follow its mission, "Does not do" list, required inputs, outputs and escalation.
3. Do the work as that role only, and finish it with the evidence the role file requires.
4. Review is a separate step: read the reviewer role's file named in "Reviewed by", and review the work as that role. Where possible, start the review in a fresh agent or session instead of the one that did the work.

## Rules that hold in both

- Nobody accepts their own work; an independent reviewer is required (DEC-040, #40). Playing two roles in one session is not independence, so say so in the result and request a separate reviewer.
- Retries are bounded; then independent diagnosis, then the Technical Director, then the owner (DEC-039, #39).
- Overlapping semantic edits are reconciled by an independent integration engineer, an on-demand specialist outside the nine (DEC-052, #52).
- Report only what was actually run and observed (DEC-016, #16).
- Reviewer and duty assignments are a proposal under DEC-040 and DEC-072, not an owner decision; the owner may change them.
