"""Unit tests for scripts/validate_plugin.py (stdlib unittest only).

Each check is shown to fail by mutating a valid fixture tree.
"""
import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("validate_plugin", REPO_ROOT / "scripts" / "validate_plugin.py")
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)

SKILL = """---
name: demo-skill
description: A demo skill.
---

# Demo
"""

CLAUDE_PLUGIN = {"name": "demo-plugin", "version": "1.2.3", "description": "Demo"}
CLAUDE_MARKETPLACE = {
    "name": "demo-market",
    "owner": {"name": "Owner"},
    "plugins": [{"name": "demo-plugin", "source": "./"}],
}
CODEX_PLUGIN = {
    "name": "demo-plugin",
    "version": "1.2.3",
    "description": "Demo",
    "skills": "./skills/",
    "interface": {"displayName": "Demo"},
}
CODEX_MARKETPLACE = {
    "name": "demo-market",
    "plugins": [
        {
            "name": "demo-plugin",
            "source": {"source": "local", "path": "./"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        }
    ],
}


def write_json(root: Path, rel: str, data) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_fixture(root: Path) -> None:
    write_json(root, ".claude-plugin/plugin.json", copy.deepcopy(CLAUDE_PLUGIN))
    write_json(root, ".claude-plugin/marketplace.json", copy.deepcopy(CLAUDE_MARKETPLACE))
    write_json(root, ".codex-plugin/plugin.json", copy.deepcopy(CODEX_PLUGIN))
    write_json(root, ".agents/plugins/marketplace.json", copy.deepcopy(CODEX_MARKETPLACE))
    write_json(root, "hooks/hooks.json", {"hooks": {}})
    (root / "skills" / "demo-skill").mkdir(parents=True)
    (root / "skills" / "demo-skill" / "SKILL.md").write_text(SKILL, encoding="utf-8")


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        build_fixture(self.root)

    def mutate(self, rel, fn):
        path = self.root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        fn(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def errors(self):
        return vp.validate(self.root)

    def assertFails(self, fragment):
        errors = self.errors()
        self.assertTrue(
            any(fragment in e for e in errors),
            f"expected an error containing {fragment!r}, got {errors}",
        )


class RealRepositoryTest(unittest.TestCase):
    def test_repository_scaffold_is_valid(self):
        self.assertEqual(vp.validate(REPO_ROOT), [])

    def test_repository_versions_and_names_agree(self):
        claude = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((REPO_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], "gamedev-studio")
        self.assertEqual((claude["name"], claude["version"]), (codex["name"], codex["version"]))


class ValidFixtureTest(FixtureCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(self.errors(), [])

    def test_main_returns_zero_and_one(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(vp.main(["validate_plugin.py", str(self.root)]), 0)
        self.assertIn("valid", out.getvalue())
        (self.root / ".codex-plugin" / "plugin.json").unlink()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(vp.main(["validate_plugin.py", str(self.root)]), 1)
        self.assertIn("ERROR: .codex-plugin/plugin.json: file is missing", out.getvalue())


class ManifestParsingTest(FixtureCase):
    def test_missing_manifest_fails(self):
        for rel in vp.MANIFESTS:
            with self.subTest(rel=str(rel)):
                build_fixture_dir = tempfile.TemporaryDirectory()
                self.addCleanup(build_fixture_dir.cleanup)
                root = Path(build_fixture_dir.name)
                build_fixture(root)
                (root / rel).unlink()
                self.assertTrue(any("file is missing" in e for e in vp.validate(root)))

    def test_invalid_json_fails(self):
        (self.root / ".agents/plugins/marketplace.json").write_text("{not json", encoding="utf-8")
        self.assertFails("cannot parse JSON")

    def test_non_object_json_fails(self):
        (self.root / ".claude-plugin/plugin.json").write_text("[]", encoding="utf-8")
        self.assertFails("top level must be a JSON object")


class NameVersionTest(FixtureCase):
    def test_name_mismatch_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(name="other-plugin"))
        self.assertFails("name mismatch")

    def test_version_mismatch_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(version="1.2.4"))
        self.assertFails("version mismatch")

    def test_non_semver_version_fails(self):
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.mutate(rel, lambda d: d.update(version="one"))
        self.assertFails("'version' must be a semver string")

    def test_non_kebab_name_fails(self):
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.mutate(rel, lambda d: d.update(name="Demo_Plugin"))
        self.assertFails("kebab-case")

    def test_reserved_prefix_fails(self):
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.mutate(rel, lambda d: d.update(name="claude-demo"))
        self.assertFails("must not start with")

    def test_marketplace_version_fails(self):
        self.mutate(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(version="1.2.3"))
        self.assertFails("must not set 'version'")


class MarketplaceSourceTest(FixtureCase):
    def test_claude_source_not_root_fails(self):
        self.mutate(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(source="./plugin"))
        self.assertFails("does not resolve to the repository root")

    def test_claude_source_parent_fails(self):
        self.mutate(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(source="../"))
        self.assertFails("does not resolve to the repository root")

    def test_codex_source_not_root_fails(self):
        self.mutate(".agents/plugins/marketplace.json", lambda d: d["plugins"][0]["source"].update(path="./sub"))
        self.assertFails("does not resolve to the repository root")

    def test_remote_source_fails(self):
        self.mutate(
            ".agents/plugins/marketplace.json",
            lambda d: d["plugins"][0].update(source={"source": "url", "url": "https://example.com/x.git"}),
        )
        self.assertFails("does not resolve to the repository root")

    def test_missing_source_fails(self):
        self.mutate(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].pop("source"))
        self.assertFails("does not resolve to the repository root")

    def test_marketplace_without_plugin_entry_fails(self):
        self.mutate(".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(name="other"))
        self.assertFails("no plugin entry named 'demo-plugin'")

    def test_codex_skills_path_missing_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills="./nope/"))
        self.assertFails("does not point to a directory")


