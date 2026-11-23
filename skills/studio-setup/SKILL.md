---
name: studio-setup
description: Set up GameDev Studio's optional tools for a game — QA browser, FFmpeg, Blender, Godot, img2threejs, skill packs, AI 3D apps, paid services and memory — by asking the person about each with clear options, installing only what they choose, and opening the studio panel. Use on first setup, when a skill needs a missing tool, or when the person asks what can be installed.
---

# Studio setup

Apply the `studio-rules` skill first. The single source of truth is [`tools/catalog.json`](../../tools/catalog.json): never offer, describe or install a tool that is not in it, and never change a command it lists. DEC-009 and DEC-130 forbid spending and paid actions without the owner's yes; DEC-094 requires a recorded licence for every asset.

## 1. See what is there

From the game folder (the one with the `.gamedev-studio` marker):

```text
python <plugin-root>/scripts/studio_tools.py status --json --lang ru
```

The result lists every tool with `installed`, `detail`, `cost` (`free`, `paid`, `account`), `commercial`, `licence_note`, `requirements`, `who` (`claude_yes`, `person`, `owner`), `install_steps` and `manual`.

## 2. Ask, group by group

Ask with the question tool, one group per question (QA, art and video, skill packs, AI 3D, engines, paid services, agents, player analytics, memory), only about tools that are not installed. For each option, give in one line: what it gives, the price, whether an account is needed, and any licence warning. Offer these answers:

- **Install** — for `claude_yes` tools: you will show the exact command and run it.
- **I'll install it myself** — for `person` tools: give the `manual` text and the source link.
- **Not now** — skip it.
- **More detail** — explain, then ask again.

Rules for the answers:

- A tool marked `commercial: non_commercial` gets the warning in the question itself ("for prototypes and reference; its files cannot ship in a game you sell"). It can be installed like any other `claude_yes` tool; read its `licence_gate` lines to the person, and after install remind them that every output is recorded with `studio_tools.py mark-reference` and blocked by the release report. `commercial_effective: licensed` or `owner_accepted` means the owner recorded a licence or chose to use the outputs at their own risk: then do not mark outputs or repeat the warning. The person switches this on in the panel or asks you to run `studio_tools.py accept-risk <tool>`; never switch it on without being asked.
- Paid services (`cost: paid`): installing their free client is fine after a yes; every generation still needs the owner's yes on the Issue.
- Owner tools (`who: owner`, for example memory): only the owner turns them on, with the GitHub link of the decision. Do not ask anyone else to decide.
- Tools with `pending_decision` are shown as waiting for their decision and never installed.

## 3. Install what was chosen

For each yes, show the `install_steps` exactly as listed, then run:

```text
python <plugin-root>/scripts/studio_tools.py install <id> --yes
```

On Windows, mention that Windows may ask for permission. Report the result from the command's output and re-run `status` to confirm. If a step fails, show the error and stop that tool; do not try another installer.

## 4. Keys and settings

Never ask for a key in the chat and never print one. The person enters keys in the panel (Tools → the tool's card) or in their own terminal:

```text
python <plugin-root>/scripts/studio_tools.py set-secret fal FAL_KEY
```

The key goes to the game's `.env`, and `.env` is added to `.gitignore`. Non-secret settings (`chromium_path`, `hindsight_url`) use `studio_tools.py set <id> <key> <value>`.

## 5. Offer the panel

For anything visual — toggling tools, saving keys, running browser QA with chosen profiles and opening reports — start the panel and give the person its address:

```text
python <plugin-root>/scripts/studio_panel.py --lang ru
```

It listens on this computer only and prints a one-time link. It stops with its button or Ctrl+C.

What is reviewed and why some tools are left out: [external tools](../../reference/external-tools.md).
