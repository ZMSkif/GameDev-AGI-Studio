#!/usr/bin/env python3
"""Optional tools of GameDev Studio: status, install, enable and configure, driven by tools/catalog.json.

The same functions serve the studio panel (scripts/studio_panel.py) and the chat flow
(the setup-tools command). Rules that hold everywhere:

  * only the exact argument lists in the catalog are started, never a shell string;
  * a tool is installed only when its catalog entry says Claude may (``who: claude_yes``) and the
    caller passed an explicit yes; tools for the person or the owner only show their instructions;
  * paid services are never used here: only their free client libraries are installed, and the
    person's own key is written to the game's ignored ``.env``;
  * the owner's tools (memory) are enabled only with the GitHub link of the owner's decision;
  * secrets are never printed, returned or written anywhere but ``.env``.

Usage:
  python scripts/studio_tools.py status [--json] [--lang ru|en] [--game DIR]
  python scripts/studio_tools.py install ID --yes [--game DIR]
  python scripts/studio_tools.py enable ID [--off] [--decision URL] [--game DIR]
  python scripts/studio_tools.py set ID KEY VALUE [--game DIR]
  python scripts/studio_tools.py set-secret ID KEY [--game DIR]   (asks for the value without echo)
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CATALOG = PLUGIN_ROOT / "tools" / "catalog.json"
MARKER = ".gamedev-studio"
SETTINGS_NAME = ".gamedev-studio.json"
WHO = {"claude_yes", "person", "owner"}
SCOPES = {"machine", "game"}
COSTS = {"free", "paid", "account"}
DETECTS = {"which", "python_module", "playwright_browser", "git_checkout", "http_health", "claude_plugin",
           "skill_folder", "none"}
COMMERCIAL = {"ok", "outputs_ok", "non_commercial", "check"}
CONFIG_KINDS = {"secret": "env", "url": "settings", "path": "settings"}
PLATFORMS = {"win32": "windows", "darwin": "darwin"}
PLATFORM_KEYS = {"windows", "darwin", "linux"}
PREREQ_CHECKS = {"which", "program_version", "python_version", "msvc", "platform", "nvidia_gpu", "tool", "manual"}
PREREQ_WHO = {"claude_yes", "person"}
PREREQ_FOR = ("install", "use")
TOKENS = {"{python}", "{game}", "{pip_user}", "{tools}"}
REFERENCE_LEDGER = ".gamedev-studio-reference-only.json"
LICENCE_URL = re.compile(r"^https://[^\s]+$")


def tools_home():
    """Machine-wide folder for third-party tools the studio installs from their own sources."""
    return Path(os.environ.get("GAMEDEV_STUDIO_TOOLS") or Path.home() / ".gamedev-studio" / "tools")


def expand(value, game, python=None):
    """Fill the catalog tokens. A path that starts with {tools} or {game} gets this system's separators,
    so Windows sees C:\\...\\tools\\Motion2MixamoRig\\.venv rather than a mixed C:\\...\\tools/Motion2MixamoRig/.venv."""
    text = (value.replace("{python}", python or sys.executable).replace("{game}", str(Path(game)))
            .replace("{tools}", str(tools_home())))
    if value.startswith(("{tools}", "{game}")):
        text = os.path.normpath(text)
    return text


DECISION_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(issues|pull)/\d+(#[A-Za-z0-9_-]+)?$")
ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
TEXT = {
    "en": {"installed": "installed", "missing": "not installed", "pending": "waiting for a decision",
           "configured": "key saved", "no_key": "key not set", "owner_only": "owner's decision",
           "found": "found: {p}", "commit_mismatch": "checkout at another commit ({c})",
           "unreachable": "not answering", "healthy": "answering", "no_url": "no URL set",
           "browser_custom": "uses {p}", "browser_found": "Chromium in {p}",
           "not_detected": "not checked automatically: see its own setup",
           "incomplete": "install did not finish: {p} is missing",
           "not_needed_here": "not needed on this system", "check_yourself": "check it yourself",
           "version_low": "{p} is version {v}, needs {m}+", "version_unknown": "{p}: version not read",
           "platform_only": "needs {p}", "no_gpu": "no NVIDIA GPU found (nvidia-smi)",
           "gpu_small": "NVIDIA GPU with {v} GB, needs {m} GB", "gpu_found": "NVIDIA GPU, {v} GB",
           "msvc_found": "C++ build tools in {p}", "met": "ready",
           "needs_install": "to install", "needs_use": "to use",
           "prereq_by_claude": "Claude after your yes: {c}", "prereq_by_person": "you: {m}",
           "prereqs_missing": "{t} needs these first ({f}):"},
    "ru": {"installed": "установлено", "missing": "не установлено", "pending": "ждёт решения",
           "configured": "ключ сохранён", "no_key": "ключ не задан", "owner_only": "решение владельца",
           "found": "найдено: {p}", "commit_mismatch": "в папке другой коммит ({c})",
           "unreachable": "не отвечает", "healthy": "отвечает", "no_url": "адрес не задан",
           "browser_custom": "используется {p}", "browser_found": "Chromium в {p}",
           "not_detected": "автоматически не проверяется: см. его установку",
           "incomplete": "установка не закончена: нет {p}",
           "not_needed_here": "на этой системе не нужно", "check_yourself": "проверьте сами",
           "version_low": "{p} версии {v}, нужна {m}+", "version_unknown": "{p}: версию прочитать не удалось",
           "platform_only": "нужна система {p}", "no_gpu": "видеокарта NVIDIA не найдена (nvidia-smi)",
           "gpu_small": "видеокарта NVIDIA на {v} ГБ, нужно {m} ГБ", "gpu_found": "видеокарта NVIDIA, {v} ГБ",
           "msvc_found": "C++ Build Tools в {p}", "met": "есть",
           "needs_install": "для установки", "needs_use": "для работы",
           "prereq_by_claude": "Claude после вашего «да»: {c}", "prereq_by_person": "вы: {m}",
           "prereqs_missing": "{t}: сначала нужно ({f}):"},
}


class ToolError(ValueError):
    """A request the catalog or the rules do not allow."""


# ---------------------------------------------------------------- catalog

def _localized(value, name):
    if not isinstance(value, dict) or set(value) != {"ru", "en"} or not all(isinstance(v, str) and v.strip() for v in value.values()):
        raise ValueError(f"{name} needs non-empty 'ru' and 'en' texts")


def _validate_steps(owner, key, argv, allow_copy=True):
    """One install spec: a single argument list or a list of steps (argument lists or copy_skills)."""
    steps = argv if isinstance(argv, list) and argv and all(isinstance(a, (list, dict)) for a in argv) else [argv]
    for step in steps:
        if isinstance(step, dict):
            if not allow_copy or set(step) != {"copy_skills"} or not isinstance(step["copy_skills"], list) \
                    or len(step["copy_skills"]) != 2:
                raise ValueError(f"{owner}: a non-command step must be {{\"copy_skills\": [from, to]}}")
            continue
        if not isinstance(step, list) or not step or not all(isinstance(a, str) and a for a in step):
            raise ValueError(f"{owner}: install.{key} must be a list of arguments or a list of steps")
        if any(re.search(r"[;&|`$]", a) and a not in TOKENS for a in step):
            raise ValueError(f"{owner}: install.{key} contains shell syntax")
        if step[0] in {"sh", "bash", "cmd", "powershell", "pwsh", "iex"} or "|" in step:
            raise ValueError(f"{owner}: install.{key} must not start a shell")


def validate_prerequisites(data, tool_ids):
    """The shared list of what tools need before they can be installed or used (see reference/external-tools.md)."""
    seen = set()
    for pre in data.get("prerequisites", []):
        pid = pre.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", pid) or pid in seen:
            raise ValueError(f"prerequisite id {pid!r} must be unique kebab-case")
        seen.add(pid)
        if not isinstance(pre.get("name"), str) or not pre["name"].strip():
            raise ValueError(f"prerequisite {pid}: name is required")
        _localized(pre.get("why"), f"prerequisite {pid}.why")
        if pre.get("who") not in PREREQ_WHO:
            raise ValueError(f"prerequisite {pid}: who must be one of {sorted(PREREQ_WHO)}")
        if not set(pre.get("platforms", [])) <= PLATFORM_KEYS:
            raise ValueError(f"prerequisite {pid}: unknown platform")
        check = pre.get("check", {})
        kind = check.get("type")
        if kind not in PREREQ_CHECKS:
            raise ValueError(f"prerequisite {pid}: check.type must be one of {sorted(PREREQ_CHECKS)}")
        if kind in {"which", "program_version"} and not (isinstance(check.get("names"), list) and check["names"]):
            raise ValueError(f"prerequisite {pid}: check.names lists the program names")
        if kind in {"program_version", "python_version"} and not re.fullmatch(r"\d+(\.\d+){0,2}", str(check.get("min", ""))):
            raise ValueError(f"prerequisite {pid}: check.min is a version such as 3.11")
        if kind == "platform" and not (set(check.get("platforms", [])) and set(check["platforms"]) <= PLATFORM_KEYS):
            raise ValueError(f"prerequisite {pid}: check.platforms lists the systems it needs")
        if kind == "tool" and check.get("tool") not in tool_ids:
            raise ValueError(f"prerequisite {pid}: check.tool names a catalog tool")
        install = pre.get("install", {})
        for key, argv in install.items():
            if key == "tool":
                if argv not in tool_ids:
                    raise ValueError(f"prerequisite {pid}: install.tool names a catalog tool")
                continue
            if key not in PLATFORM_KEYS | {"all"}:
                raise ValueError(f"prerequisite {pid}: unknown install platform {key}")
            _validate_steps(f"prerequisite {pid}", key, argv, allow_copy=False)
        if install and pre["who"] != "claude_yes":
            raise ValueError(f"prerequisite {pid}: only claude_yes prerequisites may carry install commands")
        if pre["who"] == "claude_yes" and not install:
            raise ValueError(f"prerequisite {pid}: a claude_yes prerequisite needs install commands or install.tool")
        if pre["who"] == "person" or set(install) - {"tool"} and set(install) != {"all"}:
            _localized(pre.get("manual"), f"prerequisite {pid}.manual")
    return seen


def validate_catalog(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("catalog version must be 1")
    prerequisite_ids = validate_prerequisites(data, {tool.get("id") for tool in data.get("tools", [])})
    groups = {group["id"] for group in data.get("groups", [])}
    for group in data.get("groups", []):
        _localized(group.get("name"), f"group {group.get('id')}")
    seen = set()
    for tool in data.get("tools", []):
        tid = tool.get("id")
        if not isinstance(tid, str) or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", tid) or tid in seen:
            raise ValueError(f"tool id {tid!r} must be unique kebab-case")
        seen.add(tid)
        if tool.get("group") not in groups:
            raise ValueError(f"{tid}: unknown group")
        for key in ("name", "licence", "source"):
            if not isinstance(tool.get(key), str) or not tool[key].strip():
                raise ValueError(f"{tid}: {key} is required")
        if not tool["source"].startswith("https://"):
            raise ValueError(f"{tid}: source must be an https URL")
        _localized(tool.get("gives"), f"{tid}.gives")
        if tool.get("cost", {}).get("kind") not in COSTS:
            raise ValueError(f"{tid}: cost.kind must be one of {sorted(COSTS)}")
        if tool["cost"]["kind"] != "free":
            _localized(tool["cost"].get("note"), f"{tid}.cost.note")
        if tool.get("who") not in WHO or tool.get("scope") not in SCOPES:
            raise ValueError(f"{tid}: who or scope is invalid")
        if tool.get("detect", {}).get("type") not in DETECTS:
            raise ValueError(f"{tid}: unknown detect type")
        for need in tool.get("requires", []):
            if need not in {other.get("id") for other in data["tools"]}:
                raise ValueError(f"{tid}: requires unknown tool {need}")
        if "requires_programs" in tool:
            raise ValueError(f"{tid}: requires_programs is replaced by prerequisites.install")
        needs = tool.get("prerequisites", {})
        if not isinstance(needs, dict) or not set(needs) <= set(PREREQ_FOR):
            raise ValueError(f"{tid}: prerequisites has the lists 'install' and 'use'")
        for when, ids in needs.items():
            if not isinstance(ids, list) or len(set(ids)) != len(ids) or not set(ids) <= prerequisite_ids:
                raise ValueError(f"{tid}: prerequisites.{when} must list known prerequisite ids once each")
        verify = tool.get("detect", {}).get("verify", {})
        if not isinstance(verify, dict) or not set(verify) <= PLATFORM_KEYS | {"all"} or \
                not all(isinstance(paths, list) and paths and all(isinstance(p, str) and p for p in paths)
                        for paths in verify.values()):
            raise ValueError(f"{tid}: detect.verify maps platforms to the files a finished install leaves")
        known = tool.get("detect", {}).get("known_paths", {})
        if not isinstance(known, dict) or not set(known) <= PLATFORM_KEYS or \
                not all(isinstance(paths, list) and all(isinstance(p, str) and p for p in paths) for paths in known.values()):
            raise ValueError(f"{tid}: detect.known_paths maps platforms to program paths (globs allowed)")
        install = tool.get("install", {})
        for key, argv in install.items():
            if key == "manual":
                _localized(argv, f"{tid}.install.manual")
                continue
            if key not in {"all", "windows", "darwin", "linux"}:
                raise ValueError(f"{tid}: unknown install platform {key}")
            _validate_steps(tid, key, argv)
            if tool["who"] != "claude_yes":
                raise ValueError(f"{tid}: only claude_yes tools may carry install commands")
        if tool["who"] != "claude_yes" and "manual" not in install and tool.get("status") != "pending_decision":
            raise ValueError(f"{tid}: a tool for the person or owner needs manual instructions")
        for item in tool.get("config", []):
            if item.get("kind") not in CONFIG_KINDS or item.get("target") != CONFIG_KINDS[item["kind"]]:
                raise ValueError(f"{tid}: config {item.get('key')} has an invalid kind or target")
            if item["kind"] == "secret" and not ENV_KEY.fullmatch(item.get("key", "")):
                raise ValueError(f"{tid}: secret key names are upper-case environment names")
            _localized(item.get("label"), f"{tid}.config.label")
        if tool["cost"]["kind"] == "paid" and not tool.get("account"):
            raise ValueError(f"{tid}: a paid tool needs an account")
        for item in tool.get("licence_gate", []):
            _localized(item, f"{tid}.licence_gate")
        if tool.get("licence_gate") and tool.get("commercial") != "non_commercial":
            raise ValueError(f"{tid}: a licence gate belongs to a non-commercial tool")
        if tool.get("commercial", "ok") not in COMMERCIAL:
            raise ValueError(f"{tid}: commercial must be one of {sorted(COMMERCIAL)}")
        if tool.get("commercial", "ok") != "ok":
            _localized(tool.get("licence_note"), f"{tid}.licence_note")
        for key in ("licence_note", "requirements"):
            if key in tool:
                _localized(tool[key], f"{tid}.{key}")
    if not seen:
        raise ValueError("catalog has no tools")
    return data


def load_catalog(path=CATALOG):
    return validate_catalog(json.loads(Path(path).read_text(encoding="utf-8")))


def tool_by_id(catalog, tid):
    for tool in catalog["tools"]:
        if tool["id"] == tid:
            return tool
    raise ToolError(f"Unknown tool: {tid}")


# ---------------------------------------------------------------- game folder and settings

def find_game(start=None):
    """The nearest folder with the .gamedev-studio marker, else the start folder itself."""
    current = Path(start or os.getcwd()).resolve()
    for folder in (current, *current.parents):
        if (folder / MARKER).is_file():
            return folder
    return current


def load_settings(game):
    path = Path(game) / SETTINGS_NAME
    if not path.is_file():
        return {"version": 1, "tools": {}, "settings": {}, "qa": {"scenarios": "qa", "reports": "qa-reports"}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("tools", {})
    data.setdefault("settings", {})
    data.setdefault("qa", {"scenarios": "qa", "reports": "qa-reports"})
    return data


def save_settings(game, data):
    path = Path(game) / SETTINGS_NAME
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def ensure_gitignore(game, entries):
    """Append missing entries to the game's .gitignore. Returns the entries added."""
    path = Path(game) / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    present = {line.strip() for line in lines}
    added = [entry for entry in entries if entry not in present and entry.rstrip("/") not in present]
    if added:
        text = "\n".join(lines).rstrip("\n")
        text = (text + "\n" if text else "") + "\n".join(added) + "\n"
        path.write_text(text, encoding="utf-8")
    return added


