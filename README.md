# GameDev AGI Studio

**Authoritative decisions:** [GitHub Issues · decision](../../issues?q=is%3Aissue+label%3Adecision).

**Machine-readable implementation contracts:** [`contracts/v1/`](contracts/v1/).

**AI agent instructions:** [`AGENTS.md`](AGENTS.md).

Development Issues and Projects are created by Claude/Codex from the approved decisions. No unverified vendor integration or completed implementation is implied.

## Plugin

This repository is a plugin for Claude Code and Codex named `gamedev-studio` (display name "GameDev Studio"); the repository root is both the marketplace and the plugin ([DEC-143](../../issues/146)). It ships the skill `studio-rules`, which tells an agent to fetch the binding decisions from GitHub Issues before working on a game or on this plugin, the nine base team roles as Claude Code subagents in `agents/` (see [Agent Team](#agent-team)), and the skill `studio-team`, which indexes the roles.

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

Reviewer and duty assignments are a proposal under DEC-040 and DEC-072, not an owner decision; the owner may change them.

In Claude Code, delegate to a role by name, or with `@agent-gamedev-studio:qa-engineer`.

Codex: in Codex 0.169.0, custom agents placed inside a plugin were not discovered (tested at `agents/`, `.codex/agents/` and `.codex-plugin/agents/`; the same files in `~/.codex/agents/` and in a trusted project's `.codex/agents/` were). The roles therefore reach Codex through the skill `studio-team`, which points the agent at the same `agents/<role>.md` files so it plays the roles one after another. Playing two roles in one session is not independent review; ask for a separate reviewer session.

### Validate

```
claude plugin validate . --strict
claude plugin validate skills --strict
claude plugin validate agents --strict
python scripts/validate_contracts.py
python scripts/validate_plugin.py
python -m unittest discover -s tests -v
```

`claude plugin validate .` checks the manifests only; the `skills` and `agents` forms check the components in those directories. CI runs the last three Python commands; `claude plugin validate` is run locally because the Claude Code CLI is not set up in the CI runner.
