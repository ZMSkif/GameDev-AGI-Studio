---
description: Assign an independent reviewer to one piece of work - card, diff scope, merge check, full suite, own probes, mutants, soaks where relevant - and archive the verdict verbatim. The builder never reviews itself.
argument-hint: "<piece id or issue number> [branch]"
---

Review the piece `$ARGUMENTS` with an independent reviewer, as the `orchestration-playbook` skill describes (sections "Piece cards" and "One independent reviewer per piece").

1. Find the piece's card (its GitHub Issue or the game's plan): goal, numbered acceptance lines (`Test:` / `Shot:`), Owns, Depends, Reviewer gate. If the card has no acceptance lines or no Owns list, stop and ask the coordinator to complete it.
2. Pick the reviewer by the work: `gamedev-studio:art-reviewer` for assets and screens, `gamedev-studio:i18n-native-reviewer` for text, `gamedev-studio:crowd-soak-reviewer` for crowds, NPCs and bots, `gamedev-studio:qa-engineer` for gameplay and code, `gamedev-studio:release-qa-engineer` for a release build. It must not be the agent that built the piece (DEC-040, #40). In Codex, start the review in a fresh session from the role file.
3. Brief the reviewer: the card, the branch and its base, read-only work in a scratch copy, stop servers afterwards, and these checks: diff limited to Owns; clean merge into the current main; full suite and typecheck; each acceptance line with its own probes; mutants that must die and a known-bad control that must fail; soaks longer than the tests' own windows where behaviour runs over time; numbers re-measured from shipped files. Ask for `VERDICT: CONFIRMED` or `VERDICT: BLOCKED`, must-fix, should-fix, notes, evidence paths and "could not check".
4. On BLOCKED, send the must-fix list to the builder, then send the fix round to the same reviewer.
5. Archive every verdict verbatim with `/gamedev-studio:archive-reviews` and update the progress board.
