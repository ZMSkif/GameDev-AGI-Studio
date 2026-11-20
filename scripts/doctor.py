#!/usr/bin/env python3
"""Read-only check of what the gamedev-studio plugin needs on this computer (DEC-037: preflight).

It never installs, changes or deletes anything. It only runs the version, status and list commands in
ALLOWED_COMMANDS and, with --hindsight, one HTTP GET of the memory server's /health. For every missing
piece it prints the fix and who does it: Claude (in a Claude Code session) or you (the person).

Usage: python scripts/doctor.py [--lang ru|en] [--json] [--hindsight [URL]] [--repo owner/name]
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
from pathlib import Path

REPO = "ZMSkif/GameDev-AGI-Studio"
PLUGIN_ID = "gamedev-studio@gamedev-studio"
TESTED_CLAUDE = (2, 1, 325)
MIN_PYTHON = (3, 9)
# The only commands this script may run. Each is a read: a version, a status, a list or a view.
ALLOWED_COMMANDS = (
    ("claude", "--version"),
    ("claude", "plugin", "list", "--json"),
    ("git", "--version"),
    ("bash", "--version"),
    ("python", "-c"),
    ("py", "-3", "-c"),
    ("python3", "-c"),
    ("gh", "--version"),
    ("gh", "auth", "status"),
    ("gh", "repo", "view"),
    ("gh", "issue", "list"),
    ("codex", "--version"),
)
PY_PROBE = "import sys;print('%d.%d.%d' % sys.version_info[:3])"

TEXT = {
    "ru": {
        "title": "gamedev-studio: проверка компьютера (только чтение, ничего не устанавливает)",
        "required": "обязательно", "optional": "по желанию",
        "who_claude": "Claude может сделать сам", "who_you": "делаете вы",
        "fix": "Как исправить", "summary_ok": "Всё обязательное на месте.",
        "summary_fail": "Не хватает обязательного: {n}. Исправьте пункты с {bad} сверху вниз и запустите проверку снова.",
        "claude": "Claude Code", "git": "Git", "git_bash": "Git Bash", "python": "Python",
        "gh": "GitHub CLI (gh)", "gh_auth": "Вход в GitHub (gh auth)", "repo": "Доступ к репозиторию {repo}",
        "decisions": "Чтение решений (issues с меткой decision)", "plugin": "Плагин gamedev-studio в Claude Code",
        "codex": "Codex CLI", "hindsight": "Сервер памяти Hindsight ({url})",
        "found": "найден: {v}", "not_found": "не найден", "too_old": "версия {v}, нужна {need} или новее",
        "older_than_tested": "версия {v}; руководство проверено на {tested}, обновите при проблемах",
        "store_alias": "команда есть, но это заглушка Microsoft Store, а не Python",
        "signed_in": "вход выполнен", "not_signed_in": "вход не выполнен",
        "no_access": "нет доступа (или нет входа в gh)", "access": "доступ есть",
        "installed": "установлен, версия {v}", "not_installed": "не установлен",
        "unreachable": "не отвечает", "healthy": "отвечает, база подключена",
        "skipped_needs": "пропущено: сначала исправьте «{dep}»",
        "fix_claude": "Установите Claude Code: в PowerShell `irm https://claude.ai/install.ps1 | iex` (права администратора не нужны), откройте новый терминал, запустите `claude` и войдите через браузер. Нужен план Pro, Max, Team, Enterprise или Console: бесплатного плана claude.ai недостаточно.",
        "fix_claude_old": "Обновите Claude Code: `claude update`.",
        "fix_git": "Установите Git for Windows: `winget install --id Git.Git -e --source winget` (подтвердите окно Windows), затем перезапустите Claude Code (новый терминал, `claude --continue`), чтобы он увидел новую программу.",
        "fix_git_bash": "Git Bash входит в Git for Windows. Если Git установлен в другую папку, укажите путь к bash.exe в переменной CLAUDE_CODE_GIT_BASH_PATH (раздел env в settings.json Claude Code).",
        "fix_python": "Установите Python 3.9 или новее: `winget install --id Python.Python.3.13 -e --source winget` (или установщик с python.org), затем перезапустите Claude Code (новый терминал, `claude --continue`). Если `python` открывает Microsoft Store, отключите псевдонимы «python.exe» в Параметры > Приложения > Псевдонимы выполнения приложений.",
        "fix_gh": "Установите GitHub CLI: `winget install --id GitHub.cli --source winget`, затем перезапустите Claude Code (новый терминал, `claude --continue`).",
        "fix_gh_auth": "Войдите в GitHub: `gh auth login` (выберите GitHub.com и вход через браузер).",
        "fix_repo": "Репозиторий закрытый. Попросите владельца (ZMSkif) добавить вашу учётную запись GitHub в доступ к {repo}, примите приглашение по ссылке из письма и запустите проверку снова. Без доступа плагин работает, но не видит решения студии (см. руководство, раздел «Без доступа к GitHub»).",
        "fix_plugin": "Установите плагин из распакованной папки: `claude plugin marketplace add \"<папка с плагином>\"`, затем `claude plugin install gamedev-studio@gamedev-studio`, и перезапустите Claude Code.",
        "fix_codex": "Не обязательно. Codex CLI нужен, только если вы работаете в Codex.",
        "fix_hindsight": "Не обязательно: плагин работает без памяти. Чтобы включить её, следуйте разделу «Память Hindsight (по желанию)» руководства.",
    },
    "en": {
        "title": "gamedev-studio: computer check (read only, installs nothing)",
        "required": "required", "optional": "optional",
        "who_claude": "Claude can do it", "who_you": "you do it",
        "fix": "Fix", "summary_ok": "Everything required is in place.",
        "summary_fail": "{n} required item(s) missing. Fix the {bad} items from the top and run the check again.",
        "claude": "Claude Code", "git": "Git", "git_bash": "Git Bash", "python": "Python",
        "gh": "GitHub CLI (gh)", "gh_auth": "Signed in to GitHub (gh auth)", "repo": "Access to the {repo} repository",
        "decisions": "Reading the decisions (issues labelled decision)", "plugin": "gamedev-studio plugin in Claude Code",
        "codex": "Codex CLI", "hindsight": "Hindsight memory server ({url})",
        "found": "found: {v}", "not_found": "not found", "too_old": "version {v}, needs {need} or newer",
        "older_than_tested": "version {v}; the guide was checked on {tested}, update if something fails",
        "store_alias": "the command exists but is the Microsoft Store alias, not Python",
        "signed_in": "signed in", "not_signed_in": "not signed in",
        "no_access": "no access (or not signed in to gh)", "access": "access granted",
        "installed": "installed, version {v}", "not_installed": "not installed",
        "unreachable": "not answering", "healthy": "answering, database connected",
        "skipped_needs": "skipped: fix \"{dep}\" first",
        "fix_claude": "Install Claude Code: in PowerShell `irm https://claude.ai/install.ps1 | iex` (no administrator rights needed), open a new terminal, run `claude` and sign in in the browser. A Pro, Max, Team, Enterprise or Console account is needed; the free claude.ai plan is not enough.",
        "fix_claude_old": "Update Claude Code: `claude update`.",
        "fix_git": "Install Git for Windows: `winget install --id Git.Git -e --source winget` (approve the Windows prompt), then restart Claude Code (a new terminal, `claude --continue`) so it sees the new program.",
        "fix_git_bash": "Git Bash comes with Git for Windows. If Git is installed elsewhere, set CLAUDE_CODE_GIT_BASH_PATH to the path of bash.exe (the env section of Claude Code's settings.json).",
        "fix_python": "Install Python 3.9 or newer: `winget install --id Python.Python.3.13 -e --source winget` (or the installer from python.org), then restart Claude Code (a new terminal, `claude --continue`). If `python` opens the Microsoft Store, turn off the \"python.exe\" aliases in Settings > Apps > App execution aliases.",
        "fix_gh": "Install the GitHub CLI: `winget install --id GitHub.cli --source winget`, then restart Claude Code (a new terminal, `claude --continue`).",
        "fix_gh_auth": "Sign in to GitHub: `gh auth login` (choose GitHub.com and the browser sign-in).",
        "fix_repo": "The repository is private. Ask the owner (ZMSkif) to give your GitHub account access to {repo}, accept the invitation from the e-mail, and run the check again. Without access the plugin works but cannot read the studio's decisions (see the guide, \"Without GitHub access\").",
        "fix_plugin": "Install the plugin from the unpacked folder: `claude plugin marketplace add \"<plugin folder>\"`, then `claude plugin install gamedev-studio@gamedev-studio`, and restart Claude Code.",
        "fix_codex": "Optional. The Codex CLI is needed only if you work in Codex.",
        "fix_hindsight": "Optional: the plugin works without memory. To turn it on, follow the guide's \"Hindsight memory (optional)\" section.",
    },
}


def allowed(argv: list[str]) -> bool:
    return any(tuple(argv[:len(prefix)]) == prefix for prefix in ALLOWED_COMMANDS)


def run(argv: list[str], timeout: float = 60.0) -> tuple[int, str]:
    """Run one allowed read-only command; (exit code, stdout + stderr). 127 when it is not on PATH."""
    if not allowed(argv):
        raise ValueError(f"doctor.py may not run {argv!r}")
    exe = shutil.which(argv[0])
    if not exe:
        return 127, ""
    try:
        done = subprocess.run([exe, *argv[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        return 126, str(exc)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def version_of(text: str) -> tuple[int, ...] | None:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    return tuple(int(g) for g in match.groups() if g is not None) if match else None


def fmt(v: tuple[int, ...]) -> str:
    return ".".join(str(n) for n in v)


def check_claude(t):
    code, out = run(["claude", "--version"])
    v = version_of(out) if code == 0 else None
    if not v:
        return False, t["not_found"], t["fix_claude"], "you"
    if v < TESTED_CLAUDE:
        return True, t["older_than_tested"].format(v=fmt(v), tested=fmt(TESTED_CLAUDE)), t["fix_claude_old"], "claude"
    return True, t["found"].format(v=fmt(v)), "", ""


def check_git(t):
    code, out = run(["git", "--version"])
    return (True, t["found"].format(v=out.strip()), "", "") if code == 0 else (False, t["not_found"], t["fix_git"], "claude")


def git_bash_path() -> Path | None:
    """Where Claude Code would find Git Bash on Windows: CLAUDE_CODE_GIT_BASH_PATH, else next to git."""
    env = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if env and Path(env).is_file():
        return Path(env)
    git = shutil.which("git")
    candidates = []
    if git:
        root = Path(git).resolve().parent.parent          # ...\Git\cmd\git.exe -> ...\Git
        candidates += [root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"), os.environ.get("LOCALAPPDATA")):
        if base:
            candidates += [Path(base) / "Git" / "bin" / "bash.exe", Path(base) / "Programs" / "Git" / "bin" / "bash.exe"]
    return next((c for c in candidates if c.is_file()), None)


def check_git_bash(t):
    if os.name == "nt":
        found = git_bash_path()
        return (True, t["found"].format(v=str(found)), "", "") if found else (False, t["not_found"], t["fix_git_bash"], "claude")
    code, out = run(["bash", "--version"])
    return (True, t["found"].format(v=out.splitlines()[0] if out else "bash"), "", "") if code == 0 else \
        (False, t["not_found"], t["fix_git_bash"], "claude")


def check_python(t):
    """The interpreter the plugin's hooks find, in their order: python, py -3, python3."""
    store_alias = False
    for argv in (["python", "-c", PY_PROBE], ["py", "-3", "-c", PY_PROBE], ["python3", "-c", PY_PROBE]):
        code, out = run(argv)
        v = version_of(out) if code == 0 else None
        if v and v >= MIN_PYTHON:
            return True, t["found"].format(v=f"{argv[0]} {fmt(v)}"), "", ""
        if v:
            return False, t["too_old"].format(v=fmt(v), need=fmt(MIN_PYTHON)), t["fix_python"], "claude"
        exe = shutil.which(argv[0]) or ""
        store_alias = store_alias or "WindowsApps" in exe
    return False, (t["store_alias"] if store_alias else t["not_found"]), t["fix_python"], "claude"


