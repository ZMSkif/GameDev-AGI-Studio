#!/usr/bin/env python3
"""Inventory a local build ZIP and summarize browser QA as separate evidence."""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from html import escape

from report_ui import attr, page, write_new
from review_evidence import ISSUE_URL


PLATFORMS = ("playgama", "youtube-playables")
CHECK_KINDS = {"navigation", "step", "within", "no_overlap"}


def inventory(path):
    with path.open("rb") as source:
        with ZipFile(source) as archive:
            files = [
                {"path": entry.filename, "bytes": entry.file_size, "compressed_bytes": entry.compress_size}
                for entry in archive.infolist() if not entry.is_dir()
            ]
        source.seek(0)
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {
        "name": path.name,
        "archive_bytes": size,
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "uncompressed_bytes": sum(entry["bytes"] for entry in files),
        "compressed_member_bytes": sum(entry["compressed_bytes"] for entry in files),
        "files": files,
    }


def reference_check(path, ledger_path):
    """Find archive members whose bytes match a file recorded as reference-only."""
    if not ledger_path:
        return {"status": "not_run"}
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    files = ledger.get("files") if isinstance(ledger, dict) else None
    if not isinstance(files, dict):
        raise ValueError("Invalid reference-only ledger")
    matches = []
    with ZipFile(path) as archive:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            digest = hashlib.sha256()
            with archive.open(entry) as member:
                for chunk in iter(lambda: member.read(1024 * 1024), b""):
                    digest.update(chunk)
            record = files.get(digest.hexdigest())
            if record:
                matches.append({"path": entry.filename, "source": record.get("path", ""), "tool": record.get("tool", "")})
    return {"status": "failed" if matches else "passed", "ledger_files": len(files), "matches": matches}


def field(document, key, expected):
    if not isinstance(document, dict) or type(document.get(key)) is not expected:
        raise ValueError(f"Invalid QA summary field: {key}")
    return document[key]


