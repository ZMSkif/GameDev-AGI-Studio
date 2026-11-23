---
name: game-asset-production
description: Route and govern 3D and 2D game-asset production from approved references to a verified engine import — concepts, character sheets, meshes, materials, rigs, animation, VFX, UI, levels, audio and native review. Use to choose the right production skill and to hand over a game-ready asset.
---

# Game asset production

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first, and use the current engine profile. DEC-065 and DEC-072 govern acceptance, DEC-094 governs provenance and licences, DEC-133 governs the move from a pixel concept to final smooth 3D, and DEC-130 forbids spending without the owner's yes.

Start with the intended deliverable: an image reference, editable geometry, a textured mesh, material maps, a rigged character or engine-ready animation. Inspect the supplied assets and the target engine before choosing a route.

## Choose the route

| Need | Skill |
| --- | --- |
| Explore silhouettes or make a faithful edit of an accepted image | `image-reference-workflow` |
| Strict-front sheet, isolated parts and modeling references | `character-sheet-pipeline` |
| Generate images, meshes, material maps, video or audio through fal.ai (paid) | `fal-ai-generation` |
| Work through an existing Higgsfield account (paid) | `higgsfield-workflow` |
| Editable procedural geometry in Three.js from a reference image | `img2threejs` |
| Validate and deliver a PBR material, or bake high-poly onto a game mesh | `materials-to-game` |
| Prepare or select motion references | `motion-reference-workflow` |
| Read a clip as timestamped frames | `video-watch` |
| Rig, skin, animate and export in Blender | `blender-game-animation` |
| Integrate clips and locomotion transitions in the engine | `game-animation-integration` |
| Event-driven visual effects | `game-vfx-workflow` |
| HUD or menu from concept to live game state | `game-ui-workflow` |
| A playable level or encounter layout | `game-level-design` |
| Select and integrate game sounds | `game-audio-workflow` |
| Verify the result in the actual game | `gameplay-visual-review` |

Read the selected skill before execution. Its presence does not mean that its MCP, CLI, account or editor is connected: inspect live capabilities and exact model schemas, and keep provider choices and accepted references from the current task.

## Govern the production

1. **Define the deliverable.** Record the approved reference, target camera and play distance, engine, scale and units, polygon/texture/clip budget, required material channels and clips and where the asset appears in gameplay. Confirm which local tools and accounts are available before choosing a pipeline. Record the chosen route and the acceptance criteria on the piece Issue.
2. **Resolve the reference.** A rigged character starts from a neutral strict-front reference; add other views only when they resolve missing proportions or attachment points. A revision starts from the accepted reference itself with the exact visual change written down. Motion references mark start, contact and recovery on the selected take, and the original stays when trimming. Creative choices go to the Art Director for approval (DEC-139, DEC-140).
3. **Keep the acceptance states separate.** Concept acceptance is not mesh acceptance. Check topology, scale, origin, orientation, UVs, materials, rig, root motion and engine import as they apply. A successful API request or an attractive render is not an engine handoff. A generated mesh still needs its own topology, rig and export checks.
4. **Keep provenance.** Every input and output carries its source, licence, provider and model, request or job ID and hash. Paid generations and external uploads happen only after the owner's yes for that batch; private references are uploaded only when the task needs them.
5. **Hand over the playable result.** Supply the editable source, a versioned export, the texture or clip map, the tested revision, a normal-distance in-engine capture and a short clip for moving assets. Use `review-evidence` to attach the files and have the independent reviewer check them against the approved art criteria.

This workflow works with locally supplied assets and references. Paid services stay optional.

Sources: [Mr. Mak 3D production routing](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/3d-production-routing/SKILL.md) and the linked production skills (MIT, see `reference/mr-mak-notices.md`).

## Mixar

When the person has Mixar with Connect MCP and the `mixar-claude` plugin, use its `mixar` MCP tools for scene work in Mixar: read the scene first, build with `execute_bpy_script` in a new scene tab, verify with `render_viewport` and the UV and seam checks, and export with the `web` or `godot` preset. Credit-spending calls (`enqueue_generation`, `create_layered_material`) need `mixar_tool_quote` and the owner's yes first (DEC-130). Record Mixar and the generation provider as the asset's source (DEC-094).
