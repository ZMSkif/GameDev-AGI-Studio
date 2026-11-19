---
name: art-acceptance
description: The art acceptance bar of GameDev Studio games - no primitives anywhere, the two-distance check (game camera at 1:1 and a close-up) with tiers A/B/C, reworking ready-made or AI blanks into own assets with provenance kept, 3D item icons, and the wearables posed-fit gate with the poke-through check. Use when making, reviewing or accepting any model, prop, icon, wearable, building or reward picture, or when something looks primitive, flickers or pokes through.
---

# Art acceptance

Binding: DEC-139 (#141) no primitive or template look; DEC-065 (#66) assets match the Art Bible and references; DEC-072 (#73) an independent art reviewer; DEC-040 (#40) nobody accepts own work; DEC-064 (#65) the 3D character pipeline ending in in-engine validation; DEC-133 (#135) no pixelation in final smooth 3D without the owner; DEC-094 (#95) provenance and licence for everything; DEC-140 (#142) references shown to the owner before production; DEC-016 (#16) no invented checks.

## 1. Nothing primitive ships

A primitive is anything that reads as its building blocks: code-built spheres, cylinders and boxes for items; flat or glyph icons for items, rewards or currency; basic-shape props; flat CSS stand-ins; emoji as icons. Placeholders may exist only on a branch or in a mockup, clearly labelled, never in a sandbox or release build. Keep a **primitive allowlist** file that only shrinks: a cell leaves it in the commit that ships its real model. The reviewer rejects any primitive on the piece's screens. UI pictograms (gear, ✕, sound, lock) are a separate drawn set, consistent in one style.

Cat Challenge owner, 17.11.2026: «Любое место с примитивом равно то что это не понравится игрокам. Это критически важно».

## 2. The two distances and the tiers

Check every asset at both distances; the worse one wins:
- **the game camera at 1:1**: a 1280×720 desktop frame and a phone frame (about 390×844), at the pose and yaw the level layout gives the asset under the game's fixed camera;
- **a close-up** at the distance the game can bring the camera to. It is set per game: Cat Challenge used 3 m for city buildings, the locker stage (about 1 m) and the 256 px icon for wearables.

| Tier | Meaning | Result |
|---|---|---|
| **A** | the defect shows at 1:1 in the desktop or phone game frame, layout pose included | blocks |
| **B** | at the close-up the asset reads as mangled, with several artefacts on the face the player uses | blocks |
| **C (WEAK)** | one small spot, or a face the fixed camera never shows | ships with a named follow-up in the batch's weak-spot table |

Check it yourself: both themes or lighting setups, wireframe, raw source next to the rework, the layout pose, phone tier without shadows (shadow patches are not facets). Parse the shipped files to confirm triangle counts, bytes and colliders; never trust the report's numbers. Collider vs mesh: measure the overhang at character height (0.3–1.2 m for Cat Challenge's chibi), not only at the foot.

## 3. Nothing passes into anything

The Cat Challenge owner asked that nothing flickers or sinks into anything. Coplanar faces at least 10 mm apart; overlays through one layer rule (fixed lift and `polygonOffset` tiers, `depthWrite: false`) instead of ad-hoc offsets; near and far planes chosen by measurement; a visual radius equal to the physics radius. A separate audit agent sweeps the whole game for z-fighting and intersections.

## 4. Reworking ready-made or AI blanks "as your own"

