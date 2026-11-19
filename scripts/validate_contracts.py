#!/usr/bin/env python3
"""Read-only, dependency-free local check of the contract repository."""
from pathlib import Path
import json
import re
import sys

SUPPORTED_VERSION = "1.2.0"
REPO_ISSUES = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/"
ISSUE_URL = re.compile(re.escape(REPO_ISSUES) + r"[1-9][0-9]*")
# Engine profiles (game-production-policy.json). DEC-012 (#12) made Godot 4.x the studio engine;
# the godot profile keeps it. Any other profile needs its own owner decision issue.
PRODUCTION_POLICY = "game-production-policy.json"
PRODUCTION_POLICY_VERSION = "2.0.0"
PRODUCTION_POLICY_MIGRATION = {
    "breaking": True,
    "removed": "engine",
    "read_instead": "engine_profiles.profiles.godot.engine",
}
PROFILE_IDS = {"godot", "web"}
GODOT_ENGINE = "Godot 4.x"
DEC_012_URL = REPO_ISSUES + "12"
WEB_RENDER_KEYS = {"3d", "2.5d", "2d_lite", "2d_rich"}
PROFILE_MODULES = {"godot": "godot-game", "web": "web-game"}
BOUNDARIES = "system-boundaries.json"
# Godot-scoped decisions the godot profile must list: DEC-047 (#47), DEC-069 (#70), DEC-116 (#118).
GODOT_SCOPED_URLS = {REPO_ISSUES + "47", REPO_ISSUES + "70", REPO_ISSUES + "118"}
# The decision that splits the engine into profiles; a web profile, and any use_for limit, cite it.
PROFILE_SPLIT_DECISION = "DEC-145"
# The only decision allowed to defer modules so far: owner decision #146 (DEC-143).
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
    check(isinstance(value, str) and ISSUE_URL.fullmatch(value),
          f"{where}: deferred_by must be a URL of an issue in this repository")
    check(value == PLUGIN_DECISION_URL, f"{where}: deferred_by must be {PLUGIN_DECISION_URL}")


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
    check(authority.get("execution_while_deferred") == "agent_runtime",
          f"{where}: execution_while_deferred must be agent_runtime")


def validate_openapi(spec):
    info = spec.get("info", {})
    check(info.get("x-status") == "deferred", "coordinator.openapi.json: info.x-status must be deferred")
    check_deferred_by(info.get("x-deferred-by"), "coordinator.openapi.json info")


def manifest_links(manifest, filename):
    """URL -> decision id for one contract entry; the two lists must pair up one to one."""
    entry = manifest["contracts"].get(filename)
    check(entry is not None, f"manifest must list {filename}")
    urls, ids = entry.get("decision_issue_urls", []), entry.get("decision_ids", [])
    check(len(urls) == len(ids), f"manifest {filename}: decision_issue_urls and decision_ids differ in length")
    return dict(zip(urls, ids))


def check_issue_list(value, where, field, links):
    """Issue URLs of this repository, each linked in the manifest for every contract in links."""
    check(isinstance(value, list) and value
          and all(isinstance(u, str) and ISSUE_URL.fullmatch(u) for u in value),
          f"{where}: {field} must be a non-empty list of issue URLs of this repository")
    for filename, linked in links.items():
        for url in value:
            check(url in linked, f"{where}: manifest must link {url} for {filename}")


