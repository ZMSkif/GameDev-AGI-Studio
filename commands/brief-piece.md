---
description: Build one worker brief for a piece from its GitHub Issue - decisions, skills, owned files and what they read, earlier review notes, memories with provenance, a free port range and the commit-as-you-go rule. Reads only; writes the brief outside the repository.
argument-hint: "<issue number> [port range, e.g. 5303-5305]"
---

Build the brief for `$ARGUMENTS` as the `context-brief` skill describes.

1. The first word of the arguments is the piece's issue number in the current game repository; the second, if given, is its port range. Without a range, ask the coordinator for one; never pick a range already in the registry.
2. Save the card: `gh issue view <number> --json title,body --jq '"# " + .title + "\n\n" + .body'` into a file in your scratch or temp folder, outside the repository. Note its `updatedAt` (`gh issue view <number> --json updatedAt`).
3. Save the decisions: `gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --state open --limit 1000 --json number,title,url,body` into the same folder.
4. If the project's memory bank is wired (`memory` skill), save a recall of facts for the piece's title and goal (`types: ["world", "experience"]`) as JSON there too.
5. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/brief_piece.py" --card <card> --card-source "issue #<number> updated <updatedAt>" --repo-root . --decisions <decisions> [--memories <memories>] --ports <port registry> --port-range <range> --out <scratch folder>/brief-<number>.md`.
6. Exit 3 means the port range clashes: pick another free range and run again. Exit 2 means the card is incomplete: send it back to the coordinator.
7. Show the brief and say which warnings it raised (stale names, mockup lines). Do not commit the brief.