Only where the owner allowed it for the game (Cat Challenge: «можешь и готовое брать главное подогнать так чтобы было как свое»), and never as "fully generative AI without visual rework" (Playgama 4.3). Rework keeps provenance: the source file, its generator task id or pack, the licence, the output SHA-256 and a list of changes (DEC-094).
1. **Spec lines first:** write the features the asset must show before modelling; the reviewer ticks each one.
2. **Measure the source by colour family** (sections, hue scans) before painting. The AI texture is a measuring tape only; it never draws a border. Declare the source hues of each paint rule and read a source check that flags faces whose texel belongs to another rule.
3. **Paint regions by geometry rules** (box, ellipsoid, plane, capsule, angle bands) evaluated per texel; borders must be exact curves, without sawtooth or speckles. Cut bands with an exact plane bisect before labelling, or decimation pokes single vertices across a border.
4. **Smooth noisy parts before decimating**; round posts and trunks about their axis; rebuild small raised details (knobs, studs, stars) as own low-poly parts; give wheels, lamps, doors and glass own turned or modelled parts. A hero building or the most-seen item gets an own build, not a decimated shell.
5. **Palette and theme:** colours are palette cells recoloured by the theme; no baked AI pixels, no material of its own.
6. **Raw files are untrusted input:** open them with automation disabled (Blender `--factory-startup --disable-autoexec`). The rebuild is scripted and byte-identical from the blanks.

## 5. Item icons

Cat Challenge rule (owner, 17.11.2026): items, rewards, currency, prizes and props show only 3D renders of their real models on rarity backdrops. The icon scene uses the same material contract as the game (a review found the scene's room light leaking into the coin because three.js r187 ignores `envMapIntensity` on a material without its own map, so the currency rendered pale). Coin piles grow with the amount, never shrink. A held item shows a name card, not a stuck shimmer. Names fit their tiles in every language (a German compound overflowed a 64 px tile). Mind the atlas memory on phones.

## 6. The wearables posed-fit gate

For anything worn on an animated character (Cat Challenge `assets/characters/wearables/ASSET_SPEC.md` §3.1, unmerged WA-1 branch):
- **Rest fit:** 10 mm clear of the body and every hair style it is worn with; shoes replace the base shoe.
- **Posed fit:** through every gameplay clip, including push and shove, each item point stays outside the body, **part by part** (head, torso, arms, legs, each hair style), using the part's own surface with a winding-number test near open rims. Limits: under 1.5 cm into the item's own region, under 3 cm into any other part; where the body's own 12 mm skin shell is already deeper, the shell depth sets the baseline. Roll, hit and eliminated clips are reported, not gated.
- **Still unsettled (19.11.2026):** gate v2 lets an item go shell + 1.5 cm deep. Review 68 of the Cat Challenge archive rules for a continuous `allowed = max(limit, shell + 1.5 cm)`, 12 frames per clip, a pass only at a worst excess of −0.2 cm or less, on LOD0 and LOD1. Use the stricter reading until the game's coordinator settles it.
- **Poke-through check:** a pass on the numbers with a visible poke-through is a fail. The v2 pixel check judged frames against the idle pose, so a defect already present at idle counted as "layering" (wide capes cut by the arms passed). Review 68 proposes rendering body and item depth separately and failing where both surfaces are visible within 5 mm of each other, over 20 px per part per frame and view at 640 px, in all views and all gated frames including idle.
- **Controls:** the rule is one function with its numbers under test; a known-bad item (the shipped backpack) must FAIL; mutants of the rule (baseline removed, margins ×10) must fail tests; a "test every shipped item" loop over an empty list proves nothing, so assert the expected set.
- If no design passes, do not loosen the gate: ask the owner with pictures and options (another garment, or own swing bones).

## 7. Characters

New 3D characters follow DEC-064 in either engine profile. The ten-step process that worked: finish one character and check it in the game camera; fix the shared skeleton, rest pose, axes, scale and bone names; pick the clips; retarget offline in Blender and fix feet, knees, head and hand intersections; in-place clips; a procedural layer (ears, tail, gaze, blink, squash and stretch); check front, side and game camera, slow and at speed; export GLB and check the clips before and after optimisation; test 20 skeletons at once with and without shadows; only then replicate.

## Source

Cat Challenge: `assets/city/ASSET_SPEC.md` (recipe notes), `assets/characters/wearables/ASSET_SPEC.md` (§1; §3.1 on the unmerged WA-1 branch, 19.11.2026), `STACK_PLAYBOOK.md` §6.2, reviews 05, 09, 24, 37, 41, 63, 66 and 68 of `docs/reviews/`, and the owner's rules in its `OWNER_DECISIONS.md` and memory (no primitives, 17.11.2026).
