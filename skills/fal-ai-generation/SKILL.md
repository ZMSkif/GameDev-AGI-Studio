---
name: fal-ai-generation
description: Generate and edit images, create video, audio, 3D assets or material maps through the fal.ai MCP or the bundled Python queue helper, with model discovery, reference uploads, job recovery, local delivery and an owner spending gate. Use for any fal.ai generation in a game project.
---

# fal.ai generation

Apply the `studio-rules` and `asset-licensing` skills first. **Every fal generation spends money on the recipient's own fal account.** DEC-009 and DEC-130 forbid paid actions without the owner's permission, so a real submission needs the owner's yes for that batch, recorded on the piece Issue, and the helper refuses to submit without it. Reading schemas, prices and the dry run are free.

Turn the brief and the supplied references into downloaded, reviewed assets. Use the connected fal.ai MCP when it is available. The bundled helper handles local uploads and queue recovery when the MCP cannot reach the local filesystem.

## Choose the operation

Distinguish concept exploration, faithful editing, reference-sheet preparation, motion generation, mesh generation and material creation. Keep a selected provider, model, accepted image, pose, camera and requested output count. An edit changes the requested feature; it does not redesign the whole asset.

When no model is selected, call `recommend_model` with the actual task, then read `get_model_schema` for the exact endpoint. Similar display names on different providers are not interchangeable endpoint IDs. Read `get_pricing` for the planned batch, especially video or 3D, and put the estimate in front of the owner before asking for the yes. Defaults in an old script are not a model choice.

Read [MCP calls](references/mcp-workflow.md) for parameter examples and recovery, [prompting and review](references/prompting-and-review.md) for concept, edit and material decisions, and [setup](references/setup.md) when connecting a machine. Each recipient uses their own account and credentials.

## Run and retain the job

1. Inspect the selected input files. Upload only the references the task needs. A hosted MCP cannot read a local file path: use the upload helper or a client-side upload tool, then pass the resulting URL.
2. Prepare inputs from the live schema. Fields such as `image_urls`, `image_url`, `aspect_ratio`, `image_size`, `resolution` and duration differ by endpoint. Do not pass every model the same argument object, and do not add web search, background removal, extra views or video unless they serve this task.
3. Prefer `submit_job` for long operations; `run_model` is convenient for images. Immediately save the endpoint, request ID, returned status and result URLs, the input parameters and the owner-approval link in the task directory. `processing` is normal, not failure.
4. Continue with `check_job`, then `get_job_result` when complete. Prefer the canonical URLs the service returns. A wait timeout does not authorize a duplicate submission. A terminal result can still contain a provider error. If submission returned no ID, inspect request history before trying again.
5. Download the outputs before relying on a CDN link. Inspect each asset, keep rejected takes with their reasons and make the chosen result easy to open. Record technical completion separately from visual acceptance. A generated mesh still needs its own rig, topology and export checks.

Keep the prompt, source filenames or hashes, model ID, request ID, local outputs, observed cost and review verdict together. Credentials and raw signed links never go into a shareable report, an Issue comment or a commit. Show the round with `scripts/reference_board.py` and attach it through `review-evidence`.

## Bundled helper

- [Queue helper](scripts/fal_job.py): `--help`, `upload`, `submit`, `status`, `result`. One receipt per job; an existing receipt blocks another submission. `submit` without `--dry-run` requires `--owner-approval <Issue or comment URL>`, which is stored in the receipt. `upload` sends a private file to fal, so it also needs `--owner-approval`.
- [Python dependencies](scripts/requirements.txt): `fal-client` and `python-dotenv`, installed in the project's own virtual environment.
- [Concept input](examples/concept.json) and [edit input](examples/edit.json): neutral requests with no private artwork or working URLs.
- [Example task](examples/WALKTHROUGH.md): a non-spending rehearsal followed by the commands for an approved generation.

Resolve these paths against this skill directory. Run `--help` or `submit --dry-run` to check the installation without a generation. Keys come from the environment or an explicitly selected `.env`; their values are never printed.

Source: [Mr. Mak fal.ai generation](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/.agents/skills/fal-ai-generation/SKILL.md) (MIT, see `reference/mr-mak-notices.md`). fal.ai is a separate product; this skill grants no access to it.
