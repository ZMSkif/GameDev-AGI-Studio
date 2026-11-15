#!/usr/bin/env bash
# Run with authenticated GitHub CLI. Idempotent; no paid actions, deployment, or publishing.
set -euo pipefail
REPO="${1:-ZMSkif/GameDev-AGI-Studio}"
OWNER="${REPO%%/*}"
TITLE="Decision Register"
command -v gh >/dev/null || { echo "GitHub CLI required" >&2; exit 1; }
gh auth status
project="$(gh project list --owner "$OWNER" --format json --jq ".projects[] | select(.title == \"$TITLE\") | .number" | head -n 1)"
if [[ -z "$project" ]]; then
  project="$(gh project create --owner "$OWNER" --title "$TITLE" --format json --jq '.number')"
fi
echo "Using Project #$project"
existing="$(gh project field-list "$project" --owner "$OWNER" --format json --jq '.fields[].name')"
if ! grep -qx 'Area' <<<"$existing"; then
  gh project field-create "$project" --owner "$OWNER" --name Area --data-type SINGLE_SELECT \
    --single-select-options 'Governance,Architecture,Agents,Providers,Memory,Security,Tools,Workers,Games,Assets,Audio,Platforms,QA,Publishing,Budget,Finance,Research,DevOps,UX,Analytics,LiveOps,Learning,Portfolio'
fi
if ! grep -qx 'Phase' <<<"$existing"; then
  gh project field-create "$project" --owner "$OWNER" --name Phase --data-type SINGLE_SELECT \
    --single-select-options 'Global,P0,P1,P2,P3'
fi
gh issue list -R "$REPO" --label decision --state all --limit 1000 --json url --jq '.[].url' |
while IFS= read -r url; do
  [[ -n "$url" ]] || continue
  gh project item-add "$project" --owner "$OWNER" --url "$url" >/dev/null
done
echo "Decision Register Project #$project initialized. Configure views and populate fields per Issue body."
