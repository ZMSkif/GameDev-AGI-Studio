"""Tests for the GameDev Studio quality-gate hooks (stdlib unittest only).

The hook scripts are run as real subprocesses with real JSON payloads on stdin, shaped like the
Claude Code / Codex PreToolUse and SessionStart events. Fixture repositories are created in a
temporary directory outside any studio checkout. `gh` is never called for real: the preflight
tests put fake `git`/`gh` executables on PATH.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / "hooks"
SCRIPTS = HOOKS / "scripts"
GUARD = SCRIPTS / "guard_bash.py"
SESSION = SCRIPTS / "session_start.py"
LAUNCHER = HOOKS / "run-hook.cmd"
STUDIO_ORIGIN = "https://github.com/ZMSkif/GameDev-AGI-Studio.git"

sys.path.insert(0, str(SCRIPTS))
import guard_bash  # noqa: E402
import studio_scope  # noqa: E402
import studio_shell  # noqa: E402


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_PROJECT_DIR", "GAMEDEV_STUDIO_HOOK_DEBUG") and not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env.update(extra)
    return env


def git(cwd, *args):
    done = subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
         *args],
        cwd=str(cwd), env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return done.stdout.decode("utf-8", errors="replace")


def make_repo(parent, name, origin=STUDIO_ORIGIN, branch="main", marker=False, commit=True):
    repo = Path(parent) / name
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", branch)
    if origin:
        git(repo, "remote", "add", "origin", origin)
    if marker:
        (repo / ".gamedev-studio").write_text("", encoding="utf-8")
    if commit:
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-q", "-m", "init")
    return repo


def pre_payload(command, cwd, tool="Bash"):
    return {
        "session_id": "test", "transcript_path": "", "cwd": str(cwd), "permission_mode": "default",
        "hook_event_name": "PreToolUse", "tool_name": tool, "tool_use_id": "toolu_test",
        "tool_input": {"command": command, "description": "test"},
    }


def run_script(script, payload, env=None, raw=None, python_args=()):
    data = raw if raw is not None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return subprocess.run(
        [sys.executable, "-I", *python_args, str(script)], input=data, env=env or clean_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)


def decision(done):
    """Parsed stdout JSON of a finished hook, or None when it printed nothing."""
    text = done.stdout.decode("utf-8", errors="replace").strip()
    return json.loads(text) if text else None


def _make_writable_and_retry(func, path, _exc_info):
    """rmtree error handler: git object files are read-only on Windows."""
    try:
        os.chmod(path, 0o700)
        func(path)
    except OSError:
        pass


class HookTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="studio-hooks-")))
        self.addCleanup(shutil.rmtree, str(self.tmp), False, _make_writable_and_retry)

    def guard(self, command, cwd, tool="Bash", env=None):
        done = run_script(GUARD, pre_payload(command, cwd, tool), env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return decision(done)

    def assertBlocked(self, command, cwd, needle="", tool="Bash", env=None):
        out = self.guard(command, cwd, tool, env)
        self.assertIsNotNone(out, "expected a block for: %s" % command)
        specific = out["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "PreToolUse")
        self.assertEqual(specific["permissionDecision"], "deny")
        self.assertIn(needle, specific["permissionDecisionReason"])
        return specific["permissionDecisionReason"]

    def assertAllowed(self, command, cwd, tool="Bash", env=None):
        done = run_script(GUARD, pre_payload(command, cwd, tool), env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), b"", "unexpected output for: %s -> %r" % (command, done.stdout))


def make_bare_remote(parent, name="remote.git"):
    remote = Path(parent) / name
    git(parent, "init", "-q", "--bare", "-b", "main", str(remote))
    return remote


class DirectCommitAndPushRule(HookTestCase):
    """Rule 1 (decision #1)."""

    def setUp(self):
        super().setUp()
        # Hermetic: the origin is a local bare repository that already has main and master, and the
        # marker file (not the origin URL) puts the repository in scope.
        self.remote = make_bare_remote(self.tmp)
        self.repo = make_repo(self.tmp, "studio", origin=str(self.remote), marker=True)
        git(self.repo, "branch", "master")
        git(self.repo, "push", "-q", "origin", "main", "master")

    def test_commit_on_main_is_blocked_with_actionable_reason(self):
        reason = self.assertBlocked("git commit -m test", self.repo, "direct commit to main")
        self.assertIn("branch", reason)
        self.assertIn("pull request", reason)
        self.assertIn("decision #1", reason)

    def test_commit_variants_on_main_are_blocked(self):
        for cmd in (
            "git commit --allow-empty -m test",
            'git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -m "msg"',
            "git commit --amend --no-edit",
            "GIT_AUTHOR_NAME=x git commit -m x",
            "git add README.md && git commit -m x",
            "cd . && git commit -m x",
            "bash -c 'git commit -m x'",
            'git commit -m "$(cat <<\'EOF\'\nfix\n\nCo-Authored-By: x\nEOF\n)"',
            'git commit -m "исправление ошибки"',
        ):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "direct commit to main")

    def test_commit_on_master_is_blocked(self):
        repo = make_repo(self.tmp, "masterrepo", branch="master")
        self.assertBlocked("git commit -m x", repo, "master")

    def test_initial_commit_into_an_empty_repository_is_allowed(self):
        # decision #1: the necessary initial commit into an empty repository is the one exception
        repo = make_repo(self.tmp, "fresh", commit=False, marker=True)
        self.assertAllowed("git commit --allow-empty -m x", repo)
        self.assertAllowed("git add -A && git commit -m init", repo)
        self.assertAllowed('git -c user.name=x commit -m "$(cat <<\'EOF\'\ninit\nEOF\n)"', repo)

    def test_unborn_head_still_gets_the_credential_check(self):
        repo = make_repo(self.tmp, "fresh2", commit=False, marker=True)
        (repo / ".env").write_text("S=1", encoding="utf-8")
        git(repo, "add", "-f", ".env")
        self.assertBlocked("git commit -m init", repo, ".env")

    def test_second_commit_on_main_is_blocked_again(self):
        repo = make_repo(self.tmp, "fresh3", commit=False, marker=True)
        git(repo, "commit", "-q", "--allow-empty", "-m", "initial")
        self.assertBlocked("git commit --allow-empty -m second", repo, "direct commit to main")

    def test_commit_on_feature_branch_is_allowed(self):
        git(self.repo, "switch", "-q", "-c", "feat/x")
        self.assertAllowed("git commit --allow-empty -m test", self.repo)
        self.assertAllowed('git commit -m "mentions main and git push origin main in the text"', self.repo)

    def test_detached_head_is_allowed(self):
        git(self.repo, "checkout", "-q", "--detach")
        self.assertAllowed("git commit --allow-empty -m x", self.repo)

    def test_commit_dry_run_on_main_is_allowed(self):
        self.assertAllowed("git commit --dry-run -m x", self.repo)

    def test_push_to_main_forms_are_blocked(self):
        git(self.repo, "switch", "-q", "-c", "feat/x")
        for cmd in (
            "git push origin main",
            "git push -u origin main",
            "git push --force origin main",
            "git push --force-with-lease origin main",
            "git push origin HEAD:main",
            "git push origin feat/x:main",
            "git push origin +feat/x:refs/heads/main",
            "git push origin refs/heads/main",
            "git push origin :main",
            "git push --delete origin main",
            "git push origin master",
            "git push origin feat/x main",
            "git push --all",
            "git push --mirror",
            "git push origin 'refs/heads/*:refs/heads/*'",
            "git -C . push origin main",
            "cd . && git push origin main 2>&1 | tail -3",
            "git status && git push origin main",
            "git push --recurse-submodules=check origin main",
            "git push --recurse-submodules check origin main",
            "git push -o ci.skip origin main",
            "git push --repo origin main",
        ):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "git push")

    def test_bare_push_blocked_only_when_head_is_main(self):
        self.assertBlocked("git push", self.repo, "main")
        self.assertBlocked("git push --force", self.repo, "main")
        self.assertBlocked("git push origin", self.repo, "main")
        self.assertBlocked("git push origin HEAD", self.repo, "main")
        git(self.repo, "switch", "-q", "-c", "feat/y")
        self.assertAllowed("git push", self.repo)
        self.assertAllowed("git push -u origin HEAD", self.repo)
        self.assertAllowed("git push origin", self.repo)

    def test_merge_cherry_pick_revert_rebase_on_main_are_blocked(self):
        for cmd in ("git merge feat/x", "git merge --ff-only origin/main", "git merge --no-ff feat/x -m msg",
                    "git cherry-pick abc123", "git revert HEAD", "git rebase origin/main", "git -C . merge feat/x",
                    "git checkout main && git merge feat/x"):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "would change main directly")

    def test_history_rewriters_may_be_aborted_or_continued_on_main(self):
        for cmd in ("git merge --abort", "git rebase --abort", "git rebase --continue", "git rebase --skip",
                    "git cherry-pick --quit", "git cherry-pick --continue", "git revert --abort",
                    "git merge --continue"):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_history_rewriters_are_allowed_off_main(self):
        git(self.repo, "switch", "-q", "-c", "feat/x")
        for cmd in ("git merge main", "git rebase main", "git rebase origin/main", "git cherry-pick abc123",
                    "git revert HEAD", "git switch -c feat/y && git merge main"):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_pushes_that_do_not_touch_main_are_allowed(self):
        for cmd in (
            "git push origin feat/main-menu",
            "git push -u origin feat/PLUGIN-05-quality-hooks",
            "git push origin feature",
            "git push origin main:feature",
            "git push origin HEAD:refs/heads/feat/x",
            "git push origin --tags",
            "git push --dry-run origin main",
            "git push -n origin main",
            "git push origin v1.0.0",
            "git push origin release/main-2",
        ):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_pushing_a_feature_branch_while_main_is_checked_out_is_allowed(self):
        self.assertAllowed("git push origin feature", self.repo)

    def test_reads_are_never_blocked_on_main(self):
        for cmd in ("git status", "git log --oneline -5", "git diff", "git pull --ff-only origin main",
                    "git fetch origin main", "git branch -a", "git show HEAD", "git stash list",
                    "git remote -v", "git checkout feat/x", "git switch -c feat/x"):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_text_that_merely_contains_git_commands_is_allowed(self):
        for cmd in (
            'gh pr create --title t --body "never run git push origin main or git commit on main"',
            'echo "git push origin main"',
            "cat > notes.md <<'EOF'\ngit push origin main\ngit commit -m x\nEOF\ngit status",
            "cat > notes.md <<EOF\ngit push --force origin main\nEOF",
            'printf "git commit -m x" > run.sh',
            "# git push origin main",
            "grep -rn 'git push' docs/",
        ):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_creating_a_branch_in_the_same_command_line_is_allowed(self):
        for cmd in (
            "git checkout -b feat/x && git commit -m y",
            "git switch -c feat/x && git add -A && git commit -m y",
            "git checkout -B feat/x; git commit -m y",
            "git switch -c feat/x && git push -u origin feat/x",
            "git switch -c feat/x && git push",
        ):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_switching_to_main_in_the_same_command_line_is_blocked(self):
        git(self.repo, "switch", "-q", "-c", "feat/x")
        self.assertBlocked("git checkout main && git commit -m y", self.repo, "main")
        self.assertBlocked("git switch main && git push", self.repo, "main")

    def test_linked_worktree_commit_while_session_sits_on_main_checkout(self):
        wt = self.tmp / "wt"
        git(self.repo, "worktree", "add", "-q", "-b", "feat/wt", str(wt))
        for cmd in ("cd %s && git commit --allow-empty -m x" % wt,
                    "git -C %s commit --allow-empty -m x" % wt,
                    "cd '%s' && git add -A && git commit -m x" % wt):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)
        self.assertBlocked("git -C %s commit --allow-empty -m x" % self.repo, wt, "main")
        self.assertBlocked("cd %s && git commit -m x" % self.repo, wt, "main")
        self.assertBlocked("git commit -m x", self.repo, "main")

    def test_posix_style_windows_paths_are_resolved(self):
        if os.name != "nt":
            self.skipTest("Windows only")
        wt = self.tmp / "wt2"
        git(self.repo, "worktree", "add", "-q", "-b", "feat/wt2", str(wt))
        posix = "/" + str(wt).replace("\\", "/").replace(":", "", 1)
        self.assertAllowed("cd %s && git commit --allow-empty -m x" % posix, self.repo)

    def test_unresolvable_directory_fails_open(self):
        # the target of `cd` is unknown, so the commit cannot be placed on a branch: allowed (known gap)
        self.assertAllowed('cd "$(git rev-parse --show-toplevel)" && git commit -m x', self.repo)
        self.assertAllowed('cd "$WORKTREE" && git push origin main', self.repo)
        self.assertAllowed('cd does-not-exist && git commit -m x', self.repo)
        # a later resolvable cd or an explicit -C brings the check back
        self.assertBlocked('cd "$X"; cd %s && git commit -m x' % self.repo, self.repo, "main")
        self.assertBlocked('cd "$X"; git -C %s commit -m x' % self.repo, self.repo, "main")

    def test_checkout_of_paths_from_main_is_not_a_branch_switch(self):
        git(self.repo, "switch", "-q", "-c", "feat/x")
        self.assertAllowed("git checkout main -- README.md && git commit -m y", self.repo)
        self.assertAllowed("git checkout -- README.md && git commit -m y", self.repo)
        self.assertAllowed("git restore --source=main README.md && git commit -m y", self.repo)
        self.assertBlocked("git checkout main -- && git commit -m y", self.repo, "main")

    def test_powershell_tool_payload(self):
        self.assertBlocked("git commit -m x", self.repo, "main", tool="PowerShell")
        self.assertBlocked("Set-Location . ; git push origin main", self.repo, "git push", tool="PowerShell")
        self.assertBlocked("git status; git push origin main", self.repo, "git push", tool="PowerShell")
        self.assertAllowed("git status; git log -1", self.repo, tool="PowerShell")

    def test_powershell_backtick_is_an_escape_not_a_separator(self):
        for cmd in ("git push origin `\n  main", "git push `\n  origin main", "git push origin `\r\n  main",
                    "git push origin main `\n  --force"):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "git push", tool="PowerShell")
        git(self.repo, "switch", "-q", "-c", "feat/x")
        self.assertAllowed("git push origin `\n  feat/x", self.repo, tool="PowerShell")
        self.assertAllowed("git push `\n  -u origin feat/x", self.repo, tool="PowerShell")
        self.assertBlocked('git commit -m "say `"hi`""; git push origin `\n main', self.repo, "git push",
                           tool="PowerShell")
        self.assertAllowed('git commit -m "say `"hi`" and `$x"', self.repo, tool="PowerShell")

    def test_backtick_before_a_newline_continues_the_line_in_bash_tool_payloads_too(self):
        # Codex on Windows reports tool_name "Bash" but runs PowerShell
        self.assertBlocked("git push origin `\n  main", self.repo, "git push")

    def test_codex_argv_command_payload(self):
        payload = pre_payload("", self.repo)
        payload["tool_input"] = {"command": ["git", "commit", "-m", "two words"]}
        out = decision(run_script(GUARD, payload))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_works_without_git_on_path_using_head_file(self):
        env = clean_env(PATH=os.devnull)
        self.assertBlocked("git commit -m x", self.repo, "main", env=env)


