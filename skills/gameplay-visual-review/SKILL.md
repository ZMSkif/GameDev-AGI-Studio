---
name: gameplay-visual-review
description: Verify a visual game change using controlled native captures, targeted behavioural checks and a reviewable evidence record. Use for animation, VFX, HUD, scene or feel changes whose appearance must be judged in the running game, and to prepare or assess playable visual evidence.
---

# Gameplay visual review

Apply the `studio-rules` skill first. Use the piece's acceptance lines and the `art-acceptance` or `game-feel-controls` skill when relevant. An independent reviewer is responsible for the verdict (DEC-040, DEC-072); quality claims need real engine, browser or device tests (DEC-129).

Read the requested change and its accepted baseline. Choose a short test that can reveal the difference. Preserve the current scene and unrelated systems: inspect editor state before taking control, and coordinate if another agent is already using the same editor. Do not restart an active tool merely for a capture.

## 1. Build a fair comparison

- Record the commit, engine and build, scene and saved state or seed, camera, viewport, input method and the steps that reproduce the shot.
- Use the game's actual camera, lighting, materials and normal playback speed. Keep seed, subjects, route or action and framing comparable for OFF/ON or before/after captures. Record any unavoidable difference.
- A slow-motion close-up is useful diagnostic evidence; it does not replace normal gameplay zoom. Add a close-up only when the asset needs one.
- A review lab isolates the changed feature while keeping its production code path. Do not "fix" a comparison with a separate demonstration implementation.
- If synthetic input is needed, keep it separate from physical devices and restore the prior input settings afterwards. Discard transient test orders instead of saving them into the authored scene.

## 2. Check appearance and behaviour separately

- Animation: contact, seams, interrupted transitions, responsive controls.
- VFX: contrast, overlap, attachment, cleanup.
- UI: readability, overflow, input blocking, real state, the narrow and wide supported screens.
- Terrain and levels: scale, grounding, traversal, the gameplay camera.

Counters, hashes and saved values prove wiring or unchanged inputs, not visual quality. A screenshot proves a visual state, not a timed transition. A passing browser study does not prove native rendering cost or physical-device behaviour. Measure the relevant system only and keep unrelated sound and narration quiet during visual-only checks. Record external blockers, missing test devices and any difference between the review build and the release build.

## 3. Leave useful evidence

- Record the source revision, saved configuration, exact scenario, capture type, observations and remaining issues.
- Label generated art, browser schematics, isolated engine previews and native gameplay clearly. A successful agent check does not mean the owner accepted the result.
- Provide short local loops or videos for motion and stills for detail. Keep the original capture and a lightweight review copy with provenance. Do not repeatedly recompress an already compressed delivery.
- Update the current specification when behaviour changes; put chronological details in the development log.
- Attach everything with the `review-evidence` skill: Issue, exact revision, captures and the verbatim reviewer verdict.

To inspect a clip frame by frame with timestamps, use the `video-watch` skill on the captured file.

## Browser QA

For a web build with a reproducible scenario, use [browser visual QA](../../reference/browser-visual-qa.md). Run it at the two revisions and report the failures, captures and tested sizes from its report. Use real device evidence when the acceptance line calls for a physical device or platform integration.

Example: compare a shield impact OFF/ON on dark and pale ground with identical gameplay. Deliver the visible comparison plus the cancellation and cleanup results, and leave final aesthetic acceptance explicit.

Dependencies: native engine access and a local capture method; the report viewer is optional.

Source: [Mr. Mak gameplay visual review](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/gameplay-visual-review/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
