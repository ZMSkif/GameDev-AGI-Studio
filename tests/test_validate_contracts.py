"""Stdlib unittest checks for scripts/validate_contracts.py (offline, no dependencies)."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_contracts.py"
spec = importlib.util.spec_from_file_location("validate_contracts", SCRIPT)
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)

URL_146 = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/146"
URL_1 = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/1"
NOT_REPO_ISSUE = "deferred_by must be a URL of an issue in this repository"
NOT_146 = "deferred_by must be " + URL_146
BOUNDARIES = "system-boundaries.json module "
EXECUTION = "orchestration-policy.json authority.execution: "
OPENAPI = "coordinator.openapi.json info: "


class RepositoryContracts(unittest.TestCase):
    def test_real_contracts_pass(self):
        self.assertGreaterEqual(vc.validate(REPO), 11)

    def test_cli_success_output_and_exit_code(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^Validated \d+ contracts and decision links\s*$")

    def test_deferred_modules_in_real_contracts(self):
        obj = json.loads((REPO / "contracts/v1/system-boundaries.json").read_text(encoding="utf-8"))
        deferred = {m["id"] for m in obj["modules"] if m["status"] == "deferred"}
        self.assertEqual(deferred, {"coordinator", "worker-agent", "postgresql", "control-center"})
        for m in obj["modules"]:
            if m["status"] == "deferred":
                self.assertEqual(m["deferred_by"], URL_146)
        for mid in ("github", "hindsight", "tool-registry", "godot-game", "qa-release", "studio-plugin"):
            self.assertEqual(next(m for m in obj["modules"] if m["id"] == mid)["status"], "active")


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        shutil.copytree(REPO / "contracts", self.root / "contracts")
        self.dir = self.root / "contracts" / "v1"

    def read(self, name):
        return json.loads((self.dir / name).read_text(encoding="utf-8"))

    def write(self, name, obj):
        (self.dir / name).write_text(json.dumps(obj, indent=2), encoding="utf-8")

    def module(self, obj, module_id):
        return next(m for m in obj["modules"] if m["id"] == module_id)

    def edit_boundaries(self, fn):
        b = self.read("system-boundaries.json")
        fn(b)
        self.write("system-boundaries.json", b)

    def assertFails(self, fragment):
        with self.assertRaises(vc.ContractError) as ctx:
            vc.validate(self.root)
        self.assertIn(fragment, str(ctx.exception))


class ManifestRules(FixtureCase):
    def test_fixture_copy_passes(self):
        vc.validate(self.root)

    def test_old_manifest_versions_rejected(self):
        for old in ("1.0.0", "1.1.0", "1.2.0"):
            with self.subTest(version=old):
                m = self.read("manifest.json")
                m["version"] = old
                self.write("manifest.json", m)
                self.assertFails("manifest version must be 1.3.0")

    def test_any_other_manifest_version_rejected(self):
        m = self.read("manifest.json")
        m["version"] = "1.4.0"
        self.write("manifest.json", m)
        self.assertFails("manifest version must be 1.3.0")

    def test_each_changed_contract_must_link_decision_146(self):
        for name in vc.DEFERRAL_CONTRACTS:
            with self.subTest(contract=name):
                m = self.read("manifest.json")
                m["contracts"][name]["decision_issue_urls"].remove(URL_146)
                self.write("manifest.json", m)
                self.assertFails(f"manifest: {name} must link {URL_146}")
                shutil.copy(REPO / "contracts/v1/manifest.json", self.dir / "manifest.json")


class BoundaryRules(FixtureCase):
    def test_missing_module_status(self):
        self.edit_boundaries(lambda b: self.module(b, "github").pop("status"))
        self.assertFails(BOUNDARIES + "'github': status must be one of")

    def test_invalid_module_status(self):
        self.edit_boundaries(lambda b: self.module(b, "github").update(status="paused"))
        self.assertFails(BOUNDARIES + "'github': status must be one of")

    def test_deferred_module_without_deferred_by(self):
        self.edit_boundaries(lambda b: self.module(b, "coordinator").pop("deferred_by"))
        self.assertFails(BOUNDARIES + "'coordinator': " + NOT_REPO_ISSUE)

    def test_deferred_by_outside_repository(self):
        self.edit_boundaries(lambda b: self.module(b, "postgresql").update(
            deferred_by="https://github.com/other/repo/issues/146"))
        self.assertFails(BOUNDARIES + "'postgresql': " + NOT_REPO_ISSUE)

    def test_deferred_by_not_an_issue(self):
        self.edit_boundaries(lambda b: self.module(b, "postgresql").update(
            deferred_by=vc.REPO_ISSUES + "abc"))
        self.assertFails(BOUNDARIES + "'postgresql': " + NOT_REPO_ISSUE)

    def test_deferred_by_other_repo_issue_rejected(self):
        for mid in ("coordinator", "worker-agent", "postgresql", "control-center"):
            with self.subTest(module=mid):
                self.edit_boundaries(lambda b: self.module(b, mid).update(deferred_by=URL_1))
                self.assertFails(BOUNDARIES + f"'{mid}': " + NOT_146)
                shutil.copy(REPO / "contracts/v1/system-boundaries.json", self.dir / "system-boundaries.json")

    def test_deferred_by_trailing_newline_rejected(self):
        self.edit_boundaries(lambda b: self.module(b, "coordinator").update(deferred_by=URL_146 + "\n"))
        self.assertFails(BOUNDARIES + "'coordinator': " + NOT_REPO_ISSUE)

    def test_deferred_by_other_issue_with_trailing_newline_rejected(self):
        self.edit_boundaries(lambda b: self.module(b, "coordinator").update(deferred_by=URL_1 + "\n"))
        self.assertFails(BOUNDARIES + "'coordinator': " + NOT_REPO_ISSUE)

    def test_active_module_with_deferred_by(self):
        self.edit_boundaries(lambda b: self.module(b, "github").update(deferred_by=URL_146))
        self.assertFails(BOUNDARIES + "'github': active module must not have deferred_by")

    def test_extra_deferred_module(self):
        self.edit_boundaries(lambda b: self.module(b, "tool-registry").update(
            status="deferred", deferred_by=URL_146))
        self.assertFails("system-boundaries.json: deferred modules")

    def test_missing_deferred_module(self):
        def fn(b):
            m = self.module(b, "worker-agent")
            m["status"] = "active"
            del m["deferred_by"]
        self.edit_boundaries(fn)
        self.assertFails("system-boundaries.json: deferred modules")

    def test_duplicate_module_id(self):
        self.edit_boundaries(lambda b: b["modules"].append(dict(self.module(b, "github"))))
        self.assertFails("system-boundaries.json: duplicate module id")

    def test_plugin_module_missing(self):
        def fn(b):
            b["modules"] = [m for m in b["modules"] if m["id"] != "studio-plugin"]
        self.edit_boundaries(fn)
        self.assertFails("system-boundaries.json: studio-plugin must be an active module")


class OrchestrationRules(FixtureCase):
    def edit(self, fn):
        p = self.read("orchestration-policy.json")
        fn(p["authority"])
        self.write("orchestration-policy.json", p)

    def test_execution_value_changed(self):
        self.edit(lambda a: a.update(execution="agent_runtime"))
        self.assertFails(EXECUTION + "original value must be preserved")

    def test_execution_status_missing(self):
        self.edit(lambda a: a.pop("execution_status"))
        self.assertFails(EXECUTION + "execution_status must be deferred")

    def test_execution_status_wrong_value(self):
        self.edit(lambda a: a.update(execution_status="active"))
        self.assertFails(EXECUTION + "execution_status must be deferred")

    def test_missing_deferred_by(self):
        self.edit(lambda a: a.pop("execution_deferred_by"))
        self.assertFails(EXECUTION + NOT_REPO_ISSUE)

    def test_other_issue_deferred_by(self):
        self.edit(lambda a: a.update(execution_deferred_by=URL_1))
        self.assertFails(EXECUTION + NOT_146)

    def test_trailing_newline_deferred_by(self):
        self.edit(lambda a: a.update(execution_deferred_by=URL_146 + "\n"))
        self.assertFails(EXECUTION + NOT_REPO_ISSUE)

    def test_missing_interim_authority(self):
        self.edit(lambda a: a.pop("execution_while_deferred"))
        self.assertFails(EXECUTION + "execution_while_deferred must be agent_runtime")

    def test_wrong_interim_authority(self):
        self.edit(lambda a: a.update(execution_while_deferred="postgresql"))
        self.assertFails(EXECUTION + "execution_while_deferred must be agent_runtime")


class OpenApiRules(FixtureCase):
    def edit(self, fn):
        o = self.read("coordinator.openapi.json")
        fn(o["info"])
        self.write("coordinator.openapi.json", o)

    def test_not_marked_deferred(self):
        self.edit(lambda i: i.pop("x-status"))
        self.assertFails("coordinator.openapi.json: info.x-status must be deferred")

    def test_wrong_status(self):
        self.edit(lambda i: i.update({"x-status": "active"}))
        self.assertFails("coordinator.openapi.json: info.x-status must be deferred")

    def test_missing_deferred_by(self):
        self.edit(lambda i: i.pop("x-deferred-by"))
        self.assertFails(OPENAPI + NOT_REPO_ISSUE)

    def test_other_issue_deferred_by(self):
        self.edit(lambda i: i.update({"x-deferred-by": URL_1}))
        self.assertFails(OPENAPI + NOT_146)

    def test_trailing_newline_deferred_by(self):
        self.edit(lambda i: i.update({"x-deferred-by": URL_146 + "\n"}))
        self.assertFails(OPENAPI + NOT_REPO_ISSUE)


POLICY = "game-production-policy.json"
PROFILE = POLICY + " profile "
URL_12 = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/12"
# A dummy decision for fixtures only; the real web profile cites its own owner decision issue.
URL_DUMMY = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/999"
WEB_PROFILE = {
    "engine": "Three.js or PixiJS v8 by game type",
    "decided_by": [URL_DUMMY],
    "use_for": ["html5_portal_games"],
    "render": {"3d": "threejs", "2.5d": "threejs", "2d_lite": "threejs_orthographic_dom_ui", "2d_rich": "pixijs_v8"},
}


class EngineProfileRules(FixtureCase):
    def setUp(self):
        """Start from a Godot-only copy, so these rules hold before and after the web profile is registered."""
        super().setUp()

        def godot_only(p):
            profiles = p["engine_profiles"]["profiles"]
            profiles.pop("web", None)
            profiles["godot"].pop("use_for", None)
            profiles["godot"]["decided_by"] = [URL_12]
        self.edit_policy(godot_only)
        self.edit_boundaries(lambda b: b.update(modules=[m for m in b["modules"] if m["id"] != "web-game"]))
        vc.validate(self.root)

    def edit_policy(self, fn):
        p = self.read(POLICY)
        fn(p)
        self.write(POLICY, p)

    def godot(self, p):
        return p["engine_profiles"]["profiles"]["godot"]

    def add_web(self, *, module=True, link=(POLICY, "system-boundaries.json"), profile=None, godot_cites=True):
        """Add a web profile, its module, the limit on godot and the fixture decision in the manifest."""
        def fn(p):
            p["engine_profiles"]["profiles"]["web"] = json.loads(json.dumps(profile or WEB_PROFILE))
            self.godot(p)["use_for"] = ["heavy_games", "desktop_games"]
            if godot_cites:
                self.godot(p)["decided_by"].append(URL_DUMMY)
        self.edit_policy(fn)
        if module:
            self.edit_boundaries(lambda b: b["modules"].append(
                {"id": "web-game", "status": "active", "responsibility": "x", "engine_profile": "web"}))
        m = self.read("manifest.json")
        for name in link:
            m["contracts"][name]["decision_issue_urls"].append(URL_DUMMY)
            m["contracts"][name]["decision_ids"].append("DEC-145")
        self.write("manifest.json", m)

    def test_real_policy_keeps_godot_and_any_web_profile_has_its_own_decision(self):
        p = json.loads((REPO / "contracts/v1" / POLICY).read_text(encoding="utf-8"))
        profiles = p["engine_profiles"]["profiles"]
        self.assertNotIn("engine", p)
        self.assertEqual(profiles["godot"]["engine"], "Godot 4.x")
        self.assertIn(URL_12, profiles["godot"]["decided_by"])
        self.assertLessEqual(set(profiles), {"godot", "web"})
        if "web" in profiles:
            m = json.loads((REPO / "contracts/v1/manifest.json").read_text(encoding="utf-8"))["contracts"][POLICY]
            ids = dict(zip(m["decision_issue_urls"], m["decision_ids"]))
            own = [u for u in profiles["web"]["decided_by"] if ids.get(u) == "DEC-145"]
            self.assertTrue(own, "the web profile cites DEC-145")
            self.assertNotIn(URL_DUMMY, own, "the fixture URL never reaches the real contract")

    def test_top_level_engine_rejected(self):
        self.edit_policy(lambda p: p.update(engine="Godot 4.x"))
        self.assertFails(POLICY + ": the top-level engine moved")

    def test_policy_major_version_required(self):
        for bad in ("1.0.0", "1.2.0", None):
            with self.subTest(version=bad):
                self.edit_policy(lambda p: p.update(version=bad))
                self.assertFails(POLICY + ": version must be 2.0.0 (removing engine is a breaking change)")

    def test_migration_note_required(self):
        self.edit_policy(lambda p: p.pop("migration_from_1_0_0"))
        self.assertFails(POLICY + ": migration_from_1_0_0 must tell readers of engine where it moved")
        self.edit_policy(lambda p: p.update(migration_from_1_0_0={"breaking": True, "removed": "engine", "read_instead": "x"}))
        self.assertFails(POLICY + ": migration_from_1_0_0")

    def test_missing_profiles_rejected(self):
        self.edit_policy(lambda p: p.pop("engine_profiles"))
        self.assertFails(POLICY + ": engine_profiles.profiles missing")

    def test_unknown_profile_rejected(self):
        self.edit_policy(lambda p: p["engine_profiles"]["profiles"].update(unity={"decided_by": [URL_12]}))
        self.assertFails(POLICY + ": unknown engine profile(s) ['unity']")

    def test_godot_profile_required(self):
        def fn(p):
            p["engine_profiles"]["profiles"] = {"web": dict(WEB_PROFILE)}
        self.edit_policy(fn)
        self.assertFails("the godot profile is required (DEC-012)")

    def test_godot_engine_must_stay(self):
        self.edit_policy(lambda p: self.godot(p).update(engine="Godot 5"))
        self.assertFails(PROFILE + "'godot': engine must stay Godot 4.x (DEC-012)")

    def test_godot_must_cite_dec_012(self):
        def fn(p):
            self.godot(p)["decided_by"] = ["https://github.com/ZMSkif/GameDev-AGI-Studio/issues/47"]
        self.edit_policy(fn)
        self.assertFails(PROFILE + "'godot': decided_by must include " + URL_12)

    def test_decided_by_must_be_repo_issue_urls(self):
        for bad in ([], "DEC-012", ["https://github.com/other/repo/issues/12"], [URL_12 + "\n"], ["pending:DEC-145"]):
            with self.subTest(decided_by=bad):
                self.edit_policy(lambda p: self.godot(p).update(decided_by=bad))
                self.assertFails(PROFILE + "'godot': decided_by must be a non-empty list of issue URLs")
                shutil.copy(REPO / "contracts/v1" / POLICY, self.dir / POLICY)

    def test_decision_must_be_linked_in_manifest(self):
        self.edit_policy(lambda p: self.godot(p)["profile_decision_issue_urls"].append(URL_DUMMY))
        self.assertFails(PROFILE + "'godot': manifest must link " + URL_DUMMY)

    def test_godot_module_must_name_its_profile(self):
        self.edit_boundaries(lambda b: self.module(b, "godot-game").pop("engine_profile"))
        self.assertFails("profile 'godot' needs the active module 'godot-game'")

    def test_module_naming_a_missing_profile_rejected(self):
        self.edit_boundaries(lambda b: b["modules"].append(
            {"id": "web-game", "status": "active", "responsibility": "x", "engine_profile": "web"}))
        self.assertFails("module 'web-game': engine_profile 'web' is not in " + POLICY)

    def test_module_with_the_wrong_profile_rejected(self):
        self.edit_boundaries(lambda b: self.module(b, "github").update(engine_profile="godot"))
        self.assertFails("module 'github': engine_profile 'godot' belongs to module 'godot-game'")

    def test_web_profile_with_its_own_decision_passes(self):
        self.add_web()
        vc.validate(self.root)

    def test_web_profile_needs_its_own_decision(self):
        self.add_web(profile=dict(WEB_PROFILE, decided_by=[URL_12]))
        self.assertFails(PROFILE + "'web': decided_by must cite DEC-145")

    def test_web_profile_citing_another_linked_decision_fails(self):
        url_11 = "https://github.com/ZMSkif/GameDev-AGI-Studio/issues/11"  # linked for both contracts
        self.add_web(profile=dict(WEB_PROFILE, decided_by=[url_11]))
        self.assertFails(PROFILE + "'web': decided_by must cite DEC-145")

    def test_web_decision_must_be_linked_for_the_policy(self):
        self.add_web(link=("system-boundaries.json",))
        self.assertFails("manifest must link " + URL_DUMMY + " for " + POLICY)

    def test_web_decision_must_be_linked_for_the_boundaries(self):
        self.add_web(link=(POLICY,))
        self.assertFails("manifest must link " + URL_DUMMY + " for system-boundaries.json")

    def test_godot_limit_needs_the_split_decision(self):
        self.add_web(godot_cites=False)
        self.assertFails(PROFILE + "'godot': a use_for limit needs DEC-145 in decided_by")

    def test_godot_scoped_decisions_required(self):
        self.edit_policy(lambda p: self.godot(p).update(profile_decision_issue_urls=[URL_12]))
        self.assertFails(PROFILE + "'godot': profile_decision_issue_urls must list")

    def test_every_profile_names_its_engine(self):
        web = dict(WEB_PROFILE)
        web.pop("engine")
        self.add_web(profile=web)
        self.assertFails(PROFILE + "'web': engine must name the engine")

    def test_manifest_lists_must_pair_up(self):
        m = self.read("manifest.json")
        m["contracts"][POLICY]["decision_ids"].pop()
        self.write("manifest.json", m)
        self.assertFails("decision_issue_urls and decision_ids differ in length")

    def test_web_profile_needs_its_module(self):
        self.add_web(module=False)
        self.assertFails("profile 'web' needs the active module 'web-game'")

    def test_web_render_must_cover_every_game_type(self):
        render = dict(WEB_PROFILE["render"])
        del render["2d_rich"]
        self.add_web(profile=dict(WEB_PROFILE, render=render))
        self.assertFails(PROFILE + "'web': render must name a renderer for each of")

    def test_two_profiles_each_state_use_for(self):
        self.add_web()
        self.edit_policy(lambda p: self.godot(p).pop("use_for"))
        self.assertFails(PROFILE + "'godot': with several profiles each must state use_for")

    def test_empty_use_for_rejected(self):
        self.add_web(profile=dict(WEB_PROFILE, use_for=[]))
        self.assertFails(PROFILE + "'web': use_for must be a non-empty list of strings")


KP = "knowledge-policy.json: "


class KnowledgePolicyRules(FixtureCase):
    def edit_kp(self, fn):
        p = self.read("knowledge-policy.json")
        fn(p)
        self.write("knowledge-policy.json", p)

    def backend(self, p):
        return p["memory_backend"]

    def test_real_policy_passes_and_keeps_the_decisions(self):
        p = json.loads((REPO / "contracts/v1/knowledge-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(p["scopes"], ["studio", "project", "task"])
        self.assertEqual(p["default_retrieval_mode"], "auto")
        self.assertFalse(p["memory_backend"]["capability"]["paid"])
        vc.validate(self.root)

    def test_scopes_are_the_three_levels(self):
        self.edit_kp(lambda p: p.update(scopes=["studio", "project"]))
        self.assertFails(KP + "scopes must be")

    def test_memory_never_ranks_above_decisions(self):
        def fn(p):
            p["authority_order"] = ["verified_context_memory", "binding_decision_issues",
                                    "approved_versioned_gdd_art_bible_architecture"]
        self.edit_kp(fn)
        self.assertFails("must rank above memory (DEC-103)")

    def test_only_the_owner_deletes(self):
        self.edit_kp(lambda p: p.update(persistent_project_knowledge_deletion="agent_cleanup_allowed"))
        self.assertFails("only the owner deletes memory (DEC-138)")

    def test_the_four_modes_with_auto_default(self):
        self.edit_kp(lambda p: p.update(default_retrieval_mode="memory_first"))
        self.assertFails("retrieval_modes must be")
        self.edit_kp(lambda p: p.update(default_retrieval_mode="auto", retrieval_modes=["auto", "manual"]))
        self.assertFails("retrieval_modes must be")

    def test_capability_follows_the_tool_capability_contract(self):
        self.edit_kp(lambda p: self.backend(p)["capability"].update(availability="ready"))
        self.assertFails("availability: 'ready' is not one of")

    def test_capability_without_required_field_fails(self):
        self.edit_kp(lambda p: self.backend(p)["capability"].pop("license"))
        self.assertFails("memory_backend.capability: missing ['license']")

    def test_paid_backend_fails(self):
        self.edit_kp(lambda p: self.backend(p)["capability"].update(paid=True))
        self.assertFails("must not be a paid service")

    def verified(self, p, **extra):
        cap = self.backend(p)["capability"]
        cap.update(availability="verified", last_verified_at="2026-11-19T16:40:00Z",
                   evidence_url=vc.REPO_ISSUES + "150#issuecomment-1")
        cap.update(extra)

    def test_verified_with_date_and_evidence_passes(self):
        self.edit_kp(self.verified)
        vc.validate(self.root)

    def test_verified_needs_a_date(self):
        self.edit_kp(lambda p: self.verified(p, last_verified_at=None))
        self.assertFails("a verified backend needs last_verified_at")

    def test_verified_needs_evidence_in_this_repository(self):
        for url in (None, "https://example.com/evidence", vc.REPO_ISSUES + "150x", "notes/smoke.md"):
            with self.subTest(url=url):
                self.reset_kp()
                self.edit_kp(lambda p, url=url: self.verified(p, evidence_url=url))
                self.assertFails("a verified backend needs evidence_url")

    def test_unverified_needs_no_evidence(self):
        p = json.loads((REPO / "contracts/v1/knowledge-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(p["memory_backend"]["capability"]["availability"], "unverified")
        self.assertIsNone(p["memory_backend"]["capability"]["evidence_url"])

    def test_destructive_or_unsourced_tools_fail(self):
        for tool in ("delete_bank", "clear_memories", "reflect"):
            with self.subTest(tool=tool):
                def fn(p, tool=tool):
                    self.backend(p)["mcp_enabled_tools"].append(tool)
                    self.backend(p)["capability"]["supported_actions"].append(tool)
                self.edit_kp(fn)
                self.assertFails("mcp_enabled_tools and supported_actions must not include")
                self.reset_kp()

    def test_destructive_tool_in_supported_actions_alone_fails(self):
        self.edit_kp(lambda p: self.backend(p)["capability"]["supported_actions"].append("delete_bank"))
        self.assertFails("must not include ['delete_bank']")

    def test_tool_outside_supported_actions_fails(self):
        self.edit_kp(lambda p: self.backend(p)["mcp_enabled_tools"].append("list_banks"))
        self.assertFails("must be a non-empty subset of the capability's supported_actions")

    def test_reflect_flag_and_endpoint_per_bank(self):
        self.edit_kp(lambda p: self.backend(p).update(reflect_allowed=True))
        self.assertFails("reflect_allowed must be false")
        shutil.copy(REPO / "contracts/v1/knowledge-policy.json", self.dir / "knowledge-policy.json")
        self.edit_kp(lambda p: self.backend(p).update(endpoint_per_bank=False))
        self.assertFails("one MCP endpoint per bank")

    def test_endpoint_is_not_hard_coded(self):
        self.edit_kp(lambda p: self.backend(p).update(endpoint="http://127.0.0.1:8888/mcp/"))
        self.assertFails("the endpoint is the owner's choice")

    def test_bank_naming_needs_the_repository(self):
        self.edit_kp(lambda p: self.backend(p)["bank_naming"].update(project="gamedev-studio::project"))
        self.assertFails("bank_naming must name")

    def test_never_store_and_metadata(self):
        self.edit_kp(lambda p: p["storage_rules"]["never_store"].remove("secrets"))
        self.assertFails("never_store must include")
        shutil.copy(REPO / "contracts/v1/knowledge-policy.json", self.dir / "knowledge-policy.json")
        self.edit_kp(lambda p: p["storage_rules"]["required_metadata"].remove("source_rev"))
        self.assertFails("required_metadata must include")

    def reset_kp(self):
        shutil.copy(REPO / "contracts/v1/knowledge-policy.json", self.dir / "knowledge-policy.json")

    def assertEditFails(self, fn, fragment):
        self.reset_kp()
        self.edit_kp(fn)
        self.assertFails(fragment)

    def test_learning_guards(self):
        learning = lambda **kw: (lambda p: p["learning"].update(kw))
        self.assertEditFails(learning(noise_guard_min_independent_occurrences=1), "at least 2 independent occurrences")
        self.assertEditFails(learning(push_or_pr_requires_owner_yes=False), "pushes and PRs from lessons need")
        self.assertEditFails(lambda p: p["learning"].pop("push_or_pr_requires_owner_yes"), "pushes and PRs from lessons")
        self.assertEditFails(learning(push_pr_or_issue_requires_owner_yes=True), "agents may create (DEC-008)")
        self.assertEditFails(learning(notify_every_automatic_change=False), "every automatic change is notified (DEC-100)")
        self.assertEditFails(learning(auto_apply_requires_passing_checks=False), "must be verified first (DEC-106")
        self.assertEditFails(learning(noise_guard_single_severe="any_should_fix"), "one blocker is severe")
        self.assertEditFails(learning(independence_key="file"), "independence is counted per piece")
        self.assertEditFails(learning(store_requires_explicit_keep=False), "stored only when the agent names it")
        self.assertEditFails(lambda p: p["learning"].pop("store_requires_explicit_keep"), "stored only when the agent")
        self.assertEditFails(learning(rule_sources={"noise_guard": "x"}), "rule_sources must cite")
        self.assertEditFails(learning(rule_sources={"noise_guard": "", "push_or_pr_requires_owner_yes": "y"}),
                             "rule_sources must cite")

    def test_core_guarantees(self):
        top = lambda **kw: (lambda p: p.update(kw))
        self.assertEditFails(top(memory_cannot_override_owner_decisions=False), "must not override decisions (DEC-024)")
        self.assertEditFails(top(provenance_required=False), "provenance_required must be true (DEC-102)")
        self.assertEditFails(top(context_revision_required=False), "context_revision_required must be true (DEC-102)")
        self.assertEditFails(lambda p: p.pop("context_revision_required"), "context_revision_required must be true")

    def test_backend_guarantees(self):
        backend = lambda **kw: (lambda p: self.backend(p).update(kw))
        self.assertEditFails(backend(llm_for_extraction="paid_api_allowed"), "llm_for_extraction must be")
        self.assertEditFails(backend(observations="facts"), "observations must be unverified_hints")
        self.assertEditFails(backend(recall_types_for_facts=["world", "experience", "observation"]),
                             "recall_types_for_facts must be")
        self.assertEditFails(backend(known_limits=[]), "known_limits must list")
        self.assertEditFails(backend(known_limits=[""]), "known_limits must list")
        self.assertEditFails(backend(placement="anywhere"), "placement must be one of")
        self.assertEditFails(lambda p: self.backend(p).pop("placement"), "placement must be one of")
        self.assertEditFails(backend(placement_task=vc.REPO_ISSUES + "1"), "a pending placement must link")
        self.assertEditFails(backend(url="http://127.0.0.1:8888/mcp/"), "the endpoint is the owner's choice")

    def test_schema_types_and_extra_keys(self):
        cap = lambda **kw: (lambda p: self.backend(p)["capability"].update(kw))
        self.assertEditFails(cap(permission_scopes=[None]), "permission_scopes: every item must be a non-empty string")
        self.assertEditFails(cap(permission_scopes=[""]), "permission_scopes: every item must be a non-empty string")
        self.assertEditFails(cap(supported_actions="retain"), "supported_actions: must be a list")
        self.assertEditFails(cap(paid="no"), "paid: must be true or false")
        self.assertEditFails(cap(version=""), "version: must be a string")
        self.assertEditFails(cap(endpoint="http://x"), "properties outside the schema ['endpoint']")

    def test_storage_scope_and_document_ids(self):
        rules = lambda **kw: (lambda p: p["storage_rules"].update(kw))
        self.assertEditFails(rules(scope_tags=["scope:studio"]), "the bank is the scope")
        self.assertEditFails(rules(scope_is_the_bank=False), "the bank is the scope")
        self.assertEditFails(rules(retain_never_passes=["update_mode"]), "retain_never_passes must include")

class CliFailurePath(FixtureCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_cli_accepts_valid_root_argument(self):
        result = self.run_cli(str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated", result.stdout)

    def test_cli_exits_nonzero_on_broken_copy(self):
        self.edit_boundaries(lambda b: self.module(b, "coordinator").pop("deferred_by"))
        result = self.run_cli(str(self.root))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Validated", result.stdout)
        self.assertIn("ContractError", result.stderr)
        self.assertIn(BOUNDARIES + "'coordinator': " + NOT_REPO_ISSUE, result.stderr)

    def test_cli_rejects_extra_arguments(self):
        result = self.run_cli(str(self.root), "extra")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage: validate_contracts.py [root]", result.stderr)

    def edit_boundaries(self, fn):
        b = self.read("system-boundaries.json")
        fn(b)
        self.write("system-boundaries.json", b)


if __name__ == "__main__":
    unittest.main()
