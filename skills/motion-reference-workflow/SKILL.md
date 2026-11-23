---
name: motion-reference-workflow
description: Prepare and select character motion reference videos, or transfer approved motion to a human reference for a later mocap workflow, with a take ledger and contact-level review. Use before authoring game animation from video.
---

# Motion references

Apply the `studio-rules` and `asset-licensing` skills first. Video generation is paid: run it only after the owner's yes for the batch (DEC-130).

Resolve whether the owner needs a character reference video for authored animation or human footage for a later mocap tool. The camera follows that purpose. Character-first and human-first are both valid; keep the owner's chosen route.

## Plan the take

Establish the opening pose, action, contact point, recovery, duration and camera. Use the approved character identity. Before a new video, verify its first-frame pose instead of relying on a model to invent the correct start. Keep the framing stable enough to read the relevant limbs and contacts.

Choose the provider and model from the owner's selection or current discovery, and use `fal-ai-generation` or `higgsfield-workflow` for execution and recovery. The number of candidates comes from the task; do not impose a costly fixed batch.

## Review

Read each candidate with `video-watch` (use a dense sample around the action) and by normal playback. Review support changes, strike readability, foot contact, impossible joints, interpenetration, unwanted camera motion and loop seams. Keep candidate names and decisions stable. Keep longer source motion when making a shorter gameplay variant, and record event times in seconds as well as frames.

## Appearance transfer

Use the accepted video as the motion authority and the approved human or reference image for appearance. Keep camera and timing; do not recreate the action from text. Check the transferred limbs and contacts. Generated human-looking footage is not captured skeleton data: a later mocap extraction and its quality checks are separate work.

For a creature-to-human transfer, verify which limb represents each contact and reject anatomy changes that destroy the original action. Keep the original and any timed trim; do not replace a motion reference with a new performance merely because its appearance is cleaner.

## Motion extraction and retargeting tools

The studio panel and `scripts/studio_tools.py` install these after the person's yes, at pinned revisions, into the machine's tools folder (`~/.gamedev-studio/tools`, or `GAMEDEV_STUDIO_TOOLS`):

| Tool | What it does | Commercial use |
| --- | --- | --- |
| `prompt2rig` | Prompt → fal video → GVHMR → motion on a Mixamo character, live preview at `http://localhost:5177` | No, unless the owner records a commercial licence |
| `motion2mixamorig` | Video or photo of a person → motion or pose on a Mixamo character; `m2mr` CLI or a Blender 4.2+ extension | No, unless the owner records a commercial licence |
| `kimodo` | Text and keyframes → motion on the SOMA skeleton, locally | Yes for SOMA checkpoints whose model card allows it; the SMPL-X variant is R&D only |

prompt2rig and Motion2MixamoRig are Apache-2.0 code, but they run on SMPL-X, MANO and GVHMR, whose licences allow non-commercial research only. They are fully usable in the studio for blocking, previs, timing and as reference for hand-authored animation. Their files must not ship:

1. Right after a take is saved, record it: `python3 scripts/studio_tools.py mark-reference prompt2rig <files…>`. The game's `.gamedev-studio-reference-only.json` keeps a SHA-256 for each file.
2. `build_release_report.py --reference-ledger .gamedev-studio-reference-only.json` fails (exit code 3) when any of those bytes is in the build ZIP.
3. Final animation for a game that is sold comes from Kimodo (a checkpoint whose card allows commercial use), from hand animation in Blender using the reference, or from licensed mocap.
4. If the owner buys the commercial licences (SMPL-X through Meshcapade, MANO via ps-license@tue.mpg.de, and the GVHMR authors' terms), the owner records the link with `studio_tools.py set-licence <tool> <https link>` or in the panel; outputs are then no longer marked. Claude never records this link itself. This is not legal advice.

The person registers for SMPL-X and MANO and creates the fal key; keys go to the tool folder's own `.env` or the game's `.env`, never into chat.

## Take ledger

Keep a small ledger: source, prompt or edit intent, provider and model, local result, observed problems and decision. Distinguish *generated*, *reviewed*, *selected* and *approved*. Carry the selected take's identity into the `blender-game-animation` handoff.

Example: a two-second robot walk loop with a fixed camera and readable foot contacts. A successful clip loops cleanly and keeps the approved robot; remote completion alone does not establish those properties.

Source: [Mr. Mak motion references](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/motion-reference-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