class InitialPushRule(HookTestCase):
    """Decision #1 allows the initial push into an empty remote, nothing else on main/master."""

    def setUp(self):
        super().setUp()
        self.remote = make_bare_remote(self.tmp)
        self.repo = make_repo(self.tmp, "game", origin=str(self.remote), marker=True)

    def test_plain_push_of_main_into_an_empty_remote_is_allowed(self):
        for cmd in ("git push origin main", "git push -u origin main", "git push origin HEAD:main",
                    "git push origin main:main", "git push origin refs/heads/main", "git push", "git push origin",
                    "git push -u origin HEAD", "git push --set-upstream origin main && git status"):
            with self.subTest(cmd=cmd):
                self.assertAllowed(cmd, self.repo)

    def test_master_into_an_empty_remote_is_allowed(self):
        repo = make_repo(self.tmp, "game-master", origin=str(self.remote), marker=True, branch="master")
        self.assertAllowed("git push origin master", repo)

    def test_force_push_is_denied_even_into_an_empty_remote(self):
        for cmd in ("git push --force origin main", "git push -f origin main", "git push origin +main",
                    "git push --force-with-lease origin main", "git push -fu origin main",
                    "git push origin +HEAD:main", "git push --force-if-includes origin main"):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "would update main")

    def test_deleting_or_mass_pushing_is_denied_even_into_an_empty_remote(self):
        for cmd in ("git push origin :main", "git push --delete origin main", "git push --all",
                    "git push --mirror", "git push origin 'refs/heads/*:refs/heads/*'"):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, "git push")

    def test_push_is_denied_once_the_remote_has_the_branch(self):
        git(self.repo, "push", "-q", "origin", "main")
        for cmd in ("git push origin main", "git push", "git push -u origin main", "git push origin HEAD:main"):
            with self.subTest(cmd=cmd):
                reason = self.assertBlocked(cmd, self.repo, "git push")
                self.assertIn("initial push into an empty remote", reason)

    def test_presence_is_checked_per_branch(self):
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "branch", "master")
        # main exists, master does not
        self.assertAllowed("git push origin master", self.repo)
        self.assertBlocked("git push origin main master", self.repo, "git push")

    def test_unverifiable_remote_is_denied_with_a_clear_message(self):
        repo = make_repo(self.tmp, "game2", origin=str(self.tmp / "does-not-exist.git"), marker=True)
        reason = self.assertBlocked("git push origin main", repo, "ls-remote")
        self.assertIn("failed or timed out", reason)

    def test_pushes_of_other_branches_never_need_the_remote(self):
        repo = make_repo(self.tmp, "game3", origin=str(self.tmp / "does-not-exist.git"), marker=True)
        git(repo, "switch", "-q", "-c", "feat/x")
        self.assertAllowed("git push -u origin feat/x", repo)
        self.assertAllowed("git push", repo)


