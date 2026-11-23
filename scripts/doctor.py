#!/usr/bin/env python3
"""Check of what the gamedev-studio plugin needs on this computer (DEC-037: preflight). It installs nothing.

What it does, and nothing else:
  * starts only the exact commands in ALLOWED_COMMANDS: `claude --version`, `git --version`,
    `bash --version`, one fixed Python version probe and, with --github only, `gh --version`,
    `gh auth status`, `gh repo view` and `gh issue list --limit 1`. None of them installs or configures
    anything. The Python probe runs with automatic runtime installs switched off
    (PYTHON_MANAGER_AUTOMATIC_INSTALL=false, no PYLAUNCHER_* variables).
  * reads files: Claude Code's installed_plugins.json, known_marketplaces.json and settings.json, and this
    plugin's plugin.json.
  * with --hindsight, one HTTP GET of the memory server's /health.
It does not start Codex (`codex --version` writes helper files) or `claude plugin list` (it tidies the
plugin cache); Codex and the other optional programs of tools/catalog.json are only looked up on PATH. The doctor itself writes no file. For every missing piece
it prints the fix and who does it.

Usage: python scripts/doctor.py [--lang ru|en] [--json] [--github] [--hindsight [URL]] [--repo owner/name]
Exit codes: 0 every required check passed, 1 at least one required check failed, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path, PureWindowsPath

REPO = "ZMSkif/GameDev-AGI-Studio"
PLUGIN_ID = "gamedev-studio@gamedev-studio"
MARKETPLACE = "gamedev-studio"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TESTED_CLAUDE = (2, 1, 325)
MIN_PYTHON = (3, 10)          # the plugin's commands pass newline= when saving a file, new in Python 3.10
PY_PROBE = "import sys;print('%d.%d.%d' % sys.version_info[:3])"
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
# The only commands this script may start, exactly as written; "{repo}" stands for an owner/name.
ALLOWED_COMMANDS = (
    ("claude", "--version"),
    ("git", "--version"),
    ("bash", "--version"),
    ("python", "-c", PY_PROBE),
    ("py", "-3", "-c", PY_PROBE),
    ("python3", "-c", PY_PROBE),
    ("gh", "--version"),
    ("gh", "auth", "status"),
    ("gh", "repo", "view", "{repo}", "--json", "name"),
    ("gh", "issue", "list", "-R", "{repo}", "--label", "decision", "--limit", "1", "--json", "number"),
)
NETWORK_HINTS = ("timeout", "timed out", "could not resolve host", "connect", "network", "proxy", "tls", "eof")

TEXT = {
    "ru": {
        "title": "gamedev-studio: проверка компьютера (ничего не устанавливает и не меняет)",
        "required": "обязательно", "optional": "по желанию",
        "who_claude": "Claude может сделать сам", "who_you": "делаете вы",
        "who_claude_yes": "Claude, после вашего «да»; Windows может спросить подтверждение",
        "fix": "Как исправить", "summary_ok": "Всё обязательное на месте.",
        "summary_fail": "Не хватает обязательного: {n}. Исправьте пункты с {bad} сверху вниз и запустите проверку снова.",
        "claude": "Claude Code", "git": "Git", "git_bash": "Git Bash", "python": "Python",
        "gh": "GitHub CLI (gh)", "gh_auth": "Вход в GitHub (gh auth)", "repo": "Доступ к репозиторию {repo}",
        "decisions": "Чтение решений (issues с меткой decision)", "plugin": "Плагин gamedev-studio в Claude Code",
        "codex": "Codex CLI", "hindsight": "Сервер памяти Hindsight ({url})",
        "fix_catalog_claude": "{gives} Поставить: панель студии (`python scripts/studio_panel.py`) или `python scripts/studio_tools.py install {id} --yes`.",
        "fix_catalog_person": "{gives} {manual}",
        "found": "найден: {v}", "not_found": "не найден", "too_old": "версия {v}, нужна {need} или новее",
        "older_than_tested": "версия {v}; руководство проверено на {tested}, обновите при проблемах",
        "claude_not_on_path": "установлен в {p}, но этой папки нет в PATH",
        "store_alias": "команда есть, но это заглушка Microsoft Store, а не Python",
        "bash_override_bad": "CLAUDE_CODE_GIT_BASH_PATH указывает на {p}, но это не рабочий bash",
        "signed_in": "вход выполнен", "not_signed_in": "вход не выполнен",
        "no_access": "нет доступа", "access": "доступ есть", "no_decisions": "ответ без решений",
        "cannot_check": "не удалось проверить: {why}",
        "installed_here": "установлен из этой папки и включён, версия {v}",
        "installed": "установлен и включён, версия {v}", "not_installed": "не установлен",
        "disabled": "установлен, но выключен",
        "other_place": "установлен из другого места ({p}), версия {v}; в этой папке {want}",
        "state_unreadable": "не удалось прочитать список плагинов ({why})",
        "on_path": "есть в PATH: {p}", "found_at": "установлен: {p} (не в PATH)",
        "unreachable": "не отвечает", "healthy": "отвечает, база подключена",
        "skipped_needs": "пропущено: сначала исправьте «{dep}»",
        "restart": "закройте этот терминал, откройте новое окно PowerShell и выполните `cd \"{root}\"`, затем `claude --continue`",
        "fix_claude": "Установите Claude Code: в PowerShell `irm https://claude.ai/install.ps1 | iex` (права администратора не нужны), откройте новый терминал, запустите `claude` и войдите через браузер. Нужна платная подписка Claude (например Pro или Max). Аккаунт Console (оплата API) не подходит: студия работает по подписке и не переходит на платный API (DEC-085).",
        "fix_claude_path": "Добавьте папку {d} в PATH пользователя (Параметры → Система → О системе → Дополнительные параметры системы → Переменные среды → Path → Создать), затем откройте новый терминал.",
        "fix_claude_old": "Обновите Claude Code: `claude update` (если ставили через winget: `winget upgrade Anthropic.ClaudeCode`).",
        "fix_git": "Установите Git for Windows: `winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`. Затем {restart}.",
        "fix_git_bash": "Git Bash входит в Git for Windows: установите Git (`winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`). Если Git уже стоит в другой папке, укажите путь к bash.exe в переменной CLAUDE_CODE_GIT_BASH_PATH (раздел env в settings.json Claude Code).",
        "fix_git_bash_override": "Исправьте или удалите CLAUDE_CODE_GIT_BASH_PATH в разделе env файла settings.json Claude Code: путь должен вести к bash.exe из Git for Windows, например C:\\Program Files\\Git\\bin\\bash.exe.",
        "fix_python": "Установите Python: `winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements`. Затем {restart}. Если `python` пишет про Microsoft Store, отключите псевдонимы «python.exe» и «python3.exe»: Параметры → Приложения → Дополнительные параметры приложений → Псевдонимы выполнения приложений.",
        "fix_gh": "Нужно, только если владелец дал вам доступ к GitHub. Установите GitHub CLI: `winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements`. Затем {restart}.",
        "fix_gh_auth": "Войдите в GitHub сами, в отдельном окне PowerShell: `gh auth login` (GitHub.com, вход через браузер).",
        "fix_repo": "Репозиторий {repo} закрытый, доступ к нему даёт только владелец (ZMSkif). Без доступа плагин работает, но полный список решений студии не виден (раздел «Без доступа к GitHub» руководства).",
        "fix_network": "Проверьте подключение к интернету и прокси, затем запустите проверку снова.",
        "fix_plugin": "Установите плагин из этой папки: `claude plugin marketplace add \"{root}\"`, затем `claude plugin install gamedev-studio@gamedev-studio`. Затем {restart}.",
        "fix_plugin_disabled": "Включите плагин: `claude plugin enable gamedev-studio@gamedev-studio`. Затем {restart}.",
        "fix_plugin_other": "Плагин подключён из другой папки. Запустите проверку из неё или обновите плагин по разделу «Обновление» руководства.",
        "fix_plugin_unreadable": "Посмотрите сами: `claude plugin list` должен показать gamedev-studio@gamedev-studio.",
        "fix_hindsight": "Не обязательно: плагин работает без памяти. Включать её — только по решению владельца студии (раздел «Память Hindsight» руководства).",
    },
    "en": {
        "title": "gamedev-studio: computer check (installs and changes nothing)",
        "required": "required", "optional": "optional",
        "who_claude": "Claude can do it", "who_you": "you do it",
        "who_claude_yes": "Claude, after your yes; Windows may ask you to approve",
        "fix": "Fix", "summary_ok": "Everything required is in place.",
        "summary_fail": "{n} required item(s) missing. Fix the {bad} items from the top and run the check again.",
        "claude": "Claude Code", "git": "Git", "git_bash": "Git Bash", "python": "Python",
        "gh": "GitHub CLI (gh)", "gh_auth": "Signed in to GitHub (gh auth)", "repo": "Access to the {repo} repository",
        "decisions": "Reading the decisions (issues labelled decision)", "plugin": "gamedev-studio plugin in Claude Code",
        "codex": "Codex CLI", "hindsight": "Hindsight memory server ({url})",
        "fix_catalog_claude": "{gives} Install: the studio panel (`python scripts/studio_panel.py`) or `python scripts/studio_tools.py install {id} --yes`.",
        "fix_catalog_person": "{gives} {manual}",
        "found": "found: {v}", "not_found": "not found", "too_old": "version {v}, needs {need} or newer",
        "older_than_tested": "version {v}; the guide was checked on {tested}, update if something fails",
        "claude_not_on_path": "installed in {p}, but that folder is not on PATH",
        "store_alias": "the command exists but is the Microsoft Store alias, not Python",
        "bash_override_bad": "CLAUDE_CODE_GIT_BASH_PATH points at {p}, which is not a working bash",
        "signed_in": "signed in", "not_signed_in": "not signed in",
        "no_access": "no access", "access": "access granted", "no_decisions": "the answer holds no decisions",
        "cannot_check": "could not check: {why}",
        "installed_here": "installed from this folder and enabled, version {v}",
        "installed": "installed and enabled, version {v}", "not_installed": "not installed",
        "disabled": "installed but disabled",
        "other_place": "installed from another place ({p}), version {v}; this folder is {want}",
        "state_unreadable": "could not read the plugin list ({why})",
        "on_path": "on PATH: {p}", "found_at": "installed: {p} (not on PATH)",
        "unreachable": "not answering", "healthy": "answering, database connected",
        "skipped_needs": "skipped: fix \"{dep}\" first",
        "restart": "close this terminal, open a new PowerShell window and run `cd \"{root}\"`, then `claude --continue`",
        "fix_claude": "Install Claude Code: in PowerShell `irm https://claude.ai/install.ps1 | iex` (no administrator rights needed), open a new terminal, run `claude` and sign in in the browser. A paid Claude subscription is needed (for example Pro or Max). A Console account (API billing) does not fit: the studio works on a subscription and does not switch to the paid API (DEC-085).",
        "fix_claude_path": "Add the folder {d} to your user PATH (Settings > System > About > Advanced system settings > Environment Variables > Path > New), then open a new terminal.",
        "fix_claude_old": "Update Claude Code: `claude update` (if you installed it with winget: `winget upgrade Anthropic.ClaudeCode`).",
        "fix_git": "Install Git for Windows: `winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`. Then {restart}.",
        "fix_git_bash": "Git Bash comes with Git for Windows: install Git (`winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements`). If Git is already installed elsewhere, set CLAUDE_CODE_GIT_BASH_PATH to the path of bash.exe (the env section of Claude Code's settings.json).",
        "fix_git_bash_override": "Fix or remove CLAUDE_CODE_GIT_BASH_PATH in the env section of Claude Code's settings.json: it must lead to bash.exe from Git for Windows, for example C:\\Program Files\\Git\\bin\\bash.exe.",
        "fix_python": "Install Python: `winget install --id Python.Python.3.13 -e --source winget --accept-source-agreements --accept-package-agreements`. Then {restart}. If `python` talks about the Microsoft Store, turn off the \"python.exe\" and \"python3.exe\" aliases: Settings > Apps > Advanced app settings > App execution aliases.",
        "fix_gh": "Needed only if the owner gave you GitHub access. Install the GitHub CLI: `winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements`. Then {restart}.",
        "fix_gh_auth": "Sign in to GitHub yourself, in a separate PowerShell window: `gh auth login` (GitHub.com, browser sign-in).",
        "fix_repo": "The {repo} repository is private; only the owner (ZMSkif) gives access. Without access the plugin works, but the full list of the studio's decisions is not visible (the guide's \"Without GitHub access\").",
        "fix_network": "Check the internet connection and any proxy, then run the check again.",
        "fix_plugin": "Install the plugin from this folder: `claude plugin marketplace add \"{root}\"`, then `claude plugin install gamedev-studio@gamedev-studio`. Then {restart}.",
        "fix_plugin_disabled": "Enable the plugin: `claude plugin enable gamedev-studio@gamedev-studio`. Then {restart}.",
        "fix_plugin_other": "The plugin is connected from another folder. Run the check from that folder, or update the plugin as the guide's \"Updating\" says.",
        "fix_plugin_unreadable": "Look yourself: `claude plugin list` should show gamedev-studio@gamedev-studio.",
        "fix_hindsight": "Optional: the plugin works without memory. Turn it on only when the studio owner decides so (the guide's \"Hindsight memory\" section).",
    },
}


def allowed(argv: list[str]) -> bool:
    """True only for an exact command of ALLOWED_COMMANDS. argv[0] may be a full path (a found bash.exe):
    the program name decides."""
    if not argv:
        return False
    got = (PureWindowsPath(argv[0]).stem.lower(), *argv[1:])      # accepts both \ and / separators
    for command in ALLOWED_COMMANDS:
        if len(command) == len(got) and all(
                a == b or (a == "{repo}" and REPO_RE.fullmatch(b)) for a, b in zip(command, got)):
            return True
    return False


def child_env() -> dict:
    """This environment with automatic Python runtime installs switched off (Python install manager and
    the legacy py launcher), so a version probe can never download or install anything."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYLAUNCHER_")}
    env["PYTHON_MANAGER_AUTOMATIC_INSTALL"] = "false"
    return env


