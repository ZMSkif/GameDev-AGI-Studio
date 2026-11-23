---
name: image-reference-workflow
description: Explore image concepts and make faithful edits of accepted references for game art or 3D production, with explicit model choices, a take ledger and visual review. Use for concept rounds, palette studies and single-feature edits of an approved image.
---

# Image references and faithful edits

Apply the `studio-rules`, `art-acceptance` and `asset-licensing` skills first. DEC-140 asks agents to show the owner visual references during preliminary design; DEC-139 asks the Art Director to prevent primitive, template-looking art. Paid generation runs only after the owner's yes for the batch (DEC-130).

Choose exploration or editing from the request. **Exploration** varies design dimensions; **editing** preserves an accepted asset and changes one named feature. Inspect the supplied images before choosing the operation. Respect the requested provider, model, output count, aspect ratio and intended use.

For fal.ai execution use `fal-ai-generation`; for an existing Higgsfield account use `higgsfield-workflow`. Another connected provider can be used when the owner asks for it; inspect its live model schema first.

## Concepts

Vary silhouette, construction, proportions or palette deliberately. Label candidates with stable names (A, B, C…) and keep each prompt. Use the requested number of variations; a model's ability to make more is not a reason to expand the batch.

## Edits

Identify what stays unchanged and the exact delta. Use the accepted image as input, not a reconstruction of it from text. A two-image merge explains the role of each reference (body from A, material from B). Do not inject extra style adjectives that redesign the asset.

## Camera and framing

Choose the camera for the deliverable. A hero concept can use dramatic framing; a modeling sheet needs readable parts and neutral light. Do not force the same camera on every task. When extraction is requested, use `character-sheet-pipeline` instead of treating a cinematic illustration as a parts pack.

## Ledger and review

- Keep prompt, endpoint, seed when available, request ID, cost observed and downloaded outputs together.
- Review identity, framing, missing parts, unintended additions and the requested change, at full size.
- Keep rejected takes with a short reason, and keep the chosen take untouched while making revisions.
- Present the round as an image board with direct file access: put the files and the ledger on the piece Issue through `review-evidence`, or build the local board with `python scripts/reference_board.py` (see `reference/reference-boards.md`).

Example: "Make two observatory robot concepts with different silhouettes." After a selection: "Keep B exactly; change only its blue paint to green." The review checks that the edit kept B's shape, camera, materials and small details. This is an agent workflow, not an automatic quality classifier.

Source: [Mr. Mak image references](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/image-reference-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`).