class CredentialFileRule(HookTestCase):
    """Rule 2 (decision #9)."""

    def setUp(self):
        super().setUp()
        self.repo = make_repo(self.tmp, "studio")
        git(self.repo, "switch", "-q", "-c", "feat/x")

    def write(self, rel, text="x"):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_is_credential_path(self):
        yes = [".env", ".env.local", ".env.production", "cfg/.env", "a/b/server.pem", "tls.key", "id_rsa",
               "id_rsa_work", "id_ed25519", "id_ed25519_sk", "id_ecdsa", "id_ecdsa_sk", "id_dsa", "app.keystore",
               "cert.p12", "cert.pfx", "putty.ppk", "release.jks", "SERVER.PEM", "config\\prod.pem", ".ENV"]
        no = [".env.example", ".env.sample", ".env.template", ".env.production.example", "env.py", "environment.md",
              "keyboard.cs", "monkey.txt", "pem.md", "README.md", "src/key_binding.gd", "jks.txt", "dotenv", "",
              "id_rsa.pub", "id_ed25519.pub", "id_ecdsa.pub", "id_dsa.pub", "keys/id_rsa.pub", "my.key.pub",
              "known_hosts", "keystore.md"]
        for name in yes:
            with self.subTest(yes=name):
                self.assertTrue(guard_bash.is_credential_path(name))
        for name in no:
            with self.subTest(no=name):
                self.assertFalse(guard_bash.is_credential_path(name))

    def test_add_of_each_credential_pattern_is_blocked(self):
        for name in (".env", ".env.local", "keys/server.pem", "tls.key", "id_rsa", "id_rsa_old", "a.p12", "b.pfx",
                     "c.ppk", "d.jks", "id_ed25519", "id_ecdsa", "id_dsa", "release.keystore"):
            self.write(name)
            with self.subTest(name=name):
                reason = self.assertBlocked("git add %s" % name, self.repo, "credential-like")
                self.assertIn("decision #9", reason)
                self.assertIn(os.path.basename(name), reason)

    def test_add_of_templates_and_normal_files_is_allowed(self):
        for name in (".env.example", ".env.sample", ".env.template", "src/main.gd", "id_rsa.pub", "id_ed25519.pub"):
            self.write(name)
        self.assertAllowed("git add .env.example .env.sample .env.template src/main.gd id_rsa.pub id_ed25519.pub",
                           self.repo)
        self.assertAllowed("git add -A", self.repo)
        self.assertAllowed("git add .", self.repo)

    def test_broad_add_is_checked_through_dry_run(self):
        self.write(".env")
        self.write("src/main.gd")
        for cmd in ("git add .", "git add -A", "git add --all", "git add src .", "git add -f .",
                    "git add . && git commit -m x", "git add *"):
            with self.subTest(cmd=cmd):
                self.assertBlocked(cmd, self.repo, ".env")

    def test_broad_add_is_allowed_when_the_secret_is_gitignored(self):
        self.write(".gitignore", ".env\n*.pem\n")
        self.write(".env")
        self.write("server.pem")
        self.write("src/main.gd")
        self.assertAllowed("git add .", self.repo)
        self.assertAllowed("git add -A", self.repo)
        self.assertBlocked("git add -f .env", self.repo, ".env")
        self.assertBlocked("git add -f .", self.repo, ".env")

    def test_add_dry_run_is_allowed(self):
        self.write(".env")
        self.assertAllowed("git add -n .env", self.repo)
        self.assertAllowed("git add --dry-run .", self.repo)

    def test_commit_with_staged_credential_is_blocked(self):
        self.write(".env")
        self.write("ok.txt")
        git(self.repo, "add", "-f", ".env", "ok.txt")
        reason = self.assertBlocked("git commit -m x", self.repo, ".env")
        self.assertIn("credential-like", reason)

    def test_commit_with_only_normal_staged_files_is_allowed(self):
        self.write("ok.txt")
        git(self.repo, "add", "ok.txt")
        self.assertAllowed("git commit -m x", self.repo)
        self.assertAllowed("git commit -m 'text mentioning .env and id_rsa'", self.repo)

    def test_commit_all_includes_modified_tracked_credentials(self):
        self.write("tls.key", "old")
        git(self.repo, "add", "-f", "tls.key")
        git(self.repo, "commit", "-q", "-m", "oops tracked")
        self.write("tls.key", "new")
        self.assertBlocked("git commit -am x", self.repo, "tls.key")
        self.assertBlocked("git commit -a -m x", self.repo, "tls.key")
        self.assertBlocked("git commit --all -m x", self.repo, "tls.key")
        self.assertAllowed("git commit -m x", self.repo)  # nothing staged

    def test_commit_with_explicit_credential_path_is_blocked(self):
        self.write("server.pem")
        self.assertBlocked("git commit server.pem -m x", self.repo, "server.pem")
        self.assertBlocked("git commit -m x -- server.pem", self.repo, "server.pem")

    def test_staged_deletion_of_a_credential_is_allowed(self):
        self.write("tls.key")
        git(self.repo, "add", "-f", "tls.key")
        git(self.repo, "commit", "-q", "-m", "oops")
        git(self.repo, "rm", "-q", "--cached", "tls.key")
        self.assertAllowed("git commit -m remove", self.repo)

    def test_credentials_rule_applies_on_feature_branch_and_main(self):
        self.write(".env")
        git(self.repo, "add", "-f", ".env")
        git(self.repo, "switch", "-q", "main")
        out = self.guard("git commit -m x", self.repo)
        self.assertIsNotNone(out)  # blocked by rule 1 first; either rule blocks