def run(argv: list[str], timeout: float = 60.0) -> tuple[int, str]:
    """Run one allowed command; (exit code, stdout + stderr). 127 when it is not found."""
    if not allowed(argv):
        raise ValueError(f"doctor.py may not run {argv!r}")
    exe = argv[0] if Path(argv[0]).is_absolute() else shutil.which(argv[0])
    if not exe:
        return 127, ""
    try:
        done = subprocess.run([exe, *argv[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL, env=child_env())
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    except (OSError, subprocess.SubprocessError) as exc:
        return 126, str(exc)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def version_of(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    return tuple(int(g) for g in match.groups() if g is not None) if match else None


def fmt(v: tuple[int, ...]) -> str:
    return ".".join(str(n) for n in v)


def network_trouble(code: int, out: str) -> bool:
    return code in (124, 126) or any(h in out.lower() for h in NETWORK_HINTS)


def restart(t) -> str:
    return t["restart"].format(root=PLUGIN_ROOT)


def last_line(out: str) -> str:
    return (out.strip().splitlines() or [""])[-1][:120]


def check_claude(t):
    code, out = run(["claude", "--version"])
    v = version_of(out) if code == 0 else None
    if not v:
        local = Path.home() / ".local" / "bin" / ("claude.exe" if os.name == "nt" else "claude")
        if local.is_file():
            return False, t["claude_not_on_path"].format(p=local), t["fix_claude_path"].format(d=local.parent), "you"
        return False, t["not_found"], t["fix_claude"], "you"
    if v < TESTED_CLAUDE:
        return True, t["older_than_tested"].format(v=fmt(v), tested=fmt(TESTED_CLAUDE)), t["fix_claude_old"], "claude"
    return True, t["found"].format(v=fmt(v)), "", ""


def check_git(t):
    code, out = run(["git", "--version"])
    return (True, t["found"].format(v=out.strip()), "", "") if code == 0 else \
        (False, t["not_found"], t["fix_git"].format(restart=restart(t)), "claude_yes")


def bash_candidates() -> list[Path]:
    """Where Git Bash usually is on Windows: next to git, then the standard install folders."""
    found = []
    git = shutil.which("git")
    if git:
        root = Path(git).resolve().parent.parent          # ...\Git\cmd\git.exe -> ...\Git
        found += [root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"), os.environ.get("LOCALAPPDATA")):
        if base:
            found += [Path(base) / "Git" / "bin" / "bash.exe", Path(base) / "Programs" / "Git" / "bin" / "bash.exe"]
    return found


def works_as_bash(path: Path) -> bool:
    if not path.is_file() or Path(path).stem.lower() != "bash":
        return False
    code, out = run([str(path), "--version"])
    return code == 0 and "bash" in out.lower()


def check_git_bash(t):
    if os.name != "nt":
        code, out = run(["bash", "--version"])
        return (True, t["found"].format(v=(out.splitlines() or ["bash"])[0]), "", "") if code == 0 else \
            (False, t["not_found"], t["fix_git_bash"], "claude_yes")
    override = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH") or settings_env("CLAUDE_CODE_GIT_BASH_PATH")
    if override:                                          # an explicit override must work; never paper over it
        return (True, t["found"].format(v=override), "", "") if works_as_bash(Path(override)) else \
            (False, t["bash_override_bad"].format(p=override), t["fix_git_bash_override"], "you")
    for path in bash_candidates():
        if works_as_bash(path):
            return True, t["found"].format(v=str(path)), "", ""
    return False, t["not_found"], t["fix_git_bash"], "claude_yes"


def check_python(t):
    """The interpreter the plugin's hooks find, in their order: the first one that is 3.10 or newer."""
    store_alias, too_old = False, None
    for argv in (["python", "-c", PY_PROBE], ["py", "-3", "-c", PY_PROBE], ["python3", "-c", PY_PROBE]):
        code, out = run(argv)
        v = version_of(out) if code == 0 else None
        if v and v >= MIN_PYTHON:
            return True, t["found"].format(v=f"{argv[0]} {fmt(v)}"), "", ""
        if v:
            too_old = too_old or v
        exe = shutil.which(argv[0]) or ""
        store_alias = store_alias or ("WindowsApps" in exe and not v)
    fix = t["fix_python"].format(restart=restart(t))
    if too_old:
        return False, t["too_old"].format(v=fmt(too_old), need=fmt(MIN_PYTHON)), fix, "claude_yes"
    return False, (t["store_alias"] if store_alias else t["not_found"]), fix, "claude_yes"


def check_gh(t):
    code, out = run(["gh", "--version"])
    return (True, t["found"].format(v=(out.splitlines() or [""])[0]), "", "") if code == 0 else \
        (False, t["not_found"], t["fix_gh"].format(restart=restart(t)), "claude_yes")


def check_gh_auth(t):
    code, out = run(["gh", "auth", "status"])
    if code == 0:
        return True, t["signed_in"], "", ""
    if "not logged" in out.lower() or "gh auth login" in out.lower() or not out.strip():
        return False, t["not_signed_in"], t["fix_gh_auth"], "you"
    if network_trouble(code, out):
        return False, t["cannot_check"].format(why=last_line(out)), t["fix_network"], "you"
    return False, t["not_signed_in"], t["fix_gh_auth"], "you"


def check_repo(t, repo):
    code, out = run(["gh", "repo", "view", repo, "--json", "name"])
    if code == 0:
        return True, t["access"], "", ""
    if network_trouble(code, out) and "could not resolve to a repository" not in out.lower():
        return False, t["cannot_check"].format(why=last_line(out)), t["fix_network"], "you"
    return False, t["no_access"], t["fix_repo"].format(repo=repo), "you"


def check_decisions(t, repo):
    code, out = run(["gh", "issue", "list", "-R", repo, "--label", "decision", "--limit", "1", "--json", "number"])
    if code != 0:
        if network_trouble(code, out):
            return False, t["cannot_check"].format(why=last_line(out)), t["fix_network"], "you"
        return False, t["no_access"], t["fix_repo"].format(repo=repo), "you"
    try:
        items = json.loads(out)
    except ValueError:
        items = None
    if isinstance(items, list) and items and isinstance(items[0], dict) and "number" in items[0]:
        return True, t["access"], "", ""
    return False, t["no_decisions"], t["fix_repo"].format(repo=repo), "you"


def claude_config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def settings_env(name: str) -> str:
    """A variable from the `env` section of Claude Code's user settings.json, where the guide sets it."""
    try:
        env = read_json(claude_config_dir() / "settings.json").get("env", {})
    except (OSError, ValueError, AttributeError):
        return ""
    value = env.get(name) if isinstance(env, dict) else None
    return value if isinstance(value, str) else ""


def same_folder(a, b) -> bool:
    try:
        return os.path.normcase(os.path.realpath(str(a))) == os.path.normcase(os.path.realpath(str(b)))
    except (OSError, ValueError):
        return False


def plugin_state() -> tuple[str, str, str]:
    """('missing'|'disabled'|'enabled', installed version, where it loads from), read from Claude Code's own
    files. These are Claude Code's internal files, so an unexpected shape raises ValueError, not a guess.
    A plugin from a local-folder marketplace loads in place from that folder, so the folder is what counts.
    This is the user install the guide makes: project or local settings that switch it off are not read."""
    base = claude_config_dir()
    installed = read_json(base / "plugins" / "installed_plugins.json")
    plugins = installed.get("plugins") if isinstance(installed, dict) else None
    if not isinstance(plugins, dict):
        raise ValueError("installed_plugins.json has no plugins map")
    entries = plugins.get(PLUGIN_ID)
    if not entries:
        return "missing", "", ""
    if isinstance(entries, list):                     # the guide installs for the user; prefer that entry
        entry = next((e for e in entries if isinstance(e, dict) and e.get("scope") == "user"), entries[0])
    else:
        entry = entries
    if not isinstance(entry, dict):
        raise ValueError("unexpected plugin entry")
    version = str(entry.get("version", "?"))
    places = [entry.get("installPath")]
    known_path = base / "plugins" / "known_marketplaces.json"
    known = read_json(known_path) if known_path.is_file() else {}
    market = known.get(MARKETPLACE) if isinstance(known, dict) else None
    if isinstance(market, dict):
        source = market.get("source") if isinstance(market.get("source"), dict) else {}
        places += [market.get("installLocation"), source.get("path")]
    places = [str(p) for p in places if isinstance(p, str) and p]
    where = next((p for p in places if same_folder(p, PLUGIN_ROOT)), places[0] if places else "")
    settings_path = base / "settings.json"
    enabled = read_json(settings_path).get("enabledPlugins", {}) if settings_path.is_file() else {}
    return ("enabled" if enabled.get(PLUGIN_ID) is True else "disabled"), version, where


def folder_version() -> str:
    try:
        return str(read_json(PLUGIN_ROOT / ".claude-plugin" / "plugin.json").get("version", ""))
    except (OSError, ValueError):
        return ""


def check_plugin(t):
    root = str(PLUGIN_ROOT)
    try:
        state, version, where = plugin_state()
    except (OSError, ValueError, AttributeError) as exc:
        if isinstance(exc, FileNotFoundError):
            return False, t["not_installed"], t["fix_plugin"].format(root=root, restart=restart(t)), "claude"
        return False, t["state_unreadable"].format(why=type(exc).__name__), t["fix_plugin_unreadable"], "you"
    if state == "missing":
        return False, t["not_installed"], t["fix_plugin"].format(root=root, restart=restart(t)), "claude"
    if state == "disabled":
        return False, t["disabled"], t["fix_plugin_disabled"].format(restart=restart(t)), "claude"
    want = folder_version()
    if where and same_folder(where, PLUGIN_ROOT):       # loads in place: this folder's files are the plugin
        return True, t["installed_here"].format(v=want or version), "", ""
    if want and version != want:
        return False, t["other_place"].format(p=where or "?", v=version, want=want), t["fix_plugin_other"], "you"
    return True, t["installed"].format(v=version), "", ""


STUDIO_TOOLS = None


def catalog_tools():
    """Optional machine-wide programs from tools/catalog.json that are found on PATH (gh has its own checks)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("studio_tools", Path(__file__).with_name("studio_tools.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        catalog = module.load_catalog()
    except (ImportError, OSError, ValueError):
        return []
    global STUDIO_TOOLS
    STUDIO_TOOLS = module
    return [tool for tool in catalog["tools"]
            if tool["scope"] == "machine" and tool["detect"]["type"] == "which" and tool["id"] != "gh"]


def check_catalog_tool(t, lang, tool):
    """A catalog program is only looked up on PATH; nothing is started."""
    rule = tool["detect"]
    found = [shutil.which(name) for name in rule["names"]]
    path = found[0] if all(found) else next((p for p in map(shutil.which, rule.get("alternatives", [])) if p), None)
    if path:
        return True, t["on_path"].format(p=path), "", ""
    if STUDIO_TOOLS is not None:  # installers such as Blender's MSI do not add the program to PATH
        known = STUDIO_TOOLS.known_program(rule.get("known_paths", {}).get(STUDIO_TOOLS.platform_key(), []))
        if known:
            return True, t["found_at"].format(p=known), "", ""
    gives = tool["gives"][lang]
    if tool["who"] == "claude_yes":
        return False, t["not_found"], t["fix_catalog_claude"].format(gives=gives, id=tool["id"]), "claude_yes"
    manual = tool.get("install", {}).get("manual", {}).get(lang, "")
    return False, t["not_found"], t["fix_catalog_person"].format(gives=gives, manual=manual), "you"


def check_hindsight(t, url):
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
        ok = isinstance(body, dict) and body.get("database") == "connected"
    except (urllib.error.URLError, OSError, ValueError):
        ok = False
    return (True, t["healthy"], "", "") if ok else (False, t["unreachable"], t["fix_hindsight"], "you")


def checks(lang: str, repo: str, hindsight: str | None, github: bool = False) -> list[dict]:
    """Run every check in install order; a check whose prerequisite failed is skipped, not guessed.
    The GitHub checks run only with --github: the guide's default path works without GitHub access."""
    t = TEXT[lang]
    plan = [
        ("claude", True, None, lambda: check_claude(t)),
        ("git", True, None, lambda: check_git(t)),
        ("git_bash", True, None, lambda: check_git_bash(t)),
        ("python", True, None, lambda: check_python(t)),
    ]
    if github:
        plan += [
            ("gh", True, None, lambda: check_gh(t)),
            ("gh_auth", True, "gh", lambda: check_gh_auth(t)),
            ("repo", True, "gh_auth", lambda: check_repo(t, repo)),
            ("decisions", True, "repo", lambda: check_decisions(t, repo)),
        ]
    plan += [
        ("plugin", True, "claude", lambda: check_plugin(t)),
    ]
    for tool in catalog_tools():
        plan.append((tool["id"], False, None, lambda tool=tool: check_catalog_tool(t, lang, tool)))
    if hindsight:
        plan.append(("hindsight", False, None, lambda: check_hindsight(t, hindsight)))
    results: dict[str, dict] = {}
    for key, required, needs, func in plan:
        label = t[key].format(repo=repo, url=hindsight or "") if key in t else next(
            tool["name"] for tool in catalog_tools() if tool["id"] == key)
        if needs and not results[needs]["ok"]:
            results[key] = {"key": key, "label": label, "required": required, "ok": False, "skipped": True,
                            "detail": t["skipped_needs"].format(dep=results[needs]["label"]), "fix": "", "who": ""}
            continue
        ok, detail, fix, who = func()
        results[key] = {"key": key, "label": label, "required": required, "ok": ok, "skipped": False,
                        "detail": detail, "fix": fix, "who": who}
    return list(results.values())


def render(rows: list[dict], lang: str, marks: tuple[str, str, str]) -> str:
    t = TEXT[lang]
    good, bad, skip = marks
    who_text = {"claude": t["who_claude"], "claude_yes": t["who_claude_yes"], "you": t["who_you"]}
    out = [t["title"], ""]
    for r in rows:
        mark = good if r["ok"] else (skip if r["skipped"] else bad)
        kind = t["required"] if r["required"] else t["optional"]
        out.append(f"{mark} {r['label']} ({kind}): {r['detail']}")
        if r["fix"]:
            out.append(f"    {t['fix']} [{who_text.get(r['who'], t['who_you'])}]: {r['fix']}")
    failed = sum(1 for r in rows if r["required"] and not r["ok"])
    out += ["", t["summary_fail"].format(n=failed, bad=bad) if failed else t["summary_ok"]]
    return "\n".join(out) + "\n"


def marks_for(stream) -> tuple[str, str, str]:
    """✅ / ❌ / ⏭ where the console can print them, else [OK] / [FAIL] / [SKIP]."""
    try:
        "✅❌⏭".encode(stream.encoding or "ascii")
        return "✅", "❌", "⏭"
    except (UnicodeEncodeError, LookupError):
        return "[OK]", "[FAIL]", "[SKIP]"


def prepare_stdout() -> None:
    """A pipe (Claude's tools, a log) gets UTF-8 unless PYTHONIOENCODING says otherwise: on Windows a pipe is
    the ANSI code page (cp1251), which Claude's Bash tool reads as broken Cyrillic. Never crash on a character."""
    if not hasattr(sys.stdout, "reconfigure"):
        return
    piped = not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
    if piped and not os.environ.get("PYTHONIOENCODING"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    else:
        sys.stdout.reconfigure(errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check what gamedev-studio needs on this computer (installs nothing).")
    parser.add_argument("--lang", choices=sorted(TEXT), default="ru")
    parser.add_argument("--json", action="store_true", help="print the results as JSON")
    parser.add_argument("--github", action="store_true",
                        help="also check the GitHub CLI, sign-in and access to the repository's decisions")
    parser.add_argument("--repo", default=REPO, help="the plugin repository whose access --github checks")
    parser.add_argument("--hindsight", nargs="?", const="http://127.0.0.1:8888", default=None, metavar="URL",
                        help="also check the optional Hindsight memory server (default URL http://127.0.0.1:8888)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if not REPO_RE.fullmatch(args.repo):
        print(f"--repo must be owner/name, not {args.repo!r}", file=sys.stderr)
        return 2
    prepare_stdout()
    rows = checks(args.lang, args.repo, args.hindsight, args.github)
    if args.json:
        print(json.dumps(rows, ensure_ascii=marks_for(sys.stdout)[0] != "✅", indent=2))
    else:
        print(render(rows, args.lang, marks_for(sys.stdout)), end="")
    return 1 if any(r["required"] and not r["ok"] for r in rows) else 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    sys.exit(main())
