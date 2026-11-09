"""W-11 — landing at the end of every turn, and Cowork's edits landed by
whichever surface can commit (SR-ARCHITECTURE decisions 8a, 19 and 20)."""
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from support import NO_X, ROOT, SRC, ScratchCase, git

from lockmaster import land, surface
from lockmaster.repo import LANDED, OPEN, RED, WAITING

HOOK = ROOT / "kit" / "claude" / "hooks" / "auto-land.py"


class AutoLand(ScratchCase):
    def start(self, item, *paths, session="s-1"):
        change, _ = land.start(self.repo(), item, list(paths), session)
        return Path(change["worktree"])

    def main_file(self, name):
        return git(self.root, "show", "main:" + name)

    # -------------------------------------------------------- decision 20

    def test_a_turn_end_lands_the_change_and_keeps_it_open(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("first\n")
        self.assertEqual(land.sync(self.repo(), session="s-1"), ["W-1"])
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], OPEN)
        self.assertEqual(self.main_file("a.txt"), "first")
        self.assertTrue(w.is_dir())
        self.assertEqual(git(w, "rev-parse", "HEAD"), git(self.root, "rev-parse", "main"))  # the worktree follows main
        self.assertEqual((self.root / "a.txt").read_text(), "first\n")  # main's checkout moved
        (w / "a.txt").write_text("second\n")
        self.assertEqual(land.sync(self.repo(), session="s-1"), ["W-1"])
        self.assertEqual(self.main_file("a.txt"), "second")
        self.assertEqual(len(self.repo().load("W-1")["landings"]), 2)
        self.assertEqual(land.sync(self.repo(), session="s-1"), [])  # nothing new: nothing queued

    def test_another_sessions_change_is_not_landed(self):
        w = self.start("W-1", "a.txt", session="s-other")
        (w / "a.txt").write_text("theirs\n")
        self.assertEqual(land.sync(self.repo(), session="s-1"), [])
        self.assertEqual(self.main_file("a.txt"), "a")

    def test_a_change_with_no_session_is_matched_by_the_working_directory(self):
        w = self.start("W-1", "a.txt", session="")
        (w / "a.txt").write_text("here\n")
        self.assertEqual(land.sync(self.repo(), session="s-1", cwd=str(w)), ["W-1"])

    def test_a_failed_check_holds_the_change_and_reports_once(self):
        (self.root / "lockmaster.toml").write_text("[checks]\nno-x = {}\n".format(NO_X))
        self.commit("config")
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x marks it\n")
        land.sync(self.repo(), session="s-1")
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], OPEN)  # held, not red: nothing goes to the decider
        self.assertIn("no-x", c["held"])
        reports = land.held_reports(self.repo(), session="s-1")
        self.assertEqual([i for i, _ in reports], ["W-1"])
        self.assertEqual(land.held_reports(self.repo(), session="s-1"), [])  # told once
        (w / "a.txt").write_text("good\n")
        land.sync(self.repo(), session="s-1")
        self.assertEqual(self.main_file("a.txt"), "good")
        self.assertEqual(self.repo().load("W-1")["held"], "")

    def test_the_session_end_lands_and_cleans_up(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("done\n")
        land.sync(self.repo(), session="s-1", final=True)
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)
        self.assertFalse(w.exists())

    def test_auto_off_lands_nothing(self):
        (self.root / "lockmaster.toml").write_text('[land]\nauto = "off"\n')
        self.commit("config")
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        self.assertEqual(land.sync(self.repo(), session="s-1"), [])

    def test_a_worktree_lockmaster_did_not_create_is_adopted_and_kept(self):
        wt = self.root.parent / "elsewhere"
        git(self.root, "worktree", "add", "-q", "-b", "claude/feature", str(wt))
        (wt / "new.txt").write_text("new\n")
        (wt / "b.txt").write_text("b changed\n")
        queued = land.sync(self.repo(), session="s-1", cwd=str(wt))
        self.assertEqual(queued, ["wt-feature"])
        self.assertEqual(self.main_file("new.txt"), "new")
        self.assertEqual(self.main_file("b.txt"), "b changed")
        self.assertTrue(wt.is_dir())
        (wt / "later.txt").write_text("later\n")  # the claim widens with the worktree
        land.sync(self.repo(), session="s-1", cwd=str(wt), final=True)
        self.assertEqual(self.main_file("later.txt"), "later")
        self.assertTrue(wt.is_dir())  # adopted: never removed by lockmaster

    # -------------------------------------------------------- the review's cases

    def test_standing_in_another_sessions_worktree_does_not_land_it(self):
        w = self.start("W-1", "a.txt", session="s-other")
        (w / "a.txt").write_text("theirs, half done\n")
        self.assertEqual(land.sync(self.repo(), session="s-1", cwd=str(w)), [])
        self.assertEqual(self.main_file("a.txt"), "a")

    def test_the_session_end_finishes_a_change_already_landed_kept(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("landed at a turn end\n")
        land.sync(self.repo(), session="s-1")
        self.assertEqual(land.sync(self.repo(), session="s-1", final=True), [])
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], LANDED)
        self.assertFalse(w.exists())
        self.assertEqual(git(self.root, "branch", "--list", "lm/W-1"), "")

    def test_the_session_end_drops_a_change_that_never_held_anything(self):
        w = self.start("W-1", "a.txt")
        land.sync(self.repo(), session="s-1", final=True)
        self.assertEqual(self.repo().load("W-1")["status"], "abandoned")
        self.assertFalse(w.exists())

    def test_an_orphan_worktree_is_not_adopted_and_does_not_stop_the_sessions_change(self):
        orphan = self.root.parent / "pages"
        git(self.root, "worktree", "add", "-q", "--detach", str(orphan))
        git(orphan, "checkout", "-q", "--orphan", "gh-pages")
        (orphan / "index.html").write_text("x\n")
        self.commit("pages", cwd=orphan)
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        self.assertEqual(land.sync(self.repo(), session="s-1", cwd=str(orphan)), ["W-1"])

    def test_a_dirty_generated_file_is_not_pending(self):
        (self.root / "lockmaster.toml").write_text('[generated]\n"gen.txt" = "echo built > gen.txt"\n')
        self.write_files(self.root, {"gen.txt": "built\n"})
        self.commit("config")
        w = self.start("W-1", "a.txt", "gen.txt")
        (w / "gen.txt").write_text("rebuilt by a daemon\n")
        self.assertEqual(land.sync(self.repo(), session="s-1"), [])
        self.assertEqual(self.repo().load("W-1").get("held", ""), "")

    def test_a_branch_whose_claimed_content_is_on_main_is_not_pending(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("same\n")
        self.commit("W-1 work", cwd=w)
        (self.root / "a.txt").write_text("same\n")  # the same content reached main another way
        self.commit("elsewhere")
        self.assertFalse(land.pending(self.repo(), self.repo().load("W-1")))

    def test_a_red_handoff_is_retried_on_the_same_change_once_the_checkout_is_fixed(self):
        (self.root / "lockmaster.toml").write_text("[checks]\nno-x = {}\n".format(NO_X))
        self.commit("config")
        (self.root / "a.txt").write_text("x\n")
        land.handoff(self.repo(), ["a.txt"], "W-6: a")
        item, outcome, note = land.pickup(self.repo())[0]
        self.assertEqual(outcome, "red")
        self.assertIn("no-x", note)
        change = land.handoffs(self.repo())[0]["change"]
        (self.root / "a.txt").write_text("good\n")  # fixed where it is, in main's checkout
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["landed"])
        self.assertEqual(self.main_file("a.txt"), "good")
        self.assertEqual(self.repo().load(change)["status"], LANDED)  # one change, reused
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    # -------------------------------------------------------- decision 10: drivers registered elsewhere

    def test_a_landing_re_points_drivers_registered_on_another_machine(self):
        from lockmaster import drivers
        (self.root / "lockmaster.toml").write_text('[merge]\n"a.txt" = "append"\n')
        self.commit("config")
        for name in ("append", "append-newest-first", "table-rows"):
            git(self.root, "config", "merge.lockmaster-{}.driver".format(name),
                "/usr/bin/python3 /elsewhere/lockmaster/merge.py {} %O %A %B %P".format(name))
        self.assertEqual(len(drivers.stale(self.repo())), 3)
        land.run(self.repo())
        self.assertEqual(drivers.stale(self.repo()), [])
        self.assertIn(sys.executable, git(self.root, "config", "merge.lockmaster-append.driver"))

    def test_install_on_a_surface_that_cannot_commit_registers_no_driver(self):
        from lockmaster import install
        (self.root / "lockmaster.toml").write_text('[merge]\n"a.txt" = "append"\n')
        self.commit("config")
        real = surface.can_unlink
        surface.can_unlink = lambda repo: False
        try:
            install.install(self.root, out=lambda *_: None)
        finally:
            surface.can_unlink = real
        self.assertEqual(git(self.root, "config", "--get-regexp", "merge.lockmaster", check=False), "")
        self.assertIn("lockmaster-append", (self.root / ".gitattributes").read_text())

    # -------------------------------------------------------- decision 8a

    def test_identical_edits_in_mains_checkout_do_not_stop_the_landing(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("same\n")
        (self.root / "a.txt").write_text("same\n")  # Cowork made the same edit in the checkout
        (self.root / "b.txt").write_text("unrelated edit\n")
        land.submit(self.repo(), self.repo().load("W-1"), "W-1: a")
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)
        self.assertEqual(git(self.root, "status", "--porcelain"), "M b.txt")  # the unrelated edit untouched

    def test_differing_edits_in_mains_checkout_are_named(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("someone else's\n")
        land.submit(self.repo(), self.repo().load("W-1"), "W-1: a")
        land.run(self.repo())
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], WAITING)  # W-10: waiting, not red
        self.assertIn("a.txt", c["reason"])
        self.assertEqual((self.root / "a.txt").read_text(), "someone else's\n")  # never overwritten (L3)
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "")  # nothing staged either

    # -------------------------------------------------------- decision 19

    def test_save_lands_edits_made_in_mains_checkout(self):
        (self.root / "a.txt").write_text("edited in place\n")
        (self.root / "b.txt").write_text("not mine\n")
        code, out, err = self.cli("save", "-m", "W-2: a in place", "a.txt")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.main_file("a.txt"), "edited in place")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", "main"), "W-2: a in place")
        self.assertEqual(git(self.root, "status", "--porcelain"), "M b.txt")

    def test_a_surface_that_cannot_commit_hands_off_and_claude_code_picks_up(self):
        (self.root / "a.txt").write_text("from cowork\n")
        real = surface.can_unlink
        surface.can_unlink = lambda repo: False
        try:
            code, out, _ = self.cli("save", "-m", "W-3: from Cowork", "--by", "Cowork", "a.txt")
            self.assertEqual(code, 0)  # handing off is success, not an error to raise
            self.assertIn("handed off", out)
            self.assertEqual(self.main_file("a.txt"), "a")
            code, out, _ = self.cli("can-commit")
            self.assertEqual(code, 1)
            self.assertEqual(land.pickup(self.repo()), [(land.handoffs(self.repo())[0]["item"], "skipped", "")])
        finally:
            surface.can_unlink = real
        self.assertIn("handoff", "\n".join(land.queue_lines(self.repo())))
        results = land.pickup(self.repo())
        self.assertEqual([r for _, r, _ in results], ["landed"])
        self.assertEqual(self.main_file("a.txt"), "from cowork")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", "main"), "W-3: from Cowork")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertEqual(land.handoffs(self.repo()), [])

    def test_a_handoff_already_on_main_is_dropped(self):
        (self.root / "a.txt").write_text("x\n")
        land.handoff(self.repo(), ["a.txt"], "W-4: x")
        (self.root / "a.txt").write_text("a\n")  # reverted, or landed by someone else
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["gone"])
        self.assertEqual(land.handoffs(self.repo()), [])

    def test_a_handoff_that_goes_red_waits_for_new_edits(self):
        (self.root / "lockmaster.toml").write_text("[checks]\nno-x = {}\n".format(NO_X))
        self.commit("config")
        (self.root / "a.txt").write_text("x\n")
        land.handoff(self.repo(), ["a.txt"], "W-5: x")
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["red"])
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["skipped"])  # same edits: not retried
        self.assertTrue(land.handoffs(self.repo())[0]["reason"])

    def test_a_checkout_seen_from_another_machine_cannot_commit(self):
        other = self.root.parent / "mac" / "repo"
        other.parent.mkdir()
        wt = other / ".claude" / "worktrees" / "W-9"
        git(self.root, "worktree", "add", "-q", "-b", "lm/W-9", str(wt))
        os.rename(str(self.root.parent / "mac"), str(self.root.parent / "moved"))
        repo = self.repo()
        repo.state.mkdir(parents=True, exist_ok=True)
        (repo.state / "home").write_text(str(other) + "\n")
        ok, why = surface.can_commit(repo)
        self.assertFalse(ok)
        self.assertIn("another machine", why)

    def test_without_a_recorded_home_the_missing_worktrees_are_the_evidence(self):
        other = self.root.parent / "mac" / "repo"
        git(self.root, "worktree", "add", "-q", "-b", "lm/W-9", str(other / ".claude" / "worktrees" / "W-9"))
        os.rename(str(self.root.parent / "mac"), str(self.root.parent / "moved"))
        self.assertFalse(surface.can_commit(self.repo())[0])

    def test_a_deleted_worktree_of_this_checkout_is_not_evidence(self):
        wt = self.root.parent / "side"
        git(self.root, "worktree", "add", "-q", "-b", "side", str(wt))
        import shutil
        shutil.rmtree(str(wt))
        self.assertEqual(surface.can_commit(self.repo()), (True, ""))

    def test_the_first_surface_that_commits_records_home(self):
        repo = self.repo()
        self.assertEqual(surface.can_commit(repo), (True, ""))
        self.assertEqual((repo.state / "home").read_text().strip(), os.path.realpath(str(self.root)))
        self.assertFalse((repo.state / "probe").exists())