class SkillTest(FixtureCase):
    def skill(self, text, directory="demo-skill"):
        target = self.root / "skills" / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text(text, encoding="utf-8")

    def test_missing_frontmatter_fails(self):
        self.skill("# no frontmatter\n")
        self.assertFails("missing YAML frontmatter")

    def test_missing_name_fails(self):
        self.skill("---\ndescription: x\n---\nbody\n")
        self.assertFails("frontmatter 'name' is missing")

    def test_missing_description_fails(self):
        self.skill("---\nname: demo-skill\n---\nbody\n")
        self.assertFails("frontmatter 'description' is missing")

    def test_name_directory_mismatch_fails(self):
        self.skill("---\nname: other-name\ndescription: x\n---\nbody\n")
        self.assertFails("does not match directory")

    def test_extra_frontmatter_key_fails(self):
        self.skill("---\nname: demo-skill\ndescription: x\nallowed-tools: Bash\n---\nbody\n")
        self.assertFails("outside the portable subset")

    def test_too_long_skill_fails(self):
        self.skill("---\nname: demo-skill\ndescription: x\n---\n" + "line\n" * 500)
        self.assertFails("longer than 500 lines")

    def test_skill_directory_without_skill_md_fails(self):
        (self.root / "skills" / "empty-skill").mkdir()
        self.assertFails("skills/empty-skill/SKILL.md: file is missing")

    def test_missing_skills_directory_fails(self):
        (self.root / "skills" / "demo-skill" / "SKILL.md").unlink()
        (self.root / "skills" / "demo-skill").rmdir()
        (self.root / "skills").rmdir()
        self.assertFails("skills/: directory is missing")

    def test_quoted_frontmatter_values_are_accepted(self):
        self.skill("---\nname: \"demo-skill\"\ndescription: 'quoted text'\n---\nbody\n")
        self.assertEqual(self.errors(), [])


class HooksTest(FixtureCase):
    def test_hooks_without_hooks_key_fails(self):
        write_json(self.root, "hooks/hooks.json", {"PreToolUse": []})
        self.assertFails("top-level 'hooks' key")

    def test_absent_hooks_file_is_allowed(self):
        (self.root / "hooks" / "hooks.json").unlink()
        self.assertEqual(self.errors(), [])


