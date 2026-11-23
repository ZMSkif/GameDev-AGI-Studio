---
name: game-vfx-workflow
description: Develop game effects from visual references and motion studies through an engine handoff, with event timing, lifecycle, readability, measured cost and native review. Use for combat, status, environment, object and UI-feedback effects in Godot, Three.js or PixiJS.
---

# Game VFX workflow

Apply the `studio-rules` skill first. Read the approved Art Bible, the current engine profile (`engine-profiles`) and the piece's acceptance lines. Use `game-feel-controls` for the feel gate, `asset-licensing` for every shipped source and `gameplay-visual-review` for evidence. The Art Director owns the visual direction, the Gameplay Engineer owns the integration and an independent reviewer gives the verdict (DEC-065, DEC-072, DEC-139).

Start from the effect's gameplay meaning, the actual game camera and an existing capture. Inspect the relevant animation, event and visibility code before promising a trigger. A diagram can propose appearance; only the engine can prove event timing, cleanup and rendering cost.

## 1. Establish a reviewable direction

- Identify what the player needs to notice, the in-game camera, the play distance and the surfaces behind the effect. DEC-140 asks for visual references during preliminary design: show them to the owner before committing to a direction.
- Separate three things and keep each reachable: the reference board, the proposed motion and the implemented effect. Preserve the owner's selected direction and every revision.
- For a vendor preview, record its source and what should be borrowed. Viewing a preview does not supply an asset licence.
- Use the project's approved provider when new concept art is requested, and only within the owner's spending approval (DEC-130). Do not generate another batch just to turn a chosen direction into a handoff.
- Describe the effect in layers: purpose, shape, colour, attachment, timing and intensity. Typical layers are anticipation, contact, travel, lingering state and feedback. Say what must still read with effects reduced or in low-quality mode.
- Distinguish a continuous state from a one-shot event. A small contact burst, a spreading death stain and an ongoing damage fire need separate lifecycles.
- Make attachment space explicit. A hand glow follows a socket; a released trail stays briefly in world space; a damage number lives in screen space. Treat actor sockets, world placement and screen space as distinct coordinate systems. Changing an emitter must not teleport old particles.
- For an interactive study, expose only useful comparisons: layer isolation, normal and slow playback, scale, ground contrast and the relevant interruption. Label its timings as illustrative when they are not verified animation markers. Keep old versions reachable and use stable option names.

## 2. Write the engine contract

Read [the lifecycle and review checklist](references/implementation.md) when preparing integration.

- Record real release and contact markers from the accepted animation or the gameplay clock. A projectile owns its travel; confirmed contact owns its impact. Connect a trail to travel and the hit burst to confirmed contact, never to the button press.
- A cancelled windup must not schedule a later hit effect. A miss must not play the hit burst.
- Specify where an effect is spawned, who owns it, how it fades and what removes it. Include death, cancellation, despawn, teleport, pooled reuse, scene unload, platform pause and any game-specific visibility or storage transition. Record what the emitter's clock does on pause.
- Reset trail history, particles and timers on teleport or pool reuse.
- For floor, wall and roof effects, use reviewed surface anchors, the actual collision point or validated surface sampling. A bounding box alone does not establish a valid wall, roof or ground contact.
- Use shared materials and bounded pools where profiling warrants it. Restore only this effect's material contribution: preserve team tint, hit flashes and other active states.
- Keep effect parameters outside the logic that resolves damage and status. Do not add damage, buffs or balance changes as incidental VFX work.
- Record unknown tuning values as unresolved instead of filling them from a demo.

### Engine notes

- **Godot 4.x:** drive effects from the game's signals and its own clock; use GPUParticles2D/3D or CPUParticles as the renderer allows, `one_shot` and `finished` for cleanup, and `process_mode` to follow the game's pause rules. Pool with the scene's existing pattern; verify the Web export renderer separately from the desktop one.
- **Three.js:** attach to the existing update loop and pause flow; reuse geometries, materials and instanced buffers; dispose GPU resources when an effect is retired for good. Check transparent sort order and additive blending against the actual background.
- **PixiJS:** attach to the game ticker the gameplay uses; reuse sprites and containers from a pool; destroy textures you created; respect the platform pause and visibility events.

## 3. Fit the budget

Measure the affected system: active emitters, particles, material instances, transparent overlap, allocations and frame cost. Use a representative worst-case overlap at the target viewport and on the target device class, including low-quality mode where it is offered. A passing event counter confirms lifecycle wiring, not visual quality or acceptable performance. Readability should come from silhouette, value, timing and placement before adding bloom.

## 4. Deliver and review

- Deliver the selected appearance, the motion contract, local source references, editable assets and the implementation status.
- Record **concept approval**, **native verification** and **visual acceptance** as three separate states. Use the evidence labels *generated concept*, *code-drawn study* and *native engine capture*.
- Capture a real OFF/ON comparison at normal gameplay zoom with the same action, seed and camera; make sure the underlying gameplay is unchanged. Add a normal-speed clip that proves trigger and cleanup.
- Record observed timing, active effect count, measured frame cost, revision and limitations. Hand everything to independent review through `review-evidence`.
- Add the implemented effect to the project's effect library with its trigger, usage and a native preview, not a generated illustration.

Example request: "Design a small shield impact that remains readable on pale ground, then prepare its integration handoff." Success means a selected direction, a confirmed-hit trigger, a cleanup contract and a native review plan. It does not imply that a concept preview has already been integrated.

Dependencies: the project's references and engine access for implementation. Generation tools are optional and paid ones need the owner's yes.

Source: [Mr. Mak VFX workflow](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/game-vfx-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
