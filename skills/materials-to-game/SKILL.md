---
name: materials-to-game
description: Create or apply PBR material maps and bake a textured high-poly mesh onto a game mesh, with budget, UV, channel, colour-space and export checks in the target engine. Use for retexturing, high-to-low bake-down and material delivery.
---

# Materials and game bake-down

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first, and use the current engine profile. DEC-133: a pixel concept is not turned into smooth final PBR 3D without the owner's permission.

Identify the requested operation: generate material maps, retexture an existing mesh, or optimize a textured high-poly for a game. These are different tasks. Keep the supplied geometry when only a material change was requested.

For remote material generation through fal (paid, owner's yes first), discover the current material endpoint and read its schema with `fal-ai-generation`. Evaluate the chosen material on the intended surface, not only as a preview tile. For mesh retexturing, inspect the chosen service's geometry and UV inputs separately.

## High-to-low workflow

1. Preserve the textured high-poly source. Choose the target budget from the asset's role, silhouette, camera distance and engine constraints (a portal web game usually has far smaller budgets than desktop Godot).
2. Decimate or retopologize into a separate low-poly. Inspect thin parts, hard edges and the silhouette. A fixed face count does not suit every asset.
3. Unwrap the low-poly and check texel density, seams, overlap and padding.
4. Bake the required detail from source to target. Verify cage or ray distance, transforms and the selected-to-active direction before trusting the bake.
5. Identify base colour, normal, roughness, metalness, AO and any packed channels. Colour maps are sRGB and data maps are linear. Check normal orientation in the target renderer: Godot and three.js use OpenGL-style (+Y) normal maps. Keep packed-channel conventions explicit — glTF packs occlusion, roughness and metalness into R, G and B.
6. Export the low-poly with its maps (glTF/GLB for web and Godot). Reimport from another directory and check material links, scale, silhouette, texture resolution and the compressed texture format the build uses.

## Deliver

Deliver the source, the low-poly, the maps with their colour spaces, the bake settings, measured counts and sizes, a normal-distance in-engine capture and the licences through `review-evidence`.

Example: a textured brass prop reduced for a distant game camera. Acceptance requires the same readable silhouette and a clean material at gameplay distance; a smaller file alone is not enough. Preserve the source mesh.

Dependencies: Blender or the chosen bake tool, the supplied geometry and materials, and a provider account only for a requested remote generation.

Source: [Mr. Mak materials to game](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/materials-to-game/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
