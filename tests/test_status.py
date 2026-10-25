"""W-07 — `lockmaster status`, and work/NOW.md as its generated view
(SR-ARCHITECTURE decision 14, SR-WORK-NOW decisions 2-5)."""
import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from support import ROOT, ScratchCase, git

from lockmaster import land, now

NOW_MD = """---
type: Pointer
description: "live"
---

# NOW

## In flight

| session | surface | started | working on |
|---|---|---|---|
| s-one | Claude Code | 2026-10-25 10:00 | W-1 |
| s-two | Cowork | 2026-10-25 10:05 | W-2 |

## Resources this session created

| kind | where | host | session | created |
|---|---|---|---|---|
"""


class Status(ScratchCase):
    files = {"a.txt": "a\n", "b.txt": "b\n", "work/NOW.md": NOW_MD,
             "work/MACHINE.md": "| budget | 5 GB for the whole project |\n"}

    def two_sessions(self):
        w1, _ = land.start(self.repo(), "W-1", ["a.txt"], "s-one")
        w2, _ = land.start(self.repo(), "W-2", ["b.txt"], "s-two")
        # what now-ledger.py's `sync` writes for each session's new worktree
        text = (self.root / "work/NOW.md").read_text()
        rows = "".join("| worktree | `{}` | host | {} | 2026-10-25 |\n".format(c["worktree"], c["session"])
                       for c in (w1, w2))
        (self.root / "work/NOW.md").write_text(text + rows)
        return w1, w2

    def test_status_shows_every_live_change_and_worktree(self):
        w1, w2 = self.two_sessions()
        code, out, err = self.cli("status")
        self.assertEqual(code, 0, err)
        for c in (w1, w2):
            self.assertIn("{} open {}".format(c["item"], c["branch"]), out)
            self.assertIn("{} [{}] change {}".format(c["worktree"], c["branch"], c["item"]), out)
        self.assertIn("s-one · Claude Code", out)
        self.assertIn("s-two · Cowork", out)
        self.assertIn("of the 5 GB budget", out)

    def test_now_md_equals_status_now_after_a_landing(self):
        w1, _ = self.two_sessions()
        (Path(w1["worktree"]) / "a.txt").write_text("x\n")
        repo = self.repo()
        land.submit(repo, repo.load("W-1"))
        land.run(repo)
        text = (self.root / "work/NOW.md").read_text()
        self.assertEqual(text, self.cli("status", "--now")[1])
        self.assertNotIn(w1["worktree"], text)  # the landed change's worktree row left with it
        self.assertIn("W-2", text)
        self.assertIn("s-one", text)  # sessions are the sessions' own: still in flight

    def test_now_md_equals_status_now_after_a_session_end(self):
        w1, w2 = self.two_sessions()
        spec = importlib.util.spec_from_file_location("now_ledger", ROOT / "kit/claude/hooks/now-ledger.py")
        ledger = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ledger)
        ledger.ROOT = self.root
        ledger.NOW_MD = self.root / "work/NOW.md"
        ledger.TMP = self.root / "work/.NOW.md.tmp"
        ledger.LOCK = self.root / ".claude/.now.lock"
        ledger.SESSIONS = self.root / ".claude/.sessions"
        ledger.OPEN_WORK = self.root / "work/OPEN-WORK.md"
        (self.root / ".claude").mkdir(exist_ok=True)
        ledger.close_session = lambda sid, res: [r for r in res if r[3] != sid]  # cleanup is SR-WORK-CLEANUP's test
        ledger.end("s-two", {})
        text = (self.root / "work/NOW.md").read_text()
        self.assertEqual(text, self.cli("status", "--now")[1])
        self.assertNotIn("s-two", text)

    def test_the_renderer_is_stable(self):
        once = now.render(NOW_MD, self.root)
        self.assertEqual(now.render(once, self.root), once)


if __name__ == "__main__":
    unittest.main()