def read_env(game):
    path = Path(game) / ".env"
    values = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def secret_present(game, key):
    return bool(read_env(game).get(key))


# ---------------------------------------------------------------- detection

def _which_all(names):
    found = [shutil.which(name) for name in names]
    return found if all(found) else None


def known_program(patterns):
    """The newest existing file among the platform's known install paths (globs; %VAR% and ~ expanded).

    Installers such as winget's Blender MSI do not add the program to PATH, so PATH alone misses it."""
    hits = []
    for pattern in patterns:
        expanded = os.path.expanduser(os.path.expandvars(pattern))
        if "%" in expanded:
            continue  # an environment variable this system does not have
        anchor = Path(expanded).anchor
        relative = expanded[len(anchor):] if anchor else expanded
        base = Path(anchor) if anchor else Path(".")
        hits += [path for path in base.glob(relative.replace("\\", "/")) if path.is_file()]
    return str(sorted(hits, key=lambda path: str(path))[-1]) if hits else None


def find_program(names, known_paths=None):
    """A program on PATH under one of its names, else in a known install folder of this platform."""
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return known_program((known_paths or {}).get(platform_key(), []))


def program_version(path, args=None, timeout=20):
    try:
        result = subprocess.run([path, *(args or ["--version"])], capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or b"") + b"\n" + (result.stderr or b"")
    return version_tuple(output.decode("utf-8", errors="replace"))