class SecretTest(FixtureCase):
    def assertSecretRejected(self, rel, value):
        self.mutate(rel, lambda d: d.update(note=value))
        self.assertFails("looks like a secret")

    def test_secret_value_patterns_fail(self):
        samples = {
            "github": "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4",
            "github_pat": "github_pat_" + "A" * 30,
            "openai": "sk-" + "abcdEFGH1234ijkl5678",
            "aws": "AKIA" + "ABCDEFGHIJKLMNOP",
            "slack": "xoxb-" + "1234567890-abcdef",
            "google": "AIza" + "A" * 35,
            "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.c2lnbmF0dXJlYWJjZGVm",
            "bearer": "Bearer " + "abcdefghijklmnop1234",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "url_credentials": "https://user:hunter2@example.com/x",
            "sk_underscore": "sk_" + "abcdEFGH1234ijkl5678",
            "npm": "npm_" + "A1b2C3d4E5f6G7h8I9j0K1l2",
        }
        for label, value in samples.items():
            with self.subTest(label=label):
                build_dir = tempfile.TemporaryDirectory()
                self.addCleanup(build_dir.cleanup)
                self.root = Path(build_dir.name)
                build_fixture(self.root)
                self.assertSecretRejected(".codex-plugin/plugin.json", value)

    def test_secret_in_each_manifest_fails(self):
        for rel in (
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            ".agents/plugins/marketplace.json",
        ):
            with self.subTest(rel=rel):
                build_dir = tempfile.TemporaryDirectory()
                self.addCleanup(build_dir.cleanup)
                self.root = Path(build_dir.name)
                build_fixture(self.root)
                self.assertSecretRejected(rel, "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4")

    def test_secret_named_key_with_value_fails(self):
        self.mutate(".claude-plugin/plugin.json", lambda d: d.update(api_key="abc"))
        self.assertFails("key 'api_key' looks like a secret")

    def test_nested_secret_named_key_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(mcpServers={"x": {"env": {"GITHUB_TOKEN": "abc"}}}))
        self.assertFails("GITHUB_TOKEN")

    def test_ordinary_text_is_not_flagged(self):
        self.mutate(
            ".codex-plugin/plugin.json",
            lambda d: d.update(note="Skills for tokens, secrets handling and sk-short are fine"),
        )
        self.assertEqual(self.errors(), [])

    def test_authentication_policy_is_not_flagged(self):
        # "authentication": "ON_INSTALL" is a policy setting, not a credential.
        self.assertEqual(self.errors(), [])


class SecretRefinementTest(FixtureCase):
    def test_env_reference_values_are_exempt(self):
        self.mutate(
            ".codex-plugin/plugin.json",
            lambda d: d.update(mcpServers={"x": {"env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}", "API_KEY": "$API_KEY"}}}),
        )
        self.assertEqual(self.errors(), [])

    def test_env_reference_lookalike_with_text_still_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(token="${TOKEN}-literal"))
        self.assertFails("key 'token' looks like a secret")

    def test_key_substring_alone_is_not_flagged(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(tokenizer="whitespace", secretary="Ann"))
        self.assertEqual(self.errors(), [])

    def test_camel_case_secret_keys_are_flagged(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(apiKey="abc"))
        self.assertFails("key 'apiKey' looks like a secret")

    def test_secret_in_hooks_json_fails(self):
        write_json(self.root, "hooks/hooks.json", {"hooks": {}, "note": "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4"})
        self.assertFails("hooks/hooks.json: value at 'note' looks like a secret")

    def test_secret_named_key_in_hooks_json_fails(self):
        write_json(self.root, "hooks/hooks.json", {"hooks": {}, "password": "hunter2"})
        self.assertFails("hooks/hooks.json: key 'password' looks like a secret")

    def test_secret_in_skill_body_fails(self):
        path = self.root / "skills" / "demo-skill" / "SKILL.md"
        path.write_text(SKILL + "\nUse key sk-" + "abcdEFGH1234ijkl5678 for the API.\n", encoding="utf-8")
        self.assertFails("skills/demo-skill/SKILL.md: contains a secret-looking value")


class VersionFormatTest(FixtureCase):
    def test_leading_zero_semver_fails(self):
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.mutate(rel, lambda d: d.update(version="01.02.03"))
        self.assertFails("'version' must be a semver string")

    def test_prerelease_and_build_semver_pass(self):
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.mutate(rel, lambda d: d.update(version="1.0.0-rc.1+build.5"))
        self.assertEqual(self.errors(), [])


