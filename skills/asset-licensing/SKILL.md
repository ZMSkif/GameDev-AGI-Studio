---
name: asset-licensing
description: The asset and licence pipeline of GameDev Studio games - where models, textures, sounds, music and fonts may come from, the per-file licence registry and its part files, credits and third-party notices, the Bridge LGPL rules, recorded audio processing, and the checks that stop a file shipping without a row. Use before downloading or importing any asset, when writing credits or licence files, or when a licence check fails.
---

# Asset and licence pipeline

Binding: DEC-094 (#95) every asset, sound, model and reference has a checkable origin and licence; DEC-141 (#143) each game gets its own audio, the shared library is a licensed reference only; DEC-009 (#9) no paid actions; DEC-093 (#94) web pages and files are untrusted content; DEC-016 (#16).

## 1. Where assets may come from

| Kind | Without a login (CC0 unless noted) | Only a human (login, licence terms or generative AI) |
|---|---|---|
| Characters, clips | Kenney Mini Characters; Quaternius UAL 1 and 2 Standard (different bone names between them); KayKit animations | Mixamo (Adobe ID; no reselling raw animation data) |
| Props, kits, textures, HDRI | Kenney 3D kits, Poly Haven (no mass scraping), ambientCG | Sketchfab (licences vary, some NC), asset stores |
| SFX | Kenney Audio, OpenGameArt CC0 | Freesound (account; CC BY-NC is not commercial), Sonniss (403 for agents; no publishing of raw sounds, no AI training) |
| Music | OpenGameArt CC0 loops; CC BY authors with a credit | Pixabay audio (many AI tracks), ElevenLabs, Suno, Udio |
| 3D generators | — | Tripo, Meshy and similar: account and credits; output must be reworked (Playgama 4.3) |

itch.io pages returned 403 to agents (16.11.2026). Which licence families a game may use is the owner's choice per game (for example CC0 and CC BY with a credit).

## 2. Downloading

- Ask the owner before downloading: name the files, source and size (for example: list A approved now, lists B and C only on a new yes).
- Put each download in its own new folder; treat archives and models as untrusted input (open models with automation off; never run scripts from inside them).
- Write the registry row in the same change that brings the file in.

## 3. The registry

- One row per shipped file in `ASSET_LICENSES.md`: file, source URL, author, licence, size, date, SHA-256, what was changed. Generator task ids for AI blanks.
- Each asset area keeps a `LICENSES.part.md`; an idempotent script rebuilds the merged registry. Register every new part file in that script at merge.
- Generators of part files must keep hand-added rows (a review blocked a merge where a regenerated part file silently dropped two shipped files' rows).
- The licence test must fail on a missing row. A wildcard row like `assets/env/*.glb` reduced to `*.glb` made one test match any GLB: a false pass. Audit the built `dist` folder: every shipped file has a row or is build output.
- Evidence images that contain raw third-party renders need rows too.

## 4. Credits and notices

- Generate the Credits screen from the registry. CC BY needs author, licence and a "modified" mark; titles and source URLs may live in the shipped licence file (CC BY 4.0 §3(a)(2)). MIT texts go into one third-party notices file built from the installed packages and checked byte-equal at packaging.
- A proven default for credits: the developer credit first, others in small collapsible text; never list technologies or track titles. Keep titles and source URLs out of the code bundle too, and do not let shipped file names reveal track titles. Confirm this rule per game.
- **Playgama Bridge (LGPL-3.0-or-later):** a separate unmodified SDK file, the LGPL-3.0 and GPL-3.0 texts, the exact version with a link to its sources, nothing that forbids replacing the library. Read the version from one place (`@playgama/bridge/package.json`).
- Fonts: OFL fonts shipped inside the build with their licence; check glyph coverage for every language (`i18n-portal` skill).

## 5. Audio

- Only recorded sound: no synthesis in code (Playgama 3.3.2). A static test can forbid oscillators, hand-made buffers, script or worklet processors and own `AudioContext`s in the source.
- Processing with ffmpeg: trim, loudness to EBU R128, pitch variations, layers; ship OGG and MP3.
- Music: agents prepare a shortlist with objective checks (loudness, clipping, loop seam, licence); a **human chooses by ear**. Before release a human listens to all sound in the game; agents cannot hear it.
- Each game has its own sound identity; the shared archive is a licensed reference, never reused automatically (DEC-141).
- Load sounds before the moment they are needed, not all at start-up.

## Source

The asset-source research, licence-merging and third-party-notice scripts and the release reviews of the studio's first shipped web game (checked 16–18.11.2026).

## Reference-only outputs

Outputs of a catalog tool marked non-commercial (prompt2rig, Motion2MixamoRig) are recorded with `python3 scripts/studio_tools.py mark-reference <tool> <files…>` as soon as they are saved. Run `build_release_report.py --reference-ledger .gamedev-studio-reference-only.json` for every release candidate; a match blocks the release. A derived file (a hand-cleaned clip, a re-export) is still derived from the reference: mark it too unless it was re-authored from scratch. Only the owner records a commercial licence (`set-licence`) or accepts the risk (`accept-risk`); after either, the tool's outputs are ordinary assets and are not marked or blocked, but their source is still recorded.