def version_tuple(text):
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(part or 0) for part in match.groups()) if match else None


def version_text(parts):
    return ".".join(str(part) for part in parts)


def at_least(found, minimum):
    wanted = tuple(int(part) for part in str(minimum).split("."))
    return found is not None and found[:len(wanted)] >= wanted


def vswhere_vc_tools():
    """Visual Studio (Build Tools) with the C++ x64 compiler, found the way Microsoft documents: vswhere."""
    root = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles") or r"C:\Program Files (x86)"
    vswhere = Path(root) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if vswhere.is_file():
        try:
            result = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
                                     "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                                    capture_output=True, timeout=30, check=False)
            found = result.stdout.decode("utf-8", errors="replace").strip().splitlines()
            if result.returncode == 0 and found:
                return found[0].strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return shutil.which("cl")


def nvidia_vram_gb():
    """Largest NVIDIA GPU memory in GB, or None without nvidia-smi."""
    smi = shutil.which("nvidia-smi")
    if not smi:
        return None
    try:
        result = subprocess.run([smi, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                                capture_output=True, timeout=20, check=False)
        values = [int(line.strip()) for line in result.stdout.decode("ascii", errors="replace").splitlines()
                  if line.strip().isdigit()]
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return round(max(values) / 1024, 1) if values else None


def python_has(module, python=None):
    result = subprocess.run([python or sys.executable, "-c",
                             "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)", module],
                            capture_output=True, timeout=30, check=False)
    return result.returncode == 0


def playwright_browser_dirs():
    custom = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if custom and custom != "0":
        return [Path(custom)]
    home = Path.home()
    if sys.platform == "win32":
        return [Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "ms-playwright"]
    if sys.platform == "darwin":
        return [home / "Library" / "Caches" / "ms-playwright"]
    return [home / ".cache" / "ms-playwright"]


def git_head(path):
    head = Path(path) / ".git" / "HEAD"
    if not head.is_file():
        return None
    value = head.read_text(encoding="utf-8").strip()
    if value.startswith("ref:"):
        ref = Path(path) / ".git" / value.split(":", 1)[1].strip()
        return ref.read_text(encoding="utf-8").strip() if ref.is_file() else None
    return value


def detect(tool, game, settings, lang="en"):
    """Return (installed, detail) for one tool, reading only the filesystem and PATH (and /health).

    A tool whose detect rule has ``verify`` counts as installed only when the files a finished install
    leaves are there (for example the program inside a tool's own virtualenv): a folder alone is not proof."""
    installed, detail = _detect(tool, game, settings, lang)
    if installed:
        verify = tool["detect"].get("verify", {})
        for path in verify.get(platform_key()) or verify.get("all") or []:
            full = Path(expand(path, game))
            full = full if full.is_absolute() else Path(game) / full
            if not full.exists():
                return False, TEXT[lang]["incomplete"].format(p=full)
    return installed, detail


def _detect(tool, game, settings, lang="en"):
    text = TEXT[lang]
    rule = tool["detect"]
    kind = rule["type"]
    if kind == "none":
        return False, text["pending"] if tool.get("status") == "pending_decision" else text["not_detected"]
    if kind == "which":
        found = _which_all(rule["names"]) or next((p for p in (shutil.which(n) for n in rule.get("alternatives", [])) if p), None)
        if found:
            path = found[0] if isinstance(found, list) else found
            return True, text["found"].format(p=path)
        path = known_program(rule.get("known_paths", {}).get(platform_key(), []))
        if path:
            return True, text["found"].format(p=path)
        return False, text["missing"]
    if kind == "python_module":
        if not python_has(rule["module"]):
            return False, text["missing"]
        if rule.get("secret"):
            return True, text["configured"] if secret_present(game, rule["secret"]) else text["no_key"]
        return True, text["installed"]
    if kind == "playwright_browser":
        custom = settings.get("settings", {}).get(rule.get("or_setting", ""), "")
        if custom and Path(custom).is_file():
            return True, text["browser_custom"].format(p=custom)
        for folder in playwright_browser_dirs():
            hits = sorted(folder.glob(f"{rule['browser']}-*")) if folder.is_dir() else []
            if hits:
                return True, text["browser_found"].format(p=hits[-1])
        return False, text["missing"]
    if kind == "git_checkout":
        path = Path(expand(rule["path"], game))
        path = path if path.is_absolute() else Path(game) / path
        head = git_head(path)
        if head is None:
            return False, text["missing"]
        if head != rule["commit"]:
            return False, text["commit_mismatch"].format(c=head[:12])
        return True, text["found"].format(p=path)
    if kind == "claude_plugin":
        base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
        try:
            plugins = json.loads((base / "plugins" / "installed_plugins.json").read_text(encoding="utf-8-sig")).get("plugins", {})
        except (OSError, ValueError, AttributeError):
            plugins = {}
        return (True, text["installed"]) if isinstance(plugins, dict) and plugins.get(rule["plugin"]) else (False, text["missing"])
    if kind == "skill_folder":
        path = Path(game) / rule["path"]
        if not (path / "SKILL.md").is_file() and not any(path.glob("*/SKILL.md")):
            return False, text["missing"]
        head = git_head(path) if rule.get("commit") else None
        if rule.get("commit") and head and head != rule["commit"]:
            return False, text["commit_mismatch"].format(c=head[:12])
        return True, text["found"].format(p=path)
    if kind == "http_health":
        url = settings.get("settings", {}).get(rule["setting"], "")
        if not url:
            return False, text["no_url"]
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=3) as response:
                body = json.loads(response.read().decode("utf-8") or "{}")
            ok = isinstance(body, dict) and body.get("database") == "connected"
        except (urllib.error.URLError, OSError, ValueError):
            ok = False
        return ok, text["healthy"] if ok else text["unreachable"]
    raise ValueError(kind)


