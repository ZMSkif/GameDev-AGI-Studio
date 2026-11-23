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

## Take ledger

Keep a small ledger: source, prompt or edit intent, provider and model, local result, observed problems and decision. Distinguish *generated*, *reviewed*, *selected* and *approved*. Carry the selected take's identity into the `blender-game-animation` handoff.

Example: a two-second robot walk loop with a fixed camera and readable foot contacts. A successful clip loops cleanly and keeps the approved robot; remote completion alone does not establish those properties.

Source: [Mr. Mak motion references](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/motion-reference-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
