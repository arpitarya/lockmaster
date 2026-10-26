"""W-09 — the kit's work-system hooks keep what fux's own copies were tested
for, now that fux, sheetpane, codelaw and milo all run the kit: the disk budget
(SR-WORK disk-budget law), the NOW ledger (SR-WORK-NOW), worktree cleanup and
lock release (SR-WORK-CLEANUP). Ported from fux's tests/test_agent_hooks.py,
which tested fux's hand-copied hooks; each runs here against the installed kit."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from contextlib import redirect_stdout

from support import ScratchCase, git

NOW_MD = """---
type: Pointer
---

# NOW

## In flight

| session | surface | started | working on |
|---|---|---|---|

## Resources this session created

| kind | where | host | session | created |
|---|---|---|---|---|
"""


class Installed(ScratchCase):
    def setUp(self):
        super().setUp()
        code, _, err = self.cli("install", str(self.root))
        self.assertEqual(code, 0, err)
        self.hooks = self.root / ".claude" / "hooks"

    def run_hook(self, name, *argv, payload=None):
        cmd = ([sys.executable] if name.endswith(".py") else ["bash"]) + [str(self.hooks / name)] + list(argv)
        r = subprocess.run(cmd, input=json.dumps(payload or {}), capture_output=True, text=True,
                           cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout


class DiskBudget(Installed):
    def setUp(self):
        super().setUp()
        (self.root / "work").mkdir()
        (self.root / "work" / "MACHINE.md").write_text(
            "## Disk budget\n\n| what | value |\n|---|---|\n| budget | 5 GB for the whole project |\n")
        spec = importlib.util.spec_from_file_location("kit_disk_budget", self.hooks / "disk-budget.py")
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.gb = 0.0
        self.mod.measure = lambda: int(self.gb * 1024 * 1024)

    def ask(self, tool, command="", tid="t1"):
        st = self.mod.load()
        out = io.StringIO()
        with redirect_stdout(out):
            self.mod.pre({"tool_name": tool, "tool_use_id": tid, "tool_input": {"command": command}}, st)
        self.mod.save(st)
        text = out.getvalue().strip()
        return json.loads(text)["hookSpecificOutput"]["permissionDecision"] if text else None

    def ran(self, tool, command="", tid="t1"):
        st = self.mod.load()
        with redirect_stdout(io.StringIO()):
            self.mod.post({"tool_name": tool, "tool_use_id": tid, "tool_input": {"command": command}}, st)
        self.mod.save(st)
        return st

    def test_the_number_is_read_from_machine_md(self):
        self.assertEqual(self.mod.budget_gb(), 5.0)

    def test_under_the_budget_nothing_is_asked(self):
        self.gb = 4.0
        self.assertIsNone(self.ask("Bash", "npm install"))

    def test_past_the_budget_one_yes_approves_one_gb(self):
        self.gb = 5.2
        self.assertEqual(self.ask("Bash", "npm install", "t1"), "ask")
        self.assertEqual(self.ran("Bash", "npm install", "t1")["approved_gb"], 6)
        self.assertIsNone(self.ask("Bash", "npm install", "t2"))  # 5.2 < 6
        self.assertEqual(self.ran("Bash", "ls", "t9")["approved_gb"], 6)  # an unrelated run approves nothing

    def test_a_new_agent_asks_from_ninety_percent(self):
        self.gb = 4.6
        self.assertIsNone(self.ask("Bash", "npm install"))
        self.assertEqual(self.ask("Agent", tid="t2"), "ask")

    def test_reads_never_ask(self):
        self.gb = 50.0
        self.assertIsNone(self.ask("Read"))
        self.assertIsNone(self.ask("Bash", "ls -la"))

    def test_approvals_reset_back_under_the_budget(self):
        st = self.mod.load()
        st["approved_gb"] = 8
        self.mod.save(st)
        self.gb = 1.0
        st = self.mod.load()
        self.mod.usage(st, fresh=True)
        self.assertEqual(st["approved_gb"], 0)


class NowLedger(Installed):
    def setUp(self):
        super().setUp()
        (self.root / "work").mkdir()
        (self.root / "work" / "NOW.md").write_text(NOW_MD)

    def flight(self):
        text = (self.root / "work" / "NOW.md").read_text()
        body = text.split("## In flight", 1)[1].split("##", 1)[0]
        return [l.split("|")[1].strip().strip("`") for l in body.splitlines()
                if l.startswith("|") and not l.startswith(("| session", "|---"))]

    def ledger(self, mode, sid):
        return self.run_hook("now-ledger.py", mode, payload={"session_id": sid})

    def test_a_session_has_one_row_and_loses_it_at_the_end(self):
        self.ledger("start", "s-one")
        self.ledger("start", "s-one")
        self.assertEqual(self.flight(), ["s-one"])
        self.ledger("end", "s-one")
        self.assertEqual(self.flight(), [])

    def test_another_sessions_row_is_never_touched(self):
        self.ledger("start", "s-a")
        self.ledger("start", "s-b")
        self.ledger("end", "s-a")
        self.assertEqual(self.flight(), ["s-b"])

    def test_a_dead_session_is_closed_at_the_next_start(self):
        now = self.root / "work" / "NOW.md"
        now.write_text(NOW_MD.replace("|---|---|---|---|\n", "|---|---|---|---|\n| deadbeef | Cowork | 2000-01-01 00:00 | gone |\n", 1))
        self.ledger("start", "s-new")
        self.assertEqual(self.flight(), ["s-new"])

    def test_stop_asks_once_for_an_empty_working_on_cell(self):
        self.ledger("start", "s-one")
        self.assertEqual(json.loads(self.ledger("stop", "s-one"))["decision"], "block")
        self.assertEqual(self.ledger("stop", "s-one").strip(), "")


class FiledItems(Installed):
    """W-09 / rule 37b: what a session leaves is filed under `### build (N)`, the
    count bumped, in the queue's own row style."""

    QUEUE = "# OPEN-WORK\n\n## Blocked on the decider\n\n| what | filed |\n|---|---|\n\n*Empty since 2026-10-01*\n\n---\n\n## Open items\n\n### {build} (1)\n\n{row}\n\n### testing (0)\n\n---\n"

    def leave_a_file(self, queue):
        (self.root / "work" / "open").mkdir(parents=True)
        (self.root / "work" / "OPEN-WORK.md").write_text(queue)
        (self.root / "left.txt").write_text("x\n")
        (self.root / "work" / "NOW.md").write_text(NOW_MD.replace(
            "|---|---|---|---|---|\n", "|---|---|---|---|---|\n| files | `left.txt` | here | s1 | 2026-10-26 |\n"))
        self.run_hook("now-ledger.py", "end", payload={"session_id": "s1"})
        return (self.root / "work" / "OPEN-WORK.md").read_text()

    def test_a_plain_queue_gets_a_plain_row_and_the_count_moves(self):
        text = self.leave_a_file(self.QUEUE.format(build="build", row="🟢 **W-01** `agent` x. Filed by A (B). [detail](open/W-01-x.md)"))
        self.assertIn("### build (2)", text)
        self.assertIn("🟢 **W-02** `agent` Clean up what session s1 left.", text)
        item = (self.root / "work" / "open" / "W-02-session-cleanup.md").read_text()
        self.assertIn('filed_by: "now-ledger.py (Claude Code)"', item)
        self.assertIn("## At a glance", item)

    def test_a_bulleted_queue_gets_a_bullet_row(self):
        text = self.leave_a_file(self.QUEUE.format(build="fux build", row="- 🟢 **W-07** · `agent` — x. Filed by A (B). [detail](open/W-07-x.md)"))
        self.assertIn("### fux build (2)", text)
        self.assertIn("- 🟢 **W-08** · `agent` — Clean up what session s1 left.", text)