# ---------------------------------------------------------------- prerequisites

class PrerequisiteError(ToolError):
    """A tool cannot be installed yet: something it needs is missing. ``rows`` says what and who installs it."""

    def __init__(self, message, rows):
        super().__init__(message)
        self.rows = rows


def prerequisite_by_id(catalog, pid):
    for pre in catalog.get("prerequisites", []):
        if pre["id"] == pid:
            return pre
    raise ToolError(f"Unknown prerequisite: {pid}")


def prerequisite_steps(pre, catalog, game, python=None):
    """The exact commands Claude would run for a claude_yes prerequisite here, or None (person, or no command here)."""
    if pre["who"] != "claude_yes":
        return None
    install = pre.get("install", {})
    if "tool" in install:
        return install_steps(tool_by_id(catalog, install["tool"]), game, python)
    spec = install.get(platform_key()) or install.get("all")
    if not spec:
        return None
    steps = spec if all(isinstance(item, list) for item in spec) else [spec]
    return [[expand(arg, game, python) for arg in step] for step in steps]


def check_prerequisite(pre, catalog, game, settings, lang="en", python=None):
    """(met, detail): met is True, False, or None when only the person can check it."""
    text = TEXT[lang]
    if pre.get("platforms") and platform_key() not in pre["platforms"]:
        return True, text["not_needed_here"]
    check = pre["check"]
    kind = check["type"]
    if kind == "manual":
        return None, text["check_yourself"]
    if kind == "platform":
        if platform_key() in check["platforms"]:
            return True, text["met"]
        return False, text["platform_only"].format(p=", ".join(check["platforms"]))
    if kind == "which":
        path = find_program(check["names"], check.get("known_paths"))
        return (True, text["found"].format(p=path)) if path else (False, text["missing"])
    if kind == "program_version":
        path = find_program(check["names"], check.get("known_paths"))
        if not path:
            return False, text["missing"]
        found = program_version(path, check.get("args"))
        if found is None:
            return False, text["version_unknown"].format(p=path)
        if not at_least(found, check["min"]):
            return False, text["version_low"].format(p=path, v=version_text(found), m=check["min"])
        return True, text["found"].format(p=f"{path} {version_text(found)}")
    if kind == "python_version":
        found = tuple(sys.version_info[:3]) if not python else program_version(python)
        if not at_least(found, check["min"]):
            shown = version_text(found) if found else "?"
            return False, text["version_low"].format(p=python or sys.executable, v=shown, m=check["min"])
        return True, text["found"].format(p=f"{python or sys.executable} {version_text(found)}")
    if kind == "msvc":
        path = vswhere_vc_tools()
        return (True, text["msvc_found"].format(p=path)) if path else (False, text["missing"])
    if kind == "nvidia_gpu":
        vram = nvidia_vram_gb()
        if vram is None:
            return False, text["no_gpu"]
        if check.get("min_vram_gb") and vram < check["min_vram_gb"]:
            return False, text["gpu_small"].format(v=vram, m=check["min_vram_gb"])
        return True, text["gpu_found"].format(v=vram)
    if kind == "tool":
        tool = tool_by_id(catalog, check["tool"])
        if tool["detect"]["type"] == "none":
            return None, text["check_yourself"]
        return detect(tool, game, settings, lang)
    raise ValueError(kind)


