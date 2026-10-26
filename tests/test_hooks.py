"""W-05 — the claim hook warns on a write outside the claim; the block-main
hook refuses an agent's commit or push to main (SR-ARCHITECTURE decisions 5, 12).
Each hook is run as Claude Code runs it: a process with the hook JSON on stdin."""
import json
import subprocess
import sys
import unittest

from support import ROOT, ScratchCase, git

from lockmaster import land

HOOKS = ROOT / "kit" / "claude" / "hooks"


def hook(name, payload):
    r = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(payload),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout) if r.stdout.strip() else None


class ClaimGuard(ScratchCase):
    def write(self, path, cwd):
        return hook("claim-guard.py", {"tool_name": "Write", "cwd": str(cwd),
                                       "tool_input": {"file_path": str(path), "content": "x"}})

    def test_a_write_outside_the_claim_prints_the_claim_and_the_path(self):
        change, _ = land.start(self.repo(), "W-1", ["a.txt", "docs/"])
        wt = change["worktree"]
        out = self.write(wt + "/b.txt", wt)
        self.assertIn("`b.txt` is outside the claim of W-1 (a.txt, docs)", out["systemMessage"])
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], out["systemMessage"])
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])  # warned, not refused

    def test_a_write_inside_the_claim_or_outside_any_change_is_silent(self):
        change, _ = land.start(self.repo(), "W-1", ["a.txt", "docs/"])
        wt = change["worktree"]
        self.assertIsNone(self.write(wt + "/a.txt", wt))
        self.assertIsNone(self.write(wt + "/docs/new/page.md", wt))
        self.assertIsNone(self.write(str(self.root / "b.txt"), self.root))  # the main checkout


class BlockMain(ScratchCase):
    def bash(self, command, cwd=None):
        out = hook("block-main.py", {"tool_name": "Bash", "cwd": str(cwd or self.root),
                                     "tool_input": {"command": command}})
        return out["hookSpecificOutput"]["permissionDecisionReason"] if out else None

    def test_commits_on_main_and_unplain_pushes_of_main_are_refused(self):
        for cmd in ("git commit -m x", "git add . && git commit -am 'x y'", "git -C {} commit -m x".format(self.root),
                    "git push -f origin main", "git push --force-with-lease", "git push origin +main",
                    "git push origin +lm/x:main", "git push origin :main", "git push --delete origin main",
                    "git push --no-verify origin main", "git push --all", "git push --mirror",
                    "git merge lm/W-1", "FOO=1 git cherry-pick abc", "cd {} && git commit -m x".format(self.root),
                    "cat <<EOF\nhello\nEOF\ngit commit -m x"):
            with self.subTest(cmd):
                reason = self.bash(cmd)
                self.assertIsNotNone(reason, cmd)
                self.assertIn("lockmaster submit", reason)

    def test_a_plain_push_of_main_passes(self):
        # Ruled 2026-10-26: main holds only landings, so a push that cannot force may send it.
        for cmd in ("git push", "git push origin main", "git push -u origin main", "git push origin HEAD",
                    "git push --follow-tags origin main", "git push origin main v0.0.1"):
            with self.subTest(cmd):
                self.assertIsNone(self.bash(cmd), cmd)

    def test_a_heredoc_body_is_text_not_commands(self):
        for cmd in ("python3 - <<'EOF'\nprint('git commit -m x')\nEOF",
                    "cat > f <<EOF\ngit push -f origin main\nEOF\necho done"):
            with self.subTest(cmd):
                self.assertIsNone(self.bash(cmd), cmd)

    def test_work_on_a_change_branch_and_lockmasters_landing_pass(self):
        change, _ = land.start(self.repo(), "W-1", ["a.txt"])
        wt = change["worktree"]
        for cmd, cwd in (("git commit -m wip", wt), ("git push origin lm/W-1", wt), ("lockmaster submit -m x", wt),
                         ("git status && git log", self.root), ("git merge --abort", self.root),
                         ("git push origin lm/W-1", self.root), ("echo git commit", self.root)):
            with self.subTest(cmd):
                self.assertIsNone(self.bash(cmd, cwd), cmd)

    def test_the_main_branch_comes_from_lockmaster_toml(self):
        git(self.root, "branch", "-m", "main", "trunk")
        (self.root / "lockmaster.toml").write_text('[main]\nbranch = "trunk"\n')
        self.assertIsNotNone(self.bash("git commit -m x"))
        self.assertIsNotNone(self.bash("git push origin +trunk"))
        self.assertIsNone(self.bash("git push origin +main"))  # main is not this repository's main


class WithoutTheWorkSystem(ScratchCase):
    """W-09: a repository that has lockmaster but not the work system (no
    work/NOW.md) gets no NOW ledger and no progress nudge — and no traceback."""

    def test_the_now_hooks_are_silent_and_write_nothing(self):
        code, _, err = self.cli("install", str(self.root))
        self.assertEqual(code, 0, err)
        (self.root / "a.txt").write_text("changed\n")
        hooks = self.root / ".claude" / "hooks"
        for mode in ("start", "show", "sync", "stop", "end"):
            with self.subTest(mode):
                r = subprocess.run([sys.executable, str(hooks / "now-ledger.py"), mode],
                                   input=json.dumps({"session_id": "s1"}), capture_output=True, text=True)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        r = subprocess.run(["bash", str(hooks / "require-progress.sh")], input="{}", capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertFalse((self.root / "work").exists())


if __name__ == "__main__":
    unittest.main()
