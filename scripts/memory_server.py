#!/usr/bin/env python3
"""Keep the studio memory (Hindsight) running on this computer, and connect games to it.

Every person runs their own Hindsight server: it binds 127.0.0.1 only, keeps its data on this
computer (embedded PostgreSQL, the default ``pg0`` instance) and extracts facts through the
person's own Claude subscription (``claude-code`` provider, no paid API; DEC-019, DEC-085).
Memory is never deleted here (DEC-138): this script has no delete, clear or reset command.

Usage:
  python scripts/memory_server.py status [--json]
  python scripts/memory_server.py start [--wait SECONDS]   start in the background unless it already answers
  python scripts/memory_server.py stop                     stop the server this script started (by its pid file)
  python scripts/memory_server.py autostart --yes [--off]  start it at sign-in (Windows: the per-user Run
                                                            key, no admin; macOS LaunchAgent); --off removes it
  python scripts/memory_server.py connect-game --yes [--game DIR]
                                                            add the game's project bank to its .mcp.json

Rules: only 127.0.0.1; a port held by another program is reported, never touched; a process is
stopped only when it is the one this script recorded and it is a Hindsight server. Stdlib only, so the
copy that autostart keeps in ~/.gamedev-studio/memory runs without the plugin folder.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HOST = "127.0.0.1"
PORT = 8888
URL = f"http://{HOST}:{PORT}"
STUDIO_BANK = "gamedev-studio::studio"
PROJECT_BANK = "gamedev-studio::project::{repository}"
# contracts/v1/knowledge-policy.json memory_backend.mcp_enabled_tools; a test keeps the two equal
MCP_TOOLS = ["retain", "recall", "list_memories", "get_memory", "get_bank"]
# Windows: the per-user Run key starts it at sign-in without administrator rights (a Task Scheduler
# ONLOGON task needs them); it shows in Task Manager > Startup apps, where the person can turn it off.
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "GameDevStudioMemory"
LAUNCH_AGENT = "com.gamedev-studio.memory"


def home():
    return Path(os.environ.get("GAMEDEV_STUDIO_HOME") or Path.home() / ".gamedev-studio")


def state_dir():
    return home() / "memory"


def tools_home():
    return Path(os.environ.get("GAMEDEV_STUDIO_TOOLS") or home() / "tools")


def runtime_candidates():
    """Where a Hindsight runtime may be: the studio's tools folder, then the older ~/.hindsight-runtime."""
    custom = os.environ.get("GAMEDEV_STUDIO_HINDSIGHT")
    found = [Path(custom)] if custom else []
    return found + [tools_home() / "hindsight", Path.home() / ".hindsight-runtime"]


def program(runtime):
    return runtime / ("Scripts/hindsight-api.exe" if sys.platform == "win32" else "bin/hindsight-api")


def find_runtime():
    for runtime in runtime_candidates():
        if program(runtime).is_file():
            return runtime
    return None


def server_environment():
    env = dict(os.environ)
    env.update({
        "HINDSIGHT_API_HOST": HOST,
        "HINDSIGHT_API_PORT": str(PORT),
        "HINDSIGHT_API_LLM_PROVIDER": "claude-code",
        "HINDSIGHT_API_MODEL_INIT_TIMEOUT": "900",
        "HINDSIGHT_API_MCP_ENABLED_TOOLS": ",".join(MCP_TOOLS),
        "PYTHONIOENCODING": "utf-8",
    })
    env.pop("HINDSIGHT_API_DATABASE_URL", None)  # always the default pg0 instance, where memory already is
    return env


def server_argv(runtime):
    return [str(program(runtime)), "--host", HOST, "--port", str(PORT)]


# ------------------------------------------------------------------ state

def health(timeout=2.0):
    """'hindsight' when Hindsight answers /health, 'other' when something else holds the port, None when free."""
    try:
        with urllib.request.urlopen(URL + "/health", timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8") or "{}")
        return "hindsight" if isinstance(body, dict) and "database" in body else "other"
    except urllib.error.HTTPError:
        return "other"
    except (urllib.error.URLError, OSError, ValueError):
        pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return "other" if probe.connect_ex((HOST, PORT)) == 0 else None


def pid_file():
    return state_dir() / "hindsight.pid"


def log_file():
    return state_dir() / "hindsight.log"


def process_image(pid):
    """The executable name of a running process, or None."""
    if sys.platform == "win32":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                capture_output=True, timeout=20, check=False)
        line = result.stdout.decode("utf-8", errors="replace").strip()
        return line.split('","')[0].strip('"') if line.startswith('"') else None
    try:
        return Path(os.readlink(f"/proc/{pid}/exe")).name
    except OSError:
        result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, timeout=20, check=False)
        return result.stdout.decode().strip() or None


