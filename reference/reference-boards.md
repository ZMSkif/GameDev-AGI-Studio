# Reference boards

A reference board shows a round of concepts, edits or motion stills side by side, with each take's label, provider, model, request ID, prompt, verdict and reason. It opens offline from disk; every image opens in the zoom viewer. The look follows Mr. Mak Workspace's report style.

Put the images and a `board.json` in one folder (images are local files under that folder; hashes are recorded so the board shows exactly which take was reviewed):

```json
{
  "title": "Robot · round 2",
  "subtitle": "Silhouette exploration for the observatory robot",
  "issue": "https://github.com/<owner>/<game>/issues/12",
  "note": "Owner asked for two silhouettes; B is the favourite so far.",
  "groups": [
    {
      "title": "A — tall telescope",
      "description": "Long neck, three feet.",
      "variants": [
        {"image": "a1.png", "label": "A1", "provider": "fal.ai", "model": "<endpoint>",
         "request_id": "<id>", "prompt": "…", "verdict": "selected", "reason": "Reads best at play distance"},
        {"image": "a2.png", "label": "A2", "verdict": "rejected", "reason": "Feet merge into the ground"}
      ]
    }
  ]
}
```

```text
python <plugin-root>/scripts/reference_board.py --board <folder>/board.json --out <folder>/board.html --lang ru
```

Verdicts: `candidate`, `liked`, `selected`, `approved`, `rejected`. Keep rejected takes on the board with their reason. `approved` means the owner or the independent reviewer approved it on the Issue; write that link in `reason`. A selected take is a design decision, not engine integration.

Never put credentials or signed CDN links in the board; the tool refuses values that look like signed URLs.
