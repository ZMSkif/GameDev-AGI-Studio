# Installing gamedev-studio from zero (Windows)

This guide is for a person on a clean Windows 10 or 11 PC, and for a Claude told "install by this guide". Every step is marked:

- **[Claude]**: Claude Code can do it.
- **[you]**: the person does it. That covers sign-ins, Windows prompts and e-mail invitations.
- **[Claude → you]**: Claude runs it, but asks you first. Windows may also show a prompt for you to approve.

Russian version: [INSTALL.ru.md](INSTALL.ru.md).

> **How this guide was checked.** No install on a clean machine was done: the owner asked that nothing be installed on his PC, to avoid duplicates. What was checked:
> - The check script `scripts/doctor.py` was run read-only on the owner's PC, and in an environment like a clean PC (an empty PATH). It found every missing piece and printed its fix.
> - The release archive has everything this guide needs, and `claude plugin validate` passes on an unpacked copy.
> - The commands and requirements were compared with the Claude Code, Git for Windows, GitHub CLI and Python documentation.
>
> A real clean-machine test would use Windows Sandbox, which only the PC's owner can turn on.

## Step 0. What you need first

- **Windows:** 10 version 1809 or later, or Windows 11; x64 or ARM64; 4 GB of memory or more.
- **A Claude account:** Pro, Max, Team, Enterprise or Console. The free claude.ai plan is not enough.
- **The plugin archive (zip)**, one of:
  - the archive the owner (ZMSkif) sent you;
  - the release source archive at <https://github.com/ZMSkif/GameDev-AGI-Studio/releases>: pick the version, then "Source code (zip)". The repository is private, so this needs access (step 6).
- **A GitHub account**, so the plugin can read the studio's decisions. Without it the plugin works with limits (see "Without GitHub access").

## Step 1. [you] Install Claude Code and sign in

1. Open **PowerShell** (a normal one; no administrator rights are needed) and run:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
2. Close the window, open a new one, and check: `claude --version`.
3. Run `claude` and sign in in the browser. If no browser opens, press `c` to copy the link, open it yourself, and paste the code back into the terminal.

Alternative: `winget install Anthropic.ClaudeCode`. It does not update itself, so run `claude update` by hand.

## Step 2. [Claude] Unpack the archive into a lasting folder

The plugin loads from this folder in place, so do not use Downloads or Temp, and do not delete the folder after installing.

```powershell
New-Item -ItemType Directory -Force C:\Tools | Out-Null
Expand-Archive -Path "$HOME\Downloads\GameDev-AGI-Studio-0.4.0.zip" -DestinationPath C:\Tools
```

`C:\Tools` now holds a folder such as `GameDev-AGI-Studio-0.4.0`; the rest of this guide calls it the **plugin folder**. To check it, make sure it contains `.claude-plugin\marketplace.json`.

You can now start Claude Code in the plugin folder and tell it: "Install the plugin by INSTALL.md, steps 3 to 8."

## Step 3. [Claude → you] Install Git for Windows, Python and the GitHub CLI

Claude shows the three commands and asks for your yes. Your yes also accepts the winget source and package agreements, which is why the commands carry the `--accept-…` flags. Each install may show the Windows prompt "Do you want to allow this app to make changes?"; you approve it.

```powershell
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
```

- **If `winget` is missing,** install "App Installer" from the Microsoft Store. You do this step.
- **The `Git.Git` package** is maintained by the winget community, not by the Git for Windows project. The official installer is at <https://git-scm.com/install/windows>.
- **Python** can also come from the Python install manager at <https://www.python.org/downloads/>.
- **[you] Restart Claude Code after the installs:** close the terminal, open a new one, and run `claude --continue`. Until then, Claude does not see the new programs.

## Step 4. [Claude] Check

In the plugin folder:

```powershell
python scripts\doctor.py --lang en
```

The script only reads: it installs, changes and deletes nothing. It prints ✅ or ❌ for each item. For each ❌ it shows the fix and who does it. Without `--lang en` it prints in Russian; `--json` prints JSON for Claude.

## Step 5. [you] Sign in to GitHub

`gh auth login` asks questions and opens a browser, so run it **yourself, in a separate PowerShell window**, not through Claude:

```powershell
gh auth login
```

Choose GitHub.com, then "Login with a web browser". To check, run `gh auth status`.

## Step 6. [you] Get access to the private repository

1. Send the owner (ZMSkif) your GitHub login.
2. The owner gives you access to `ZMSkif/GameDev-AGI-Studio`.
3. Accept the invitation from GitHub's e-mail.
4. [Claude] Run `python scripts\doctor.py --lang en` again. "Access to the repository" and "Reading the decisions" should now show ✅.

## Step 7. [Claude] Install the plugin

Use the path to **your** plugin folder:

