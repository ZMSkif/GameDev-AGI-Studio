---
name: memory
description: Long-term studio and project memory through Hindsight over MCP (DEC-024) - which bank and tags to use for the studio, project and task scopes, what to store and never store, provenance on every memory, the four retrieval modes, why approved decisions and documents always win over memory, and how to start, connect and verify the server. Use before storing or recalling a lesson, a recurring failure or a decision's provenance, when wiring Hindsight into a game repository, or when a memory contradicts a source.
---

# Memory (Hindsight)

Binding:
- DEC-024 (#24): memory is retrievable, never authoritative.
- DEC-101 (#102): studio, project and task levels.
- DEC-102 (#103): only relevant sources, with revision and provenance.
- DEC-103 (#104): the approved source of truth wins over memory.
- DEC-104 (#106): Auto, Always Verify, Memory First and Manual.
- DEC-138 (#140): memory stays until the owner deletes it.
- DEC-019 (#19), DEC-085 (#86): no paid API.
- DEC-090 (#91): no secrets in prompts or stores.

The contract is `contracts/v1/knowledge-policy.json`.

**Where it runs (owner, 24.11.2026):** every person who installs the plugin has **their own** Hindsight server on their own computer, bound to 127.0.0.1, holding only their memory; it starts at sign-in, and the plugin connects it to Claude in every session. There is no shared server: Hindsight has no authentication, so a shared one would expose everyone's memory. Memory is installed like any catalog tool, after the person's yes (`studio-setup`); installing the plugin alone does not install it.

## 1. Banks and scopes

| Scope | Where | Example |
|---|---|---|
| studio | bank `gamedev-studio::studio` | "Every piece gets its own reviewer; mutants catch tests that cannot fail." |
| project | bank `gamedev-studio::project::<repository>` | "In this game the round-3 lesson runs inside the first show." |
| task | the project bank, tag `task:<issue number>` | "Issue 42: the collar spike came from an unbisected border." |

- **The bank is the scope.** Do not add `scope:` tags. Tag a task memory `task:<issue number>`.
- **One MCP endpoint per bank.** The multi-bank endpoint `/mcp/` accepts any `bank_id`, so a session there can read other games. The smoke test showed it. Only per-bank endpoints are used.

## 2. How Claude is connected (nothing to wire by hand)

The plugin starts its own `memory` MCP server with every Claude Code session (`.claude-plugin/plugin.json` → `scripts/memory_mcp.py`). It is always connected, also when Hindsight is not installed or not running yet, and it forwards to the local server's per-bank endpoints:

- `studio_retain`, `studio_recall`, `studio_list_memories`, `studio_get_memory`, `studio_get_bank`: the studio bank, in every session;
- `project_*` (the same five): the bank of the studio game this session runs in (the nearest folder with `.gamedev-studio`; the bank name comes from the repository name). Outside a studio game they answer that there is no project bank. A `bank_id` argument is dropped, so no call reaches another game's bank.

If the server is not running, the first call starts it and answers "starting": go on with the task and call again in about a minute. If Hindsight is not installed, the call says so: offer it through `studio-setup` and work in **Manual** mode until then. Say so in the result; do not work around it.

- **Codex** (optional): add the same server to the trusted project's `.codex/config.toml`: `[mcp_servers.gamedev-studio-memory]` with `command = "python"` and `args = ["<plugin-root>/scripts/memory_mcp.py"]`.
- **Do not use** the `@vectorize-io/hindsight-coding-agents` installer. Its default stores whole session transcripts, which breaks the never-store list below. Do not add Hindsight's HTTP endpoints to a game's `.mcp.json` either: the plugin's server already covers both banks.

## 3. Store (retain)

Store only what helps later work and is backed by a source:
- a verified lesson, with the review files and commits that show it;
- a pointer to a decision's provenance: the issue number and the line that matters, never a copy that could drift;
- a recurring failure class (`lessons` skill);
- a piece's outcome, with its review verdict file.

Every retain carries `metadata` with:
- `source_type`;
- `source`: a file, issue or commit;
- `source_rev`: a commit or date;
- `recorded_by`: the role;
- `verified`: `"false"` unless a reviewer confirmed it.

A memory without provenance is not stored.

**Never pass `document_id` or `update_mode`.** In Hindsight 1.2.2, a retain whose `document_id` already exists replaces that document: its earlier memories are deleted (the default `update_mode` is `replace`). That would delete memory, which only the owner may do (DEC-138). Leave both out, and Hindsight makes a new document for each item. The plugin's scripts (`mine_lessons.py`, `hindsight_smoke.py`) never send them either.

**Never store:**
- secrets, tokens, keys or passwords;
- personal data, such as names, e-mail addresses or local user paths;
- unverified claims written as facts;
- whole transcripts;
- copyrighted text.

Before a retain, check the whole payload (content, metadata and tags) as `scripts/archive_reviews.py` checks a verdict: secret patterns and the project's `--forbid` patterns.

Retain over MCP is asynchronous, so a recall right after it can come back empty. Recall again after about 20 s.

## 4. Recall and the four modes

| Mode | When | What to do |
|---|---|---|
| **Auto** (default) | normal work | Recall, then check every memory you act on against its source before relying on it. |
| **Always Verify** | decisions, money, publishing, anything risky | Recall only as a pointer and act only on the source. Read the source itself (issue, file, commit). For an uncertain provider or tool claim, also check the official docs or run a small experiment. |
| **Memory First** | low-risk recall of studio practice | Use the memory directly, still showing its provenance, and say it is from memory. |
| **Manual** | the owner asked for it, or no memory server is wired | Do not recall; ask the owner. |

- Recall facts with `types: ["world", "experience"]`. Derived observations come back without provenance, so they are hints, never evidence.
- Recall from both the project bank and the studio bank. For one task's memories, pass `tags: ["task:<n>"]` with `tags_match: "any_strict"`. The default `any` also returns untagged memories.
- `reflect` is not used: its answers carry no sources, and the server's MCP allowlist leaves it out.
- **The approved source of truth always wins** (DEC-103). The order is: the decision issues, then the approved GDD, Art Bible and architecture, then memory. When a memory contradicts a source, follow the source. Report the stale memory to the owner; never delete or "fix" it yourself.

## 5. Running the server (local)

`scripts/memory_server.py` runs it; nothing else should start Hindsight:

| Command | What it does |
|---|---|
| `status [--json]` | installed, running, autostart, the studio bank's endpoint |
| `start [--wait 600]` | starts it in the background unless it already answers; never a second copy, never over another program on port 8888 |
| `stop` | stops only the process it started and recorded; the data stays |
| `autostart --yes` / `--off` | start at sign-in: the Windows per-user startup entry `GameDevStudioMemory` (no administrator rights; Task Manager > Startup apps) or a macOS LaunchAgent, running a copy of the script kept in `~/.gamedev-studio/memory` so plugin updates do not break it |

Install (`studio_tools.py install hindsight --yes`) puts Hindsight in `~/.gamedev-studio/tools/hindsight`; an older `~/.hindsight-runtime` is still used. Data lives in the default embedded PostgreSQL instance (`~/.pg0`): never point a server at another instance, or memory looks empty. Before an upgrade, stop the server and copy `~/.pg0` aside.

The server is always started with:
- `HINDSIGHT_API_HOST=127.0.0.1`: the default is 0.0.0.0 with an unauthenticated MCP endpoint.
- `HINDSIGHT_API_MCP_ENABLED_TOOLS=retain,recall,list_memories,get_memory,get_bank`.
- `HINDSIGHT_API_LLM_PROVIDER=claude-code`: the person's own Claude subscription (no API key; each retain uses a little of its limit). The `openai-codex` provider and a local Ollama model are the other no-paid-API options; neither was tested.
- The first start downloads the search models from Hugging Face. It can take longer than the default 300 s init timeout.
- After any change, run `python scripts/hindsight_smoke.py --run <new id>`. With `--json` it prints rows for `contracts/v1/integration-evidence.schema.json`.
- To check persistence, restart the server, then run `--recall-only --run <the same id> --after-restart`. Without `--after-restart`, S8 is MANUAL.

## 6. Deleting

Only the owner deletes memory, by their own means (DEC-138). The 1.2.2 admin CLI has no delete command. The REST API's DELETE routes are open on the server without auth, and only this rule keeps agents off them.

Agents never call delete or clear tools, even on smoke banks, and never send DELETE to the REST API. If memory must go, ask the owner and name the bank and the memories.

## Source

- Hindsight docs at hindsight.vectorize.io (installation, models, MCP server, configuration, memories API; read 19.11.2026), and the 1.2.2 source for `document_id`, `update_mode` and `tags_match`.
- Smoke test on the owner's PC, 19.11.2026, `scripts/hindsight_smoke.py`:
  - Claude Code and Codex both read and write one bank over MCP;
  - the multi-bank endpoint crosses banks;
  - observations and reflect carry no sources;
  - REST DELETE is open on localhost.
