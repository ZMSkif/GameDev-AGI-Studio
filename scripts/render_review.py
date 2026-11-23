#!/usr/bin/env python3
"""Render an offline HTML report for a verified review evidence manifest."""

import argparse
from html import escape
from pathlib import Path, PurePosixPath
from os.path import relpath
import sys
from urllib.parse import quote

from report_ui import STYLES, frame, markers, page, seconds, write_new
from review_evidence import IMAGE_SUFFIXES, load_document, measure


VIDEOS = {".mp4", ".ogv", ".webm"}
COPY = {
    "en": {
        "default_title": "Review evidence", "issue_label": "GitHub issue", "back_label": "All viewports",
        "revision_label": "Reviewed revision", "verdict_heading": "Recorded verdict",
        "capture_heading": "Captures", "gallery_label": "Gallery", "compare_label": "Compare",
        "range_label": "Amount of the Before capture shown", "file_details": "File details",
        "file_note": "Files matched their SHA-256 manifest when this report was generated. Keep this page and its evidence in their existing relative locations.",
        "empty_gallery": "File details are available below.",
        "unsupported_video": "Your browser cannot play this video.",
        "before": "Before", "after": "After", "clip": "Clip", "build": "Build",
        "test": "Test", "source": "Source", "export": "Export", "bytes_unit": "B",
        "reference": "Reference", "decision_label": "Approval record",
        "confirmed": "Confirmed", "blocked": "Blocked", "pending": "Pending",
        "inspector_heading": "Checks", "markers": "Markers", "show_on_frame": "Show on frame",
        "video_at": "Clip at", "expected": "Expected", "actual": "Actual", "at": "at", "seconds_unit": "s",
        "no_checks": "No checks were recorded for this build.", "browser_errors": "Browser errors",
        "passed": "Passed", "failed": "Failed", "ready": "Ready in", "unit": "ms",
        "baseline_revision": "Baseline", "candidate_revision": "Candidate",
        "end_state": "State at the end of the scenario",
        "type_navigation": "load", "type_step": "step", "type_within": "in viewport",
        "type_no_overlap": "no overlap", "type_error": "error",
        "timing_note": "Times are measured from the moment the browser page opened, which is also when the clip starts.",
    },
    "ru": {
        "default_title": "Материалы приёмки", "issue_label": "Задача на GitHub", "back_label": "Все размеры",
        "revision_label": "Проверенный коммит", "verdict_heading": "Записанный вердикт",
        "capture_heading": "Кадры и видео", "gallery_label": "Галерея", "compare_label": "Сравнить",
        "range_label": "Доля видимой области кадра до изменений", "file_details": "Сведения о файлах",
        "file_note": "При создании отчёта файлы совпали с манифестом SHA-256. Сохраняйте расположение отчёта и материалов относительно друг друга.",
        "empty_gallery": "Сведения о файлах доступны ниже.",
        "unsupported_video": "Браузер не может воспроизвести это видео.",
        "before": "До", "after": "После", "clip": "Видео", "build": "Сборка",
        "test": "Тест", "source": "Исходник", "export": "Экспорт", "bytes_unit": "Б",
        "reference": "Референс", "decision_label": "Решение об утверждении",
        "confirmed": "Принято", "blocked": "Заблокировано", "pending": "Ожидается",
        "inspector_heading": "Проверки", "markers": "Маркеры", "show_on_frame": "Показать на кадре",
        "video_at": "Видео на", "expected": "Ожидалось", "actual": "Получено", "at": "на", "seconds_unit": "с",
        "no_checks": "Для этой сборки проверки не записаны.", "browser_errors": "Ошибки браузера",
        "passed": "Пройдено", "failed": "Ошибка", "ready": "Готова за", "unit": "мс",
        "baseline_revision": "Исходная", "candidate_revision": "Новая",
        "end_state": "Состояние в конце сценария",
        "type_navigation": "загрузка", "type_step": "шаг", "type_within": "в экране",
        "type_no_overlap": "без наложения", "type_error": "ошибка",
        "timing_note": "Время отсчитывается от открытия страницы в браузере; с этого же момента начинается видео.",
    },
}
VERDICTS = ("confirmed", "blocked", "pending")


def verify_files(root, document):
    for entry in document["files"]:
        name = entry["path"]
        try:
            actual = measure(root, entry)
        except (OSError, ValueError, RuntimeError) as error:
            raise ValueError(f"{name}: {error}") from error
        if actual != {"bytes": entry["bytes"], "sha256": entry["sha256"]}:
            raise ValueError(f"{name}: bytes or SHA-256 changed")


def asset_url(root, directory, entry):
    path = root / PurePosixPath(entry["path"])
    relative = Path(relpath(path, directory)).as_posix()
    return escape(quote(relative, safe="/"), quote=True)


