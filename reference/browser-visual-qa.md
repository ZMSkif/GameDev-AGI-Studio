# Browser visual QA

Run the same scenario against two revisions in independent Chromium browser contexts. The project supplies and serves its own builds. Use URLs on the local machine, a full Git commit for each revision and a readiness selector exposed by the game. Start both builds before running the script. The runner leaves the build servers under the project's control.

Run trusted project builds. Each build must keep its main page at the configured origin during the scenario. The browser can still load resources requested by the build.

The optional Python Playwright dependency uses the project's Python environment. Install it and its Chromium browser there if the project has not already set them up. The runner also accepts an explicit Chromium executable for environments with their own browser.

```text
python -m pip install playwright
python -m playwright install chromium
python <plugin-root>/scripts/capture_review.py --config <scenario.json> --out <new-output-dir> --lang ru
```

For short clips, add `--record-video`. Playwright provides its video recorder with the browser installation. Use `--executable-path` if the installed browser must be selected explicitly. See the [Playwright browser installation](https://playwright.dev/python/docs/browsers) and [video recording](https://playwright.dev/python/docs/videos) references.

## Scenario example

Replace the Issue, revisions and selectors with those from the current project. DOM controls, canvas focus targets and explicit game-provided test hooks can all be named as selectors. Record the game state that each action is expected to produce. Keep declarative data in the scenario.

```json
{
  "issue": "https://github.com/example/project/issues/42",
  "before": {"url": "http://127.0.0.1:8100/", "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "after": {"url": "http://127.0.0.1:8101/", "commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
  "ready_selector": "#ready",
  "steps": [
    {"action": "click", "selector": "#start"},
    {"action": "text", "selector": "#status", "text": "Running"}
  ],
  "viewports": ["portrait", "landscape", "square"],
  "layout": {
    "within": ["#pause", "#status"],
    "no_overlap": [["#pause", "#status"]]
  }
}
```

The default layouts are portrait 390 × 844, landscape 844 × 390 and square 512 × 512. Use selectors for visible elements whose geometry matters. Canvas-rendered content still needs game-provided assertions or visual review. These viewport runs test browser layout. Physical device checks, GPU behavior and platform adapters need their own scenarios and evidence.

Use `tap` for an explicit touch step. A step `{"action":"reload"}` reloads the current build and waits for the configured readiness selector in the same browser context. Give behavior assertions unique `label` values if they should appear as named observations in the pre-release report. For example, label the assertion that a Pause action stops the simulation `pause-verified` and the assertion that a saved value survives reloading `save-restored`.

## Results

Open `index.html` in the output directory. It shows the totals, then one card per layout with the baseline and candidate captures side by side, the failed checks listed in the card and their regions marked on the candidate capture. Each card opens that layout's `review.html`, the check inspector:

- every check of both builds with its type, the moment it ran (measured from the page opening, which is also the start of the clip), and for failures the expected and actual values;
- *Show on frame* highlights the measured region of a layout check on the capture; *Clip at …* moves the recorded clip to that moment;
- every image opens in the zoom viewer (wheel or +/−, drag to pan, ←/→ to switch, a markers toggle); the gallery also has a before/after slider.

`summary.json` records both revisions, timing to the configured readiness state, each check with `at_ms`, measured `regions` in CSS pixels and `expected`/`actual` where the runner measured them, plus errors. Older summaries without these fields still render. Keep the reports with their images and clips. A failed probe is evidence of what the runner observed. Use the task's independent review to record acceptance.

## Local pre-release report

Combine a build archive and observations from the run. Supply the ZIP corresponding to the served candidate. The report measures the ZIP separately and identifies the browser observations by the candidate's Git commit. The platform names identify the target profiles. Supply an archive size budget only when the project has confirmed that budget for the current target. The tool records checks with evidence and leaves missing checks unverified.

```text
python <plugin-root>/scripts/build_release_report.py --archive <build.zip> --qa-result <summary.json> --platform playgama --platform youtube-playables --out <release-report.json>
```

Use `--pause-check pause-verified --save-check save-restored` when the scenario has run those named assertions. `--max-archive-bytes` records the limit comparison in the JSON. Add `--html <release-report.html> --lang ru` for an offline view of the same report: archive size against the budget, the candidate's browser results per layout, the named checks, the largest files, and every platform and archive-to-build match shown as unverified.

Run platform-specific acceptance through the approved flow for the game. Use a current requirement source for each platform.