def load_candidate_qa(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if field(data, "version", int) != 1:
        raise ValueError("Unsupported QA summary version")
    issue = field(data, "issue", str)
    if not ISSUE_URL.fullmatch(issue):
        raise ValueError("Expected the QA summary to link a GitHub issue")
    build = field(field(data, "builds", dict), "after", dict)
    commit = field(build, "commit", str)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full candidate Git commit in QA summary")
    viewports = []
    names = set()
    for viewport in field(data, "viewports", list):
        name = field(viewport, "name", str)
        if not name.strip() or name in names:
            raise ValueError("Expected unique names for QA viewports")
        names.add(name)
        after = field(field(viewport, "builds", dict), "after", dict)
        startup = after.get("ready_ms")
        if startup is not None and (type(startup) not in (int, float)
                                    or not 0 <= startup <= sys.float_info.max
                                    or not math.isfinite(startup)):
            raise ValueError(f"Invalid ready_ms for viewport {name}")
        checks = []
        for check in field(after, "checks", list):
            label = field(check, "name", str)
            kind = field(check, "type", str)
            if kind not in CHECK_KINDS or not label.strip():
                raise ValueError(f"Invalid check name or type for viewport {name}")
            checks.append({
                "name": label,
                "type": kind,
                "passed": field(check, "passed", bool),
                "detail": field(check, "detail", str),
            })
        errors = field(after, "errors", list)
        if any(not isinstance(error, str) for error in errors):
            raise ValueError(f"Invalid browser error for viewport {name}")
        viewports.append({
            "name": name,
            "ready_ms": startup,
            "scenario_passed": field(after, "scenario_passed", bool),
            "errors": errors,
            "checks": checks,
        })
    if not viewports:
        raise ValueError("QA summary must contain a viewport")
    return {"issue": issue, "candidate_commit": commit, "viewports": viewports}


def named_check(viewports, name):
    if not name:
        return {"status": "not_run"}
    observations = []
    for viewport in viewports:
        matches = [check for check in viewport["checks"]
                   if check["type"] == "step" and check["name"] == name]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous step {name!r} for viewport {viewport['name']}")
        observations.append({
            "viewport": viewport["name"],
            "status": ("passed" if matches[0]["passed"] else "failed") if matches else "not_run",
        })
    statuses = {entry["status"] for entry in observations}
    if "failed" in statuses:
        status = "failed"
    elif statuses == {"passed"}:
        status = "passed"
    elif "passed" in statuses:
        status = "incomplete"
    else:
        status = "not_run"
    return {"status": status, "step": name, "observations": observations}


def build_report(archive, qa_result, platforms, limit, pause_check, save_check, ledger=None):
    build = inventory(archive)
    reference = reference_check(archive, ledger)
    qa = load_candidate_qa(qa_result) if qa_result else None
    viewports = qa["viewports"] if qa else []
    budget = {"status": "not_run"}
    if limit is not None:
        budget = {
            "status": "passed" if build["archive_bytes"] <= limit else "failed",
            "max_archive_bytes": limit,
        }
    return {
        "version": 1,
        "archive": build,
        "archive_budget": budget,
        "reference_only": reference,
        "candidate_browser_qa": qa,
        "archive_browser_match": {"status": "unverified"} if qa else {"status": "not_run"},
        "pause": named_check(viewports, pause_check),
        "save": named_check(viewports, save_check),
        "platforms": [{"name": platform, "status": "unverified"} for platform in dict.fromkeys(platforms)],
    }


COPY = {
    "en": {
        "title": "Pre-release report", "eyebrow": "Release candidate", "issue": "GitHub issue",
        "archive_size": "Archive size", "files": "Files", "uncompressed": "Uncompressed", "platforms": "Targets",
        "checks_heading": "Checks", "files_heading": "Largest files in the archive", "path": "Path",
        "size": "Size", "compressed": "Compressed",
        "reference": "Reference-only files",
        "reference_none": "No reference-only file is in the archive.",
        "reference_found": "These files came from a tool whose licence forbids commercial use. Replace them before release.",
        "reference_not_run": "No reference-only ledger was given (--reference-ledger).",
        "budget": "Archive budget", "browser": "Candidate browser QA", "match": "Archive matches the tested build",
        "pause": "Pause", "save": "Save and restore", "platform": "Platform",
        "passed": "Passed", "failed": "Failed", "not_run": "Not run", "unverified": "Unverified", "incomplete": "Incomplete",
        "limit": "Limit", "measured": "Measured", "commit": "Candidate commit", "step": "Step",
        "no_budget": "No archive budget was supplied for this target.",
        "no_qa": "No browser QA summary was supplied.",
        "match_text": "The ZIP and the served build are measured separately. Their bytes are not compared by this tool.",
        "platform_text": "Platform acceptance is done through that platform's own flow and current requirements.",
        "caveat": "Only measured facts are marked as passed. Everything this tool cannot check stays unverified until the approved release flow confirms it.",
        "note": "Generated offline from the local ZIP and the recorded browser QA summary.",
        "ready": "ready", "ms": "ms", "overall_failed": "Blocked by a failed check", "overall_open": "Open checks remain",
    },
    "ru": {
        "title": "Предрелизный отчёт", "eyebrow": "Кандидат в релиз", "issue": "Задача на GitHub",
        "archive_size": "Размер архива", "files": "Файлов", "uncompressed": "Без сжатия", "platforms": "Платформ",
        "checks_heading": "Проверки", "files_heading": "Самые большие файлы архива", "path": "Путь",
        "size": "Размер", "compressed": "Сжато",
        "budget": "Бюджет архива", "browser": "Браузерный QA кандидата", "match": "Архив совпадает с проверенной сборкой",
        "pause": "Пауза", "save": "Сохранение и восстановление", "platform": "Платформа",
        "reference": "Файлы только для референса",
        "reference_none": "В архиве нет файлов, отмеченных как «только референс».",
        "reference_found": "Эти файлы сделаны инструментом, лицензия которого запрещает коммерческое использование. Замените их до релиза.",
        "reference_not_run": "Реестр «только референс» не передан (--reference-ledger).",
        "passed": "Пройдено", "failed": "Ошибка", "not_run": "Не запускалось", "unverified": "Не подтверждено",
        "incomplete": "Не полностью",
        "limit": "Лимит", "measured": "Измерено", "commit": "Коммит кандидата", "step": "Шаг",
        "no_budget": "Бюджет архива для этой платформы не задан.",
        "no_qa": "Сводка браузерного QA не передана.",
        "match_text": "ZIP и запущенная сборка измерены отдельно. Этот инструмент не сравнивает их байты.",
        "platform_text": "Приёмка на платформе идёт через её собственный процесс и актуальные требования.",
        "caveat": "Пройденным отмечено только измеренное. Всё, что инструмент проверить не может, остаётся неподтверждённым, пока это не подтвердит утверждённый процесс релиза.",
        "note": "Создан офлайн из локального ZIP и записанной сводки браузерного QA.",
        "ready": "готова", "ms": "мс", "overall_failed": "Есть проваленная проверка", "overall_open": "Остались открытые проверки",
    },
}


def size(value):
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def card(title, status, copy, body):
    return (f'<section class="release-card panel" data-status="{status}"><header><h2>{title}</h2>'
            f'<span class="pill" data-status="{status}">{copy[status]}</span></header>{body}</section>')


def render_html(report, out, lang):
    copy = COPY[lang]
    archive = report["archive"]
    qa = report["candidate_browser_qa"]
    budget = report["archive_budget"]
    cards = []
    if budget["status"] == "not_run":
        cards.append(card(copy["budget"], "not_run", copy, f'<p>{copy["no_budget"]}</p>'))
    else:
        share = min(100, archive["archive_bytes"] / budget["max_archive_bytes"] * 100)
        cards.append(card(copy["budget"], budget["status"], copy,
                          f'<dl class="kv"><dt>{copy["measured"]}</dt><dd>{size(archive["archive_bytes"])}</dd>'
                          f'<dt>{copy["limit"]}</dt><dd>{size(budget["max_archive_bytes"])}</dd></dl>'
                          f'<div class="meter" data-status="{budget["status"]}"><span style="width:{share:.1f}%"></span></div>'))
    reference = report.get("reference_only", {"status": "not_run"})
    if reference["status"] == "not_run":
        cards.append(card(copy["reference"], "not_run", copy, f'<p>{copy["reference_not_run"]}</p>'))
    elif reference["matches"]:
        items = "".join(f'<dt><code>{escape(item["path"])}</code></dt><dd>{escape(item["tool"])}</dd>'
                        for item in reference["matches"])
        cards.append(card(copy["reference"], "failed", copy, f'<p>{copy["reference_found"]}</p><dl class="kv">{items}</dl>'))
    else:
        cards.append(card(copy["reference"], "passed", copy, f'<p>{copy["reference_none"]}</p>'))
    if qa:
        rows = []
        for view in qa["viewports"]:
            state = "passed" if view["scenario_passed"] else "failed"
            ready = f' · {copy["ready"]} {view["ready_ms"]:g} {copy["ms"]}' if view["ready_ms"] is not None else ""
            rows.append(f'<dt>{escape(view["name"])}</dt><dd><span class="pill" data-status="{state}">'
                        f'{copy[state]}</span><span class="muted">{ready}</span></dd>')
        rows = "".join(rows)
        status = "passed" if all(view["scenario_passed"] for view in qa["viewports"]) else "failed"
        cards.append(card(copy["browser"], status, copy,
                          f'<dl class="kv"><dt>{copy["commit"]}</dt><dd><code>{qa["candidate_commit"][:12]}</code></dd>{rows}</dl>'))
    else:
        cards.append(card(copy["browser"], "not_run", copy, f'<p>{copy["no_qa"]}</p>'))
    cards.append(card(copy["match"], report["archive_browser_match"]["status"], copy, f'<p>{copy["match_text"]}</p>'))
    for key in ("pause", "save"):
        check = report[key]
        body = ""
        if check.get("step"):
            observations = "".join(f'<dt>{escape(item["viewport"])}</dt><dd>{copy[item["status"]]}</dd>'
                                   for item in check["observations"])
            body = f'<dl class="kv"><dt>{copy["step"]}</dt><dd><code>{escape(check["step"])}</code></dd>{observations}</dl>'
        cards.append(card(copy[key], check["status"], copy, body))
    for platform in report["platforms"]:
        cards.append(card(f'{copy["platform"]}: {escape(platform["name"])}', platform["status"], copy,
                          f'<p>{copy["platform_text"]}</p>'))
    statuses = {budget["status"], reference["status"], report["pause"]["status"], report["save"]["status"]}
    if qa:
        statuses.add("passed" if all(view["scenario_passed"] for view in qa["viewports"]) else "failed")
    overall = ("failed", copy["overall_failed"]) if "failed" in statuses else ("unverified", copy["overall_open"])
    largest = sorted(archive["files"], key=lambda entry: entry["bytes"], reverse=True)[:15]
    files = (f'<table class="data"><thead><tr><th>{copy["path"]}</th><th class="num">{copy["size"]}</th>'
             f'<th class="num">{copy["compressed"]}</th></tr></thead><tbody>'
             + "".join(f'<tr><td><code>{escape(entry["path"])}</code></td><td class="num">{size(entry["bytes"])}</td>'
                       f'<td class="num">{size(entry["compressed_bytes"])}</td></tr>' for entry in largest)
             + "</tbody></table>")
    stats = "".join(f'<div class="stat"><dt>{label}</dt><dd>{value}</dd></div>' for label, value in (
        (copy["archive_size"], size(archive["archive_bytes"])), (copy["files"], archive["file_count"]),
        (copy["uncompressed"], size(archive["uncompressed_bytes"])), (copy["platforms"], len(report["platforms"])),
    ))
    issue_link = ""
    if qa:
        issue_link = f'<a class="action primary" href="{attr(qa["issue"])}">{copy["issue"]} #{qa["issue"].rsplit("/", 1)[1]}</a>'
    write_new(out, page(
        "release-report.html", lang, title=copy["title"], eyebrow=copy["eyebrow"],
        subtitle=f'{escape(archive["name"])} · <code title="{archive["sha256"]}">sha256 {archive["sha256"][:16]}</code>',
        overall_key=overall[0], overall_label=overall[1], stats=stats, caveat=copy["caveat"],
        checks_heading=copy["checks_heading"], cards="".join(cards), files_heading=copy["files_heading"],
        file_count=archive["file_count"], files=files, note=copy["note"], issue_link=issue_link,
    ))


def positive_bytes(value):
    size = int(value)
    if size <= 0:
        raise argparse.ArgumentTypeError("Expected a positive byte count")
    return size


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="The archive SHA-256 identifies the ZIP. Browser QA describes the served build recorded "
               "in the supplied summary. Matching those bytes requires separate verification.",
    )
    parser.add_argument("--archive", type=Path, required=True, help="Local ZIP to inventory")
    parser.add_argument("--out", type=Path, required=True, help="New JSON report path")
    parser.add_argument("--qa-result", type=Path, help="summary.json from capture_review.py")
    parser.add_argument("--platform", choices=PLATFORMS, action="append", default=[],
                        help="Record a target as unverified. Repeat for multiple targets.")
    parser.add_argument("--max-archive-bytes", type=positive_bytes)
    parser.add_argument("--pause-check", help="Exact name of the scenario step asserting pause behavior")
    parser.add_argument("--save-check", help="Exact name of the scenario step asserting save behavior")
    parser.add_argument("--reference-ledger", type=Path,
                        help="The game's .gamedev-studio-reference-only.json; matching archive files fail the report")
    parser.add_argument("--html", type=Path, help="Also write an offline HTML view of the report to this new file")
    parser.add_argument("--lang", choices=COPY, default="en", help="Language of the HTML view")
    args = parser.parse_args(argv)
    if not args.qa_result and (args.pause_check or args.save_check):
        parser.error("Named checks require --qa-result")
    try:
        report = build_report(
            args.archive, args.qa_result, args.platform, args.max_archive_bytes, args.pause_check, args.save_check,
            args.reference_ledger,
        )
        with args.out.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.write("\n")
        if args.html:
            render_html(report, args.html, args.lang)
    except (BadZipFile, OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Release report: {args.out}" + (f" and {args.html}" if args.html else ""))
    if report["reference_only"]["status"] == "failed":
        for item in report["reference_only"]["matches"]:
            print(f"Reference-only file in the archive: {item['path']} ({item['tool']})", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    raise SystemExit(main())
