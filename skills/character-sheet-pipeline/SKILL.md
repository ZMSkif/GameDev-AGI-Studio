---
name: character-sheet-pipeline
description: Prepare strict-front character sheets, isolated parts and optional multiview references for 3D modeling from an approved character image, with a structured verification rubric and a manifest. Use before modeling, rigging or image-to-3D work on a character.
---

# Character sheets and isolated parts

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first. Image generation is paid: run it only after the owner's yes for the batch (DEC-130) and through the provider the owner chose (`fal-ai-generation`, `higgsfield-workflow` or another connected tool).

Create a consistent reference pack from the owner's supplied character. This is an agent-guided workflow with prompts and visual inspection. It does not bundle a standalone classifier or an automatic mesh-generation service.

Use the supplied design as the authority. Establish the relevant parts, symmetry, pose and the downstream use (modeling, `img2threejs`, a mesh service). Preserve scope that is already approved; do not ask again for an approval the owner has given. Optional views and videos are separate scope with their own cost.

## Steps

1. Inspect the reference and propose the useful body and accessory inventory.
2. Prepare a strict-front A-pose sheet with [01a](prompts/01a_apose_front.md). Match the character's anatomy; keep feet and hands visible, lighting flat and the background neutral. Check identity and pose before extracting any parts.
3. A supplementary multiview sheet can help communicate the whole design: [01b](prompts/01b_character_sheet.md). It does not replace the approved front source for extraction.
4. Extract approved parts from that same source: [body](prompts/02_parts_body.md), [paired items](prompts/03_parts_paired.md), [accessories](prompts/04_parts_accessory.md) and [hair](prompts/05_parts_hair.md). Keep the front camera and the original pose. Do not turn isolated props into hero shots or add new equipment.
5. Inspect every image with the host's image tools or an explicitly configured vision service. [08](prompts/08_3q_classifier.md) supplies the strict-front, side and back rubrics and the retry template. Record *pass*, *soft fail* or *hard fail* with reasons. Retry a failed criterion within the approved budget; repeated failure is a decision to bring to the owner, not a reason for an unlimited paid loop.
6. Only if requested, add [side and back views](prompts/06_multiview.md) for selected parts. Only if requested and budgeted, add [turntables](prompts/07_360_video.md) with a locked camera and a rotating subject. Do not create optional video by default.
7. Deliver an inventory with prompt, provider and model, source hash, local files and review verdicts. Label which source is approved and which outputs still need a decision. Texture, rigging and mesh generation are later tasks.

## About the prompt files

The prompt files are kept as written upstream. Their model lines ("Nano Banana Pro", "GPT Image", a vision model) are the defaults of the original workflow, not restrictions on the owner's explicit choice, and their cost notes are upstream estimates, not prices. Verify current endpoint IDs, schemas and prices with the selected provider before every batch.

Example: a robot with three feet and one telescope. Extract the body, telescope and foot set from the approved front reference. Acceptance means matching shape, pose and lighting, with no missing foot and no new perspective drift.

Source: [Mr. Mak character sheets](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/character-sheet-pipeline/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
