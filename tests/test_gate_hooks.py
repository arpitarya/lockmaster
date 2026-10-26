"""W-09 — lockmaster's own git steps run the repository's gate hooks and not its
post-* hooks (SR-ARCHITECTURE decision 18). fux's post-commit, post-merge and
post-checkout re-index its docs; run inside a landing they would write into a
worktree lockmaster is about to remove, and into main's checkout."""
import os
import stat
import sys
import unittest
from pathlib import Path

from support import ScratchCase, git

from lockmaster import land
from lockmaster.repo import LANDED, RED


class GateHooksOnly(ScratchCase):
    def hook(self, name, body):
        f = self.root / ".git" / "hooks" / name
        f.write_text("#!/bin/sh\n" + body + "\n")
        f.chmod(f.stat().st_mode | stat.S_IXUSR)

    def land(self, item, path, text, message):
        change, _ = land.start(self.repo(), item, [path])
        (Path(change["worktree"]) / path).write_text(text)
        repo = self.repo()
        land.submit(repo, repo.load(item), message)
        land.run(repo)
        return self.repo().load(item)

    @unittest.skipIf(sys.platform == "win32", "sh hooks")
    def test_post_hooks_stay_quiet_and_commit_msg_still_guards(self):
        marks = self.root.parent / "marks"
        for name in ("post-commit", "post-merge", "post-checkout"):
            self.hook(name, 'echo {} >> "{}"'.format(name, marks))
        self.hook("commit-msg", 'grep -q REJECT "$1" && exit 1; exit 0')
        self.assertEqual(self.land("W-1", "a.txt", "a\nW-1\n", "W-1: fine")["status"], LANDED)
        self.assertFalse(marks.exists(), marks.read_text() if marks.exists() else "")
        self.assertEqual(self.land("W-2", "b.txt", "b\nW-2\n", "W-2: REJECT me")["status"], RED)
        git(self.root, "commit", "--allow-empty", "-q", "-m", "a person's own commit")
        self.assertIn("post-commit", marks.read_text())  # outside lockmaster, the repo's hooks are untouched


if __name__ == "__main__":
    unittest.main()