def side_overlay(qa, side):
    """Markers for every measured region of one build, keyed so checks can point at them."""
    if not qa:
        return ""
    viewport = qa["viewport"]
    result = viewport["builds"].get(side, {})
    return "".join(
        markers(check.get("regions"), viewport["width"], viewport["height"], not check["passed"],
                id_prefix=f"r-{side}-{index}")
        for index, check in enumerate(result.get("checks", []))
    )


def preview(root, directory, entry, copy, qa=None):
    path = PurePosixPath(entry["path"])
    label = copy[entry["role"]]
    name = escape(path.name)
    note = ""
    if path.suffix.lower() in IMAGE_SUFFIXES:
        url = asset_url(root, directory, entry)
        side = entry["role"] if entry["role"] in ("before", "after") else None
        overlay = side_overlay(qa, side) if side else ""
        media = '<div class="media">' + frame(url, f"{label}. {path.name}", overlay=overlay, group="evidence",
                                              caption=f"{label} · {path.name}", lazy=False) + "</div>"
        if qa and side:
            note = f'<span>{copy["end_state"]}</span>'
    elif path.suffix.lower() in VIDEOS:
        url = asset_url(root, directory, entry)
        identifier = f' id="clip-{escape(path.stem, quote=True)}"' if qa else ""
        still = path.with_suffix(".png")
        poster = ""
        if qa and (root / still).is_file():
            poster = f' poster="{escape(quote(Path(relpath(root / still, directory)).as_posix(), safe="/"), quote=True)}"'
        media = (
            f'<video{identifier}{poster} src="{url}" controls playsinline preload="metadata" aria-label="{label}, {name}">'
            f'{copy["unsupported_video"]}</video>'
        )
    else:
        return ""
    decision = ""
    if "decision_url" in entry:
        url = escape(entry["decision_url"], quote=True)
        decision = f'<a class="spacer" href="{url}">{copy["decision_label"]}</a>'
    return (
        f'<figure class="capture panel" data-role="{entry["role"]}">{media}'
        f'<figcaption><strong>{label}</strong><span>{name}</span>{note}{decision}</figcaption></figure>'
    )


def check_item(check, index, side, copy, clip):
    passed = check["passed"]
    kind = check.get("type", "step")
    at = check.get("at_ms")
    unit = copy["seconds_unit"]
    timing = f'<span class="at">{copy["at"]} {seconds(at)} {unit}</span>' if isinstance(at, (int, float)) else ""
    compare = ""
    if "expected" in check or "actual" in check:
        rows = []
        if "expected" in check:
            rows.append(f'<dt>{copy["expected"]}</dt><dd>{escape(str(check["expected"]))}</dd>')
        if "actual" in check:
            rows.append(f'<dt>{copy["actual"]}</dt><dd class="actual">{escape(str(check["actual"]))}</dd>')
        compare = f'<dl class="compare">{"".join(rows)}</dl>'
    tools = []
    regions = check.get("regions") or []
    if passed:
        regions, clip = [], ""
    if regions:
        ids = " ".join(f"r-{side}-{index}-{n}" for n in range(len(regions)))
        tools.append(f'<button type="button" class="action small" data-show-region="{ids}">'
                     f'{copy["show_on_frame"]}</button>')
    if clip and isinstance(at, (int, float)):
        tools.append(f'<button type="button" class="action small" data-video="{clip}" '
                     f'data-seek="{seconds(at)}">{copy["video_at"]} {seconds(at)} {unit}</button>')
    tool_row = f'<div class="tools">{"".join(tools)}</div>' if tools else ""
    return (
        f'<li class="check" data-passed="{str(passed).lower()}"><span class="icon" aria-hidden="true">'
        f'{"✓" if passed else "✕"}</span><div class="title"><b>{escape(check["name"])}</b>'
        f'<span class="type">{copy.get("type_" + kind, kind)}</span>{timing}</div>'
        f'<p class="detail">{escape(str(check.get("detail", "")))}</p>{compare}{tool_row}</li>'
    )