```powershell
claude plugin marketplace add "C:\Tools\GameDev-AGI-Studio-0.4.0"
claude plugin install gamedev-studio@gamedev-studio
```

[you] Restart Claude Code (a new terminal, `claude --continue`). To check, run `claude plugin list`; it shows `gamedev-studio@gamedev-studio`.

**Codex (optional)**, if you work in Codex:

```powershell
codex plugin marketplace add "C:\Tools\GameDev-AGI-Studio-0.4.0"
codex plugin add gamedev-studio@gamedev-studio
```

## Step 8. [Claude] Final check

1. `python scripts\doctor.py --lang en` shows every required item with ✅.
2. In a new Claude Code session, ask "which skills does the gamedev-studio plugin have?". The answer lists `studio-rules`, `engine-profiles`, `memory` and the others.

## Without GitHub access

What works:
- the skills;
- the agent roles;
- the `/gamedev-studio:…` commands;
- the hooks. They need only Git and Python, and their GitHub preflight fails open.

What does not:
- The `studio-rules` skill must read the studio's decisions from GitHub Issues (label `decision`). Without access, Claude cannot see them.
- The release source archive cannot be downloaded.

**Fallback.** The owner exports the decisions to a file and sends it with the archive:

```powershell
gh issue list -R ZMSkif/GameDev-AGI-Studio --label decision --state open --limit 1000 --json number,title,url,body > decisions.json
```

- Put `decisions.json` in the plugin folder. At the start of a session, tell Claude: "the studio's decisions are in decisions.json; read them from there".
- The brief command takes the file directly: `--decisions decisions.json`.
- The file goes stale, so ask for a new one with each release.

## Updating

1. Get the new archive.
2. Unpack it next to the old one, into a new folder named after the version.
3. Install the plugin from the new folder (step 7 with the new path).
4. Restart Claude Code.

If the plugin folder is a git clone rather than an unpacked archive, run:

```powershell
claude plugin marketplace update gamedev-studio
claude plugin update gamedev-studio@gamedev-studio
```

## Hindsight memory (optional)

The plugin works without memory. Memory is switched on separately, and only with the studio owner's agreement. Where the server runs is decided in task [#150](https://github.com/ZMSkif/GameDev-AGI-Studio/issues/150).

> **Not tested on a clean machine.** On the owner's PC:
> - the server runs from a virtual environment (venv) made by uv 0.13.1 on Python 3.11.9;
> - with `hindsight-api` 1.2.2;
> - about 1.8 GB.
>
> The commands below are the standard `venv` + `pip` route, which was not run as written.

1. **[Claude → you] Install** (about 2 GB, after your yes):
   ```powershell
   python -m venv "$HOME\.hindsight-runtime"
   & "$HOME\.hindsight-runtime\Scripts\python.exe" -m pip install hindsight-api==1.2.2
   ```
2. **[Claude] Start** the server. It runs on this PC only (127.0.0.1). It extracts facts through your Claude subscription (provider `claude-code`): no paid API, but Claude Code must be installed and signed in.
   ```powershell
   $env:HINDSIGHT_API_LLM_PROVIDER = "claude-code"
   $env:HINDSIGHT_API_HOST = "127.0.0.1"
   $env:HINDSIGHT_API_PORT = "8888"
   $env:HINDSIGHT_API_MODEL_INIT_TIMEOUT = "900"
   $env:HINDSIGHT_API_MCP_ENABLED_TOOLS = "retain,recall,list_memories,get_memory,get_bank"
   & "$HOME\.hindsight-runtime\Scripts\hindsight-api.exe" --host 127.0.0.1 --port 8888
   ```
   The first start downloads the search models from Hugging Face (`BAAI/bge-small-en-v1.5` and `hindsight-ai/hs-rerank-1`). That can take several minutes, hence the 900 s timeout.
3. **[Claude] Check:** `python scripts\doctor.py --lang en --hindsight`. The full test is `python scripts\hindsight_smoke.py --run <new id>`; it creates test banks, which only the owner deletes.
4. **Connecting a game** is described in section 2 of the `memory` skill. Each step there needs the owner's yes.

Warning: the Hindsight server's REST DELETE routes are open without authorisation. Only the rule in the `memory` skill keeps agents off them.

## If something goes wrong

- **`claude` is not found after installing:** open a new terminal. If that does not help, restart the computer.
- **`python` opens the Microsoft Store:** in Settings → Apps → Advanced app settings → App execution aliases, turn off both "python" entries.
- **Claude Code cannot find Git Bash:** set `CLAUDE_CODE_GIT_BASH_PATH` to the path of `bash.exe` in the `env` section of Claude Code's `settings.json`, for example `C:\Program Files\Git\bin\bash.exe`.
- **Any other ❌:** `python scripts\doctor.py` prints its fix.
