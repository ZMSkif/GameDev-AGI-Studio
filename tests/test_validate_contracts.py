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

    def assertFails(self, fragment):
        with self.assertRaises(vc.ContractError) as ctx:
            vc.validate(self.root)
        self.assertIn(fragment, str(ctx.exception))


class RepositoryContracts(unittest.TestCase):
    def test_real_contracts_pass(self):
        self.assertGreaterEqual(vc.validate(REPO), 11)

    def test_cli_output_and_exit_code(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^Validated \d+ contracts and decision links\s*$")

    def test_deferred_modules_in_real_contracts(self):
        obj = json.loads((REPO / "contracts/v1/system-boundaries.json").read_text(encoding="utf-8"))
        deferred = {m["id"] for m in obj["modules"] if m["status"] == "deferred"}
        self.assertEqual(deferred, {"coordinator", "worker-agent", "postgresql", "control-center"})
        for mid in ("github", "hindsight", "tool-registry", "godot-game", "qa-release", "studio-plugin"):
            self.assertEqual(next(m for m in obj["modules"] if m["id"] == mid)["status"], "active")


class BrokenFixtures(FixtureCase):
    def test_fixture_copy_passes(self):
        vc.validate(self.root)

    def test_old_manifest_version_rejected(self):
        m = self.read("manifest.json")
        m["version"] = "1.0.0"
        self.write("manifest.json", m)
        self.assertFails("manifest version")

    def test_any_other_manifest_version_rejected(self):
        m = self.read("manifest.json")
        m["version"] = "1.2.0"
        self.write("manifest.json", m)
        self.assertFails("manifest version")

    def test_missing_module_status(self):
        b = self.read("system-boundaries.json")
        del self.module(b, "github")["status"]
        self.write("system-boundaries.json", b)
        self.assertFails("status must be one of")

    def test_invalid_module_status(self):
        b = self.read("system-boundaries.json")
        self.module(b, "github")["status"] = "paused"
        self.write("system-boundaries.json", b)
        self.assertFails("status must be one of")

    def test_deferred_module_without_deferred_by(self):
        b = self.read("system-boundaries.json")
        del self.module(b, "coordinator")["deferred_by"]
        self.write("system-boundaries.json", b)
        self.assertFails("deferred_by")

    def test_deferred_by_outside_repository(self):
        b = self.read("system-boundaries.json")
        self.module(b, "postgresql")["deferred_by"] = "https://github.com/other/repo/issues/146"
        self.write("system-boundaries.json", b)
        self.assertFails("deferred_by")

    def test_deferred_by_not_an_issue(self):
        b = self.read("system-boundaries.json")
        self.module(b, "postgresql")["deferred_by"] = vc.REPO_ISSUES + "abc"
        self.write("system-boundaries.json", b)
        self.assertFails("deferred_by")

    def test_active_module_with_deferred_by(self):
        b = self.read("system-boundaries.json")
        self.module(b, "github")["deferred_by"] = vc.PLUGIN_DECISION_URL
        self.write("system-boundaries.json", b)
        self.assertFails("must not have deferred_by")

    def test_extra_deferred_module(self):
        b = self.read("system-boundaries.json")
        m = self.module(b, "tool-registry")
        m["status"], m["deferred_by"] = "deferred", vc.PLUGIN_DECISION_URL
        self.write("system-boundaries.json", b)
        self.assertFails("deferred modules")

    def test_missing_deferred_module(self):
        b = self.read("system-boundaries.json")
        m = self.module(b, "worker-agent")
        m["status"] = "active"
        del m["deferred_by"]
        self.write("system-boundaries.json", b)
        self.assertFails("deferred modules")

    def test_duplicate_module_id(self):
        b = self.read("system-boundaries.json")
        b["modules"].append(dict(self.module(b, "github")))
        self.write("system-boundaries.json", b)
        self.assertFails("duplicate module id")

    def test_plugin_module_missing(self):
        b = self.read("system-boundaries.json")
        b["modules"] = [m for m in b["modules"] if m["id"] != "studio-plugin"]
        self.write("system-boundaries.json", b)
        self.assertFails("studio-plugin")

    def test_orchestration_execution_not_marked_deferred(self):
        p = self.read("orchestration-policy.json")
        del p["authority"]["execution_status"]
        self.write("orchestration-policy.json", p)
        self.assertFails("execution_status")

    def test_orchestration_missing_deferred_by(self):
        p = self.read("orchestration-policy.json")
        del p["authority"]["execution_deferred_by"]
        self.write("orchestration-policy.json", p)
        self.assertFails("deferred_by")

    def test_orchestration_missing_interim_authority(self):
        p = self.read("orchestration-policy.json")
        del p["authority"]["execution_while_deferred"]
        self.write("orchestration-policy.json", p)
        self.assertFails("execution_while_deferred")

    def test_openapi_not_marked_deferred(self):
        o = self.read("coordinator.openapi.json")
        del o["info"]["x-status"]
        self.write("coordinator.openapi.json", o)
        self.assertFails("x-status")

    def test_openapi_missing_deferred_by(self):
        o = self.read("coordinator.openapi.json")
        del o["info"]["x-deferred-by"]
        self.write("coordinator.openapi.json", o)
        self.assertFails("deferred_by")

    def test_manifest_missing_decision_146_link(self):
        m = self.read("manifest.json")
        urls = m["contracts"]["system-boundaries.json"]["decision_issue_urls"]
        urls.remove(vc.PLUGIN_DECISION_URL)
        self.write("manifest.json", m)
        self.assertFails("must link")


if __name__ == "__main__":
    unittest.main()