def prerequisite_rows(tool, catalog, game, settings=None, lang="en", python=None):
    """What the tool needs, for install and for use, each with its state and who installs it."""
    settings = settings if settings is not None else load_settings(game)
    rows = []
    for when in PREREQ_FOR:
        for pid in tool.get("prerequisites", {}).get(when, []):
            pre = prerequisite_by_id(catalog, pid)
            met, detail = check_prerequisite(pre, catalog, game, settings, lang, python)
            steps = prerequisite_steps(pre, catalog, game, python)
            rows.append({
                "id": pid, "name": pre["name"], "for": when, "met": met, "detail": detail, "who": pre["who"],
                "why": pre["why"][lang], "install_steps": steps,
                "command": f"python scripts/studio_tools.py prereq {pid} --yes" if steps else "",
                "manual": pre.get("manual", {}).get(lang, ""),
            })
    return rows


def describe_missing(tool, rows, when, lang="en"):
    text = TEXT[lang]
    label = text["needs_install"] if when == "install" else text["needs_use"]
    lines = [text["prereqs_missing"].format(t=tool["id"], f=label)]
    for row in rows:
        how = (text["prereq_by_claude"].format(c=row["command"]) if row["command"]
               else text["prereq_by_person"].format(m=row["manual"] or row["why"]))
        lines.append(f"  - {row['name']} ({row['detail']}): {row['why']} {how}")
    return "\n".join(lines)


def install_prerequisite(catalog, pid, game, yes, on_line=None, python=None, lang="en"):
    """Install one claude_yes prerequisite after an explicit yes; the person's ones only show instructions."""
    if not yes:
        raise ToolError("Installing needs an explicit yes from the person")
    pre = prerequisite_by_id(catalog, pid)
    if pre["who"] != "claude_yes":
        raise ToolError(f"{pid}: {pre.get('manual', {}).get(lang) or pre['why'][lang]}")
    if "tool" in pre.get("install", {}):
        return install(tool_by_id(catalog, pre["install"]["tool"]), game, yes, on_line, python, catalog=catalog, lang=lang)
    steps = prerequisite_steps(pre, catalog, game, python)
    if not steps:
        raise ToolError(f"{pid}: {pre.get('manual', {}).get(lang) or pre['why'][lang]}")
    code = _run_steps(steps, game, on_line or (lambda line: None))
    return {"returncode": code, "argv": steps[-1], "steps": steps, "gitignore_added": []}


# ---------------------------------------------------------------- install

def platform_key():
    return PLATFORMS.get(sys.platform, "linux")


def resolve_program(name):
    """The program a command name starts. On Windows, an extensionless file with the same name earlier on PATH
    (for example an empty C:\\Windows\\System32\\winget) is skipped: only real executables count."""
    path = shutil.which(name)
    if path and sys.platform == "win32" and not Path(path).suffix:
        path = next((found for found in (shutil.which(name + ext) for ext in
                                         os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if ext) if found), None)
    return path


def in_virtualenv():
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def install_steps(tool, game, python=None):
    """The exact argument lists this machine would run for the tool, or None when it is manual only."""
    if tool["who"] != "claude_yes":
        return None
    install = tool.get("install", {})
    spec = install.get(platform_key()) or install.get("all")
    if not spec:
        return None
    steps = spec if all(isinstance(item, (list, dict)) for item in spec) else [spec]
    result = []
    for step in steps:
        if isinstance(step, dict):
            source, target = (expand(value, game, python) for value in step["copy_skills"])
            result.append({"copy_skills": [source, target]})
            continue
        argv = []
        for arg in step:
            if arg == "{pip_user}":
                if not in_virtualenv():
                    argv.append("--user")
                continue
            argv.append(expand(arg, game, python))
        result.append(argv)
    return result


def install_command(tool, game, python=None):
    """The first install step (most tools have exactly one)."""
    steps = install_steps(tool, game, python)
    return steps[0] if steps else None


