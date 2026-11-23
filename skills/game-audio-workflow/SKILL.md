---
name: game-audio-workflow
description: Build and review game sound banks, map chosen takes to real events, and prepare or verify runtime playback with timing, repetition and mix limits. Use for unit voices, foley, impacts, UI cues, alerts, music and ambience.
---

# Game audio workflow

Apply the `studio-rules` skill first. Read `asset-licensing`, the game's audio direction and the current engine profile. DEC-141 (#143) gives every game its own audio identity: a shared library never copies sounds into a game automatically. For web builds, `web-audio-lifecycle` covers unlock, focus, visibility and advertisement pauses.

Start with an event inventory and native motion or gameplay references. Separate unit voice, movement and gear, weapon air, material impact, recipient reaction, UI, strategic alerts, music and ambience. A good recording can still be wrong for the event, the camera distance or the crowd mix.

## 1. Define the event map

For each event record its meaning, the authoritative game event, the motion anchor measured from the accepted clip or live state, the source or generation route, the desired length, the bus or mixer group, distance, concurrency, variation and review state.

## 2. Prepare and select material

- Reuse the owner's chosen provider, voice and references. Inspect current tool capabilities instead of copying a stale model identifier. Paid generation follows the owner's spending approval (DEC-130).
- Keep generation IDs so a pending job can be recovered without duplicating it.
- Use stable take IDs and direct local playback. Keep **source**, **audition edit** and **runtime file** distinct. Record cut points, fades, gain, pitch and time changes and source hashes. A compressed preview is not a lossless production master.
- Inspect and listen to the actual samples for clipping, silence, format, duration and loop seams. Technical checks do not establish the desired performance or tone.
- Keep the states *candidate*, *liked for comparison*, *accepted*, *integrated* and *mix-reviewed* separate. Preserve rejected history without presenting it as selected. Do not normalize or replace an accepted original silently. One accepted source may map to several events without duplicate files.

## 3. Follow the real event

- Split an attack into optional effort, swing air, confirmed material contact and recipient reaction. A cancelled attack produces no contact sound. A death voice is separate from the body's actual landing.
- Footsteps follow planted-foot events or the project's verified distance/phase system. An arbitrary timer or a full audition loop drifts from the animation.
- Play one appropriate speaker for a group command, with per-speaker repetition limits. Repeated path updates may change movement without repeating the voice.
- Choose concurrency, variation and distance limits from the actual mix. Coalesce related alerts. Fire a match result once from the authoritative result event, not whenever the HUD refreshes. Do not add a parry cue without a real parry event.

## 4. Integrate and listen

- Use the project's buses (Godot) or mixer groups (web) and its persistent settings. Verify pause, mute, scene changes, interruption, visibility, focus loss, advertisement breaks and source cleanup.
- Audition at gameplay distance and with a representative crowd, then on normal device output. Preserve the owner's mix; do not replay unrelated narration during a focused test.
- Deliver an event-to-file manifest, provenance and licences, original and derived files, selected states, event anchors, a native listening capture and the open mix decisions. Say which checks were technical and which were actually listened to. Attach it through `review-evidence` for independent review.

Example: a robot's walk, swing, metal impact and shutdown. A successful delivery keeps the impact conditional on a hit, aligns the steps, limits crowd repetition and preserves the approved takes.

Dependencies: an audio editor or FFmpeg for edits, the chosen generation or stock tools when requested, and engine access for integration.

Source: [Mr. Mak game audio](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-audio-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