class ScopeGuard(HookTestCase):
    """Every hook is a silent no-op outside a GameDev Studio project."""

    BLOCKING = ("git commit -m x", "git push origin main", "git add .env", "git push --force origin main")

    def assertSilentEverywhere(self, directory):
        (Path(directory) / ".env").write_text("x", encoding="utf-8")
        for cmd in self.BLOCKING:
            with self.subTest(cmd=cmd, directory=str(directory)):
                done = run_script(GUARD, pre_payload(cmd, directory))
                self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"", b""))
        done = run_script(SESSION, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(directory)})
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"", b""))

    def test_other_repository_is_untouched(self):
        self.assertSilentEverywhere(make_repo(self.tmp, "cs2", origin="https://github.com/ZMSkif/cs2-video-toolkit.git"))

    def test_repository_without_remote_is_untouched(self):
        self.assertSilentEverywhere(make_repo(self.tmp, "local", origin=None))

    def test_directory_that_is_not_a_repository_is_untouched(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.assertSilentEverywhere(plain)

    def test_lookalike_origins_are_out_of_scope(self):
        for i, url in enumerate((
            "https://github.com/ZMSkif/GameDev-AGI-Studio-fork.git",
            "https://github.com/someone/ZMSkif/GameDev-AGI-Studio.git",
            "https://github.com.evil.example/ZMSkif/GameDev-AGI-Studio.git",
            "https://evilgithub.com/ZMSkif/GameDev-AGI-Studio.git",
            "https://example.com/ZMSkif/GameDev-AGI-Studio.git",
            "https://github.com/ZMSkif/GameDev-AGI-Studio.git.bak",
            "git@github.com:other/GameDev-AGI-Studio.git",
        )):
            with self.subTest(url=url):
                self.assertFalse(studio_scope.is_studio_origin(url))
                self.assertSilentEverywhere(make_repo(self.tmp, "look%d" % i, origin=url))

    def test_studio_origin_url_forms_are_in_scope(self):
        for i, url in enumerate((
            "https://github.com/ZMSkif/GameDev-AGI-Studio.git",
            "https://github.com/ZMSkif/GameDev-AGI-Studio",
            "https://github.com/zmskif/gamedev-agi-studio.git",
            "https://github.com/ZMSkif/GameDev-AGI-Studio/",
            "https://ghp_token@github.com/ZMSkif/GameDev-AGI-Studio.git",
            "git@github.com:ZMSkif/GameDev-AGI-Studio.git",
            "ssh://git@github.com/ZMSkif/GameDev-AGI-Studio.git",
            "git://github.com/ZMSkif/GameDev-AGI-Studio.git",
        )):
            with self.subTest(url=url):
                repo = make_repo(self.tmp, "in%d" % i, origin=url)
                self.assertBlocked("git commit -m x", repo, "main")

    def test_marker_file_puts_a_repository_in_scope_without_any_remote(self):
        repo = make_repo(self.tmp, "game", origin=None, marker=True)
        self.assertBlocked("git commit -m x", repo, "main")
        self.assertBlocked("git push origin main", repo, "git push")
        git(repo, "switch", "-q", "-c", "feat/x")
        self.assertAllowed("git commit --allow-empty -m x", repo)

    def test_marker_beats_a_foreign_origin(self):
        repo = make_repo(self.tmp, "game2", origin="https://github.com/me/mygame.git", marker=True)
        self.assertBlocked("git commit -m x", repo, "main")

    def test_marker_in_a_non_git_directory_is_in_scope(self):
        plain = self.tmp / "gamefolder"
        (plain / "sub").mkdir(parents=True)
        (plain / ".gamedev-studio").write_text("", encoding="utf-8")
        self.assertTrue(studio_scope.is_studio_dir(str(plain / "sub")))

    def test_subdirectory_of_a_studio_repository_is_in_scope(self):
        repo = make_repo(self.tmp, "deep")
        sub = repo / "a" / "b"
        sub.mkdir(parents=True)
        self.assertBlocked("git commit -m x", sub, "main")

    def test_nested_foreign_repository_inside_a_marker_directory_is_out_of_scope(self):
        outer = self.tmp / "outer"
        outer.mkdir()
        (outer / ".gamedev-studio").write_text("", encoding="utf-8")
        inner = make_repo(outer, "inner", origin="https://github.com/x/y.git")
        self.assertSilentEverywhere(inner)

    def test_linked_worktree_inherits_scope_from_the_common_git_dir(self):
        repo = make_repo(self.tmp, "main-checkout")
        wt = self.tmp / "linked"
        git(repo, "worktree", "add", "-q", "-b", "feat/wt", str(wt))
        self.assertTrue(studio_scope.is_studio_dir(str(wt)))
        self.assertAllowed("git commit --allow-empty -m x", wt)

    def test_studio_target_is_guarded_from_any_session_directory(self):
        # no session-level gate: the directory a git command targets decides
        repo = make_repo(self.tmp, "proj", origin=None, marker=True)
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        foreign = make_repo(self.tmp, "foreign", origin="https://github.com/x/y.git")
        for session in (elsewhere, foreign):
            for cmd in ("git -C %s commit -m x" % repo, "cd %s && git commit -m x" % repo,
                        "git -C %s push origin main" % repo, "cd %s; git push --force origin main" % repo):
                with self.subTest(session=session.name, cmd=cmd):
                    self.assertBlocked(cmd, session, "main")
        self.assertBlocked("git -C %s commit -m x" % repo, elsewhere, "main", env=clean_env(CLAUDE_PROJECT_DIR=str(repo)))

    def test_out_of_scope_targets_stay_silent_from_any_session(self):
        repo = make_repo(self.tmp, "proj3")
        other = make_repo(self.tmp, "other2", origin="https://github.com/x/y.git")
        plain = self.tmp / "plain"
        plain.mkdir()
        (other / ".env").write_text("x", encoding="utf-8")
        for session in (repo, plain):
            for cmd in ("git -C %s commit -m x" % other, "cd %s && git commit -m x" % other,
                        "git -C %s push origin main" % other, "git -C %s add .env" % other):
                with self.subTest(session=session.name, cmd=cmd):
                    self.assertAllowed(cmd, session)

    def test_session_start_scope_also_uses_claude_project_dir(self):
        repo = make_repo(self.tmp, "proj4")
        elsewhere = self.tmp / "elsewhere2"
        elsewhere.mkdir()
        payload = {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(elsewhere)}
        self.assertEqual(run_script(SESSION, payload).stdout, b"")
        done = run_script(SESSION, payload, env=clean_env(CLAUDE_PROJECT_DIR=str(repo)))
        self.assertIn(b"gamedev-studio:studio-rules", done.stdout)


class FailOpen(HookTestCase):
    def test_malformed_and_unexpected_input_exits_zero_silently(self):
        repo = make_repo(self.tmp, "studio")
        garbage = (
            ("empty", b""),
            ("not json", b"this is not json"),
            ("truncated", b'{"cwd": "'),
            ("array", b"[1, 2, 3]"),
            ("string", b'"git commit"'),
            ("null", b"null"),
            ("bad utf8", bytes([0xFF, 0xFE]) + b'{"cwd": 1}'),
        )
        for label, raw in garbage:
            for script in (GUARD, SESSION):
                with self.subTest(case=label, script=script.name):
                    done = run_script(script, None, raw=raw)
                    self.assertEqual((done.returncode, done.stdout), (0, b""), done.stderr)
        # structurally valid JSON with unexpected shapes: the guard stays silent
        shapes = (
            ("no tool_input", {"cwd": str(repo), "tool_name": "Bash"}),
            ("tool_input string", {"cwd": str(repo), "tool_input": "git commit"}),
            ("command null", {"cwd": str(repo), "tool_input": {"command": None}}),
            ("command number", {"cwd": str(repo), "tool_input": {"command": 5}}),
            ("command dict", {"cwd": str(repo), "tool_input": {"command": {"a": "git commit"}}}),
            ("cwd number", {"cwd": 5, "tool_input": {"command": "git commit"}}),
            ("cwd missing dir", pre_payload("git commit -m x", self.tmp / "missing")),
        )
        for label, payload in shapes:
            with self.subTest(case=label):
                done = run_script(GUARD, payload)
                self.assertEqual((done.returncode, done.stdout), (0, b""), done.stderr)

    def test_unbalanced_quote_does_not_crash(self):
        repo = make_repo(self.tmp, "studio")
        done = run_script(GUARD, pre_payload('git commit -m "unterminated', repo))
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_internal_error_exits_zero_and_prints_nothing(self):
        repo = make_repo(self.tmp, "studio")
        code = textwrap.dedent("""
            import sys
            sys.path.insert(0, %r)
            import guard_bash, studio_scope
            def boom(*a, **k):
                raise RuntimeError("boom")
            guard_bash.evaluate = boom
            studio_scope.fail_open(guard_bash.main)
        """ % str(SCRIPTS))
        done = subprocess.run([sys.executable, "-I", "-c", code], input=json.dumps(pre_payload("git commit -m x", repo)).encode(),
                              env=clean_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"", b""))

    def test_internal_error_is_visible_only_with_debug_env(self):
        code = textwrap.dedent("""
            import sys
            sys.path.insert(0, %r)
            import studio_scope
            def boom():
                raise RuntimeError("boom")
            studio_scope.fail_open(boom)
        """ % str(SCRIPTS))
        done = subprocess.run([sys.executable, "-I", "-c", code], env=clean_env(GAMEDEV_STUDIO_HOOK_DEBUG="1"),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.assertEqual(done.returncode, 0)
        self.assertIn(b"boom", done.stderr)

    def test_hooks_are_fast_outside_scope(self):
        import time
        plain = self.tmp / "plain"
        plain.mkdir()
        start = time.time()
        run_script(GUARD, pre_payload("git commit -m x", plain))
        self.assertLess(time.time() - start, 3.0)


def make_fake_tool(directory: Path, name: str, exit_code: int = 0, sleep: float = 0.0):
    """A fake executable that records its arguments in <name>.log, sleeps, then exits with exit_code."""
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / (name + ".log")
    body = ("import sys,time\nopen(%r,'a').write(' '.join(sys.argv[1:])+chr(10))\ntime.sleep(%s)\nsys.exit(%d)\n"
            % (str(log), sleep, exit_code))
    script = directory / (name + "_impl.py")
    script.write_text(body, encoding="utf-8")
    if os.name == "nt":
        (directory / (name + ".cmd")).write_text('@echo off\r\n"%s" "%s" %%*\r\n' % (sys.executable, script),
                                                 encoding="utf-8")
    else:
        path = directory / name
        path.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, script), encoding="utf-8")
        path.chmod(0o755)


