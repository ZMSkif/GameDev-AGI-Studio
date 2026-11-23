#!/usr/bin/env python3
"""Sample a local video into timestamped frames and an offline visual report.

Frames come from scene changes, an even sampling step and an optional dense range
(for gait, hits and other fast action). Uses only FFmpeg and ffprobe; no Python
packages and no network. URL downloads are out of scope: fetch the clip first,
with the owner's permission, and point this tool at the local file.
"""

import argparse
from hashlib import sha256
from html import escape
import json
from os.path import relpath
from pathlib import Path
import re
import shutil
import subprocess
import sys

from report_ui import attr, frame, page, url as file_url, write_new


COPY = {
    "en": {
        "title": "Video frames", "eyebrow": "Video watch", "duration": "Duration", "fps": "Frame rate",
        "resolution": "Resolution", "frames": "Frames sampled", "unit": "s", "play": "Play from here",
        "reason_scene": "scene", "reason_uniform": "even step", "reason_dense": "dense",
        "player": "Original clip", "current": "Current time", "timeline": "Sampled moments",
        "note": "These are sampled frames, not every frame. Confirm timing, contacts and continuity by playing the original.",
        "no_source": "The original clip is not next to this report; open it separately to play.",
        "frame": "frame", "sha": "Source SHA-256", "grid": "Frames",
    },
    "ru": {
        "title": "Кадры видео", "eyebrow": "Разбор видео", "duration": "Длительность", "fps": "Частота кадров",
        "resolution": "Разрешение", "frames": "Кадров взято", "unit": "с", "play": "Смотреть отсюда",
        "reason_scene": "смена сцены", "reason_uniform": "шаг", "reason_dense": "плотно",
        "player": "Исходное видео", "current": "Текущее время", "timeline": "Взятые моменты",
        "note": "Это выборка кадров, а не каждый кадр. Тайминг, контакты и непрерывность подтверждайте просмотром оригинала.",
        "no_source": "Исходного видео рядом с отчётом нет; откройте его отдельно.",
        "frame": "кадр", "sha": "SHA-256 исходника", "grid": "Кадры",
    },
}
PLAYABLE = {".mp4", ".webm", ".ogv", ".mov", ".m4v"}


def tool(name):
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} is required; install FFmpeg and make sure {name} is on PATH")
    return found


def run(arguments):
    return subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def rate(value):
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        top, bottom = value.split("/", 1)
        return float(top) / float(bottom) if float(bottom) else None
    return float(value)


