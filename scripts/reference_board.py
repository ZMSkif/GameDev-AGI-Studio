#!/usr/bin/env python3
"""Render an offline board of concept rounds: variants, prompts, providers and verdicts.

The board is described in a small JSON file next to the images. Images are local
files only; every one is hashed, so the board records exactly which take was
shown. The HTML opens from disk and needs no network.
"""

import argparse
from hashlib import sha256
from html import escape
import json
from os.path import relpath
from pathlib import Path, PurePosixPath
import re
import sys

from report_ui import attr, frame, page, url as file_url, write_new
from review_evidence import ISSUE_URL


IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
VERDICTS = ("candidate", "liked", "selected", "approved", "rejected")
COPY = {
    "en": {"eyebrow": "Reference board", "prompt": "Prompt", "issue": "GitHub issue", "variants": "variants",
           "rounds": "Rounds", "takes": "Takes", "selected_count": "Selected or approved", "rejected_count": "Rejected",
           "candidate": "Candidate", "liked": "Liked", "selected": "Selected", "approved": "Approved", "rejected": "Rejected",
           "note": "A selected take is a design decision, not engine integration. Approval comes from the owner or the independent reviewer on the Issue."},
    "ru": {"eyebrow": "Доска референсов", "prompt": "Промпт", "issue": "Задача на GitHub", "variants": "вариантов",
           "rounds": "Раундов", "takes": "Вариантов", "selected_count": "Выбрано или утверждено", "rejected_count": "Отклонено",
           "candidate": "Кандидат", "liked": "Понравился", "selected": "Выбран", "approved": "Утверждён", "rejected": "Отклонён",
           "note": "Выбранный вариант — это решение по дизайну, а не интеграция в движок. Утверждение даёт владелец или независимый ревьюер в задаче."},
}
STATUS = {"candidate": "pending", "liked": "info", "selected": "selected", "approved": "passed", "rejected": "failed"}
TEXT_FIELDS = {"label", "provider", "model", "request_id", "prompt", "reason", "verdict", "image", "source"}


def text(value, name, limit=4000, required=False):
    if value is None and not required:
        return ""
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f"{name} must be a string of at most {limit} characters")
    if re.search(r"https?://[^\s]*[?&](token|sig|signature|key|X-Amz-)[^\s]*", value, re.I):
        raise ValueError(f"{name} looks like a signed URL; keep signed links out of shareable boards")
    return value


def load(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list) or not data["groups"]:
        raise ValueError("The board needs a non-empty 'groups' list")
    unknown = data.keys() - {"title", "subtitle", "issue", "note", "groups"}
    if unknown:
        raise ValueError(f"Unknown board fields: {sorted(unknown)}")
    issue = data.get("issue")
    if issue is not None and (not isinstance(issue, str) or not ISSUE_URL.fullmatch(issue)):
        raise ValueError("issue must be a full GitHub Issue URL")
    root = path.parent.resolve()
    for group in data["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("variants"), list) or not group["variants"]:
            raise ValueError("Each group needs a non-empty 'variants' list")
        text(group.get("title"), "group title", 200, required=True)
        text(group.get("description"), "group description", 2000)
        for variant in group["variants"]:
            if not isinstance(variant, dict) or variant.keys() - TEXT_FIELDS:
                raise ValueError(f"Variant fields must be among {sorted(TEXT_FIELDS)}")
            for key in TEXT_FIELDS:
                text(variant.get(key), f"variant {key}", required=key in {"image", "label"})
            verdict = variant.get("verdict", "candidate")
            if verdict not in VERDICTS:
                raise ValueError(f"verdict must be one of {VERDICTS}")
            image = PurePosixPath(variant["image"])
            if image.is_absolute() or ".." in image.parts or image.suffix.lower() not in IMAGES:
                raise ValueError(f"{variant['image']}: images are local files under the board folder")
            local = (root / image).resolve(strict=True)
            if root not in local.parents or not local.is_file():
                raise ValueError(f"{variant['image']}: image must be a file under the board folder")
            variant["_path"] = local
            variant["_sha256"] = sha256(local.read_bytes()).hexdigest()
    return data


def render(board_path, out, lang):
    data = load(board_path)
    copy = COPY[lang]
    directory = out.parent.resolve(strict=True)
    groups = []
    takes = selected = rejected = 0
    for number, group in enumerate(data["groups"], 1):
        cards = []
        for variant in group["variants"]:
            takes += 1
            verdict = variant.get("verdict", "candidate")
            selected += verdict in {"selected", "approved"}
            rejected += verdict == "rejected"
            source = file_url(Path(relpath(variant["_path"], directory)))
            caption = f'{group["title"]} · {variant["label"]}'
            image = frame(source, caption, group="board", caption=caption).replace("<img ", '<img class="shot" ', 1)
            meta = " · ".join(escape(variant[key]) for key in ("provider", "model", "request_id") if variant.get(key))
            meta = f'<p class="meta">{meta}</p>' if meta else ""
            prompt = ""
            if variant.get("prompt"):
                prompt = (f'<details><summary>{copy["prompt"]}</summary><pre>{escape(variant["prompt"])}</pre></details>')
            reason = f'<p class="reason">{escape(variant["reason"])}</p>' if variant.get("reason") else ""
            cards.append(
                f'<figure class="variant" data-verdict="{verdict}">{image}<figcaption>'
                f'<div class="label"><span>{escape(variant["label"])}</span>'
                f'<span class="pill" data-status="{STATUS[verdict]}">{copy[verdict]}</span></div>'
                f'{meta}{reason}'
                f'<p class="meta mono" title="{variant["_sha256"]}">sha256 {variant["_sha256"][:12]}</p>{prompt}'
                f'</figcaption></figure>'
            )
        description = f'<p>{escape(group["description"])}</p>' if group.get("description") else ""
        featured = " featured" if any(v.get("verdict") in {"selected", "approved"} for v in group["variants"]) else ""
        groups.append(
            f'<section class="board-group panel{featured}"><header><h2><span class="card-num">{number}</span>'
            f'{escape(group["title"])}</h2>'
            f'<span class="muted">{len(group["variants"])} {copy["variants"]}</span>{description}</header>'
            f'<div class="variants">{"".join(cards)}</div></section>'
        )
    stats = "".join(f'<div class="stat"><dt>{label}</dt><dd>{value}</dd></div>' for label, value in (
        (copy["rounds"], len(data["groups"])), (copy["takes"], takes),
        (copy["selected_count"], selected), (copy["rejected_count"], rejected),
    ))
    issue = data.get("issue")
    issue_link = (f'<a class="action primary" href="{attr(issue)}">{copy["issue"]} #{issue.rsplit("/", 1)[1]}</a>'
                  if issue else "")
    callout = f'<p class="callout">{escape(text(data.get("note"), "note", 2000))}</p>' if data.get("note") else ""
    write_new(out, page(
        "reference-board.html", lang,
        title=escape(text(data.get("title"), "title", 200) or copy["eyebrow"]),
        eyebrow=copy["eyebrow"], subtitle=escape(text(data.get("subtitle"), "subtitle", 500)),
        issue_link=issue_link, stats=stats, callout=callout, groups="".join(groups), note=copy["note"],
    ))
    return takes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, required=True, help="Board JSON next to its images")
    parser.add_argument("--out", type=Path, required=True, help="New HTML file")
    parser.add_argument("--lang", choices=COPY, default="en")
    args = parser.parse_args(argv)
    try:
        takes = render(args.board, args.out, args.lang)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Reference board: {args.out} ({takes} takes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
