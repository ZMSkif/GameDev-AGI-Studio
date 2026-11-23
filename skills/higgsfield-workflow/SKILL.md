---
name: higgsfield-workflow
description: Use the official Higgsfield CLI or its Blender integration to discover models, generate owner-approved assets and resume recorded jobs without duplicate spending. Use when the owner has a Higgsfield account and chose it for images, video or 3D.
---

# Higgsfield operations

Apply the `studio-rules` and `asset-licensing` skills first. Higgsfield jobs spend credits on the recipient's own account: create a job only after the owner's yes for that batch, recorded on the piece Issue (DEC-009, DEC-130). Installing the CLI and signing in are done by the person themselves.

Install the official CLI and vendor skills from their maintained sources; they are not copied into this plugin. The CLI and the Blender-native integration run in different contexts; keep the working route the task selected.

## Read-only discovery (free)

```text
higgsfield --version
higgsfield model list --json
higgsfield model get <job-type> --json
higgsfield workflow list --json
higgsfield generate get <job-id> --json
```

Inspect the exact model's input and media schema before creating a job. A display name, a fal endpoint and a Higgsfield job type are different identifiers. Model IDs and flags change; use the current CLI help and catalog. Do not replace the owner's chosen provider or model with a skill's historical default.

## Approved generation

1. Put the job type, inputs, count and the CLI's credit estimate in front of the owner and wait for the yes.
2. Create the job with the current `generate create` syntax and save the returned job ID, the inputs and the approval link immediately in the task directory.
3. Resume a slow job with `generate get` or `generate wait`. A waiting timeout does not justify submitting again. Inspect a terminal error before retrying, and retry only within the approved batch.
4. Keep estimated credits separate from observed billing.
5. Download the outputs and inspect them. For the Blender integration, verify that the asset was imported and the scene saved, not merely that the remote job finished.

Do not replay numbered project scripts that can submit jobs or depend on old checkpoints; they are not necessarily safe to run twice.

Example: one prop from a supplied reference. Save its job ID, download the model and verify its materials in a disposable Blender scene. Do not claim a rigged or game-ready result from a successful mesh generation; that is `materials-to-game` and `blender-game-animation` work.

Dependencies: the [official CLI](https://github.com/higgsfield-ai/cli), the [vendor skills](https://github.com/higgsfield-ai/skills), the person's own account, and the Blender companion only when that route is used.

Source: [Mr. Mak Higgsfield operations](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/higgsfield-workflow/SKILL.md) (MIT, see `reference/mr-mak-notices.md`). Higgsfield is a separate product; this skill grants no access to it.
