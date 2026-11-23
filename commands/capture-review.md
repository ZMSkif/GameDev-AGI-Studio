---
description: Run a project's browser visual QA scenario on two local builds and produce before/after evidence for the configured viewports.
argument-hint: "<scenario JSON path> <new output directory>"
---

Read the browser QA section of the `gameplay-visual-review` skill and its reference. Use the project's supplied configuration and new output directory in `$ARGUMENTS`. Verify both local build URLs and revisions and run `scripts/capture_review.py`. Return the report paths and the observed checks, including failures or missing scenarios. Independent reviewers record acceptance separately.
