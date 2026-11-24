---
name: studio-setup
description: Set up GameDev Studio's optional tools for a game — QA browser, FFmpeg, Blender, Godot, img2threejs, skill packs, AI 3D apps, paid services and memory — by asking the person about each with clear options, installing only what they choose, and opening the studio panel. Use on first setup, when a skill needs a missing tool, or when the person asks what can be installed.
---

# Studio setup

Apply the `studio-rules` skill first. The single source of truth is [`tools/catalog.json`](../../tools/catalog.json): never offer, describe or install a tool that is not in it, and never change a command it lists. DEC-009 and DEC-130 forbid spending and paid actions without the owner's yes; DEC-094 requires a recorded licence for every asset.

## 1. See what is there

**Which folder is the game.** The game is the folder the person started Claude in (or its nearest parent with the `.gamedev-studio` marker). A folder without the marker is still the person's game: run the studio scripts there with `--game <that folder>`. Never switch to a temporary or empty folder instead, and never decide on your own that the game must not be touched: reading status and opening the panel change nothing in it. Ask once whether to add the marker (an empty `.gamedev-studio` file at the game's root) so the studio's hooks work there; add it only on yes. Only actions the person chooses (an install into the game, a key, a setting) write into the game folder.

From the game folder:

```text
python <plugin-root>/scripts/studio_tools.py status --json --lang ru
```

The result lists every tool with `installed`, `detail`, `cost` (`free`, `paid`, `account`), `commercial`, `licence_note`, `requirements`, `who` (`claude_yes`, `person`, `owner`), `install_steps` and `manual`, and its `prerequisites`: one row per thing it needs, with `for` (`install` or `use`), `met` (`true`, `false`, or `null` when only the person can check it), `detail`, `why`, `who` (`claude_yes` with the exact `install_steps` and `command`, or `person` with `manual`). `ready_to_install` and `ready_to_use` sum them up (nothing known to be missing); `confirm_with_person` lists the rows only the person can confirm. An installed tool is reported as installed only when the files a finished install leaves are there (`detect.verify`), so a half-finished install shows as not installed.

On Windows `python3` may be the Microsoft Store alias that runs nothing: use `python`, or `py -3`.

## 2. Ask, group by group

Ask with the question tool, one group per question (QA, art and video, skill packs, AI 3D, engines, paid services, agents, player analytics, memory), only about tools that are not installed. For each option, give in one line: what it gives, the price, whether an account is needed, any licence warning, and **every prerequisite row that is not met**, for install and for use, with who installs it (for example "needs Microsoft C++ Build Tools, ~6–8 GB, Claude installs it; to use it: your SMPL-X registration"). Never let the person find out about a missing prerequisite from a failed install. Offer these answers:

- **Install** — for `claude_yes` tools: you will show the exact command and run it.
- **I'll install it myself** — for `person` tools: give the `manual` text and the source link.
- **Not now** — skip it.
- **More detail** — explain, then ask again.

Rules for the answers:

- A tool marked `commercial: non_commercial` gets the warning in the question itself ("for prototypes and reference; its files cannot ship in a game you sell"). It can be installed like any other `claude_yes` tool; read its `licence_gate` lines to the person, and after install remind them that every output is recorded with `studio_tools.py mark-reference` and blocked by the release report. `commercial_effective: licensed` or `owner_accepted` means the owner recorded a licence or chose to use the outputs at their own risk: then do not mark outputs or repeat the warning. The person switches this on in the panel or asks you to run `studio_tools.py accept-risk <tool>`; never switch it on without being asked.
- Paid services (`cost: paid`): installing their free client is fine after a yes; every generation still needs the owner's yes on the Issue.
- Owner tools (`who: owner`): only the owner turns them on, with the GitHub link of the decision. Do not ask anyone else to decide.
- **Memory (Hindsight) is recommended for everyone** and asked first on a first setup: each person gets their own local memory (see "Memory" below).
- Tools with `pending_decision` are shown as waiting for their decision and never installed.

## 3. Install what was chosen

For each yes, show the `install_steps` exactly as listed, and the `install_steps` of every unmet `claude_yes` install prerequisite, then run:

```text
python <plugin-root>/scripts/studio_tools.py install <id> --yes
```

Add `--with-prerequisites` only when the person said yes with those prerequisite commands in front of them; Claude's own prerequisites are then installed first. A prerequisite can also be installed on its own: `studio_tools.py prereq <prerequisite-id> --yes`. Prerequisites the person installs (`who: person`) are never run by Claude: give their `manual` text, and the install stops with the list of what is missing until they are done. Every install prerequisite is checked before the first command runs, so nothing is half-installed for a known reason.

On Windows, mention that Windows may ask for permission (Build Tools and other winget installers need administrator rights). Report the result from the command's output and re-run `status` to confirm. If a step fails, show the error and stop that tool; do not try another installer. A retry after a failed step is safe: a folder that is already a clone is not cloned again. If the error names something the catalog does not list (a compiler, a library, a system), say so and propose adding it as a prerequisite in `tools/catalog.json` in a plugin pull request.

## Before using a tool

Any skill that uses a catalog tool first runs, from the game folder:

```text
python <plugin-root>/scripts/studio_tools.py check <id> --json
```

Exit code 0: installed and no `use` prerequisite is missing. Exit code 3: not ready; tell the person which rows are missing (`met: false`), who does each, and offer the install through this skill. `confirm_with_person` lists the rows only the person can confirm (`met: null`: an account, a key, a registration, an app the studio cannot see): ask about them once before the first use in a session, and never assume them.

## Memory

Memory is the person's own Hindsight server on this computer (the `memory` skill). After the person said yes to installing `hindsight`:

1. Install it as any tool: `python <plugin-root>/scripts/studio_tools.py install hindsight --yes` (about 2 GB; Windows may ask nothing, it needs no administrator rights).
2. Ask, as its own question, whether memory should start at sign-in, so it is ready whenever Claude starts (recommended). On yes: `python <plugin-root>/scripts/memory_server.py autostart --yes` (Windows Task Scheduler task "GameDev Studio memory", or a macOS LaunchAgent; `--off` removes it).
3. Start it now: `python <plugin-root>/scripts/memory_server.py start --wait 600`. The first start downloads the search models and can take several minutes.
4. Nothing else to wire: the plugin's `memory` MCP server is connected in every session and reaches the studio bank and the bank of the game the session runs in. New sessions see it; the current one already has it.
5. Check: `python <plugin-root>/scripts/memory_server.py status`.

## 4. Keys and settings

Never ask for a key in the chat and never print one. The person enters keys in the panel (Tools → the tool's card) or in their own terminal:

```text
python <plugin-root>/scripts/studio_tools.py set-secret fal FAL_KEY
```

The key goes to the game's `.env`, and `.env` is added to `.gitignore`. Non-secret settings (`chromium_path`) use `studio_tools.py set <id> <key> <value>`.

## 5. Offer the panel

For anything visual — toggling tools, saving keys, running browser QA with chosen profiles and opening reports — start the panel and give the person its address:

```text
python <plugin-root>/scripts/studio_panel.py --lang ru
```

It listens on this computer only and prints a one-time link. It stops with its button or Ctrl+C.

What is reviewed and why some tools are left out: [external tools](../../reference/external-tools.md).
