---
name: game-vfx-workflow
description: Design and integrate game VFX around confirmed gameplay events, with visual references, effect cleanup, readability and measured cost in the actual build.
---

# Game VFX workflow

Read `studio-rules`, the approved Art Bible and the current engine profile. Use `game-feel-controls` for the feel gate and `gameplay-visual-review` for evidence.

1. **Design for a signal.** Identify what the player needs to notice, the in-game camera and the surfaces behind the effect. Break the visual reference into useful layers such as contact, travel, lingering state and feedback. Describe shape, contrast, duration, attach point and what should read with effects reduced. Keep concept timings clearly labelled until the engine can confirm them.
2. **Bind it to the real event.** Trace the gameplay event that distinguishes a windup, release, confirmed hit and miss. Connect a projectile trail to travel and the hit effect to confirmed contact. Treat actor sockets, world placement and screen space as distinct coordinate systems. Use an approved surface anchor or actual collision point for floor and wall effects. Keep effect parameters outside the logic that resolves damage and status.
3. **Handle the lifetime.** Record who owns the emitter, what its clock does on pause and which paths end it. Exercise cancellation, teleport, despawn, reuse, scene exit and platform pause where applicable. Reset particles, trail points and timers on pool reuse. Preserve material layers used by other features, such as team tint.
4. **Fit the engine and budget.** In Godot, use the game's signals, clock, renderer and particle/material tooling. In Three.js/PixiJS, attach to the existing game update and pause flow and reuse compatible buffers or sprites where profiling warrants it. Measure a representative worst-case overlap at the target viewport, including low-quality mode where offered.
5. **Show it in play.** Capture on/off at the same camera, seed and action, with a normal-speed clip proving trigger and cleanup. Record the observed timing, active effect count and measured frame cost along with the revision and limitations. Hand it to independent review through `review-evidence`.

[Mr. Mak VFX workflow](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-vfx-workflow/SKILL.md).
