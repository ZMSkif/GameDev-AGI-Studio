---
name: studio-rules
description: Binding GameDev AGI Studio rules for the ZMSkif/GameDev-AGI-Studio repository. Use before any planning, implementation, pull request or review work on a GameDev Studio game or on this plugin; it tells the agent to fetch the owner's approved decisions from GitHub Issues with gh and how to apply them.
---

# GameDev Studio rules

Decisions and tasks live in GitHub Issues and Projects of `ZMSkif/GameDev-AGI-Studio`, never in Markdown trackers (DEC-002, #2).

Before designing interfaces, read the studio's `AGENTS.md` and `contracts/v1/`. When the current directory is a game repository they are not local, so read them from GitHub instead of searching the working tree:

- `gh api repos/ZMSkif/GameDev-AGI-Studio/contents/AGENTS.md -H "Accept: application/vnd.github.raw"`
- `gh api repos/ZMSkif/GameDev-AGI-Studio/contents/contracts/v1 --jq '.[].name'` to list the contracts, then the same call with a file path and the `Accept` header above to read one.

Rules (a) to (i) apply to any work on a GameDev Studio game or on this plugin:

- (a) Fetch the decisions first. Run `gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --state open --limit 1000`, then read the relevant ones with `gh issue view <n> -R ZMSkif/GameDev-AGI-Studio`. A new agent gets all accepted requirements from GitHub, not from earlier chats (DEC-010, #10).
- (b) Decisions are binding. Never re-ask a question the owner already answered, and never modify, bypass or supersede a decision (DEC-003, #3).
- (c) When a source is missing or you are unsure what the owner decided, ask the owner instead of inventing the decision or leaving a silent gap (DEC-004, #4).
- (d) Never present invented tests, tools or stubs as finished results; report only what you actually ran and observed (DEC-016, #16).
- (e) Work in a separate branch and open a pull request; never push directly to `main` (DEC-001, #1).
- (f) No secrets in the repository, and no paid actions or publishing without explicit owner approval (DEC-009, #9).
- (g) Never accept your own work; an independent reviewer is required (DEC-040, #40).
- (h) Deferred for good by DEC-146 (#164), which confirms DEC-143 (#146): the decisions listed in #146 under "Затрагивает", such as the self-hosted coordinator, PostgreSQL execution, workers and Studio Control Center. They are closed as not planned. Do not build or plan them; only a new owner decision can bring one back. Memory (DEC-024, DEC-100 to DEC-106, DEC-138) stays in force.
- (i) Engine: `contracts/v1/game-production-policy.json` (`engine_profiles`) names the engine profiles: web for HTML5 portal games and Godot 4.x for heavy or desktop games (DEC-145 (#161); DEC-012, #12). Read the `engine-profiles` skill before you choose an engine or apply a rule that names Godot. The owner approves each game's profile with its architecture (DEC-080, #81).