def probe(video):
    result = run([tool("ffprobe"), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(video)])
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe could not read the video: {result.stderr.strip()[:300]}")
    data = json.loads(result.stdout)
    streams = [stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"]
    if not streams:
        raise ValueError("The file has no video stream")
    stream = streams[0]
    duration = float(stream.get("duration") or data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise ValueError("Could not determine the video duration")
    fps = rate(stream.get("avg_frame_rate")) or rate(stream.get("r_frame_rate"))
    return {"duration": round(duration, 3), "fps": round(fps, 3) if fps else None,
            "width": stream.get("width"), "height": stream.get("height"), "codec": stream.get("codec_name"),
            "has_audio": any(item.get("codec_type") == "audio" for item in data.get("streams", []))}


def scene_times(video, threshold):
    result = run([tool("ffmpeg"), "-hide_banner", "-nostats", "-i", str(video), "-an",
                  "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg scene detection failed: {result.stderr.strip()[-300:]}")
    return [float(match) for match in re.findall(r"pts_time:([0-9.]+)", result.stderr)]


def plan(info, scenes, every, dense, max_frames):
    """Choose the moments to extract, keeping the reason for each."""
    duration = info["duration"]
    step = 1 / info["fps"] if info["fps"] else 0.04
    last = max(0.0, duration - step)
    candidates = [(0.0, "scene")] + [(time, "scene") for time in scenes if time < duration]
    every = every or max(duration / 12, step)
    time = every
    while time < last:
        candidates.append((round(time, 3), "uniform"))
        time += every
    dense_moments = []
    if dense:
        start, end, fps = dense
        start, end = max(0.0, start), min(last, end)
        if end <= start:
            raise ValueError("--range must end after it starts and inside the clip")
        time = start
        while time <= end + 1e-9:
            dense_moments.append((round(time, 3), "dense"))
            time += 1 / fps
    chosen = []
    for moment in sorted(dense_moments + candidates, key=lambda item: (item[0], item[1] != "dense")):
        if chosen and moment[0] - chosen[-1][0] < step * 0.9:
            continue
        chosen.append(moment)
    if len(chosen) > max_frames:
        dense_kept = [item for item in chosen if item[1] == "dense"][:max_frames]
        others = [item for item in chosen if item[1] != "dense"]
        room = max_frames - len(dense_kept)
        if room > 0 and others:
            others = [others[round(index * (len(others) - 1) / max(room - 1, 1))] for index in range(room)]
            others = list(dict.fromkeys(others))
        else:
            others = []
        chosen = sorted(dense_kept + others)
    return chosen


def extract(video, moments, directory, max_width):
    directory.mkdir()
    frames = []
    for index, (time, reason) in enumerate(moments, 1):
        name = f"{index:04d}.jpg"
        result = run([tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-ss", f"{time:.3f}", "-i", str(video),
                      "-frames:v", "1", "-vf", f"scale='min({max_width},iw)':-2", "-q:v", "3", str(directory / name)])
        if result.returncode != 0 or not (directory / name).is_file():
            continue
        frames.append({"index": index, "file": f"frames/{name}", "t": time, "reason": reason})
    if not frames:
        raise RuntimeError("ffmpeg extracted no frames")
    return frames


def digest(path):
    hasher = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def report(out, document, source_link, lang, title):
    copy = COPY[lang]
    info = document["source"]
    unit = copy["unit"]
    duration = info["duration"]
    player = f'<p class="callout warning">{copy["no_source"]}</p>'
    if source_link:
        player = (
            f'<section class="player panel" aria-label="{copy["player"]}">'
            f'<video id="clip" src="{source_link}" controls playsinline preload="metadata" data-time-readout="readout"></video>'
            f'<div class="player-bar"><span>{copy["current"]}</span><b id="readout" class="time">0.00 {unit}</b>'
            f'<span class="muted">· {escape(info["name"])}</span></div></section>'
        )
    ticks = []
    for item in document["frames"]:
        left = item["t"] / duration * 100 if duration else 0
        ticks.append(f'<button type="button" class="tick" data-reason="{item["reason"]}" style="left:{left:.3f}%" '
                     f'data-video="clip" data-seek="{item["t"]:.3f}" title="{item["t"]:.2f} {unit}" '
                     f'aria-label="{item["t"]:.2f} {unit}"></button>')
    dense = document["settings"].get("range")
    band = ""
    if dense and duration:
        band = (f'<span class="range" style="left:{dense[0] / duration * 100:.3f}%;'
                f'width:{(dense[1] - dense[0]) / duration * 100:.3f}%"></span>')
    used = sorted({item["reason"] for item in document["frames"]}, key=["scene", "uniform", "dense"].index)
    legend = "".join(f'<span class="{reason}">{copy["reason_" + reason]}</span>' for reason in used)
    timeline = (f'<div class="timeline" aria-label="{copy["timeline"]}">{band}{"".join(ticks)}'
                f'<div class="scale"><span>0</span><span>{duration / 2:.2f}</span><span>{duration:.2f} {unit}</span></div></div>'
                f'<div class="legend">{legend}</div>')
    ratio = f'{info["width"]} / {info["height"]}' if info.get("width") and info.get("height") else "16 / 9"
    cards = []
    for item in document["frames"]:
        frame_number = f' · {copy["frame"]} {round(item["t"] * info["fps"])}' if info.get("fps") else ""
        caption = f'{item["t"]:.2f} {unit}{frame_number}'
        image = frame(file_url(item["file"]), caption, group="frames", caption=caption)
        image = image.replace('<img ', '<img class="shot" ', 1)
        play = (f'<button type="button" class="action small" data-video="clip" data-seek="{item["t"]:.3f}">'
                f'▶ {copy["play"]}</button>' if source_link else "")
        cards.append(f'<figure class="frame-card">{image}<figcaption><span class="time">{item["t"]:.2f} {unit}</span>'
                     f'<span class="muted">{frame_number.lstrip(" · ")}</span>'
                     f'<span class="reason" data-reason="{item["reason"]}">{copy["reason_" + item["reason"]]}</span>{play}</figcaption></figure>')
    resolution = f'{info["width"]} × {info["height"]}' if info.get("width") else "—"
    stats = "".join(f'<div class="stat"><dt>{label}</dt><dd>{value}</dd></div>' for label, value in (
        (copy["duration"], f'{duration:.2f}<small>{unit}</small>'),
        (copy["fps"], f'{info["fps"]:g}' if info.get("fps") else "—"),
        (copy["resolution"], resolution),
        (copy["frames"], str(len(document["frames"]))),
    ))
    write_new(out / "report.html", page(
        "video-watch.html", lang,
        title=escape(title or copy["title"]), eyebrow=copy["eyebrow"], subtitle=escape(info["name"]),
        stats=stats, player=player, timeline=timeline, ratio=attr(ratio),
        grid_heading=f'{copy["grid"]}<span class="count">{len(document["frames"])}</span>',
        cards="".join(cards), note=copy["note"], sha_label=copy["sha"], sha=info["sha256"],
    ))


def watch(video, out, *, scene, every, dense, max_frames, max_width, copy_source, lang, title):
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError("The input must be a local video file")
    if out.exists() or out.is_symlink():
        raise ValueError(f"Output directory already exists: {out}")
    info = probe(video)
    moments = plan(info, scene_times(video, scene), every, dense, max_frames)
    out.mkdir(parents=True)
    frames = extract(video, moments, out / "frames", max_width)
    source_link = ""
    if copy_source:
        target = out / f"source{video.suffix.lower()}"
        shutil.copy2(video, target)
        source_link = file_url(target.name)
    elif video.suffix.lower() in PLAYABLE:
        source_link = file_url(Path(relpath(video, out)))
    document = {
        "version": 1,
        "source": {"name": video.name, "bytes": video.stat().st_size, "sha256": digest(video), **info},
        "settings": {"scene_threshold": scene, "every_s": every, "range": list(dense[:2]) if dense else None,
                     "dense_fps": dense[2] if dense else None, "max_frames": max_frames},
        "frames": frames,
    }
    with (out / "frames.json").open("x", encoding="utf-8", newline="\n") as output:
        json.dump(document, output, ensure_ascii=False, indent=2)
        output.write("\n")
    report(out, document, source_link, lang, title)
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path, help="Local video file")
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    parser.add_argument("--scene", type=float, default=0.3, help="FFmpeg scene-change threshold, 0–1 (default 0.3)")
    parser.add_argument("--every", type=float, help="Even sampling step in seconds (default: duration / 12)")
    parser.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="Dense range in seconds")
    parser.add_argument("--dense-fps", type=float, default=12.0, help="Frames per second inside --range (default 12)")
    parser.add_argument("--max-frames", type=int, default=60, help="Upper limit of extracted frames (default 60)")
    parser.add_argument("--max-width", type=int, default=960, help="Maximum frame width in pixels (default 960)")
    parser.add_argument("--copy-source", action="store_true", help="Copy the clip next to the report for playback")
    parser.add_argument("--title", help="Report title")
    parser.add_argument("--lang", choices=COPY, default="en")
    args = parser.parse_args(argv)
    if not 0 < args.scene < 1:
        parser.error("--scene must be between 0 and 1")
    if args.every is not None and args.every <= 0 or args.dense_fps <= 0 or not 1 <= args.max_frames <= 500:
        parser.error("--every and --dense-fps must be positive and --max-frames between 1 and 500")
    dense = (*args.range, args.dense_fps) if args.range else None
    try:
        document = watch(args.video, args.out.absolute(), scene=args.scene, every=args.every, dense=dense,
                         max_frames=args.max_frames, max_width=args.max_width, copy_source=args.copy_source,
                         lang=args.lang, title=args.title)
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Video frames: {args.out / 'report.html'} ({len(document['frames'])} frames)")
    return 0


if __name__ == "__main__":
    from console_io import prepare_console
    prepare_console()
    raise SystemExit(main())