def run_key_value():
    """The command in the per-user Run key, or None."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            return winreg.QueryValueEx(key, RUN_VALUE)[0]
    except OSError:
        return None


def autostart_state():
    if sys.platform == "win32":
        return bool(run_key_value())
    if sys.platform == "darwin":
        return (Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT}.plist").is_file()
    return False


def status():
    runtime = find_runtime()
    return {"installed": bool(runtime), "runtime": str(runtime) if runtime else "", "url": URL,
            "server": health() or "stopped", "studio_bank": STUDIO_BANK,
            "studio_mcp": f"{URL}/mcp/{STUDIO_BANK}/", "autostart": autostart_state(), "log": str(log_file())}


# ------------------------------------------------------------------ start and stop

def lock_file():
    return state_dir() / "start.lock"


def take_lock(stale=180.0):
    """An exclusive lock around check-and-spawn, so two sessions starting at once start one server.

    A lock older than ``stale`` seconds is left over from a crashed start and is replaced."""
    state_dir().mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            os.close(os.open(lock_file(), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return True
        except FileExistsError:
            try:
                if time.time() - lock_file().stat().st_mtime < stale:
                    return False
                lock_file().unlink()
            except OSError:
                return False
    return False


def start(wait=0.0, out=print):
    if not take_lock():
        out("another start of the memory server is in progress")
        return 0
    try:
        code, process = _start(out)
    finally:
        lock_file().unlink(missing_ok=True)
    if not wait or code != 0:
        return code
    deadline = time.monotonic() + wait  # also waits for a server another session is booting
    while time.monotonic() < deadline:
        if health() == "hindsight":
            out(f"memory server answers at {URL}")
            return 0
        if process is not None and process.poll() is not None:
            out(f"memory server exited with code {process.returncode}; see {log_file()}")
            return 1
        time.sleep(2)
    return 4


def _start(out):
    """Start the server unless it answers or is booting; (exit code, the new process or None)."""
    state = health()
    if state == "hindsight":
        out(f"memory server already answers at {URL}")
        return 0, None
    if state == "other":
        out(f"port {PORT} on {HOST} is used by another program; the memory server was not started")
        return 3, None
    starting = recorded_server()
    if starting:
        out(f"memory server is still starting (pid {starting}); the first start can take several minutes")
        return 0, None
    runtime = find_runtime()
    if not runtime:
        out("Hindsight is not installed: python scripts/studio_tools.py install hindsight --yes")
        return 2, None
    state_dir().mkdir(parents=True, exist_ok=True)
    log = open(log_file(), "ab")
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": subprocess.STDOUT, "env": server_environment(),
              "cwd": str(state_dir())}
    if sys.platform == "win32":
        kwargs["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                                   | subprocess.CREATE_NO_WINDOW)
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(server_argv(runtime), **kwargs)
    log.close()
    pid_file().write_text(str(process.pid), encoding="ascii")
    out(f"memory server starting (pid {process.pid}); log: {log_file()}")
    return 0, process


def recorded_server():
    """The pid this script recorded, when that process is still a running Hindsight server."""
    try:
        pid = int(pid_file().read_text(encoding="ascii").strip() or 0)
    except (OSError, ValueError):
        return None
    image = process_image(pid) if pid else None
    return pid if image and "hindsight" in image.lower() else None


def stop(out=print):
    if not pid_file().is_file():
        out("no memory server was started by this script")
        return 0
    pid = recorded_server()
    if not pid:
        out("the recorded process is not a running Hindsight server; nothing stopped")
        pid_file().unlink(missing_ok=True)
        return 0
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30, check=False)
    else:
        os.kill(pid, 15)
    pid_file().unlink(missing_ok=True)
    out(f"memory server stopped (pid {pid}); its data stays")
    return 0


# ------------------------------------------------------------------ autostart

def launcher_copy():
    """A copy of this script outside the plugin folder, which is replaced on every plugin update."""
    target = state_dir() / "memory_server.py"
    state_dir().mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).resolve(), target)
    return target


def windowless_python():
    exe = Path(sys.executable)
    quiet = exe.with_name("pythonw.exe")
    return quiet if sys.platform == "win32" and quiet.is_file() else exe


def autostart_command(launcher):
    return f'"{windowless_python()}" "{launcher}" start'


def autostart(enable, out=print):
    if sys.platform == "win32":
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if not enable:
                try:
                    winreg.DeleteValue(key, RUN_VALUE)
                    out("autostart removed")
                except OSError:
                    out("no autostart entry to remove")
                return 0
            command = autostart_command(launcher_copy())
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, command)
        out(f"autostart added (Windows sign-in, Task Manager > Startup apps): {command}")
        return 0
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT}.plist"
        if not enable:
            plist.unlink(missing_ok=True)
            out("autostart removed")
            return 0
        launcher = launcher_copy()
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LAUNCH_AGENT}</string>
  <key>ProgramArguments</key><array><string>{sys.executable}</string><string>{launcher}</string><string>start</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>
""", encoding="utf-8")
        out(f"autostart added: {plist}")
        return 0
    out("Linux: add `python <plugin>/scripts/memory_server.py start` to your desktop's autostart or a systemd user unit")
    return 2