class Cleanup(Installed):
    def worktree(self, name):
        path = self.root.parent / name
        git(self.root, "worktree", "add", "-q", "-b", name, str(path))
        return path

    def sweep(self):
        return self.run_hook("worktree-cleanup.py", "--apply")

    def test_a_merged_clean_worktree_is_removed_with_its_branch(self):
        (self.root / ".gitignore").write_text("node_modules/\nnotes.local\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "ignore")
        path = self.worktree("done")
        (path / "node_modules").mkdir()
        (path / "node_modules" / "x.js").write_text("x")  # build output
        out = self.sweep()
        self.assertIn("ok", out)
        self.assertFalse(path.exists())
        self.assertEqual(git(self.root, "branch", "--list", "done"), "")

    def test_an_unmerged_commit_is_red_and_untouched(self):
        path = self.worktree("wip")
        (path / "c.txt").write_text("c\n")
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "wip")
        out = self.sweep()
        self.assertIn("RED", out)
        self.assertIn("not in main", out)
        self.assertTrue(path.exists())

    def test_an_unsaved_or_ignored_non_build_file_is_red(self):
        (self.root / ".gitignore").write_text("notes.local\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "ignore")
        for name in ("untracked.md", "notes.local"):
            with self.subTest(name):
                path = self.worktree("dirty-" + name.replace(".", "-"))
                (path / name).write_text("keep me\n")
                self.assertIn("RED  " + str(path), self.sweep())
                self.assertTrue((path / name).exists())

    def test_cleanup_never_forces(self):
        src = (self.hooks / "worktree-cleanup.py").read_text()
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("#", '"')))
        self.assertNotIn('"--force"', code)
        self.assertNotIn('"-D"', code)


@unittest.skipIf(sys.platform == "win32" or not shutil.which("jq"), "bash + jq hook")
class ReleaseLocks(Installed):
    def test_frees_its_own_and_a_stale_lock_and_keeps_a_fresh_foreign_one(self):
        locks = self.root / ".claude" / ".locks"
        now = int(time.time())
        for key, owner, when in (("mine", "me", now), ("theirs", "them", now), ("stale", "them", now - 3600)):
            (locks / key).mkdir(parents=True)
            (locks / key / "owner").write_text("{} {} x.md\n".format(owner, when))
        self.run_hook("release-locks.sh", payload={"session_id": "me"})
        self.assertEqual(sorted(p.name for p in locks.iterdir()), ["theirs"])


if __name__ == "__main__":
    unittest.main()
