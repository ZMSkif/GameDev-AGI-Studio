---
name: video-watch
description: Inspect a local video as timestamped frames — scene changes, an even step and a dense range around fast action — with an offline report that seeks the original clip. Use for motion references, animation timing, QA clips and gameplay captures.
---

# Video watch

Apply the `studio-rules` skill first. This skill reads a clip; it does not prove timing on its own.

`scripts/video_watch.py` needs only FFmpeg and ffprobe on PATH (`python scripts/doctor.py` reports them). It works on local files. To study an online video, the person downloads it first, with the owner's permission and respecting its licence (`asset-licensing`); the tool never fetches URLs.

```text
python <plugin-root>/scripts/video_watch.py clip.mp4 --out <new-folder> --lang ru
python <plugin-root>/scripts/video_watch.py walk.webm --out <new-folder> --range 1.2 2.4 --dense-fps 24 --copy-source
```

- `--scene` sets the FFmpeg scene-change threshold (default 0.3); `--every` sets the even step (default: a twelfth of the clip).
- `--range START END` with `--dense-fps` samples fast action densely: gait contacts, a strike, a VFX burst. For a walk cycle look for contact, passing, lift and recovery poses.
- `--max-frames` caps the sample (default 60). `--copy-source` copies the clip next to the report so the report stays playable when moved; otherwise the report links to the clip where it is.

The output folder holds `frames/`, `frames.json` (source SHA-256, duration, frame rate, resolution, and each frame's time, frame number and why it was taken) and `report.html`. In the report every frame opens in the zoom viewer, and *Play from here* seeks the original clip to that moment; the timeline shows where the samples fall.

## How to use what you see

- Inspect the extracted images and cite timestamps (and frame numbers) for every observation.
- A sample is not every frame. When sparse samples cannot establish timing or continuity, re-run with a denser range or play the original. Do not claim to have watched every frame from a contact sheet.
- Keep visual observations separate from audio or transcript claims. Check `has_audio` in `frames.json`; transcription needs a separately configured tool.
- Use a new output folder for each source or setting.
- Attach the report folder or its key frames through `review-evidence` when it supports a verdict.

Used by `motion-reference-workflow`, `blender-game-animation`, `game-animation-integration`, `game-vfx-workflow` and `gameplay-visual-review`.

Source: [Mr. Mak video watch](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/video-watch/SKILL.md) (MIT, see `reference/mr-mak-notices.md`), reimplemented on FFmpeg without Python packages or downloads.
