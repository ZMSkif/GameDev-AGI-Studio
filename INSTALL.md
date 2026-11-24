# Installing gamedev-studio from zero (Windows)

This guide is for a person on a clean Windows 10 or 11 PC, and for a Claude told "install by this guide". Each step is marked:

- **[Claude]**: Claude Code does it itself.
- **[you]**: the person does it: sign-ins, Windows prompts, restarts.
- **[Claude → you]**: Claude runs it, but asks for your yes first; Windows may also show an approval prompt.

Russian version: [INSTALL.ru.md](INSTALL.ru.md).

**In short:** get the zip from the owner → install Claude Code → unpack the zip → Claude installs Git and Python if they are missing → Claude installs the plugin → check. No GitHub access is needed.

## For the owner: before handing over

1. **Download the zip.** On the [Releases](https://github.com/ZMSkif/GameDev-AGI-Studio/releases) page, open version 0.4.1 or newer and take `gamedev-studio-0.4.1.zip` under Assets. Or use one command:
   ```powershell
   gh release download v0.4.1 -R ZMSkif/GameDev-AGI-Studio -p "gamedev-studio-*.zip"
   ```
   Take this file, not "Source code (zip)": it holds a single `gamedev-studio` folder, as this guide expects. The 0.4.0 and older zips have neither this guide nor the check script.
2. **Send the person** the zip and the `INSTALL.md` file. The guide is also inside the zip. A GitHub link to it opens only for people with access to the repository.
3. **No GitHub access is needed.** If you want the person to download new versions themselves, invite them: the repository → Settings → Collaborators → Add people. Mind GitHub's rule: in a private repository of a personal account, an invited person always gets write access. They can then change the code and the decisions and publish releases, so invite only people you trust.

## How this was checked

Nothing was installed on the owner's PC. A real install ran on 2026-11-20 on a clean GitHub Actions virtual machine: Windows Server 2025, the `windows-latest` image, workflow "Clean install on Windows". This is what passed there:

- the zip was built the same way as the release zip and unpacked with Windows PowerShell 5.1 into `C:\Tools`; it holds this guide, the check script and the studio rules;
- Claude Code 2.1.329 was installed with the official installer. The installer itself warned that `.local\bin` is not on PATH, which is why step 1 has the PATH item;
- `claude plugin validate` passed;
- `claude plugin marketplace add` and `claude plugin install` passed. `claude plugin list` showed plugin 0.4.1, enabled and read from `C:\Tools\gamedev-studio`. The plugin holds 17 skills, 7 commands, 14 agent roles and 2 hooks;
- `python scripts/doctor.py`: every required item ✅, the plugin "installed from this folder and enabled";
- with a stripped PATH the script showed ❌ and the fixes for Claude Code, Git and Python;
- updating by replacing the folder, as "Updating" says: with no reinstall, `claude plugin list` showed the version from the new folder right away;
- the game folder of step 8: through Git Bash the hooks answered at start, blocked a commit straight to `main`, and stayed silent in a folder without the `.gamedev-studio` file;
- Hindsight memory, following the "Hindsight memory" section, installed and answered its health check.

What that run cannot cover:

- the GitHub machine already has Git and Python, so steps 3 and 4 (winget) did not run;
- signing in to Claude and using the plugin in a real session, hooks and step 8 included: nobody signs in to Claude on the GitHub machine;
- home editions of Windows 10 and 11: the GitHub machine runs Windows Server 2025;
- Codex.

## Step 0. What you need

- **Windows:** 10 version 1809 or newer, or Windows 11. x64 or ARM64, 4 GB of memory or more, and an internet connection.
- **A paid Claude subscription**, for example Pro or Max. A Console account (API billing) does not fit: the studio works on a subscription and does not switch to the paid API.
- **The `gamedev-studio-<version>.zip` file** from the owner, version 0.4.1 or newer.

## Step 1. [you] Install Claude Code and sign in

1. Open **PowerShell** (a normal one; no administrator rights needed) and run:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
2. Close the window, open a new one and check: `claude --version`.
   - If the command is not found, or the installer said `...\.local\bin is not in your PATH`, the install folder is not on PATH. The installer puts the program in `%USERPROFILE%\.local\bin` but may not add it to PATH. Add that folder to your user PATH: Settings → System → About → Advanced system settings → Environment Variables → `Path` in the upper list → Edit → New → `%USERPROFILE%\.local\bin` → OK. Then open a new PowerShell window.
3. Run `claude`. When it asks how to sign in, choose the Claude account with a subscription, not Console. Sign in in the browser. If the browser does not open, press `c` to copy the link, open it yourself and paste the code back into the terminal. Then leave with `/exit`.

Alternative: `winget install Anthropic.ClaudeCode`. That install does not update itself, and `claude update` does nothing for it. Update it with `winget upgrade Anthropic.ClaudeCode`.

## Step 2. [you] Unpack the zip and start Claude in the plugin folder

```powershell
New-Item -ItemType Directory -Force C:\Tools | Out-Null
Expand-Archive -Path "$HOME\Downloads\gamedev-studio-0.4.1.zip" -DestinationPath C:\Tools
cd C:\Tools\gamedev-studio
claude
```

- If the zip has another name or is in another folder, fix the path in `Expand-Archive`.
- The zip holds one folder, `gamedev-studio`: this is the **plugin folder**. To check, it contains `.claude-plugin\marketplace.json`.
- The plugin loads straight from this folder, so do not delete or move it after installing. This folder is only for installing and updating: do not make games in it, because an update replaces it whole (step 8 says where games go).
- Claude Code asks whether you trust this folder. Answer yes.

Now tell Claude: "Install the plugin by INSTALL.md, steps 3–7".

> **For Claude:** the `AGENTS.md` file in this folder holds the rules for people who develop the studio itself in its repository (GitHub Issues, Projects, pull requests). They do not apply to an install by this guide: do not run `gh`, and create nothing on GitHub.

## Step 3. [Claude] See what is already installed

In PowerShell, installing nothing:

```powershell
$env:PYTHON_MANAGER_AUTOMATIC_INSTALL = "false"
Get-Command git, python, py -ErrorAction SilentlyContinue | Format-Table Name, Source
git --version
python --version
py -3 --version
```

The first line stops the Python install manager from installing Python by itself during the check. Step 4 installs only what is missing:

- **Git**, if `git` is not found.
- **Python**, if neither `python` nor `py -3` showed version 3.10 or newer. A `python` under `...\WindowsApps\` that talks about the Microsoft Store is a stub, not Python.

## Step 4. [Claude → you] Install what is missing

Claude shows the commands and asks for your yes. Your yes also accepts the winget source and package terms; that is why the commands carry `--accept-source-agreements` and `--accept-package-agreements`. An install may show the Windows prompt "Do you want to allow this app to make changes?", which you approve.

```powershell
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements
```

- **If there is no `winget` command**, install "App Installer" from the Microsoft Store. You do this.
- **The `Git.Git` package** is maintained by the winget community, not by the Git for Windows project. The official installer is at <https://git-scm.com/install/windows>.
- **[you] Restart Claude Code after installing**, or it will not see the new programs. Close the window, open a new PowerShell window and run:
  ```powershell
  cd C:\Tools\gamedev-studio
  claude --continue
  ```
  `claude --continue` continues the latest conversation **in the current folder**, so the `cd` comes first.

## Step 5. [Claude] Check the computer

In the plugin folder:

```powershell
python scripts/doctor.py
```

If `python` is not found but `py` is: `py -3 scripts/doctor.py`.

The script prints ✅ or ❌ for each item; for each ❌ it says how to fix it and who does it. Until step 6 the "plugin" item is ❌, which is expected. Use `--lang en` for English and `--json` for Claude.

The script installs and changes nothing:

- it starts only version checks: `claude --version`, `git --version`, `bash --version` and one line of Python that prints its version;
- it switches off automatic Python installs while doing so;
- it reads Claude Code's plugin list files;
- it never starts Codex; it only looks Codex up on PATH;
- the script itself writes no file.

## Step 6. [Claude] Install the plugin

```powershell
claude plugin marketplace add "C:\Tools\gamedev-studio"
claude plugin install gamedev-studio@gamedev-studio
```

**[you]** Restart Claude Code as in step 4: a new window, `cd C:\Tools\gamedev-studio`, `claude --continue`.

**Codex (optional)**, if you already have it installed:

```powershell
codex plugin marketplace add "C:\Tools\gamedev-studio"
codex plugin add gamedev-studio@gamedev-studio
```

## Step 7. Final check

1. **[Claude]** `python scripts/doctor.py`: every required item is ✅, and the plugin says "installed from this folder and enabled".
2. **[you]** Open a new Claude Code session and ask "which skills does the gamedev-studio plugin have?". The answer should list `studio-rules`, `engine-profiles`, `memory` and others.

The plugin is installed.

## Step 8. [you] Your game, in its own folder

Make each game in a separate folder **outside** the plugin folder, for example `C:\Games\<name>`:

```powershell
New-Item -ItemType Directory -Force C:\Games\my-game | Out-Null
cd C:\Games\my-game
git init -b main
New-Item -ItemType File .gamedev-studio | Out-Null
claude
```

- The `.gamedev-studio` file marks the folder as a studio game. The plugin's checks (hooks) work only in such a folder:
  - a rules reminder at start;
  - no commits straight to `main`, except the very first commit into an empty repository;
  - no committed passwords or keys.
- In Claude, start the game with `/gamedev-studio:new-web-game "Title"`. Claude runs an interview with answer options and creates or downloads nothing without your yes.
- **The game's tasks** go in the GitHub Issues of the game's own repository (DEC-002), not in files. That needs your own free GitHub account and the GitHub CLI: `winget install --id GitHub.cli -e --source winget --accept-source-agreements --accept-package-agreements`, then `gh auth login` in a separate PowerShell window. It is your own account; it neither gives nor needs access to the studio's repository. Without it, Claude says there is nowhere to keep tasks and asks you.

## Without access to the studio's repository (the usual case)

Everything needed for games works:

- the skills, agent roles and `/gamedev-studio:…` commands;
- the hook checks in a game folder that has the `.gamedev-studio` file (step 8);
- the studio rules: they are in the plugin's skills and in the `contracts/v1/` and `reference/` folders inside the plugin folder.

What is missing is the owner's full list of decisions. It is kept in the GitHub Issues of the studio's private repository. Claude says once that the list is not available and then works by the plugin's rules. If it needs a decision the plugin does not cover, Claude asks you instead of making one up; then ask the owner.

If the GitHub CLI is missing or not signed in, Claude Code warns `GameDev Studio tool preflight FAILED` when it starts in a game folder. Only tasks that need GitHub stop, such as the game's tasks (step 8); other work goes on. There is no need to ask for access to the studio's repository.

## Updating

1. **[you]** Get the new zip from the owner.
2. **[you]** Close every Claude Code window: Windows will not rename a folder that a program has open.
3. **[you]** In PowerShell:
   ```powershell
   Rename-Item C:\Tools\gamedev-studio gamedev-studio-old
   Expand-Archive -Path "$HOME\Downloads\gamedev-studio-0.4.2.zip" -DestinationPath C:\Tools
   ```
   If `gamedev-studio-old` is left over from an earlier update, delete it first.
4. **[you]** Start Claude Code in the plugin folder: `cd C:\Tools\gamedev-studio`, then `claude`. There is no need to reinstall the plugin: it loads from this folder, and the Claude Code docs say changes there take effect at the next start.
5. **[Claude]** `python scripts/doctor.py` shows the new version. Once everything works, delete `C:\Tools\gamedev-studio-old` yourself.

Checked on a clean GitHub machine: after the folder was replaced, `claude plugin list` showed the new folder's version with no reinstall, and `python scripts/doctor.py` said "installed from this folder and enabled". No real session ran there after the update, and updating Codex was not checked. An update does not touch the games in `C:\Games`.

## Hindsight memory (recommended)

Everyone who installs the plugin has **their own** memory: the Hindsight server runs only on this computer (127.0.0.1) and keeps only your memory. There is no shared server: Hindsight has no password, so a shared one would expose everyone's memory. The plugin also works without memory, but with it agents keep the studio's and your game's lessons between sessions.

1. **[Claude → you]** In the game folder: `/gamedev-studio:setup-tools` and choose "Memory". After your yes Claude installs Hindsight 1.2.3, about 2.9 GB with its models, into `~\.gamedev-studio	ools\hindsight`. It needs Python 3.11 or newer (step 4) and no administrator rights.
2. **[Claude → you]** Claude asks whether memory should **start automatically at Windows sign-in** (recommended). On yes it adds the startup entry "GameDevStudioMemory" for your user (no administrator rights; you see it in Task Manager > Startup apps); to remove it: `python scripts/memory_server.py autostart --off`.
3. **[Claude]** First start: `python scripts/memory_server.py start --wait 600`. The first start downloads the search models from Hugging Face (`BAAI/bge-small-en-v1.5`, `hindsight-ai/hs-rerank-1`), which can take several minutes.
4. **Nothing else to connect.** The plugin connects memory to Claude in every session (the `memory` MCP server): the studio bank everywhere and the bank of the game Claude runs in. If the server is not running yet, the first memory call starts it.
5. **[Claude]** Check: `python scripts/memory_server.py status` and `python scripts/doctor.py --hindsight`.

Facts are extracted by your Claude subscription (the `claude-code` provider, for Pro and Max): no paid API, but each memory uses a little of the subscription's limit, and Claude Code must be installed and signed in. While the server runs it uses about 1.6 GB of RAM and no GPU; it takes about 2.9 GB of disk in all (measured 24.11.2026).

> **Checked on a clean GitHub Actions machine** (Windows Server 2025, Python 3.12 and 3.13): the install took about 5 minutes and 2.2 GB; the server set up its database, downloaded the models and answered `healthy` after 35–52 seconds. Fact extraction was not checked there, because nobody is signed in to Claude on that machine.

Only the memory's owner deletes memory, by their own means. Warning: the Hindsight server's REST DELETE routes are open without authorization, and only the rule in the `memory` skill keeps agents off them.

## Troubleshooting

- **`claude` not found:** open a new window. If that does not help, add the folder to PATH as step 1 says.
- **`python` talks about the Microsoft Store:** go to Settings → Apps → Advanced app settings → App execution aliases and turn off "python.exe" and "python3.exe". If you installed the Python install manager, leave its aliases alone.
- **Claude Code cannot find Git Bash:** set `CLAUDE_CODE_GIT_BASH_PATH` to the path of `bash.exe` in the `env` section of Claude Code's `settings.json`, for example `C:\Program Files\Git\bin\bash.exe`.
- **Any other ❌:** `python scripts/doctor.py` prints the fix.
