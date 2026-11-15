#!/usr/bin/env python3
"""Read-only, dependency-free local check of the contract repository."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
directory = root / "contracts" / "v1"
manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
assert manifest["version"] == "1.0.0"
assert len(manifest["contracts"]) >= 11

for filename, reference in manifest["contracts"].items():
    path = directory / filename
    assert path.is_file(), filename
    obj = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(obj, dict), filename
    if filename.endswith(".schema.json"):
        assert obj.get("$schema") == "https://json-schema.org/draft/2020-12/schema", filename
        assert obj.get("additionalProperties") is False, filename
    assert reference["decision_issue_urls"], filename
    assert all(s.startswith("https://github.com/ZMSkif/GameDev-AGI-Studio/issues/") for s in reference["decision_issue_urls"]), filename
print(f"Validated {len(manifest['contracts'])} contracts and decision links")