class CodexSkillsPathTest(FixtureCase):
    def test_absolute_posix_path_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills="/etc"))
        self.assertFails("must be relative, not absolute")

    def test_absolute_path_of_real_directory_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills=str(self.root / "skills")))
        self.assertFails("must be relative, not absolute")

    def test_windows_drive_path_fails(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills="C:\\skills"))
        self.assertFails("must be relative, not absolute")

    def test_parent_escape_fails(self):
        outside = self.root.parent / "outside-skills"
        outside.mkdir(exist_ok=True)
        self.addCleanup(outside.rmdir)
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills="../outside-skills"))
        self.assertFails("escapes the repository root")

    def test_non_string_skills_fails(self):
        for value in (["./skills/"], 5, None, ""):
            with self.subTest(value=value):
                self.mutate(".codex-plugin/plugin.json", lambda d, v=value: d.update(skills=v))
                self.assertFails("must be a relative path string")

    def test_path_that_normalizes_inside_root_passes(self):
        self.mutate(".codex-plugin/plugin.json", lambda d: d.update(skills="./skills/../skills"))
        self.assertEqual(self.errors(), [])


class SkillFrontmatterLimitsTest(FixtureCase):
    def write_skill(self, directory, text):
        target = self.root / "skills" / directory
        target.mkdir(exist_ok=True)
        (target / "SKILL.md").write_text(text, encoding="utf-8")

    def test_overlong_name_fails(self):
        name = "a" * (vp.MAX_SKILL_NAME + 1)
        self.write_skill(name, f"---\nname: {name}\ndescription: x\n---\nbody\n")
        self.assertFails(f"name is longer than {vp.MAX_SKILL_NAME} characters")

    def test_name_at_limit_passes(self):
        name = "a" * vp.MAX_SKILL_NAME
        self.write_skill(name, f"---\nname: {name}\ndescription: x\n---\nbody\n")
        self.assertEqual(self.errors(), [])

    def test_overlong_description_fails(self):
        text = f"---\nname: demo-skill\ndescription: {'d' * (vp.MAX_SKILL_DESCRIPTION + 1)}\n---\nbody\n"
        self.write_skill("demo-skill", text)
        self.assertFails(f"description is longer than {vp.MAX_SKILL_DESCRIPTION} characters")

    def test_description_at_limit_passes(self):
        text = f"---\nname: demo-skill\ndescription: {'d' * vp.MAX_SKILL_DESCRIPTION}\n---\nbody\n"
        self.write_skill("demo-skill", text)
        self.assertEqual(self.errors(), [])

    def test_invalid_frontmatter_line_fails(self):
        self.write_skill("demo-skill", "---\nname: demo-skill\nthis line has no colon\n---\nbody\n")
        self.assertFails("invalid frontmatter line")

    def test_unterminated_frontmatter_fails(self):
        self.write_skill("demo-skill", "---\nname: demo-skill\n")
        self.assertFails("missing YAML frontmatter")

    def test_skills_directory_without_skills_fails(self):
        (self.root / "skills" / "demo-skill" / "SKILL.md").unlink()
        (self.root / "skills" / "demo-skill").rmdir()
        self.assertFails("skills/: no skill directories found")


class HooksShapeTest(FixtureCase):
    def test_hooks_not_an_object_fails(self):
        for value in ([], "none", 3, None):
            with self.subTest(value=value):
                write_json(self.root, "hooks/hooks.json", {"hooks": value})
                self.assertFails("'hooks' must be an object")

    def test_invalid_hooks_json_fails(self):
        (self.root / "hooks" / "hooks.json").write_text("{broken", encoding="utf-8")
        self.assertFails("hooks/hooks.json: cannot parse JSON")

    def test_hooks_json_not_an_object_fails(self):
        (self.root / "hooks" / "hooks.json").write_text("[]", encoding="utf-8")
        self.assertFails("hooks/hooks.json: top level must be a JSON object")


if __name__ == "__main__":
    unittest.main()
