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
TOKENS = {"{python}", "{game}", "{pip_user}", "{tools}"}
REFERENCE_LEDGER = ".gamedev-studio-reference-only.json"
LICENCE_URL = re.compile(r"^https://[^\s]+$")


def tools_home():
    """Machine-wide folder for third-party tools the studio installs from their own sources."""
    return Path(os.environ.get("GAMEDEV_STUDIO_TOOLS") or Path.home() / ".gamedev-studio" / "tools")


def expand(value, game, python=None):
    return (value.replace("{python}", python or sys.executable).replace("{game}", str(Path(game)))
            .replace("{tools}", str(tools_home())))
DECISION_URL = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(issues|pull)/\d+(#[A-Za-z0-9_-]+)?$")
ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
TEXT = {
    "en": {"installed": "installed", "missing": "not installed", "pending": "waiting for a decision",
           "configured": "key saved", "no_key": "key not set", "owner_only": "owner's decision",
           "found": "found: {p}", "commit_mismatch": "checkout at another commit ({c})",
           "unreachable": "not answering", "healthy": "answering", "no_url": "no URL set",
           "browser_custom": "uses {p}", "browser_found": "Chromium in {p}",
           "not_detected": "not checked automatically: see its own setup"},
    "ru": {"installed": "установлено", "missing": "не установлено", "pending": "ждёт решения",
           "configured": "ключ сохранён", "no_key": "ключ не задан", "owner_only": "решение владельца",
           "found": "найдено: {p}", "commit_mismatch": "в папке другой коммит ({c})",
           "unreachable": "не отвечает", "healthy": "отвечает", "no_url": "адрес не задан",
           "browser_custom": "используется {p}", "browser_found": "Chromium в {p}",
           "not_detected": "автоматически не проверяется: см. его установку"},
}


class ToolError(ValueError):
    """A request the catalog or the rules do not allow."""


# ---------------------------------------------------------------- catalog

def _localized(value, name):
    if not isinstance(value, dict) or set(value) != {"ru", "en"} or not all(isinstance(v, str) and v.strip() for v in value.values()):
        raise ValueError(f"{name} needs non-empty 'ru' and 'en' texts")


def validate_catalog(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("catalog version must be 1")
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
        install = tool.get("install", {})
        for key, argv in install.items():
            if key == "manual":
                _localized(argv, f"{tid}.install.manual")
                continue
            if key not in {"all", "windows", "darwin", "linux"}:
                raise ValueError(f"{tid}: unknown install platform {key}")
            steps = argv if isinstance(argv, list) and argv and all(isinstance(a, (list, dict)) for a in argv) else [argv]
            for step in steps:
                if isinstance(step, dict):
                    if set(step) != {"copy_skills"} or not isinstance(step["copy_skills"], list) or len(step["copy_skills"]) != 2:
                        raise ValueError(f"{tid}: a non-command step must be {{\"copy_skills\": [from, to]}}")
                    continue
                if not isinstance(step, list) or not step or not all(isinstance(a, str) and a for a in step):
                    raise ValueError(f"{tid}: install.{key} must be a list of arguments or a list of steps")
                if any(re.search(r"[;&|`$]", a) and a not in TOKENS for a in step):
                    raise ValueError(f"{tid}: install.{key} contains shell syntax")
                if step[0] in {"sh", "bash", "cmd", "powershell", "pwsh", "iex"} or "|" in step:
                    raise ValueError(f"{tid}: install.{key} must not start a shell")
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
    """Return (installed, detail) for one tool, reading only the filesystem and PATH (and /health)."""
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


# ---------------------------------------------------------------- install

def platform_key():
    return PLATFORMS.get(sys.platform, "linux")


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


def install(tool, game, yes, on_line=None, python=None):
    """Run the catalog command for a free tool after an explicit yes. Returns a result dict."""
    if not yes:
        raise ToolError("Installing needs an explicit yes from the person")
    if tool.get("status") == "pending_decision":
        raise ToolError(f"{tool['id']} waits for a decision and cannot be installed yet")
    steps = install_steps(tool, game, python)
    if steps is None:
        raise ToolError(f"{tool['id']} is installed by the person or the owner: follow its instructions")
    for program in tool.get("requires_programs", []):
        if not shutil.which(program):
            raise ToolError(f"{tool['id']} needs {program} first")
    for argv in steps:
        if isinstance(argv, dict) or str(tools_home()) in argv[0]:
            continue  # copied skills, or a program an earlier step creates (a tool's own virtualenv)
        if not Path(argv[0]).is_file() and not shutil.which(argv[0]):
            raise ToolError(f"{argv[0]} is not available on this computer; install the tool by hand")
    on_line = on_line or (lambda line: None)
    code = 0
    tools_home().mkdir(parents=True, exist_ok=True)
    for argv in steps:
        if isinstance(argv, dict):
            on_line("· " + describe_step(argv))
            code = copy_skills(*argv["copy_skills"], on_line)
            if code != 0:
                break
            continue
        on_line("$ " + " ".join(argv))
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", errors="replace", cwd=str(game))
        for line in process.stdout:
            on_line(line.rstrip("\n"))
        code = process.wait()
        if code != 0:
            break
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
    if settings["tools"].get(tid, {}).get("commercial_licence"):
        raise ToolError(f"{tid} has a recorded commercial licence; its outputs are not reference-only")
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
            "commercial_effective": "licensed" if state.get("commercial_licence") else tool.get("commercial", "ok"),
        })
    return rows


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
                for row in rows:
                    mark = "✓" if row["installed"] else ("…" if row["pending"] else "·")
                    print(f"{mark} {row['id']:<28} {row['cost']:<7} {row['commercial_effective']:<14} {row['detail']}")
            return 0
        tool = tool_by_id(catalog, args.id)
        if args.command == "install":
            result = install(tool, game, args.yes, on_line=print)
            return 0 if result["returncode"] == 0 else 1
        if args.command == "enable":
            print(json.dumps(set_enabled(catalog, game, args.id, not args.off, args.decision), ensure_ascii=False))
            return 0
        if args.command == "set-licence":
            print(json.dumps(set_licence(catalog, game, args.id, args.url), ensure_ascii=False))
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
    raise SystemExit(main())
