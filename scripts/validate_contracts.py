#!/usr/bin/env python3
"""Read-only, dependency-free local check of the contract repository."""
from pathlib import Path
import json
import re
import sys

SUPPORTED_VERSION = "1.4.0"
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
# Owner decision #164 (DEC-146): the parts DEC-143 deferred stay deferred for good.
PERMANENT_DECISION_URL = REPO_ISSUES + "164"
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


def check_permanent(value, where):
    check(value == PERMANENT_DECISION_URL,
          f"{where}: deferred_permanently_by must be {PERMANENT_DECISION_URL} (DEC-146)")


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
            check_permanent(module.get("deferred_permanently_by"), where)
        else:
            check("deferred_by" not in module, f"{where}: active module must not have deferred_by")
            check("deferred_permanently_by" not in module,
                  f"{where}: active module must not have deferred_permanently_by")
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
    check_permanent(authority.get("execution_deferred_permanently_by"), where)
    check(authority.get("execution_while_deferred") == "agent_runtime",
          f"{where}: execution_while_deferred must be agent_runtime")


def validate_openapi(spec):
    info = spec.get("info", {})
    check(info.get("x-status") == "deferred", "coordinator.openapi.json: info.x-status must be deferred")
    check_deferred_by(info.get("x-deferred-by"), "coordinator.openapi.json info")
    check_permanent(info.get("x-deferred-permanently-by"), "coordinator.openapi.json info")


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


KNOWLEDGE_POLICY = "knowledge-policy.json"
KNOWLEDGE_SCOPES = ["studio", "project", "task"]                              # DEC-101
RETRIEVAL_MODES = ["auto", "always_verify", "memory_first", "manual"]        # DEC-104
# Tools an agent may never reach in the memory backend: deletion is the owner's (DEC-138), and
# reflect answers carry no sources (provenance_required).
FORBIDDEN_MEMORY_TOOLS = {"delete_bank", "clear_memories", "delete_document", "delete_mental_model",
                          "delete_memory", "invalidate_memory", "reflect"}
NEVER_STORE = {"secrets", "personal_data", "unverified_claims_as_facts"}
REQUIRED_MEMORY_METADATA = {"source_type", "source", "source_rev", "recorded_by", "verified"}
PLACEMENT_VALUES = {"owner_decision_pending", "local", "server"}
PLACEMENT_TASK = REPO_ISSUES + "150"
EVIDENCE_URL = re.compile(re.escape(REPO_ISSUES) + r"[1-9][0-9]*(#issuecomment-[0-9]+)?")
NO_PAID_EXTRACTION = "subscription_or_local_model_never_paid_api"            # DEC-019, DEC-085
FACT_TYPES = ["world", "experience"]
RETAIN_NEVER_PASSES = {"document_id", "update_mode"}                          # DEC-138


def check_against_schema(value, schema, where):
    """The subset of JSON Schema the tool-capability contract uses: required, properties, enums, types."""
    check(isinstance(value, dict), f"{where}: must be an object")
    missing = sorted(set(schema.get("required", [])) - set(value))
    check(not missing, f"{where}: missing {missing}")
    extra = sorted(set(value) - set(schema.get("properties", {})))
    check(not extra or schema.get("additionalProperties", True), f"{where}: properties outside the schema {extra}")
    for key, rule in schema.get("properties", {}).items():
        if key not in value:
            continue
        item = value[key]
        if "enum" in rule:
            check(item in rule["enum"], f"{where}.{key}: {item!r} is not one of {rule['enum']}")
        if rule.get("type") == "boolean":
            check(isinstance(item, bool), f"{where}.{key}: must be true or false")
        if rule.get("type") == "array":
            check(isinstance(item, list) and len(item) >= rule.get("minItems", 0), f"{where}.{key}: must be a list")
            items = rule.get("items", {})
            if items.get("type") == "string":
                check(all(isinstance(i, str) and len(i) >= items.get("minLength", 0) for i in item),
                      f"{where}.{key}: every item must be a non-empty string")
        if rule.get("type") == "string":
            check(isinstance(item, str) and len(item) >= rule.get("minLength", 0), f"{where}.{key}: must be a string")


