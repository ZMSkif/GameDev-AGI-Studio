---
name: review-evidence
description: Assemble an owner-facing acceptance card and verify the exact local captures, clips, exports and build used as review evidence. Use when handing off visual or release work.
---

# Review evidence

Apply the `studio-rules` skill. Add the card to the corresponding GitHub Issue or PR with the `orchestration-playbook` skill. A visual workspace or report can display that card. Decisions and task status are recorded in GitHub (DEC-002). Store large artifacts through the approved storage path (DEC-026 and DEC-115).

Include these fields in the player's or owner's language:

| Field | What to record |
| --- | --- |
| Piece | Issue and PR links, one-sentence goal and tested commit |
| Playable result | Where to open it and the steps to see the change |
| Evidence | Before and after images from comparable runs, a short clip for timing, and the relevant test report or build link |
| Review | Builder, independent reviewer, link to their verbatim verdict and anything they could not check |
| Next step | What needs a decision or what to do next |

For a local file set, use `scripts/review_evidence.py` from the plugin root. Supply paths relative to a shared evidence root. Keep files stable during capture and verification. An example plan shape follows. Replace the sample Issue, commit and paths with those used in the review.

```json
{
  "issue": "https://github.com/example/game/issues/100",
  "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "files": [
    {"role": "before", "path": "captures/before.png"},
    {"role": "after", "path": "captures/after.png"},
    {"role": "clip", "path": "captures/playback.mp4"}
  ]
}
```

```text
python <plugin-root>/scripts/review_evidence.py build --root <evidence-dir> --plan <plan.json> --out <manifest.json>
python <plugin-root>/scripts/review_evidence.py verify --root <evidence-dir> --manifest <manifest.json>
```

Roles are `before`, `after`, `clip`, `build`, `test`, `source` and `export`. `build` writes JSON to stdout by default and refuses to overwrite an existing output file. `verify` reports changed or missing files. Use a trusted copy of the manifest. Successful verification establishes file identity by size and SHA-256. The independent reviewer establishes quality and acceptance separately.

## Open the evidence in a browser

Generate a review page directly from the checked files. Give it a title from the task and record a verdict only when you have the independent result.

```text
python <plugin-root>/scripts/render_review.py --root <evidence-dir> --manifest <manifest.json> --out <evidence-dir>/review.html --title "Mobile HUD review"
```

Open the generated HTML in your browser. Use `--lang ru` for Russian labels. A pair of before and after images of the same dimensions enables the comparison slider. Keep the page and its evidence files in their original relative locations. The page links to the Issue and revision for the decision and discussion. Store or share the bundle using the project's existing evidence policy.

Sources for the workflow: [Mr. Mak cards](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/docs/editable-cards.md) and [asset delivery evidence](https://github.com/witnesstodark/mr-mak-workspace/blob/v0.6.6/scripts/asset-delivery/README.md).
