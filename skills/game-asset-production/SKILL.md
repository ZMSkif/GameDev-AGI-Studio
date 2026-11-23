---
name: game-asset-production
description: Produce reviewable game-ready 3D assets from approved references through model, materials, rig or animation, and engine import. Use for character sheets, Blender, baked materials and repeatable export checks.
---

# Game asset production

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills. Use the current game engine profile. DEC-065 and DEC-072 govern acceptance, DEC-094 governs source provenance, and DEC-133 governs the transition from pixel concept to final 3D.

1. **Define the deliverable.** Identify the asset's approved reference, target camera and distances, engine, scale, budget, required channels and clips, and where it appears in gameplay. Confirm which local tools and accounts are available before choosing a pipeline.
2. **Resolve the reference.** For a rigged character, start with a neutral front reference, then add other views only if they resolve missing proportions or attachment points. Keep the silhouette, alignment and optional parts consistent. Record creative choices that need the Art Director's approval.
3. **Build and verify the mesh and materials.** Keep an editable source. Verify scale, origin, orientation, UVs and material channels. Where baking is needed, inspect normal orientation, seams and texture bleed using the target engine and expected distance. Record licensed inputs and derivative work.
4. **Rig or animate when required.** Inspect the bind pose, naming, root motion and important contacts. Confirm clip boundaries, looping, transitions and exported actions or NLA tracks in Blender. Test idle, extreme poses and relevant attachment fit, then repeat in the game runtime using the actual controller.
5. **Hand over the playable result.** Supply the editable source, versioned export, texture or clip map and the tested revision. Take a normal-distance in-engine capture and a short clip for moving assets. Use the `review-evidence` skill to attach files and have the independent reviewer check the approved art criteria.

This workflow uses existing, approved tools. Paid services and external uploads follow the owner's authorization. It works with locally supplied assets and references.

Sources for the workflow: [character sheets](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/character-sheet-pipeline/SKILL.md), [materials and baking](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/materials-to-game/SKILL.md), [Blender animation](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/blender-game-animation/SKILL.md).