def validate_engine_profiles(policy, links):
    """Profile-aware engine choice; returns the profile ids.

    links maps each contract that carries profile data to its manifest URL -> decision id map.
    """
    policy_links = links[PRODUCTION_POLICY]
    split_urls = {u for u, d in policy_links.items() if d == PROFILE_SPLIT_DECISION}
    where = PRODUCTION_POLICY
    check("engine" not in policy, f"{where}: the top-level engine moved to engine_profiles.profiles")
    check(policy.get("version") == PRODUCTION_POLICY_VERSION,
          f"{where}: version must be {PRODUCTION_POLICY_VERSION} (removing engine is a breaking change)")
    check(policy.get("migration_from_1_0_0") == PRODUCTION_POLICY_MIGRATION,
          f"{where}: migration_from_1_0_0 must tell readers of engine where it moved")
    profiles = policy.get("engine_profiles", {}).get("profiles")
    check(isinstance(profiles, dict) and profiles, f"{where}: engine_profiles.profiles missing")
    unknown = sorted(set(profiles) - PROFILE_IDS)
    check(not unknown, f"{where}: unknown engine profile(s) {unknown}")
    check("godot" in profiles, f"{where}: the godot profile is required (DEC-012)")
    for pid, profile in profiles.items():
        at = f"{where} profile {pid!r}"
        check(isinstance(profile, dict), f"{at}: must be an object")
        check(isinstance(profile.get("engine"), str) and profile["engine"].strip(), f"{at}: engine must name the engine")
        check_issue_list(profile.get("decided_by"), at, "decided_by", links)
        if "profile_decision_issue_urls" in profile:
            check_issue_list(profile["profile_decision_issue_urls"], at, "profile_decision_issue_urls",
                             {PRODUCTION_POLICY: policy_links})
        if "use_for" in profile:
            use_for = profile["use_for"]
            check(isinstance(use_for, list) and use_for and all(isinstance(u, str) and u for u in use_for),
                  f"{at}: use_for must be a non-empty list of strings")
            # The web profile's own check below covers it.
            check(pid == "web" or split_urls & set(profile["decided_by"]),
                  f"{at}: a use_for limit needs {PROFILE_SPLIT_DECISION} in decided_by (DEC-012 alone names one engine)")
    godot = profiles["godot"]
    check(godot.get("engine") == GODOT_ENGINE, f"{where} profile 'godot': engine must stay {GODOT_ENGINE} (DEC-012)")
    check(DEC_012_URL in godot["decided_by"], f"{where} profile 'godot': decided_by must include {DEC_012_URL}")
    check(GODOT_SCOPED_URLS <= set(godot.get("profile_decision_issue_urls", [])),
          f"{where} profile 'godot': profile_decision_issue_urls must list {sorted(GODOT_SCOPED_URLS)}")
    if "web" in profiles:
        web = profiles["web"]
        check(split_urls & set(web["decided_by"]),
              f"{where} profile 'web': decided_by must cite {PROFILE_SPLIT_DECISION}, its own owner decision")
        render = web.get("render")
        check(isinstance(render, dict) and set(render) == WEB_RENDER_KEYS
              and all(isinstance(v, str) and v for v in render.values()),
              f"{where} profile 'web': render must name a renderer for each of {sorted(WEB_RENDER_KEYS)}")
    if len(profiles) > 1:
        for pid, profile in profiles.items():
            check("use_for" in profile, f"{where} profile {pid!r}: with several profiles each must state use_for")
    return set(profiles)


def validate_profile_modules(boundaries, profile_ids):
    """Each engine profile has exactly its game module, and no module names a missing profile."""
    modules = {m["id"]: m for m in boundaries["modules"]}
    for module in boundaries["modules"]:
        named = module.get("engine_profile")
        if named is not None:
            check(named in profile_ids,
                  f"system-boundaries.json module {module['id']!r}: engine_profile {named!r} is not in {PRODUCTION_POLICY}")
            check(PROFILE_MODULES.get(named) == module["id"],
                  f"system-boundaries.json module {module['id']!r}: engine_profile {named!r} belongs to module {PROFILE_MODULES.get(named)!r}")
    for pid in sorted(profile_ids):
        module = modules.get(PROFILE_MODULES[pid])
        check(module is not None and module.get("engine_profile") == pid and module.get("status") == "active",
              f"system-boundaries.json: profile {pid!r} needs the active module {PROFILE_MODULES[pid]!r} with engine_profile {pid!r}")


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

    boundaries = load(directory / "system-boundaries.json")
    validate_boundaries(boundaries)
    links = {name: manifest_links(manifest, name) for name in (PRODUCTION_POLICY, BOUNDARIES)}
    profile_ids = validate_engine_profiles(load(directory / PRODUCTION_POLICY), links)
    validate_profile_modules(boundaries, profile_ids)
    validate_orchestration(load(directory / "orchestration-policy.json"))
    validate_openapi(load(directory / "coordinator.openapi.json"))
    return len(manifest["contracts"])


def main(argv=None):
    """Validate the repository, or the tree at the optional root path argument."""
    args = sys.argv[1:] if argv is None else argv
    check(len(args) <= 1, "usage: validate_contracts.py [root]")
    root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    count = validate(root)
    print(f"Validated {count} contracts and decision links")


if __name__ == "__main__":
    main()