def describe_step(step):
    if isinstance(step, dict):
        source, target = step["copy_skills"]
        return f"copy every skill folder from {source} to {target}"
    return " ".join(step)


def copy_skills(source, target, on_line):
    """Copy each folder with a SKILL.md into the target, never replacing a skill that is already there."""
    source, target = Path(source), Path(target)
    if not source.is_dir():
        on_line(f"missing {source}")
        return 1
    target.mkdir(parents=True, exist_ok=True)
    for folder in sorted(source.iterdir()):
        if not (folder / "SKILL.md").is_file():
            continue
        destination = target / folder.name
        if destination.exists():
            on_line(f"kept existing {destination.name}")
            continue
        shutil.copytree(folder, destination)
        on_line(f"added skill {destination.name}")
    return 0


def manual_text(tool, lang):
    manual = tool.get("install", {}).get("manual")
    return manual[lang] if manual else ""


def step_environment():
    """The environment for install commands.

    On Windows, Visual Studio's vcvarsall.bat calls vswhere.exe by name, and the Build Tools installer does not
    add its folder to PATH (nor does a session started before the install see a new PATH). Then vcvarsall prints
    an error into the output setuptools parses, and every C/C++ build fails with "Unable to find a compatible
    Visual Studio installation" although the compiler is installed. The installer folder is added here."""
    env = dict(os.environ)
    if sys.platform == "win32":
        # os.environ, not the copy: on Windows only os.environ looks names up without regard to case
        root = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles") or r"C:\Program Files (x86)"
        installer = Path(root) / "Microsoft Visual Studio" / "Installer"
        paths = env.get("PATH", "").split(os.pathsep)
        if (installer / "vswhere.exe").is_file() and str(installer).lower() not in {p.lower().rstrip("\\") for p in paths}:
            env["PATH"] = os.pathsep.join([*paths, str(installer)])
    return env


