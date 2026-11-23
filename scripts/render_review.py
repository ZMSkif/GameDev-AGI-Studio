#!/usr/bin/env python3
"""Render an offline HTML report for a verified review evidence manifest."""

import argparse
from html import escape
from pathlib import Path, PurePosixPath
from os.path import relpath
from string import Template
import sys
from urllib.parse import quote

from review_evidence import load_document, measure


TEMPLATE = Path(__file__).resolve().parents[1] / "ui" / "review.html"
IMAGES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
VIDEOS = {".mp4", ".ogv", ".webm"}
COPY = {
    "en": {
        "default_title": "Review evidence", "issue_label": "Open GitHub issue",
        "revision_label": "Reviewed revision", "verdict_heading": "Recorded verdict",
        "capture_heading": "Captures", "gallery_label": "Gallery", "compare_label": "Compare",
        "range_label": "Amount of the Before capture shown", "file_details": "File details",
        "file_note": "Files matched their SHA-256 manifest when this report was generated. Keep this page and its evidence in their existing relative locations.",
        "empty_gallery": "File details are available below.",
        "unsupported_video": "Your browser cannot play this video.",
        "before": "Before", "after": "After", "clip": "Clip", "build": "Build",
        "test": "Test", "source": "Source", "export": "Export", "bytes_unit": "B",
        "confirmed": "Confirmed", "blocked": "Blocked", "pending": "Pending",
    },
    "ru": {
        "default_title": "Материалы приёмки", "issue_label": "Открыть задачу на GitHub",
        "revision_label": "Проверенный коммит", "verdict_heading": "Записанный вердикт",
        "capture_heading": "Кадры и видео", "gallery_label": "Галерея", "compare_label": "Сравнить",
        "range_label": "Доля видимой области кадра до изменений", "file_details": "Сведения о файлах",
        "file_note": "При создании отчёта файлы совпали с манифестом SHA-256. Сохраняйте расположение отчёта и материалов относительно друг друга.",
        "empty_gallery": "Сведения о файлах доступны ниже.",
        "unsupported_video": "Браузер не может воспроизвести это видео.",
        "before": "До", "after": "После", "clip": "Видео", "build": "Сборка",
        "test": "Тест", "source": "Исходник", "export": "Экспорт", "bytes_unit": "Б",
        "confirmed": "Принято", "blocked": "Заблокировано", "pending": "Ожидается",
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


def preview(root, directory, entry, copy):
    path = PurePosixPath(entry["path"])
    label = copy[entry["role"]]
    name = escape(path.name)
    if path.suffix.lower() in IMAGES:
        url = asset_url(root, directory, entry)
        media = f'<img src="{url}" alt="{label}. {name}" decoding="async">'
    elif path.suffix.lower() in VIDEOS:
        url = asset_url(root, directory, entry)
        media = (
            f'<video src="{url}" controls playsinline preload="metadata" aria-label="{label}, {name}">'
            f'{copy["unsupported_video"]}</video>'
        )
    else:
        return ""
    return (
        f'<figure class="capture" data-role="{entry["role"]}">{media}'
        f'<figcaption><strong>{label}</strong><span>{name}</span></figcaption></figure>'
    )


def file_row(entry, copy):
    return (
        f'<li><strong>{copy[entry["role"]]}</strong><span>{escape(entry["path"])}</span>'
        f'<span>{entry["bytes"]:,} {copy["bytes_unit"]}</span><code>{entry["sha256"]}</code></li>'
    )


def render(root, manifest, out, title, verdict, lang):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("The evidence root must be a directory")
    document = load_document(manifest, manifest=True)
    verify_files(root, document)

    directory = out.parent.resolve(strict=True)
    copy = COPY[lang]
    gallery = "".join(preview(root, directory, entry, copy) for entry in document["files"])
    if not gallery:
        gallery = f'<p class="empty">{copy["empty_gallery"]}</p>'
    issue = document["issue"]
    issue_number = issue.rsplit("/", 1)[1]
    repo = issue.rsplit("/issues/", 1)[0]
    commit = document["commit"]
    template = Template(TEMPLATE.read_text(encoding="utf-8"))
    rendered = template.substitute(
        **copy,
        lang=lang,
        title=escape(title or copy["default_title"]),
        issue_url=escape(issue, quote=True),
        issue_number=issue_number,
        commit_url=escape(f"{repo}/commit/{commit}", quote=True),
        commit=commit,
        short_commit=commit[:12],
        verdict_key=verdict,
        verdict_label=copy[verdict],
        gallery=gallery,
        file_count=len(document["files"]),
        file_rows="".join(file_row(entry, copy) for entry in document["files"]),
    )
    with out.open("x", encoding="utf-8", newline="\n") as report:
        report.write(rendered)


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
