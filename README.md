# GameDev AGI Studio

**Authoritative decisions:** [GitHub Issues · decision](../../issues?q=is%3Aissue+label%3Adecision).

**Machine-readable implementation contracts:** [`contracts/v1/`](contracts/v1/).

**AI agent instructions:** [`AGENTS.md`](AGENTS.md).

Development Issues and Projects are created by Claude/Codex from the approved decisions. No unverified vendor integration or completed implementation is implied.

## Plugin

This repository is a plugin for Claude Code and Codex named `gamedev-studio` (display name "GameDev Studio"); the repository root is both the marketplace and the plugin ([DEC-143](../../issues/146)). It ships the skill `studio-rules`, which tells an agent to fetch the binding decisions from GitHub Issues before working on a game or on this plugin, the nine base team roles and five on-demand specialists as Claude Code subagents in `agents/` (see [Agent Team](#agent-team)), the skill `studio-team`, which indexes the roles, the production skills below, and Claude Code commands in `commands/`.

### Engine profiles

`contracts/v1/game-production-policy.json` 2.0.0 names the engine per profile (`engine_profiles`). Today it holds only the Godot profile: Godot 4.x, [DEC-012](../../issues/12). Readers of the old top-level `engine` key read `engine_profiles.profiles.godot.engine` instead.

The owner chose two profiles on 19.11.2026: web for HTML5 portal games (Three.js for 3D, 2.5D and light 2D; PixiJS v8 for rich 2D) and Godot 4.x for heavy or desktop games. The skill `engine-profiles` describes both. The web profile enters the contract only once the owner's decision issue DEC-145 exists; until then the skills mark the web text "DEC-145, not yet registered".

### Production skills

All are short, cite their decisions and name their sources (the Cat Challenge web game, 16–19.11.2026):

| Skill | For |
| --- | --- |
| `engine-profiles` | the profile of a game and which decisions bind in it; the web stack tables (`references/web-profile.md`) |
| `web-stack-choice` | choosing the renderer and libraries for 2D, 2.5D or 3D |
| `playgama-release` | Bridge steps, requirement numbers, packaging, release gate, sandbox flow and the owner's gates |
| `web-monetization` | ads, purchases, telemetry, KPIs, scenarios, live-ops |
| `art-acceptance` | no primitives, tiers A/B/C, rework of blanks, icons, the wearables posed-fit gate |
| `asset-licensing` | sources, the licence registry, credits, notices, audio processing |
| `i18n-portal` | languages, validator, length and glyph checks, the ru/uk language review |
| `fair-bots-balance` | fair bots, balance tests, determinism, crowd soaks |
| `game-feel-controls` | juice, the feel gate, one-hand touch, teaching controls |
| `web-audio-lifecycle` | music after pauses, the Howler trap, iOS, ads |
| `orchestration-playbook` | piece cards, independent reviewers with mutants, review archive, board, resume, three-way decisions |
| `gamekit` | the reusable TypeScript packages and their extraction spec |

### Commands (Claude Code)

`/gamedev-studio:new-web-game`, `/gamedev-studio:release-gate`, `/gamedev-studio:package-playgama`, `/gamedev-studio:review-piece` and `/gamedev-studio:archive-reviews`. Each is a short wrapper over a skill; Codex does not load plugin commands, so in Codex use the skills directly. `python scripts/archive_reviews.py` saves reviewer verdicts verbatim from a session transcript.

Layout: `.claude-plugin/` (Claude manifest and marketplace), `.codex-plugin/` (Codex manifest), `.agents/plugins/marketplace.json` (Codex marketplace), `skills/`, `agents/`, `hooks/`. The version is set only in the two `plugin.json` files and must match; `python scripts/validate_plugin.py` checks this.

### Install from a local clone

Verified on Claude Code 2.1.325 and Codex 0.169.0, using a throwaway config directory (`CLAUDE_CONFIG_DIR` / `CODEX_HOME`):

```
# Claude Code
claude plugin marketplace add <path-to-this-clone>
claude plugin install gamedev-studio@gamedev-studio

# Codex
codex plugin marketplace add <path-to-this-clone>
codex plugin add gamedev-studio@gamedev-studio
```

To try the plugin in a single Claude Code session without installing it: `claude --plugin-dir <path-to-this-clone>` (verified).

### Install from GitHub

These commands install the default branch and need GitHub access to the private repository.

```
claude plugin marketplace add ZMSkif/GameDev-AGI-Studio
claude plugin install gamedev-studio@gamedev-studio

codex plugin marketplace add ZMSkif/GameDev-AGI-Studio
codex plugin add gamedev-studio@gamedev-studio
```

## Agent Team

The base team is the `minimum_roles` list in [`contracts/v1/agent-team-policy.json`](contracts/v1/agent-team-policy.json) ([DEC-031](../../issues/31), [DEC-142](../../issues/144)). It can be extended with specialists but never reduced. Each role is defined once, in `agents/<role>.md`: mission, responsibilities, what it does not do, required inputs, outputs with evidence, escalation, and which role reviews its work.

| Role | Claude Code subagent |
| --- | --- |
| Studio Director | `gamedev-studio:studio-director` |
| Producer | `gamedev-studio:producer` |
| Game Designer | `gamedev-studio:game-designer` |
| Art Director | `gamedev-studio:art-director` |
| Technical Director | `gamedev-studio:technical-director` |
| Gameplay Engineer | `gamedev-studio:gameplay-engineer` |
| Asset Pipeline Artist | `gamedev-studio:asset-pipeline-artist` |
| QA Engineer | `gamedev-studio:qa-engineer` |
| Publishing & Analytics Agent | `gamedev-studio:publishing-analytics-agent` |

On-demand specialists (DEC-032, DEC-142):

| Specialist | Claude Code subagent |
| --- | --- |
| Release QA Engineer | `gamedev-studio:release-qa-engineer` |
| Pre-publish Reviewer | `gamedev-studio:pre-publish-reviewer` |
| Art Reviewer | `gamedev-studio:art-reviewer` |
| i18n Language Reviewer | `gamedev-studio:i18n-language-reviewer` |
| Crowd and NPC Soak Reviewer | `gamedev-studio:crowd-soak-reviewer` |

Reviewer and duty assignments are a proposal under DEC-040 and DEC-072, not an owner decision; the owner may change them.

In Claude Code, delegate to a role by name, or with `@agent-gamedev-studio:qa-engineer`.

Codex: in Codex 0.169.0, custom agents placed inside a plugin were not discovered (tested at `agents/`, `.codex/agents/` and `.codex-plugin/agents/`; the same files in `~/.codex/agents/` and in a trusted project's `.codex/agents/` were). The roles therefore reach Codex through the skill `studio-team`, which points the agent at the same `agents/<role>.md` files so it plays the roles one after another. Playing two roles in one session is not independent review; ask for a separate reviewer session.

### Validate

```
claude plugin validate . --strict
claude plugin validate skills --strict
claude plugin validate agents --strict
claude plugin validate commands --strict
python scripts/validate_contracts.py
python scripts/validate_plugin.py
python -m unittest discover -s tests -v
```

`claude plugin validate .` checks the manifests only; the `skills`, `agents` and `commands` forms check the components in those directories. CI runs the last three Python commands; `claude plugin validate` is run locally because the Claude Code CLI is not set up in the CI runner.
