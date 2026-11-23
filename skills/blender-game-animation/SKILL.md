---
name: blender-game-animation
description: Rig and animate supplied characters in Blender, revise motion from references, and deliver editable sources plus a verified game export (glTF/GLB or FBX) with a clip manifest. Use for rigging, skinning, clip authoring, bake and export checks before engine integration.
---

# Blender game animation

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first, and use the current engine profile. Integration in the game is `game-animation-integration`; evidence goes through `review-evidence`.

Build an editable animation project from the supplied mesh and references. Inspect existing work before changing it. Establish anatomy, skeleton needs, forward axis, units, frame rate, clips, loop and root-motion behaviour and gameplay events from the task. Do not regenerate a supplied model as an incidental step.

When continuing another artist's file, inventory the rigs, Actions, slots, constraints, reference media and export settings before editing. Keep a source copy and distinguish approved clips from experiments.

## Rig and skin

- Place joints from anatomy and give them stable rolls and bend directions. Keep global placement separate from local body motion. Use editable contact controls where they help.
- Automatic weights are a starting point. Inspect disconnected islands, opposite-side influence, shoulders, hips and rigid items. Normalize after pruning and respect the destination's influence limit (four per vertex for glTF in Godot and three.js).
- Test joint extremes before authoring the whole action library. An IK collapse can be a target or reach problem rather than a weight problem.

## Motion and revisions

- Block support changes, contact, impact and recovery before secondary motion. Judge floor contact on deformed sole geometry.
- Compare the same event in the source video (read it with `video-watch`) and in Blender, and inspect angles absent from the reference. Single-camera depth reconstruction is inferred motion, not measured mocap.
- Keep approved actions while creating revisions. When a frame looks broken, check nearby frames, interpolation, constraints and playback range before adding more animation.
- Stabilize foot support, then add body compression, head response, follow-through and tail motion where appropriate. Check loops through their seam.
- Readability from the game camera and a responsive recovery matter more than a long decorative anticipation. Keep approved gameplay event times.

## Timing and ordinary playback

- Use `duration = (last_frame - first_frame) / fps`. Store duration and contact times in seconds as well as frames. Changing fps alone changes speed; resample in time when converting a clip.
- Keep a source action when making a compact game variant. Each action needs explicit range and fps metadata. Check scene range, preview range and NLA settings separately.
- Test action switching and ordinary Play after saving and reopening; review scenes do not replace this check.
- Bind the intended Action and its compatible slot explicitly. If several rigs share a scene, playback-range ownership includes the rig, Action, slot and clip metadata, not just an Action name. Returning from an effect rig to a character restores the character's range. Suspend automatic range changes while the owner is posing.
- Save a readable textured viewport and verify it after reopening; a render alone does not establish a usable authoring file.

## Bake and hand off

- Bake evaluated motion onto a separate runtime skeleton and keep the control rig. Export the intended mesh, runtime bones and clips; exclude helper bones, unrelated scenes and muted library actions.
- Record textures, clip names, durations, loop flags, root motion and events in the manifest.
- Reimport from a copied directory into a clean scene. Verify bone count, skin, textures, duration and sampled poses in a common coordinate system. Account for UV and normal seam duplicates when comparing geometry; a raw vertex-index comparison can mislead after a valid export. Check permanent mesh edits across every affected action, not just one pose.
- Read [export and integration checks](references/engine-handoff.md) for separate model and clip files, bind-basis failures and the turn-to-locomotion handoff.

Deliver the editable source, the runtime export, source references, review evidence and a short engine guide. Keep **source approval**, **export verification** and **engine integration** separate: a valid GLB or FBX does not wire a gameplay event or an animation tree.

Example: one supplied robot with Idle and Walk. Verify all foot contacts, the loop seam, normal action playback and a clean reimport.

Dependencies: Blender, the supplied mesh and references, and target-engine access for an integration check. This is a production workflow, not a one-click rigging script.

Source: [Mr. Mak Blender game animation](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/blender-game-animation/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