def check_gh(t):
    code, out = run(["gh", "--version"])
    return (True, t["found"].format(v=(out.splitlines() or [""])[0]), "", "") if code == 0 else \
        (False, t["not_found"], t["fix_gh"], "claude")


def check_gh_auth(t):
    code, _ = run(["gh", "auth", "status"])
    return (True, t["signed_in"], "", "") if code == 0 else (False, t["not_signed_in"], t["fix_gh_auth"], "you")


def check_repo(t, repo):
    code, _ = run(["gh", "repo", "view", repo, "--json", "name"])
    return (True, t["access"], "", "") if code == 0 else \
        (False, t["no_access"], t["fix_repo"].format(repo=repo), "you")


def check_decisions(t, repo):
    code, out = run(["gh", "issue", "list", "-R", repo, "--label", "decision", "--limit", "1", "--json", "number"])
    ok = code == 0 and out.strip().startswith("[") and out.strip() != "[]"
    return (True, t["access"], "", "") if ok else (False, t["no_access"], t["fix_repo"].format(repo=repo), "you")


def check_plugin(t):
    code, out = run(["claude", "plugin", "list", "--json"])
    try:
        items = json.loads(out) if code == 0 else []
    except ValueError:
        items = []
    entry = next((i for i in items if isinstance(i, dict) and i.get("id") == PLUGIN_ID), None)
    if entry:
        return True, t["installed"].format(v=entry.get("version", "?")), "", ""
    return False, t["not_installed"], t["fix_plugin"], "claude"