class SessionStartHook(HookTestCase):
    def setUp(self):
        super().setUp()
        self.repo = make_repo(self.tmp, "studio")
        self.bin = self.tmp / "bin"

    def env(self, with_git=True, gh=0):
        if with_git:
            make_fake_tool(self.bin, "git")
        if gh is not None:
            make_fake_tool(self.bin, "gh", exit_code=gh)
        extra = {"PATH": str(self.bin)}
        if os.name == "nt":
            extra["SystemRoot"] = os.environ.get("SystemRoot", r"C:\Windows")
            extra["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
        return clean_env(**extra)

    def start(self, env, source="startup", code_patch=""):
        payload = {"session_id": "t", "hook_event_name": "SessionStart", "source": source, "cwd": str(self.repo)}
        if not code_patch:
            done = run_script(SESSION, payload, env=env)
        else:
            code = "import sys; sys.path.insert(0, %r)\nimport session_start as s\n%s\nimport studio_scope\nstudio_scope.fail_open(s.main)" % (
                str(SCRIPTS), code_patch)
            done = subprocess.run([sys.executable, "-I", "-c", code], input=json.dumps(payload).encode(), env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return decision(done)

    def test_healthy_tools_emit_only_the_reminder(self):
        out = self.start(self.env())
        self.assertNotIn("systemMessage", out)
        specific = out["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "SessionStart")
        text = specific["additionalContext"]
        self.assertNotIn("preflight FAILED", text)
        self.assertIn("gamedev-studio:studio-rules", text)
        self.assertIn("actually ran", text)
        self.assertIn("independent review", text)
        self.assertLessEqual(len(text.splitlines()), 4)

    def test_reminder_is_emitted_for_every_session_source(self):
        env = self.env()
        for source in ("startup", "resume", "clear", "compact"):
            with self.subTest(source=source):
                self.assertIn("gamedev-studio:studio-rules", self.start(env, source)["hookSpecificOutput"]["additionalContext"])

    def test_missing_gh_is_reported_and_does_not_block(self):
        out = self.start(self.env(gh=None))
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("preflight FAILED", text)
        self.assertIn("`gh` (GitHub CLI) was not found", text)
        self.assertIn("stop and request recovery", text)
        self.assertIn("gamedev-studio:studio-rules", text)  # reminder still present
        self.assertIn("gh", out["systemMessage"])
        self.assertNotIn("decision", out)
        self.assertNotIn("continue", out)

    def test_unauthenticated_gh_is_reported(self):
        out = self.start(self.env(gh=1))
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("`gh auth status` failed (exit 1)", text)
        # a non-zero exit may be a network error, so it must not be reported as "not authenticated"
        self.assertIn("gh authentication failed or could not be verified (possibly a network error)", text)
        self.assertIn("possibly a network error", out["systemMessage"])
        self.assertNotIn("not authenticated", text + out["systemMessage"])

    def test_gh_auth_status_is_scoped_to_github_com(self):
        self.start(self.env())
        calls = (self.bin / "gh.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls, ["auth status --hostname github.com"])

    def test_missing_git_is_reported(self):
        out = self.start(self.env(with_git=False))
        self.assertIn("`git` was not found", out["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("`gh` (GitHub CLI) was not found", out["hookSpecificOutput"]["additionalContext"])

    def test_both_tools_missing_are_both_named(self):
        out = self.start(self.env(with_git=False, gh=None))
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("`git` was not found", text)
        self.assertIn("`gh` (GitHub CLI) was not found", text)

    def test_gh_auth_timeout_is_reported_as_unverified(self):
        make_fake_tool(self.bin, "git")
        make_fake_tool(self.bin, "gh", exit_code=0, sleep=5)
        out = self.start(self.env(with_git=False, gh=None), code_patch="s.GH_AUTH_TIMEOUT = 1")
        self.assertIn("could not be verified", out["hookSpecificOutput"]["additionalContext"])

    def test_output_is_a_single_json_object(self):
        done = run_script(SESSION, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(self.repo)},
                          env=self.env())
        text = done.stdout.decode("ascii")  # ASCII-only JSON, safe on any console code page
        self.assertNotIn("\r", text)
        self.assertEqual(text.count("\n"), 1)
        json.loads(text)


class ParserUnits(unittest.TestCase):
    def git_events(self, command):
        return [e for e in studio_shell.parse(command) if e[0] == "git"]

    def test_global_options_and_env_prefixes(self):
        ev = self.git_events('FOO=1 BAR="a b" git -C ../x -c user.name="A B" --no-pager commit -m "msg"')
        self.assertEqual(ev, [("git", ["../x"], "commit", ["-m", "msg"], False)])

    def test_operators_split_commands(self):
        ev = self.git_events("git status && git add . || git push; git log | cat")
        self.assertEqual([e[2] for e in ev], ["status", "add", "push", "log"])

    def test_quoted_operators_do_not_split(self):
        ev = self.git_events('git commit -m "a && git push origin main; b"')
        self.assertEqual([e[2] for e in ev], ["commit"])

    def test_heredoc_commit_message_and_redirect_tokens(self):
        cmd = 'git commit -m "$(cat <<\'EOF\'\nline && git push origin main\nEOF\n)" 2>&1'
        self.assertEqual([e[2:4] for e in self.git_events(cmd)], [("commit", ["-m", "$(cat <<'EOF'\n)"])])

    def test_unterminated_heredoc_keeps_following_commands(self):
        ev = self.git_events("echo a <<EOF\ngit push origin main")
        self.assertEqual([e[2] for e in ev], ["push"])

    def test_windows_backslash_paths_are_kept(self):
        ev = self.git_events(r"git add C:\work\game\.env")
        self.assertEqual(ev[0][3], [r"C:\work\game\.env"])

    def test_nested_shells(self):
        self.assertEqual([e[2] for e in self.git_events("bash -lc 'cd x && git push origin main'")], ["push"])
        self.assertEqual([e[2] for e in self.git_events('pwsh -NoProfile -Command "git commit -m x"')], ["commit"])

    def test_powershell_backtick_tokenization(self):
        ps = studio_shell.parse("git push origin `\n  main", powershell=True)
        self.assertEqual([e[2:4] for e in ps], [("push", ["origin", "main"])])
        ps = studio_shell.parse("git commit -m \"a `\"b`\" c\"; git status", powershell=True)
        self.assertEqual([e[2:4] for e in ps], [("commit", ["-m", 'a "b" c']), ("status", [])])
        # without powershell=True a backtick opens a command substitution (separator)...
        bash = studio_shell.parse("echo `git status`")
        self.assertEqual([e[2] for e in bash], ["status"])
        # ... except right before a newline
        bash = studio_shell.parse("git push origin `\n main")
        self.assertEqual([e[2:4] for e in bash], [("push", ["origin", "main"])])

    def test_cd_events(self):
        self.assertEqual(studio_shell.parse("cd a/b && git status")[0], ("cd", "a/b"))

    def test_git_dir_option_marks_the_invocation_unresolvable(self):
        self.assertTrue(self.git_events("git --git-dir=/x/.git commit -m y")[0][4])


class Configuration(unittest.TestCase):
    def load(self, name):
        return json.loads((HOOKS / name).read_text(encoding="utf-8"))

    def commands(self, data):
        for event, groups in data["hooks"].items():
            for group in groups:
                for hook in group["hooks"]:
                    yield event, group, hook

    def test_claude_hooks_json(self):
        data = self.load("hooks.json")
        events = {e for e, _g, _h in self.commands(data)}
        self.assertEqual(events, {"SessionStart", "PreToolUse"})
        for event, group, hook in self.commands(data):
            self.assertEqual(hook["type"], "command")
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", hook["command"])
            self.assertIn("run-hook.cmd", hook["command"])
            script = hook["command"].rsplit(" ", 1)[1]
            self.assertTrue((SCRIPTS / (script + ".py")).is_file(), script)
            self.assertLessEqual(hook["timeout"], 20)
            if event == "PreToolUse":
                self.assertEqual(hook["onFailure"], "continue")  # a crashed hook must not block work
                self.assertIn(group["matcher"], ("Bash", "PowerShell"))
                self.assertIn("git", hook["if"])
            else:
                self.assertIn("compact", group["matcher"])

    def test_codex_hooks_file_and_manifest(self):
        manifest = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("hooks"), "./hooks/codex-hooks.json")
        data = self.load("codex-hooks.json")
        for event, group, hook in self.commands(data):
            self.assertEqual(hook["type"], "command")
            self.assertIn("run-hook.cmd", hook["command"])
            self.assertIn("run-hook.cmd", hook["commandWindows"])
            name = hook["command"].rsplit(" ", 1)[1]
            self.assertTrue((SCRIPTS / (name + ".py")).is_file(), name)
            self.assertEqual(hook["commandWindows"].rsplit(" ", 1)[1], name)

    def test_launcher_is_executable_in_git_and_lf_only(self):
        self.assertNotIn(b"\r", LAUNCHER.read_bytes())
        if shutil.which("git") and (REPO_ROOT / ".git").exists():
            done = subprocess.run(["git", "ls-files", "-s", "hooks/run-hook.cmd"], cwd=str(REPO_ROOT),
                                  stdout=subprocess.PIPE, env=clean_env())
            out = done.stdout.decode()
            if out.strip():
                self.assertTrue(out.startswith("100755"), out)

    def test_scripts_are_stdlib_only(self):
        stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else None
        local = {"studio_scope", "studio_shell", "guard_bash", "session_start"}
        import ast
        for path in SCRIPTS.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module.split(".")[0]]
                for name in names:
                    self.assertTrue(name in local or stdlib is None or name in stdlib, "%s imports %s" % (path.name, name))


BS_GIT = r"C:\Program Files\Git\bin\bash.exe"
BS_GIT86 = r"C:\Program Files (x86)\Git\bin\bash.exe"


class Launcher(HookTestCase):
    """The polyglot run-hook.cmd must pass stdin through and fail open."""

    def shells(self, launcher=None):
        """Argv builders, one per way the hook command can reach the launcher."""
        launcher = Path(launcher or LAUNCHER)
        if os.name == "nt":
            # On Windows both cmd.exe and Git Bash (which hands .cmd files to cmd.exe) run the batch half.
            builders = [("cmd", lambda name: ["cmd", "/c", str(launcher), name])]
            for candidate in (BS_GIT, BS_GIT86):
                if os.path.exists(candidate):
                    # like Claude Code: bash -c '"<plugin root>/hooks/run-hook.cmd" name'
                    builders.append(("git-bash -c", lambda name, c=candidate: [c, "-c", '"%s" %s' % (launcher, name)]))
                    # the POSIX half, run explicitly by bash
                    builders.append(("git-bash file (POSIX half)",
                                     lambda name, c=candidate: [c, launcher.as_posix(), name]))
                    break
            return builders
        builders = []
        for label in ("sh", "bash"):
            exe = shutil.which(label)
            if exe:
                builders.append((label + " file", lambda name, e=exe: [e, str(launcher), name]))
                builders.append((label + " -c exec", lambda name, e=exe: [e, "-c", '"%s" %s' % (launcher, name)]))
        return builders

    def run_launcher(self, build, name, data, env=None):
        return subprocess.run(build(name), input=data, env=env or clean_env(), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=60)

    def test_block_decision_and_stdin_pass_through(self):
        repo = make_repo(self.tmp, "studio")
        data = json.dumps(pre_payload("git commit -m x", repo)).encode()
        for label, build in self.shells():
            with self.subTest(shell=label):
                done = self.run_launcher(build, "guard_bash", data)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allowed_command_is_silent(self):
        repo = make_repo(self.tmp, "studio")
        data = json.dumps(pre_payload("git status", repo)).encode()
        for label, build in self.shells():
            with self.subTest(shell=label):
                done = self.run_launcher(build, "guard_bash", data)
                self.assertEqual((done.returncode, done.stdout), (0, b""))

    def test_missing_arguments_and_unknown_script_fail_open(self):
        for label, build in self.shells():
            for name in ("", "does_not_exist", "../scripts/guard_bash"):
                with self.subTest(shell=label, name=name):
                    done = self.run_launcher(build, name, b"{}")
                    self.assertEqual((done.returncode, done.stdout), (0, b""))

    def test_python_exit_codes_other_than_0_and_2_fail_open(self):
        hooks = self.tmp / "hooks"
        (hooks / "scripts").mkdir(parents=True)
        launcher = hooks / "run-hook.cmd"
        shutil.copyfile(str(LAUNCHER), str(launcher))
        launcher.chmod(0o755)
        for name, body in (("ok", "print('hi')"), ("crash", "raise RuntimeError('boom')"),
                           ("exit1", "import sys; sys.exit(1)"), ("exit3", "import sys; sys.exit(3)"),
                           ("exit255", "import sys; sys.exit(255)"), ("block", "import sys; sys.exit(2)"),
                           ("syntax", "def (:")):
            (hooks / "scripts" / (name + ".py")).write_text(body + "\n", encoding="utf-8")
        expected = {"ok": 0, "crash": 0, "exit1": 0, "exit3": 0, "exit255": 0, "block": 2, "syntax": 0}
        for label, build in self.shells(launcher):
            for name, code in expected.items():
                with self.subTest(shell=label, script=name):
                    done = self.run_launcher(build, name, b"{}")
                    self.assertEqual(done.returncode, code, done.stderr)
                    self.assertEqual(done.stdout.strip(), b"hi" if name == "ok" else b"")

    def test_launcher_requires_python_3_8(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertEqual(text.count("sys.version_info>=(3,8)"), 4)  # three cmd probes, one POSIX probe
        self.assertNotIn("version_info[0]==3", text)

    def test_attribution_for_the_adapted_technique(self):
        head = LAUNCHER.read_text(encoding="utf-8").split("CMDBLOCK")[1]
        for needle in ("superpowers", "Jesse Vincent", "MIT"):
            self.assertIn(needle, head)

    @unittest.skipIf(os.name == "nt", "py.exe lives in the Windows directory on PATH")
    def test_no_python_on_path_fails_open_silently(self):
        sh = shutil.which("sh") or "/bin/sh"
        done = subprocess.run([sh, str(LAUNCHER), "guard_bash"], input=b"{}", env={"PATH": str(self.tmp)},
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.assertEqual((done.returncode, done.stdout), (0, b""))


if __name__ == "__main__":
    unittest.main()
