---
name: game-audio-workflow
description: Select and integrate game sounds with traceable takes, confirmed runtime events, mixer limits and listening tests at gameplay distance.
---

# Game audio workflow

Read `studio-rules`, `asset-licensing`, the game's audio direction and the current engine profile. DEC-141 (#143) calls for a distinct audio identity per game. For web builds use `web-audio-lifecycle` for platform-specific playback checks.

1. **Define the event map.** Identify distinct meanings such as UI press, movement, release, confirmed material contact, reaction and result. Record the authoritative event, expected timing and intended bus or mixer group, distance, concurrency and variation. Measure the anchor from the accepted clip or live game state.
2. **Track the takes.** Keep a stable take ID, editable source, audition export and runtime asset with provenance and licence. Record selected takes, cut points, fades and gain changes. Check clipping, silence, duration and loop seams by inspecting and listening to the actual files. Keep creative acceptance separate from import validation.
3. **Wire the approved sounds.** Reuse existing event bindings, audio settings and buses (Godot) or game mixer/groups (web). Bind footsteps to observed contact or verified distance and phase. Play a hit sound once for confirmed contact, suppress it when the action is canceled, and play result cues once from the result event. Limit repeated cues in crowds and alert bursts to the approved mix.
4. **Listen inside the game.** Test normal gameplay distance, a representative crowd, pause, mute, scene transitions and cleanup, including focus and advertisement lifecycle where relevant. Record tested event times, observed mix/concurrency, device or browser and relevant gaps. Attach a native listening clip and event-to-file mapping for independent review.

[Mr. Mak game audio](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-audio-workflow/SKILL.md).