# ------------------------------------------------------------------ games

def repository_name(game):
    """The game's repository name: the origin remote's last path part, else the folder name."""
    try:
        result = subprocess.run(["git", "-C", str(game), "remote", "get-url", "origin"], capture_output=True,
                                timeout=20, check=False)
        remote = result.stdout.decode("utf-8", errors="replace").strip()
    except OSError:
        remote = ""
    name = remote.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1] if remote else Path(game).resolve().name
    return name[:-4] if name.endswith(".git") else name


def project_mcp_url(game):
    return f"{URL}/mcp/{PROJECT_BANK.format(repository=repository_name(game))}/"


def game_connected(game):
    path = Path(game) / ".mcp.json"
    try:
        servers = json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})
    except (OSError, ValueError, AttributeError):
        return False
    return isinstance(servers, dict) and "hindsight-project" in servers


def connect_game(game, out=print):
    """Add the game's own project bank (one MCP endpoint per bank) to the game's .mcp.json."""
    if game_connected(game):
        out("the game is already connected to its project memory")
        return 0
    url = project_mcp_url(game)
    claude = shutil.which("claude")
    if not claude:
        out("Claude Code CLI not found; add this to the game's .mcp.json by hand: " + url)
        return 2
    argv = [claude, "mcp", "add", "--transport", "http", "--scope", "project", "hindsight-project", url]
    result = subprocess.run(argv, capture_output=True, timeout=60, check=False, cwd=str(game))
    out((result.stdout + result.stderr).decode("utf-8", errors="replace").strip() or f"connected: {url}")
    return 0 if result.returncode == 0 else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("status")
    show.add_argument("--json", action="store_true")
    run = commands.add_parser("start")
    run.add_argument("--wait", type=float, default=0.0, help="seconds to wait until the server answers")
    commands.add_parser("stop")
    auto = commands.add_parser("autostart")
    auto.add_argument("--yes", action="store_true", help="the person said yes to starting memory at sign-in")
    auto.add_argument("--off", action="store_true")
    game = commands.add_parser("connect-game")
    game.add_argument("--yes", action="store_true", help="the person said yes to adding the game's memory bank")
    game.add_argument("--game", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.command == "status":
        state = status()
        if args.json:
            print(json.dumps(state, ensure_ascii=False, indent=2))
        else:
            for key, value in state.items():
                print(f"{key}: {value}")
        return 0
    if args.command == "start":
        return start(args.wait)
    if args.command == "stop":
        return stop()
    if not args.yes and not (args.command == "autostart" and args.off):
        print("this changes the computer or the game: run it again with --yes after the person agreed", file=sys.stderr)
        return 2
    if args.command == "autostart":
        return autostart(not args.off)
    return connect_game(args.game)


if __name__ == "__main__":
    try:  # the autostart copy in ~/.gamedev-studio/memory runs without the plugin's console_io
        from console_io import prepare_console
        prepare_console()
    except ImportError:
        pass
    raise SystemExit(main())
