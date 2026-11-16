# GameDev AGI Studio

**Authoritative decisions:** [GitHub Issues · decision](../../issues?q=is%3Aissue+label%3Adecision).

**Machine-readable implementation contracts:** [`contracts/v1/`](contracts/v1/).

**AI agent instructions:** [`AGENTS.md`](AGENTS.md).

Development Issues and Projects are created by Claude/Codex from the approved decisions. No unverified vendor integration or completed implementation is implied.

## Plugin

This repository is a plugin for Claude Code and Codex named `gamedev-studio` (display name "GameDev Studio"); the repository root is both the marketplace and the plugin ([DEC-143](../../issues/146)). It currently ships one skill, `studio-rules`, which tells an agent to fetch the binding decisions from GitHub Issues before working on a game or on this plugin.

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

Unverified: these forms have not been run. They use the `owner/repo` source documented by both CLIs and require GitHub access to the private repository.

```
claude plugin marketplace add ZMSkif/GameDev-AGI-Studio
claude plugin install gamedev-studio@gamedev-studio

codex plugin marketplace add ZMSkif/GameDev-AGI-Studio
codex plugin add gamedev-studio@gamedev-studio
```

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