def inspector(qa, copy, directory):
    viewport = qa["viewport"]
    columns = []
    for side in ("before", "after"):
        result = viewport["builds"].get(side)
        if result is None:
            continue
        commit = qa["revisions"].get(side, "")
        status = "passed" if result.get("scenario_passed") else "failed"
        clip = f"clip-{side}" if (directory / f"{side}.webm").is_file() else ""
        items = [check_item(check, index, side, copy, clip) for index, check in enumerate(result.get("checks", []))]
        for error in result.get("errors", []):
            items.append(
                f'<li class="check" data-passed="false"><span class="icon" aria-hidden="true">!</span>'
                f'<div class="title"><b>{copy["browser_errors"]}</b><span class="type">{copy["type_error"]}</span></div>'
                f'<p class="detail">{escape(error)}</p></li>'
            )
        body = f'<ul class="checks">{"".join(items)}</ul>' if items else f'<p class="not-measured">{copy["no_checks"]}</p>'
        ready = result.get("ready_ms")
        timing = f' · {copy["ready"]} {ready} {copy["unit"]}' if ready is not None else ""
        columns.append(
            f'<section class="column panel" data-status="{status}" aria-label="{copy[side]}"><header><div><h3>{copy[side]}</h3>'
            f'<code>{escape(commit[:12])}{timing}</code></div>'
            f'<span class="pill" data-status="{status}">{copy[status]}</span></header>{body}</section>'
        )
    return (
        f'<section class="section" aria-labelledby="inspector-heading"><div class="section-head">'
        f'<h2 id="inspector-heading">{copy["inspector_heading"]}</h2></div>'
        f'<div class="inspector">{"".join(columns)}</div><p class="note">{copy["timing_note"]}</p></section>'
    )


def file_row(entry, copy):
    return (
        f'<li><strong>{copy[entry["role"]]}</strong><span>{escape(entry["path"])}</span>'
        f'<span>{entry["bytes"]:,} {copy["bytes_unit"]}</span><code>{entry["sha256"]}</code></li>'
    )


def render(root, manifest, out, title, verdict, lang, *, from_capture=False, qa=None):
    """Write the evidence page. ``qa`` adds the check inspector and measured markers for a browser run."""
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("The evidence root must be a directory")
    document = load_document(manifest, manifest=True)
    verify_files(root, document)

    directory = out.parent.resolve(strict=True)
    copy = COPY[lang]
    # Keep the two stills together when the manifest interleaves captures and clips.
    priority = {"before": 0, "after": 1, "reference": 2}
    gallery_entries = sorted(document["files"], key=lambda entry: priority.get(entry["role"], 3))
    gallery = "".join(preview(root, directory, entry, copy, qa) for entry in gallery_entries)
    if not gallery:
        gallery = f'<p class="empty">{copy["empty_gallery"]}</p>'
    issue = document["issue"]
    issue_number = issue.rsplit("/", 1)[1]
    repo = issue.rsplit("/issues/", 1)[0]
    commit = document["commit"]
    revisions = (f'<div><dt>{copy["revision_label"]}</dt><dd><a href="{escape(f"{repo}/commit/{commit}", quote=True)}" '
                 f'title="{commit}"><code>{commit[:12]}</code></a></dd></div>')
    if qa and qa["revisions"].get("before"):
        baseline = qa["revisions"]["before"]
        revisions = (
            f'<div><dt>{copy["baseline_revision"]} → {copy["candidate_revision"]}</dt><dd>'
            f'<a href="{escape(f"{repo}/commit/{baseline}", quote=True)}" title="{baseline}"><code>{baseline[:12]}</code></a>'
            f'<span class="commit-arrow">→</span>'
            f'<a href="{escape(f"{repo}/commit/{commit}", quote=True)}" title="{commit}"><code>{commit[:12]}</code></a></dd></div>'
        )
    has_markers = bool(qa) and any(check.get("regions") for build in qa["viewport"]["builds"].values()
                                   for check in build.get("checks", []))
    rendered = page(
        "review.html", lang,
        **copy,
        title=escape(title or copy["default_title"]),
        revisions=revisions,
        inspector=inspector(qa, copy, directory) if qa else "",
        marker_toggle=(f'<button type="button" class="action" data-toggle-markers aria-pressed="true">'
                       f'{copy["markers"]}</button>' if has_markers else ""),
        back_link=(f'<a class="back-link" href="../index.html"><span aria-hidden="true">←</span> '
                   f'{copy["back_label"]}</a>' if from_capture else ""),
        issue_url=escape(issue, quote=True),
        issue_number=issue_number,
        verdict_key=verdict,
        verdict_label=copy[verdict],
        gallery=gallery,
        file_count=len(document["files"]),
        file_rows="".join(file_row(entry, copy) for entry in document["files"]),
    )
    write_new(out, rendered)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Evidence directory")
    parser.add_argument("--manifest", required=True, type=Path, help="Existing manifest JSON")
    parser.add_argument("--out", required=True, type=Path, help="New HTML report path; keep its position relative to the evidence files")
    parser.add_argument("--title")
    parser.add_argument("--verdict", choices=VERDICTS, default="pending", help="Recorded independent verdict from the Issue or PR")
    parser.add_argument("--lang", choices=COPY, default="en", help="Report language")
    args = parser.parse_args(argv)
    try:
        render(args.root, args.manifest, args.out, args.title, args.verdict, args.lang)
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Review report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
