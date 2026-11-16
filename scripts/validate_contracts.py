#!/usr/bin/env python3
"""Read-only, dependency-free local check of the contract repository."""
from pathlib import Path
import json
import re

SUPPORTED_VERSION = "1.1.0"
REPO_ISSUES = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/"
ISSUE_URL = re.compile(r"^" + re.escape(REPO_ISSUES) + r"[1-9][0-9]*$")
PLUGIN_DECISION_URL = REPO_ISSUES + "146"
MODULE_STATUSES = {"active", "deferred"}
# Owner decision #146 (DEC-143): exactly these modules are deferred, not cancelled.
DEFERRED_MODULES = {"coordinator", "worker-agent", "postgresql", "control-center"}
# Contracts changed by #146; the manifest must link the decision for each.
DEFERRAL_CONTRACTS = (
    "system-boundaries.json",
    "orchestration-policy.json",
    "coordinator.openapi.json",
)


class ContractError(AssertionError):
    """A contract check failed (an AssertionError, like the original asserts)."""


def check(condition, message):
    if not condition:
        raise ContractError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_deferred_by(value, where):
    check(isinstance(value, str) and ISSUE_URL.match(value),
          f"{where}: deferred_by must be a URL of an issue in this repository")


def validate_boundaries(boundaries):
    modules = boundaries.get("modules")
    check(isinstance(modules, list) and modules, "system-boundaries.json: modules missing")
    ids = [m.get("id") for m in modules]
    check(len(ids) == len(set(ids)), "system-boundaries.json: duplicate module id")
    for module in modules:
        where = f"system-boundaries.json module {module.get('id')!r}"
        check(module.get("status") in MODULE_STATUSES,
              f"{where}: status must be one of {sorted(MODULE_STATUSES)}")
        if module["status"] == "deferred":
            check_deferred_by(module.get("deferred_by"), where)
        else:
            check("deferred_by" not in module, f"{where}: active module must not have deferred_by")
    deferred = {m["id"] for m in modules if m["status"] == "deferred"}
    check(deferred == DEFERRED_MODULES,
          f"system-boundaries.json: deferred modules {sorted(deferred)} != {sorted(DEFERRED_MODULES)}")
    plugin = [m for m in modules if m["id"] == "studio-plugin"]
    check(len(plugin) == 1 and plugin[0]["status"] == "active",
          "system-boundaries.json: studio-plugin must be an active module")


def validate_orchestration(policy):
    authority = policy.get("authority", {})
    where = "orchestration-policy.json authority.execution"
    check(authority.get("execution") == "postgresql", f"{where}: original value must be preserved")
    check(authority.get("execution_status") == "deferred", f"{where}: execution_status must be deferred")
    check_deferred_by(authority.get("execution_deferred_by"), where)
    check(authority.get("execution_while_deferred") == "agent_session_and_github_issues_prs",
          f"{where}: execution_while_deferred must name the active execution authority")


def validate_openapi(spec):
    info = spec.get("info", {})
    check(info.get("x-status") == "deferred", "coordinator.openapi.json: info.x-status must be deferred")
    check_deferred_by(info.get("x-deferred-by"), "coordinator.openapi.json info")


def validate(root):
    """Validate the contract set under root; return the number of contracts."""
    directory = Path(root) / "contracts" / "v1"
    manifest = load(directory / "manifest.json")
    check(manifest["version"] == SUPPORTED_VERSION, f"manifest version must be {SUPPORTED_VERSION}")
    check(len(manifest["contracts"]) >= 11, "manifest lists fewer than 11 contracts")

    for filename, reference in manifest["contracts"].items():
        path = directory / filename
        check(path.is_file(), filename)
        obj = load(path)
        check(isinstance(obj, dict), filename)
        if filename.endswith(".schema.json"):
            check(obj.get("$schema") == "https://json-schema.org/draft/2020-12/schema", filename)
            check(obj.get("additionalProperties") is False, filename)
        check(reference["decision_issue_urls"], filename)
        check(all(s.startswith(REPO_ISSUES) for s in reference["decision_issue_urls"]), filename)

    for filename in DEFERRAL_CONTRACTS:
        check(filename in manifest["contracts"], f"manifest must list {filename}")
        check(PLUGIN_DECISION_URL in manifest["contracts"][filename]["decision_issue_urls"],
              f"manifest: {filename} must link {PLUGIN_DECISION_URL}")

    validate_boundaries(load(directory / "system-boundaries.json"))
    validate_orchestration(load(directory / "orchestration-policy.json"))
    validate_openapi(load(directory / "coordinator.openapi.json"))
    return len(manifest["contracts"])


def main():
    count = validate(Path(__file__).resolve().parents[1])
    print(f"Validated {count} contracts and decision links")


if __name__ == "__main__":
    main()