def check_codex(t):
    code, out = run(["codex", "--version"])
    return (True, t["found"].format(v=out.strip()), "", "") if code == 0 else (False, t["not_found"], t["fix_codex"], "you")


def check_hindsight(t, url):
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
        ok = isinstance(body, dict) and body.get("database") == "connected"
    except (urllib.error.URLError, OSError, ValueError):
        ok = False
    return (True, t["healthy"], "", "") if ok else (False, t["unreachable"], t["fix_hindsight"], "you")


def checks(lang: str, repo: str, hindsight: str | None) -> list[dict]:
    """Run every check in install order; a check whose prerequisite failed is skipped, not guessed."""
    t = TEXT[lang]
    plan = [
        ("claude", True, None, lambda: check_claude(t)),
        ("git", True, None, lambda: check_git(t)),
        ("git_bash", True, None, lambda: check_git_bash(t)),
        ("python", True, None, lambda: check_python(t)),
        ("gh", True, None, lambda: check_gh(t)),
        ("gh_auth", True, "gh", lambda: check_gh_auth(t)),
        ("repo", True, "gh_auth", lambda: check_repo(t, repo)),
        ("decisions", True, "repo", lambda: check_decisions(t, repo)),
        ("plugin", True, "claude", lambda: check_plugin(t)),
        ("codex", False, None, lambda: check_codex(t)),
    ]
    if hindsight:
        plan.append(("hindsight", False, None, lambda: check_hindsight(t, hindsight)))
    results: dict[str, dict] = {}
    for key, required, needs, func in plan:
        label = t[key].format(repo=repo, url=hindsight or "")
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
    out = [t["title"], ""]
    for r in rows:
        mark = good if r["ok"] else (skip if r["skipped"] else bad)
        kind = t["required"] if r["required"] else t["optional"]
        out.append(f"{mark} {r['label']} ({kind}): {r['detail']}")
        if r["fix"] and (not r["ok"] or r["detail"].startswith(("версия", "version"))):
            who = t["who_claude"] if r["who"] == "claude" else t["who_you"]
            out.append(f"    {t['fix']} [{who}]: {r['fix']}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only check of what gamedev-studio needs (installs nothing).")
    parser.add_argument("--lang", choices=sorted(TEXT), default="ru")
    parser.add_argument("--json", action="store_true", help="print the results as JSON")
    parser.add_argument("--repo", default=REPO, help="the plugin repository whose access is checked")
    parser.add_argument("--hindsight", nargs="?", const="http://127.0.0.1:8888", default=None, metavar="URL",
                        help="also check the optional Hindsight memory server (default URL http://127.0.0.1:8888)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # a piped Windows console is cp1251: never crash on a character
    rows = checks(args.lang, args.repo, args.hindsight)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2) if marks_for(sys.stdout)[0] == "✅" else json.dumps(rows, indent=2))
    else:
        print(render(rows, args.lang, marks_for(sys.stdout)), end="")
    return 1 if any(r["required"] and not r["ok"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