class Hook(ScratchCase):
    def hook(self, mode, payload):
        env = dict(os.environ, LOCKMASTER_SRC=str(SRC), LOCKMASTER_FOREGROUND="1")
        env.pop("CLAUDE_ENV_FILE", None)
        r = subprocess.run([sys.executable, str(HOOK), mode], input=json.dumps(payload), capture_output=True,
                           text=True, env=env, cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else {}

    def test_stop_lands_the_sessions_change(self):
        change, _ = land.start(self.repo(), "W-1", ["a.txt"], "s-1")
        Path(change["worktree"], "a.txt").write_text("by the hook\n")
        out = self.hook("stop", {"session_id": "s-1", "cwd": str(self.root)})
        self.assertIn("landed W-1", out.get("systemMessage", ""))
        self.assertNotIn("decision", out)
        self.assertEqual(git(self.root, "show", "main:a.txt"), "by the hook")

    def test_edits_in_mains_checkout_get_one_reminder(self):
        f = self.root / "b.txt"
        f.write_text("edited\n")
        self.hook("edit", {"session_id": "s-1", "cwd": str(self.root), "tool_input": {"file_path": str(f)}})
        out = self.hook("stop", {"session_id": "s-1", "cwd": str(self.root)})
        self.assertEqual(out.get("decision"), "block")
        self.assertIn("save -m", out["reason"])
        self.assertIn("b.txt", out["reason"])
        self.assertEqual(self.hook("stop", {"session_id": "s-1", "cwd": str(self.root)}), {})

    def test_a_stop_while_already_continuing_never_blocks_again(self):
        f = self.root / "b.txt"
        f.write_text("edited\n")
        self.hook("edit", {"session_id": "s-1", "cwd": str(self.root), "tool_input": {"file_path": str(f)}})
        out = self.hook("stop", {"session_id": "s-1", "cwd": str(self.root), "stop_hook_active": True})
        self.assertNotIn("decision", out)
        self.assertIn("save -m", out["systemMessage"])

    def test_without_foreground_the_landing_runs_after_the_hook_returns(self):
        import time
        change, _ = land.start(self.repo(), "W-1", ["a.txt"], "s-1")
        Path(change["worktree"], "a.txt").write_text("in the background\n")
        env = dict(os.environ, LOCKMASTER_SRC=str(SRC))
        env.pop("LOCKMASTER_FOREGROUND", None)
        r = subprocess.run([sys.executable, str(HOOK), "stop"], input=json.dumps({"session_id": "s-1",
                           "cwd": str(self.root)}), capture_output=True, text=True, env=env, cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        for _ in range(100):
            if git(self.root, "show", "main:a.txt") == "in the background":
                break
            time.sleep(0.2)
        self.assertEqual(git(self.root, "show", "main:a.txt"), "in the background")
        for _ in range(50):  # let the detached lander finish before the scratch repo goes
            if self.repo().load("W-1")["status"] == "open" and not (self.repo().state / "land.lock").exists():
                break
            time.sleep(0.2)
        out = self.hook("stop", {"session_id": "s-1", "cwd": str(self.root)})
        self.assertIn("landed W-1", out.get("systemMessage", ""))  # said at the next Stop

    def test_start_exports_the_session_id(self):
        env_file = self.root.parent / "env"
        env = dict(os.environ, LOCKMASTER_SRC=str(SRC), CLAUDE_ENV_FILE=str(env_file))
        subprocess.run([sys.executable, str(HOOK), "start"], input=json.dumps({"session_id": "s-9", "cwd": str(self.root)}),
                       capture_output=True, text=True, env=env, cwd=str(self.root), check=True)
        self.assertIn("export CLAUDE_SESSION_ID=s-9", env_file.read_text())
        log = self.repo().state / "auto-land.log"  # the detached pickup: let it finish before the
        for _ in range(100):                       # repository is deleted (Windows keeps the log locked)
            if log.exists() and log.read_text(errors="replace").strip():
                break
            time.sleep(0.1)
        time.sleep(0.5)


if __name__ == "__main__":
    unittest.main()