def _run_steps(steps, game, on_line):
    """Run argument lists and copy_skills steps in order; stop at the first failure. Returns the exit code."""
    code = 0
    env = step_environment()
    tools_home().mkdir(parents=True, exist_ok=True)
    for argv in steps:
        if isinstance(argv, dict):
            on_line("· " + describe_step(argv))
            code = copy_skills(*argv["copy_skills"], on_line)
            if code != 0:
                break
            continue
        if len(argv) >= 4 and argv[:2] == ["git", "clone"] and (Path(argv[-1]) / ".git").is_dir():
            on_line(f"· {argv[-1]}: already cloned, the next step pins the commit")
            continue  # a retry after a failed later step: git clone refuses an existing folder
        on_line("$ " + " ".join(argv))
        program = argv[0] if Path(argv[0]).is_file() else (resolve_program(argv[0]) or argv[0])
        process = subprocess.Popen([program, *argv[1:]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", errors="replace", cwd=str(game), env=env)
        for line in process.stdout:
            on_line(line.rstrip("\n"))
        code = process.wait()
        if code != 0:
            break
    return code


def install(tool, game, yes, on_line=None, python=None, catalog=None, with_prerequisites=False, lang="en"):
    """Run the catalog command for a free tool after an explicit yes. Returns a result dict.

    Everything the tool lists under ``prerequisites.install`` is checked before the first command runs.
    A missing one stops the install with PrerequisiteError naming it and who installs it; with
    ``with_prerequisites`` (the person said yes to those too) Claude's own ones are installed first."""
    if not yes:
        raise ToolError("Installing needs an explicit yes from the person")
    if tool.get("status") == "pending_decision":
        raise ToolError(f"{tool['id']} waits for a decision and cannot be installed yet")
    steps = install_steps(tool, game, python)
    if steps is None:
        raise ToolError(f"{tool['id']} is installed by the person or the owner: follow its instructions")
    catalog = catalog or load_catalog()
    on_line = on_line or (lambda line: None)
    missing = [row for row in prerequisite_rows(tool, catalog, game, lang=lang, python=python)
               if row["for"] == "install" and row["met"] is False]
    if missing and with_prerequisites:
        for row in missing:
            if row["install_steps"]:
                on_line(f"· {row['name']}")
                result = install_prerequisite(catalog, row["id"], game, True, on_line, python, lang)
                if result["returncode"] != 0:
                    return {**result, "prerequisite": row["id"]}
        missing = [row for row in prerequisite_rows(tool, catalog, game, lang=lang, python=python)
                   if row["for"] == "install" and row["met"] is False]
    if missing:
        raise PrerequisiteError(describe_missing(tool, missing, "install", lang), missing)
    for argv in steps:
        if isinstance(argv, dict) or str(tools_home()) in argv[0]:
            continue  # copied skills, or a program an earlier step creates (a tool's own virtualenv)
        if not Path(argv[0]).is_file() and not resolve_program(argv[0]):
            raise ToolError(f"{argv[0]} is not available on this computer; install the tool by hand")
    code = _run_steps(steps, game, on_line)
    if code == 0 and tool["detect"].get("verify"):
        finished, detail = detect(tool, game, load_settings(game), lang)
        if not finished:
            on_line(detail)
            code = 1
    argv = steps[-1] if isinstance(steps[-1], list) else []
    added = []
    if code == 0 and tool.get("gitignore"):
        added = ensure_gitignore(game, tool["gitignore"])
        if added:
            on_line(".gitignore: + " + ", ".join(added))
    return {"returncode": code, "argv": argv, "steps": steps, "gitignore_added": added}


# ---------------------------------------------------------------- enable and configure

def set_enabled(catalog, game, tid, enabled, decision=None):
    tool = tool_by_id(catalog, tid)
    if tool.get("status") == "pending_decision" and enabled:
        raise ToolError(f"{tid} waits for a decision")
    entry = {"enabled": bool(enabled)}
    if tool["who"] == "owner" and enabled:
        if not decision or not DECISION_URL.fullmatch(decision):
            raise ToolError(f"{tid} is the owner's decision: give the GitHub link where the owner turned it on")
        entry["decision"] = decision
    data = load_settings(game)
    data["tools"][tid] = {**data["tools"].get(tid, {}), **entry}
    save_settings(game, data)
    return data["tools"][tid]


def config_item(tool, key):
    for item in tool.get("config", []):
        if item["key"] == key:
            return item
    raise ToolError(f"{tool['id']} has no setting {key}")


def set_setting(catalog, game, tid, key, value):
    tool = tool_by_id(catalog, tid)
    item = config_item(tool, key)
    if item["kind"] == "secret":
        raise ToolError("Secrets go through set-secret")
    value = (value or "").strip()
    if value and item["kind"] == "url" and not re.fullmatch(r"https?://[^\s]+", value):
        raise ToolError("Expected an http(s) URL")
    if value and item["kind"] == "path" and not Path(value).is_file():
        raise ToolError("That file does not exist")
    data = load_settings(game)
    if value:
        data["settings"][key] = value
    else:
        data["settings"].pop(key, None)
    save_settings(game, data)
    return value


def set_secret(catalog, game, tid, key, value):
    """Store a secret in the game's .env, making sure .env is ignored by git. Never returns the value."""
    tool = tool_by_id(catalog, tid)
    item = config_item(tool, key)
    if item["kind"] != "secret":
        raise ToolError(f"{key} is not a secret")
    value = (value or "").strip()
    if not value or len(value) > 4096 or "\n" in value or "\r" in value:
        raise ToolError("The key must be one non-empty line")
    added = ensure_gitignore(game, [".env"])
    path = Path(game) / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    replaced = False
    for index, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[index] = f"{key}={value}"
            replaced = True
    if not replaced:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name == "posix":
        os.chmod(path, 0o600)
    return {"saved": True, "gitignore_added": added}


def set_licence(catalog, game, tid, url):
    """Record the owner's evidence of a commercial licence for a non-commercial tool, or clear it."""
    tool = tool_by_id(catalog, tid)
    if not tool.get("licence_gate"):
        raise ToolError(f"{tid} needs no separate commercial licence")
    url = (url or "").strip()
    if url and not LICENCE_URL.fullmatch(url):
        raise ToolError("Give an https link to the licence or to the Issue that records it")
    data = load_settings(game)
    entry = data["tools"].setdefault(tid, {})
    if url:
        entry["commercial_licence"] = url
    else:
        entry.pop("commercial_licence", None)
    save_settings(game, data)
    return entry


def accept_risk(catalog, game, tid, accepted=True):
    """The owner's choice to use a non-commercial tool's outputs commercially at their own risk.

    Stored in the game's settings; afterwards the tool's outputs are not marked and the release
    report no longer blocks files already recorded for it.
    """
    tool = tool_by_id(catalog, tid)
    if not tool.get("licence_gate"):
        raise ToolError(f"{tid} has no commercial restriction")
    data = load_settings(game)
    entry = data["tools"].setdefault(tid, {})
    released = 0
    if accepted:
        from datetime import datetime, timezone
        entry["owner_accepted_risk"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ledger = load_ledger(game)
        kept = {digest: item for digest, item in ledger["files"].items() if item.get("tool") != tid}
        released = len(ledger["files"]) - len(kept)
        if released:
            ledger["files"] = kept
            (Path(game) / REFERENCE_LEDGER).write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    else:
        entry.pop("owner_accepted_risk", None)
    save_settings(game, data)
    return {"tool": tid, "owner_accepted_risk": entry.get("owner_accepted_risk", ""), "released": released}


def unrestricted(settings, tid):
    entry = settings["tools"].get(tid, {})
    return bool(entry.get("commercial_licence") or entry.get("owner_accepted_risk"))


def file_hash(path):
    import hashlib
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_ledger(game):
    path = Path(game) / REFERENCE_LEDGER
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"version": 1, "files": {}}


def mark_reference(catalog, game, tid, files):
    """Record outputs of a tool that may not ship, so the release report blocks them."""
    tool = tool_by_id(catalog, tid)
    settings = load_settings(game)
    if tool.get("commercial") != "non_commercial":
        raise ToolError(f"{tid} has no commercial restriction to record")
    if unrestricted(settings, tid):
        raise ToolError(f"{tid} is cleared for commercial use in this game; its outputs are not reference-only")
    ledger = load_ledger(game)
    from datetime import datetime, timezone
    added = []
    for name in files:
        path = Path(name).resolve()
        if not path.is_file():
            raise ToolError(f"Not a file: {name}")
        digest = file_hash(path)
        try:
            shown = path.relative_to(Path(game).resolve()).as_posix()
        except ValueError:
            shown = path.name
        ledger["files"][digest] = {"path": shown, "tool": tid,
                                   "marked": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        added.append(shown)
    target = Path(game) / REFERENCE_LEDGER
    target.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


# ---------------------------------------------------------------- status

def status(catalog, game, lang="en"):
    settings = load_settings(game)
    text = TEXT[lang]
    groups = {group["id"]: group["name"][lang] for group in catalog["groups"]}
    rows = []
    for tool in catalog["tools"]:
        installed, detail = detect(tool, game, settings, lang)
        state = settings["tools"].get(tool["id"], {})
        command = install_steps(tool, game)
        prerequisites = prerequisite_rows(tool, catalog, game, settings, lang)
        config = []
        for item in tool.get("config", []):
            if item["kind"] == "secret":
                config.append({"key": item["key"], "kind": "secret", "label": item["label"][lang],
                               "set": secret_present(game, item["key"])})
            else:
                config.append({"key": item["key"], "kind": item["kind"], "label": item["label"][lang],
                               "value": settings["settings"].get(item["key"], "")})
        rows.append({
            "id": tool["id"], "name": tool["name"], "group": tool["group"], "group_name": groups[tool["group"]],
            "gives": tool["gives"][lang], "cost": tool["cost"]["kind"],
            "cost_note": tool["cost"].get("note", {}).get(lang, ""), "account": bool(tool.get("account")),
            "licence": tool["licence"], "source": tool["source"], "who": tool["who"], "scope": tool["scope"],
            "pending": tool.get("status") == "pending_decision", "recommended": bool(tool.get("recommended")),
            "installed": installed, "detail": detail, "enabled": state.get("enabled", installed),
            "decision": state.get("decision", ""), "install_steps": command, "manual": manual_text(tool, lang),
            "commercial": tool.get("commercial", "ok"), "licence_note": tool.get("licence_note", {}).get(lang, ""),
            "requirements": tool.get("requirements", {}).get(lang, ""), "kind": tool.get("kind", "program"),
            "requires": tool.get("requires", []), "used_by": tool.get("used_by", []), "config": config,
            "owner_only": tool["who"] == "owner", "owner_label": text["owner_only"],
            "licence_gate": [item[lang] for item in tool.get("licence_gate", [])],
            "commercial_licence": state.get("commercial_licence", ""),
            "owner_accepted_risk": state.get("owner_accepted_risk", ""),
            "commercial_effective": ("licensed" if state.get("commercial_licence") else
                                     "owner_accepted" if state.get("owner_accepted_risk") else tool.get("commercial", "ok")),
            "prerequisites": prerequisites,
            "ready_to_install": all(row["met"] is not False for row in prerequisites if row["for"] == "install"),
            "ready_to_use": installed and all(row["met"] is not False for row in prerequisites if row["for"] == "use"),
            "confirm_with_person": [row["id"] for row in prerequisites if row["met"] is None],
        })
    return rows


def print_status(rows, lang):
    text = TEXT[lang]
    for row in rows:
        mark = "✓" if row["installed"] else ("…" if row["pending"] else "·")
        print(f"{mark} {row['id']:<28} {row['cost']:<7} {row['commercial_effective']:<14} {row['detail']}")
        for pre in row["prerequisites"]:
            if pre["met"] is True:
                continue
            sign = "?" if pre["met"] is None else "!"
            label = text["needs_install"] if pre["for"] == "install" else text["needs_use"]
            how = (text["prereq_by_claude"].format(c=pre["command"]) if pre["command"]
                   else text["prereq_by_person"].format(m=pre["manual"] or pre["why"]))
            print(f"    {sign} {label}: {pre['name']} — {pre['detail']}. {how}")


def readiness(catalog, game, tid, lang="en"):
    """One tool's state for an agent about to use it: installed, and what is still missing to install or use it."""
    row = next(item for item in status(catalog, game, lang) if item["id"] == tid)
    return {key: row[key] for key in ("id", "name", "installed", "detail", "who", "manual", "install_steps",
                                      "requirements", "prerequisites", "ready_to_install", "ready_to_use", "confirm_with_person",
                                      "commercial_effective", "licence_gate")}


# ---------------------------------------------------------------- command line

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", type=Path, help="Game folder (default: nearest folder with .gamedev-studio)")
    parser.add_argument("--lang", choices=TEXT, default="en")
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("status")
    show.add_argument("--json", action="store_true")
    put = commands.add_parser("install")
    put.add_argument("id")
    put.add_argument("--yes", action="store_true", help="The person said yes to this exact command")
    put.add_argument("--with-prerequisites", action="store_true",
                     help="The person also said yes to installing the missing prerequisites Claude may install")
    ready = commands.add_parser("check", help="Before using a tool: installed, and what is missing to install or use it")
    ready.add_argument("id")
    ready.add_argument("--json", action="store_true")
    pre = commands.add_parser("prereq", help="Install one prerequisite that Claude may install, after a yes")
    pre.add_argument("id")
    pre.add_argument("--yes", action="store_true")
    toggle = commands.add_parser("enable")
    toggle.add_argument("id")
    toggle.add_argument("--off", action="store_true")
    toggle.add_argument("--decision", help="GitHub link of the owner's decision (owner tools)")
    setting = commands.add_parser("set")
    setting.add_argument("id")
    setting.add_argument("key")
    setting.add_argument("value")
    secret = commands.add_parser("set-secret")
    secret.add_argument("id")
    secret.add_argument("key")
    licence = commands.add_parser("set-licence", help="Record (or clear with an empty value) a commercial licence link")
    licence.add_argument("id")
    licence.add_argument("url", nargs="?", default="")
    risk = commands.add_parser("accept-risk", help="Owner: use a non-commercial tool's outputs commercially at own risk")
    risk.add_argument("id")
    risk.add_argument("--off", action="store_true")
    mark = commands.add_parser("mark-reference", help="Record files made by a non-commercial tool as reference-only")
    mark.add_argument("id")
    mark.add_argument("files", nargs="+")
    args = parser.parse_args(argv)
    game = (args.game or find_game()).resolve()
    try:
        catalog = load_catalog()
        if args.command == "status":
            rows = status(catalog, game, args.lang)
            if args.json:
                print(json.dumps({"game": str(game), "platform": platform_key(), "tools": rows}, ensure_ascii=False, indent=2))
            else:
                print_status(rows, args.lang)
            return 0
        if args.command == "prereq":
            result = install_prerequisite(catalog, args.id, game, args.yes, on_line=print, lang=args.lang)
            return 0 if result["returncode"] == 0 else 1
        tool = tool_by_id(catalog, args.id)
        if args.command == "check":
            state = readiness(catalog, game, args.id, args.lang)
            if args.json:
                print(json.dumps(state, ensure_ascii=False, indent=2))
            else:
                print_status([next(row for row in status(catalog, game, args.lang) if row["id"] == args.id)], args.lang)
            return 0 if state["ready_to_use"] else 3
        if args.command == "install":
            result = install(tool, game, args.yes, on_line=print, catalog=catalog,
                             with_prerequisites=args.with_prerequisites, lang=args.lang)
            return 0 if result["returncode"] == 0 else 1
        if args.command == "enable":
            print(json.dumps(set_enabled(catalog, game, args.id, not args.off, args.decision), ensure_ascii=False))
            return 0
        if args.command == "set-licence":
            print(json.dumps(set_licence(catalog, game, args.id, args.url), ensure_ascii=False))
            return 0
        if args.command == "accept-risk":
            print(json.dumps(accept_risk(catalog, game, args.id, not args.off), ensure_ascii=False))
            return 0
        if args.command == "mark-reference":
            for name in mark_reference(catalog, game, args.id, args.files):
                print(f"reference-only: {name}")
            return 0
        if args.command == "set":
            set_setting(catalog, game, args.id, args.key, args.value)
            print("saved")
            return 0
        value = getpass.getpass(f"{args.key}: ")
        print(json.dumps(set_secret(catalog, game, args.id, args.key, value), ensure_ascii=False))
        return 0
    except (ToolError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    raise SystemExit(main())
