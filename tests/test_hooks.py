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

    def test_commit_and_push_to_main_are_refused(self):
        for cmd in ("git commit -m x", "git add . && git commit -am 'x y'", "git -C {} commit -m x".format(self.root),
                    "git push origin main", "git push", "git push origin HEAD", "git push origin +lm/x:main",
                    "git merge lm/W-1", "FOO=1 git cherry-pick abc", "cd {} && git commit -m x".format(self.root)):
            with self.subTest(cmd):
                reason = self.bash(cmd)
                self.assertIsNotNone(reason, cmd)
                self.assertIn("lockmaster submit", reason)

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
        self.assertIsNotNone(self.bash("git push origin trunk"))
        self.assertIsNone(self.bash("git push origin main"))


if __name__ == "__main__":
    unittest.main()