def validate_knowledge_policy(policy, tool_schema):
    """Memory and learning rules: DEC-024, DEC-046, DEC-101 to DEC-106, DEC-125, DEC-138."""
    where = KNOWLEDGE_POLICY
    check(policy.get("scopes") == KNOWLEDGE_SCOPES, f"{where}: scopes must be {KNOWLEDGE_SCOPES} (DEC-101)")
    order = policy.get("authority_order", [])
    check(order[:1] == ["binding_decision_issues"] and "verified_context_memory" in order
          and order.index("verified_context_memory") > order.index("approved_versioned_gdd_art_bible_architecture"),
          f"{where}: decisions and approved documents must rank above memory (DEC-103)")
    check(policy.get("memory_cannot_override_owner_decisions") is True, f"{where}: memory must not override decisions (DEC-024)")
    check(policy.get("persistent_project_knowledge_deletion") == "manual_owner_action_only",
          f"{where}: only the owner deletes memory (DEC-138)")
    check(policy.get("provenance_required") is True, f"{where}: provenance_required must be true (DEC-102)")
    check(policy.get("context_revision_required") is True,
          f"{where}: context_revision_required must be true (DEC-102)")
    check(policy.get("retrieval_modes") == RETRIEVAL_MODES and policy.get("default_retrieval_mode") == "auto",
          f"{where}: retrieval_modes must be {RETRIEVAL_MODES} with default auto (DEC-104)")
    backend = policy.get("memory_backend")
    check(isinstance(backend, dict), f"{where}: memory_backend missing")
    capability = backend.get("capability")
    check_against_schema(capability, tool_schema, f"{where} memory_backend.capability")
    check(capability["paid"] is False, f"{where}: the memory backend must not be a paid service (DEC-019, DEC-085)")
    check(backend.get("llm_for_extraction") == NO_PAID_EXTRACTION,
          f"{where}: llm_for_extraction must be {NO_PAID_EXTRACTION!r} (DEC-019, DEC-085)")
    if capability["availability"] == "verified":
        check(isinstance(capability.get("last_verified_at"), str) and capability["last_verified_at"],
              f"{where}: a verified backend needs last_verified_at (DEC-046, DEC-125)")
        check(isinstance(capability.get("evidence_url"), str) and bool(EVIDENCE_URL.fullmatch(capability["evidence_url"])),
              f"{where}: a verified backend needs evidence_url on an issue or comment in this repository (DEC-046, DEC-125)")
    check(backend.get("placement") in PLACEMENT_VALUES, f"{where}: placement must be one of {sorted(PLACEMENT_VALUES)}")
    if backend.get("placement") == "owner_decision_pending":
        check(backend.get("placement_task") == PLACEMENT_TASK, f"{where}: a pending placement must link {PLACEMENT_TASK}")
    check("endpoint" not in backend and "url" not in backend,
          f"{where}: the endpoint is the owner's choice (task #150) and lives in each game's MCP config, not here")
    tools = set(backend.get("mcp_enabled_tools", []))
    check(tools and tools <= set(capability["supported_actions"]),
          f"{where}: mcp_enabled_tools must be a non-empty subset of the capability's supported_actions")
    banned = sorted((tools | set(capability["supported_actions"])) & FORBIDDEN_MEMORY_TOOLS)
    check(not banned, f"{where}: mcp_enabled_tools and supported_actions must not include {banned}")
    check(backend.get("reflect_allowed") is False, f"{where}: reflect has no sources; reflect_allowed must be false")
    check(backend.get("endpoint_per_bank") is True, f"{where}: one MCP endpoint per bank keeps projects apart (DEC-101)")
    check(backend.get("recall_types_for_facts") == FACT_TYPES,
          f"{where}: recall_types_for_facts must be {FACT_TYPES}; observations carry no provenance")
    check(backend.get("observations") == "unverified_hints", f"{where}: observations must be unverified_hints")
    limits = backend.get("known_limits")
    check(isinstance(limits, list) and bool(limits) and all(isinstance(x, str) and x for x in limits),
          f"{where}: known_limits must list what the smoke test found")
    naming = backend.get("bank_naming", {})
    check(set(naming) == set(KNOWLEDGE_SCOPES) and "{repository}" in naming.get("project", ""),
          f"{where}: bank_naming must name the studio, project ({{repository}}) and task scopes")
    rules = policy.get("storage_rules", {})
    check(NEVER_STORE <= set(rules.get("never_store", [])), f"{where}: never_store must include {sorted(NEVER_STORE)}")
    check(REQUIRED_MEMORY_METADATA <= set(rules.get("required_metadata", [])),
          f"{where}: required_metadata must include {sorted(REQUIRED_MEMORY_METADATA)}")
    check(rules.get("scope_is_the_bank") is True and "scope_tags" not in rules,
          f"{where}: the bank is the scope; scope tags hid memories in the smoke test")
    check(RETAIN_NEVER_PASSES <= set(rules.get("retain_never_passes", [])),
          f"{where}: retain_never_passes must include {sorted(RETAIN_NEVER_PASSES)}; a repeated document_id "
          f"replaces memory (DEC-138)")
    learning = policy.get("learning", {})
    check(isinstance(learning.get("noise_guard_min_independent_occurrences"), int)
          and learning["noise_guard_min_independent_occurrences"] >= 2,
          f"{where}: a lesson needs at least 2 independent occurrences (or one severe)")
    check(learning.get("noise_guard_single_severe") == "blocker" and learning.get("independence_key") == "piece",
          f"{where}: one blocker is severe, and independence is counted per piece")
    check(learning.get("store_requires_explicit_keep") is True,
          f"{where}: a lesson is stored only when the agent names it after reading the hits (DEC-138)")
    check(learning.get("notify_every_automatic_change") is True, f"{where}: every automatic change is notified (DEC-100)")
    check(learning.get("auto_apply_requires_passing_checks") is True,
          f"{where}: automatic changes must be verified first (DEC-106: safe, verified, non-creative)")
    check(learning.get("push_or_pr_requires_owner_yes") is True,
          f"{where}: pushes and PRs from lessons need the owner's yes")
    check("push_pr_or_issue_requires_owner_yes" not in learning,
          f"{where}: Issues are engineering tasks agents may create (DEC-008); the rule covers push and PR only")
    sources = learning.get("rule_sources", {})
    check(isinstance(sources, dict) and all(isinstance(sources.get(k), str) and sources[k] for k in
                                            ("noise_guard", "push_or_pr_requires_owner_yes")),
          f"{where}: learning.rule_sources must cite where the noise guard and the push/PR rule come from")

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
        check(PERMANENT_DECISION_URL in manifest["contracts"][filename]["decision_issue_urls"],
              f"manifest: {filename} must link {PERMANENT_DECISION_URL}")

    boundaries = load(directory / "system-boundaries.json")
    validate_boundaries(boundaries)
    links = {name: manifest_links(manifest, name) for name in (PRODUCTION_POLICY, BOUNDARIES)}
    profile_ids = validate_engine_profiles(load(directory / PRODUCTION_POLICY), links)
    validate_profile_modules(boundaries, profile_ids)
    validate_knowledge_policy(load(directory / KNOWLEDGE_POLICY), load(directory / "tool-capability.schema.json"))
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
