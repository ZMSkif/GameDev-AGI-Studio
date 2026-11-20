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

[The result of the clean Windows run in GitHub Actions goes here.]

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
   - If the command is not found, the install folder is not on PATH. The installer puts the program in `%USERPROFILE%\.local\bin`. Add that folder to your user PATH: Settings → System → About → Advanced system settings → Environment Variables → `Path` in the upper list → Edit → New → `%USERPROFILE%\.local\bin` → OK. Then open a new PowerShell window.
3. Run `claude` and sign in in the browser. If the browser does not open, press `c` to copy the link, open it yourself and paste the code back into the terminal. Then leave with `/exit`.

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
- The plugin loads straight from this folder, so do not delete or move it after installing.

Now tell Claude: "Install the plugin by INSTALL.md, steps 3–7".

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
- **Python**, if neither `python` nor `py -3` showed version 3.9 or newer. A `python` under `...\WindowsApps\` that talks about the Microsoft Store is a stub, not Python.

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

Done; you can make games.

## Without GitHub access (the usual case)

Everything needed for games works:

- the skills, agent roles and `/gamedev-studio:…` commands;
- the hook checks;
- the studio rules: they are in the plugin's skills and in the `AGENTS.md`, `contracts/v1/` and `reference/` files inside the plugin folder.

What is missing is the owner's full list of decisions. It is kept in the GitHub Issues of the private repository. Claude says once that the list is not available and then works by the plugin's rules. If it needs a decision the plugin does not cover, Claude asks you instead of making one up; then ask the owner.

When Claude Code starts in a game folder, it may warn `GameDev Studio tool preflight FAILED: gh (GitHub CLI) was not found`. Without GitHub this is expected: only tasks that need GitHub stop, and other work goes on.

## Updating

1. **[you]** Get the new zip from the owner.
2. **[you]** Close every Claude Code window: Windows will not rename a folder that a program has open.
3. **[you]** In PowerShell:
   ```powershell
   Rename-Item C:\Tools\gamedev-studio gamedev-studio-old
   Expand-Archive -Path "$HOME\Downloads\gamedev-studio-0.4.2.zip" -DestinationPath C:\Tools
   ```
   If `gamedev-studio-old` is left over from an earlier update, delete it first.
4. **[you]** Start Claude Code. There is no need to reinstall the plugin: it loads from this folder, and the Claude Code docs say changes there take effect at the next start.
5. **[Claude]** `python scripts/doctor.py` shows the new version. Once everything works, delete `C:\Tools\gamedev-studio-old` yourself.

This update path has not been tested on a real install.

## Hindsight memory (optional, only when the owner decides)

The plugin works without memory. The owner decides where and how the studio's memory runs, so follow these steps only when the owner says so.

> [The result of the trial Hindsight install in GitHub Actions goes here.] The owner's PC runs the server on Python 3.11.9 with `hindsight-api` 1.2.2, about 1.8 GB.

1. **[Claude → you]** Install, about 2 GB, after your yes. It needs Python 3.11 or newer:
   ```powershell
   python -m venv "$HOME\.hindsight-runtime"
   & "$HOME\.hindsight-runtime\Scripts\python.exe" -m pip install hindsight-api==1.2.2
   ```
2. **[you] Start it in a separate PowerShell window.** The server runs while the window is open, and only on this PC (127.0.0.1). It extracts facts through your Claude subscription; the `claude-code` provider is documented for Pro and Max. No paid API is needed, but Claude Code must be installed and signed in.
   ```powershell
   $env:HINDSIGHT_API_LLM_PROVIDER = "claude-code"
   $env:HINDSIGHT_API_HOST = "127.0.0.1"
   $env:HINDSIGHT_API_PORT = "8888"
   $env:HINDSIGHT_API_MODEL_INIT_TIMEOUT = "900"
   $env:HINDSIGHT_API_MCP_ENABLED_TOOLS = "retain,recall,list_memories,get_memory,get_bank"
   & "$HOME\.hindsight-runtime\Scripts\hindsight-api.exe" --host 127.0.0.1 --port 8888
   ```
   The first start downloads the search models from Hugging Face, `BAAI/bge-small-en-v1.5` and `hindsight-ai/hs-rerank-1`. That can take several minutes.
3. **[Claude]** Check: `python scripts/doctor.py --hindsight`.
4. **Connecting it to a game** is in section 2 of the `memory` skill.

Only the studio owner deletes memory. Warning: the Hindsight server's REST DELETE routes are open without authorization, and only the rule in the `memory` skill keeps agents away from them.

## Troubleshooting

- **`claude` not found:** open a new window. If that does not help, add the folder to PATH as step 1 says.
- **`python` talks about the Microsoft Store:** go to Settings → Apps → Advanced app settings → App execution aliases and turn off "python.exe" and "python3.exe". If you installed the Python install manager, leave its aliases alone.
- **Claude Code cannot find Git Bash:** set `CLAUDE_CODE_GIT_BASH_PATH` to the path of `bash.exe` in the `env` section of Claude Code's `settings.json`, for example `C:\Program Files\Git\bin\bash.exe`.
- **Any other ❌:** `python scripts/doctor.py` prints the fix.
