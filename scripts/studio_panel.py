#!/usr/bin/env python3
"""GameDev Studio panel: a local page to set up optional tools and run browser QA for one game.

    python scripts/studio_panel.py [--game DIR] [--lang ru|en] [--port N] [--no-open]

Safety:
  * listens on 127.0.0.1 only and accepts only the Host names 127.0.0.1/localhost on its port;
  * the URL it prints carries a one-time token; the page then uses an HttpOnly cookie, and every
    action also needs the token in a header, so other sites in the browser cannot act through it;
  * actions are fixed: install a catalog tool after the person's yes, enable or configure it,
    save a key to the game's ignored .env, run scripts/capture_review.py on a scenario in the game's
    qa/ folder, and serve finished reports from qa-reports/. Nothing is published, nothing is paid
    for, and no free-form command is ever run.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
from urllib.parse import parse_qs, unquote, urlsplit
import urllib.error
import urllib.request
import webbrowser

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import studio_tools  # noqa: E402
from report_ui import page as render_page  # noqa: E402

MAX_BODY = 64 * 1024
TEXT = {
    "ru": {
        "title": "Студия", "tab_tools": "Инструменты", "tab_qa": "Проверка", "tab_reports": "Отчёты",
        "stop": "Выключить панель", "stopped": "Панель выключена. Это окно можно закрыть.",
        "tools_title": "Инструменты студии", "qa_title": "Браузерная проверка", "reports_title": "Отчёты проверок",
        "installed": "Установлено", "missing": "Не установлено", "pending": "Ждёт решения", "owner": "Решение владельца",
        "free": "Бесплатно", "paid": "Платно", "account": "Нужен аккаунт", "scope_machine": "на компьютер",
        "scope_game": "в папку игры", "install": "Установить", "reinstall": "Переустановить", "source": "Источник",
        "enabled": "Включён для этой игры", "decision": "Ссылка на решение владельца в GitHub",
        "save": "Сохранить", "saved": "Сохранено", "key_saved": "ключ сохранён", "key_placeholder": "вставьте ключ",
        "requires": "Сначала нужен", "used_by": "Используют", "manual": "Ставите вы", "who_owner": "Включает владелец студии",
        "confirm_title": "Установить {name}?", "confirm_body": "Панель выполнит ровно эту команду из каталога студии:",
        "confirm_windows": "Windows может спросить разрешение — подтвердите его.", "cancel": "Отмена", "yes": "Да, установить",
        "log": "Журнал", "running": "Выполняется…", "done": "Готово", "failed": "Ошибка", "close": "Закрыть",
        "filter_all": "Все", "filter_recommended": "Рекомендуемые", "filter_missing": "Не установлено", "filter_paid": "Платные",
        "summary": "{installed} из {total} установлено · {paid} платных · {pending} ждут решения",
        "scenarios": "Сценарии", "no_scenarios": "В папке qa/ игры нет сценариев.",
        "make_example": "Создать пример сценария", "profiles": "Профили экрана", "options": "Параметры",
        "video": "Записывать видео", "step_frames": "Кадр после каждого шага", "language": "Язык отчёта",
        "run": "Запустить проверку", "build_up": "сборка отвечает", "build_down": "сборка не отвечает",
        "builds_hint": "Перед запуском поднимите обе сборки игры на своих адресах.", "open_report": "Открыть отчёт",
        "no_reports": "Отчётов пока нет.", "passed": "Пройдено", "failed_run": "Есть ошибки", "invalid": "Сценарий с ошибкой",
        "before": "Исходная", "after": "Новая", "secret_note": "Ключ хранится только в .env этой игры; .env добавляется в .gitignore.",
        "paid_note": "Каждая генерация — только после «да» владельца в задаче.", "game": "Игра",
        "needs": "Нужно", "commercial_outputs_ok": "Результаты можно продавать",
        "commercial_non_commercial": "Не для коммерческого релиза", "commercial_check": "Проверьте лицензию моделей",
    },
    "en": {
        "title": "Studio", "tab_tools": "Tools", "tab_qa": "QA", "tab_reports": "Reports",
        "stop": "Stop the panel", "stopped": "The panel has stopped. You can close this window.",
        "tools_title": "Studio tools", "qa_title": "Browser QA", "reports_title": "QA reports",
        "installed": "Installed", "missing": "Not installed", "pending": "Waiting for a decision", "owner": "Owner's decision",
        "free": "Free", "paid": "Paid", "account": "Account needed", "scope_machine": "on this computer",
        "scope_game": "in the game folder", "install": "Install", "reinstall": "Reinstall", "source": "Source",
        "enabled": "Enabled for this game", "decision": "GitHub link of the owner's decision",
        "save": "Save", "saved": "Saved", "key_saved": "key saved", "key_placeholder": "paste the key",
        "requires": "Needs first", "used_by": "Used by", "manual": "You install it", "who_owner": "The studio owner turns it on",
        "confirm_title": "Install {name}?", "confirm_body": "The panel will run exactly this command from the studio catalog:",
        "confirm_windows": "Windows may ask for permission — approve it.", "cancel": "Cancel", "yes": "Yes, install",
        "log": "Log", "running": "Running…", "done": "Done", "failed": "Failed", "close": "Close",
        "filter_all": "All", "filter_recommended": "Recommended", "filter_missing": "Not installed", "filter_paid": "Paid",
        "summary": "{installed} of {total} installed · {paid} paid · {pending} waiting for a decision",
        "scenarios": "Scenarios", "no_scenarios": "The game's qa/ folder has no scenarios.",
        "make_example": "Create an example scenario", "profiles": "Screen profiles", "options": "Options",
        "video": "Record clips", "step_frames": "Frame after every step", "language": "Report language",
        "run": "Run QA", "build_up": "build answers", "build_down": "build not answering",
        "builds_hint": "Start both game builds at their addresses before running.", "open_report": "Open report",
        "no_reports": "No reports yet.", "passed": "Passed", "failed_run": "Has failures", "invalid": "Invalid scenario",
        "before": "Baseline", "after": "Candidate", "secret_note": "The key is kept only in this game's .env; .env is added to .gitignore.",
        "paid_note": "Every generation needs the owner's yes on the task.", "game": "Game",
        "needs": "Needs", "commercial_outputs_ok": "Outputs may be sold",
        "commercial_non_commercial": "Not for a commercial release", "commercial_check": "Check the model licences",
    },
}
EXAMPLE_SCENARIO = {
    "issue": "https://github.com/OWNER/GAME/issues/1",
    "title": "Example: start, tap and pause",
    "before": {"url": "http://127.0.0.1:8100/", "commit": "0" * 40},
    "after": {"url": "http://127.0.0.1:8101/", "commit": "1" * 40},
    "ready_selector": "canvas",
    "step_frames": True,
    "profiles": {
        "phone": {"width": 390, "height": 844, "dpr": 2, "label": "Phone"},
        "desktop": {"width": 1280, "height": 720, "input": "mouse", "label": "Desktop"},
    },
    "viewports": ["phone", "desktop"],
    "steps": [
        {"action": "tap_at", "selector": "canvas", "x": 0.5, "y": 0.6, "label": "Tap to start"},
        {"action": "state", "path": "scene", "equals": "game", "label": "Game started"},
        {"action": "command", "name": "pause", "label": "Pause"},
        {"action": "state", "path": "paused", "equals": True, "label": "pause-verified"},
    ],
}


class Job:
    def __init__(self, kind, title):
        self.id = secrets.token_hex(6)
        self.kind, self.title = kind, title
        self.status, self.result = "running", {}
        self.lines = deque(maxlen=4000)
        self.offset = 0
        self.lock = threading.Lock()

    def log(self, line):
        with self.lock:
            if len(self.lines) == self.lines.maxlen:
                self.offset += 1
            self.lines.append(line)

    def view(self, since=0):
        with self.lock:
            start = max(0, since - self.offset)
            return {"id": self.id, "kind": self.kind, "title": self.title, "status": self.status,
                    "result": self.result, "next": self.offset + len(self.lines), "lines": list(self.lines)[start:]}


class Panel:
    def __init__(self, game, lang, executable_path=None):
        self.game = Path(game).resolve()
        self.lang = lang
        self.token = secrets.token_urlsafe(24)
        self.catalog = studio_tools.load_catalog()
        self.jobs = {}
        self.busy = threading.Lock()
        self.executable_path = executable_path
        self.server = None

    # ------------------------------------------------------------ data
    def settings(self):
        return studio_tools.load_settings(self.game)

    def folder(self, key, default):
        name = self.settings().get("qa", {}).get(key, default)
        path = (self.game / name).resolve()
        if self.game not in (path, *path.parents):
            raise studio_tools.ToolError("QA folders must be inside the game folder")
        return path

    def scenarios(self):
        import capture_review
        folder = self.folder("scenarios", "qa")
        items = []
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            item = {"file": path.relative_to(self.game).as_posix(), "name": path.stem}
            try:
                config = capture_review.load_config(path)
            except (OSError, ValueError) as error:
                items.append({**item, "error": str(error)})
                continue
            item.update(title=config.get("title") or path.stem, issue=config["issue"], profiles=config["resolved_profiles"],
                        builds={side: {"url": config[side]["url"], "commit": config[side]["commit"][:12],
                                       "up": self.reachable(config[side]["url"])} for side in ("before", "after")},
                        steps=len(config["steps"]), step_frames=config.get("step_frames", False))
            items.append(item)
        return items

    @staticmethod
    def reachable(url):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.status < 500
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def runs(self):
        folder = self.folder("reports", "qa-reports")
        items = []
        for summary in sorted(folder.glob("*/summary.json"), reverse=True) if folder.is_dir() else []:
            try:
                data = json.loads(summary.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            directory = summary.parent
            thumb = next((f"{directory.name}/{v['name']}/after.png" for v in data.get("viewports", [])
                          if (directory / v["name"] / "after.png").is_file()), "")
            items.append({"dir": directory.name, "title": data.get("title") or directory.name,
                          "passed": bool(data.get("passed")), "issue": data.get("issue", ""),
                          "profiles": [v.get("label") or v["name"] for v in data.get("viewports", [])],
                          "created": datetime.fromtimestamp(summary.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                          "report": f"/files/{directory.name}/index.html", "thumb": f"/files/{thumb}" if thumb else ""})
        return items[:60]

    def state(self):
        rows = studio_tools.status(self.catalog, self.game, self.lang)
        return {"lang": self.lang, "game": str(self.game), "game_name": self.game.name,
                "platform": studio_tools.platform_key(), "tools": rows,
                "groups": [{"id": g["id"], "name": g["name"][self.lang]} for g in self.catalog["groups"]],
                "scenarios": self.scenarios(), "runs": self.runs(),
                "jobs": [job.view(len(job.lines) + job.offset) for job in self.jobs.values() if job.status == "running"]}

    # ------------------------------------------------------------ actions
    def start(self, job, work):
        if not self.busy.acquire(blocking=False):
            raise studio_tools.ToolError("Another install or QA run is still going")
        self.jobs[job.id] = job

        def run():
            try:
                job.result = work(job) or {}
                job.status = "done" if job.result.get("ok", True) else "failed"
            except (studio_tools.ToolError, ValueError, OSError, subprocess.SubprocessError) as error:
                job.log(str(error))
                job.status = "failed"
            finally:
                self.busy.release()
        threading.Thread(target=run, daemon=True).start()
        return job.view()

    def install(self, body):
        tool = studio_tools.tool_by_id(self.catalog, str(body.get("id", "")))
        if body.get("confirm") is not True:
            raise studio_tools.ToolError("Installing needs the person's yes")

        def work(job):
            result = studio_tools.install(tool, self.game, True, on_line=job.log)
            return {"ok": result["returncode"] == 0, "gitignore_added": result["gitignore_added"]}
        return self.start(Job("install", tool["name"]), work)

    def run_qa(self, body):
        folder = self.folder("scenarios", "qa")
        name = str(body.get("file", ""))
        path = (self.game / name).resolve()
        if path.parent != folder or path.suffix != ".json" or not path.is_file():
            raise studio_tools.ToolError("Choose a scenario from the game's qa folder")
        profiles = body.get("profiles") or []
        if not isinstance(profiles, list) or not all(isinstance(p, str) and re.fullmatch(r"[a-z0-9-]{1,40}", p) for p in profiles):
            raise studio_tools.ToolError("Invalid profile list")
        lang = body.get("lang") if body.get("lang") in TEXT else self.lang
        reports = self.folder("reports", "qa-reports")
        reports.mkdir(parents=True, exist_ok=True)
        out = reports / f"{datetime.now():%Y%m%d-%H%M%S}-{path.stem}"
        argv = [sys.executable, str(SCRIPTS / "capture_review.py"), "--config", str(path), "--out", str(out), "--lang", lang]
        if body.get("video"):
            argv.append("--record-video")
        if body.get("step_frames"):
            argv.append("--step-frames")
        if profiles:
            argv += ["--profiles", ",".join(profiles)]
        chromium = self.executable_path or self.settings().get("settings", {}).get("chromium_path")
        if chromium:
            argv += ["--executable-path", chromium]
        studio_tools.ensure_gitignore(self.game, [reports.relative_to(self.game).as_posix() + "/"])

        def work(job):
            job.log("$ capture_review.py " + " ".join(argv[3:]))
            process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                       encoding="utf-8", errors="replace", cwd=str(self.game))
            for line in process.stdout:
                job.log(line.rstrip("\n"))
            code = process.wait()
            report = out / "index.html"
            return {"ok": code in (0, 1) and report.is_file(), "passed": code == 0,
                    "report": f"/files/{out.name}/index.html" if report.is_file() else ""}
        return self.start(Job("qa", path.stem), work)

    def example(self):
        folder = self.folder("scenarios", "qa")
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "example.json"
        if target.exists():
            raise studio_tools.ToolError("qa/example.json already exists")
        target.write_text(json.dumps(EXAMPLE_SCENARIO, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"file": target.relative_to(self.game).as_posix()}

    def act(self, route, body):
        if route == "/api/tools/install":
            return self.install(body)
        if route == "/api/tools/enable":
            return studio_tools.set_enabled(self.catalog, self.game, str(body.get("id", "")), bool(body.get("enabled")),
                                            body.get("decision") or None)
        if route == "/api/tools/config":
            tool = studio_tools.tool_by_id(self.catalog, str(body.get("id", "")))
            item = studio_tools.config_item(tool, str(body.get("key", "")))
            if item["kind"] == "secret":
                return studio_tools.set_secret(self.catalog, self.game, tool["id"], item["key"], str(body.get("value", "")))
            return {"value": studio_tools.set_setting(self.catalog, self.game, tool["id"], item["key"], str(body.get("value", "")))}
        if route == "/api/qa/run":
            return self.run_qa(body)
        if route == "/api/qa/example":
            return self.example()
        if route == "/api/shutdown":
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return {"stopping": True}
        raise LookupError(route)

    # ------------------------------------------------------------ page
    def page(self):
        script = (Path(__file__).resolve().parents[1] / "ui" / "panel.js").read_text(encoding="utf-8")
        return render_page("panel.html", self.lang, title=TEXT[self.lang]["title"], token=self.token,
                           panel_script=script,
                           texts=json.dumps(TEXT[self.lang], ensure_ascii=False).replace("</", "<\\/"),
                           game_name=self.game.name)


def handler_for(panel):
    class Handler(BaseHTTPRequestHandler):
        server_version = "GameDevStudioPanel"

        def log_message(self, *args):
            pass

        def allowed_host(self):
            port = self.server.server_address[1]
            return self.headers.get("Host", "") in {f"127.0.0.1:{port}", f"localhost:{port}"}

        def authed(self):
            cookies = dict(part.strip().split("=", 1) for part in self.headers.get("Cookie", "").split(";") if "=" in part)
            return secrets.compare_digest(cookies.get("gds", ""), panel.token)

        def send(self, status, body=b"", kind="application/json; charset=utf-8", headers=()):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def json(self, status, value):
            self.send(status, json.dumps(value, ensure_ascii=False).encode("utf-8"))

        def do_GET(self):
            if not self.allowed_host():
                return self.send(HTTPStatus.MISDIRECTED_REQUEST, b"wrong host", "text/plain")
            parts = urlsplit(self.path)
            if parts.path == "/" and parse_qs(parts.query).get("t", [""])[0]:
                if not secrets.compare_digest(parse_qs(parts.query)["t"][0], panel.token):
                    return self.send(HTTPStatus.FORBIDDEN, b"bad token", "text/plain")
                return self.send(HTTPStatus.SEE_OTHER, headers=[
                    ("Location", "/"), ("Set-Cookie", f"gds={panel.token}; HttpOnly; SameSite=Strict; Path=/")])
            if not self.authed():
                return self.send(HTTPStatus.FORBIDDEN, b"Open the address the panel printed.", "text/plain; charset=utf-8")
            if parts.path == "/":
                return self.send(HTTPStatus.OK, panel.page().encode("utf-8"), "text/html; charset=utf-8")
            if parts.path == "/api/state":
                return self.json(HTTPStatus.OK, panel.state())
            match = re.fullmatch(r"/api/jobs/([0-9a-f]{12})", parts.path)
            if match:
                job = panel.jobs.get(match.group(1))
                if not job:
                    return self.json(HTTPStatus.NOT_FOUND, {"error": "no such job"})
                since = int(parse_qs(parts.query).get("since", ["0"])[0] or 0)
                return self.json(HTTPStatus.OK, job.view(since))
            if parts.path.startswith("/files/"):
                return self.file(unquote(parts.path[len("/files/"):]))
            return self.send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

        def file(self, relative):
            root = panel.folder("reports", "qa-reports")
            path = (root / relative).resolve()
            if root not in path.parents or not path.is_file():
                return self.send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if kind.startswith("text/") or kind in {"application/json", "application/javascript"}:
                kind += "; charset=utf-8"
            return self.send(HTTPStatus.OK, path.read_bytes(), kind)

        def do_POST(self):
            if not self.allowed_host() or not self.authed():
                return self.send(HTTPStatus.FORBIDDEN, b"forbidden", "text/plain")
            if not secrets.compare_digest(self.headers.get("X-Studio-Token", ""), panel.token):
                return self.send(HTTPStatus.FORBIDDEN, b"missing token", "text/plain")
            origin = self.headers.get("Origin")
            port = self.server.server_address[1]
            if origin and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
                return self.send(HTTPStatus.FORBIDDEN, b"foreign origin", "text/plain")
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self.send(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, b"too large", "text/plain")
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                return self.json(HTTPStatus.OK, panel.act(urlsplit(self.path).path, body))
            except LookupError:
                return self.json(HTTPStatus.NOT_FOUND, {"error": "unknown action"})
            except (studio_tools.ToolError, ValueError, OSError) as error:
                return self.json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", type=Path, help="Game folder (default: nearest folder with .gamedev-studio)")
    parser.add_argument("--lang", choices=TEXT, default="ru")
    parser.add_argument("--port", type=int, default=0, help="Local port (default: any free port)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser")
    parser.add_argument("--executable-path", help="Chromium or Chrome for QA runs")
    args = parser.parse_args(argv)
    game = (args.game or studio_tools.find_game()).resolve()
    if not game.is_dir():
        print(f"Not a folder: {game}", file=sys.stderr)
        return 2
    panel = Panel(game, args.lang, args.executable_path)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(panel))
    panel.server = server
    url = f"http://127.0.0.1:{server.server_address[1]}/?t={panel.token}"
    print(f"GameDev Studio panel for {game}\n{url}\nStop with Ctrl+C or the panel's button.", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
