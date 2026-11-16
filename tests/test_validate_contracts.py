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

    def test_old_manifest_version_rejected(self):
        m = self.read("manifest.json")
        m["version"] = "1.0.0"
        self.write("manifest.json", m)
        self.assertFails("manifest version must be 1.1.0")

    def test_any_other_manifest_version_rejected(self):
        m = self.read("manifest.json")
        m["version"] = "1.2.0"
        self.write("manifest.json", m)
        self.assertFails("manifest version must be 1.1.0")

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
