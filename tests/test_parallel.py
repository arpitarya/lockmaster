"""SR-LAW-8 — parallel requests — with real concurrent processes, and
SR-LAW-9 decision 3 — what lands from a handoff is what was handed over (W-13, W-14)."""
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path

from support import SRC, ScratchCase, git

from lockmaster import land
from lockmaster.repo import LANDED, LandLock

N = 6

WORKER = textwrap.dedent("""
    import sys, time
    sys.path.insert(0, {src!r})
    from pathlib import Path
    from lockmaster import land
    from lockmaster.repo import Repo
    root, kind, name, go = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    while time.time() < go:  # every worker starts at the same instant
        time.sleep(0.001)
    r = Repo(root)
    if kind == "submit":
        c, _ = land.start(r, name, [name + ".txt"])
        Path(c["worktree"], name + ".txt").write_text(name + "\\n")
        land.submit(r, c, name + ": add")
        land.run(r)
    elif kind == "save":
        land.save(r, [name + ".txt"], name + ": saved")
    elif kind == "handoff":
        land.handoff(r, [name + ".txt"], name + ": handed off", item="same", by="Cowork")
""")


class Parallel(ScratchCase):
    def at_once(self, kind, names):
        go = str(time.time() + 1.5)
        procs = [subprocess.Popen([sys.executable, "-c", WORKER.format(src=str(SRC)), str(self.root), kind, n, go],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for n in names]
        for p in procs:
            o, e = p.communicate(timeout=180)
            self.assertEqual(p.returncode, 0, "a caller was refused or failed:\n" + o + e)

    def assert_clean_state(self):
        state = self.repo().state
        torn = [f.name for f in state.rglob("*") if ".tmp" in f.name or f.name.endswith(".part")]
        self.assertEqual(torn, [], "half-written state left behind")
        self.assertFalse((state / "land.lock").exists(), "the land lock was left held")
        landing = state / "landing"
        self.assertEqual(list(landing.iterdir()) if landing.is_dir() else [], [], "a landing worktree was left")

    def landed_on_main(self, names):
        for n in names:
            self.assertEqual(git(self.root, "show", "main:{}.txt".format(n)), n)

    # -------------------------------------------------------- SR-LAW-8

    def test_sessions_starting_and_submitting_at_once_all_land(self):
        names = ["W-{}".format(i) for i in range(N)]
        self.at_once("submit", names)
        repo = self.repo()
        self.assertEqual([repo.load(n)["status"] for n in names], [LANDED] * N)  # none lost, none red
        self.landed_on_main(names)
        self.assertEqual(len(git(self.root, "log", "--first-parent", "--format=%H", "main").split()), N + 1)
        self.assert_clean_state()

    def test_saves_from_mains_checkout_in_the_same_second_all_land(self):
        names = ["s{}".format(i) for i in range(N)]
        for n in names:
            (self.root / (n + ".txt")).write_text(n + "\n")
        self.at_once("save", names)
        self.landed_on_main(names)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assert_clean_state()

    def test_handoffs_written_at_once_never_overwrite_each_other(self):
        names = ["h{}".format(i) for i in range(N)]
        for n in names:
            (self.root / (n + ".txt")).write_text(n + "\n")
        self.at_once("handoff", names)  # every one asks for the same name
        self.assertEqual(len(land.handoffs(self.repo())), N)
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["landed"] * N)
        self.landed_on_main(names)
        self.assert_clean_state()

    def test_an_end_of_turn_landing_skips_while_the_same_session_is_landing(self):
        c, _ = land.start(self.repo(), "W-1", ["a.txt"], "s-1")
        (Path(c["worktree"]) / "a.txt").write_text("turn\n")
        lock = LandLock(self.repo(), "sync.s-1.lock")
        self.assertTrue(lock.acquire())
        try:
            self.assertEqual(land.sync(self.repo(), session="s-1"), [])
        finally:
            lock.release()
        self.assertEqual(land.sync(self.repo(), session="s-1"), ["W-1"])

    # -------------------------------------------------------- SR-LAW-9 decision 3

    def test_a_file_edited_after_its_handoff_is_held_not_swept_in(self):
        (self.root / "a.txt").write_text("handed over\n")
        land.handoff(self.repo(), ["a.txt"], "W-7: a", by="Cowork")
        (self.root / "a.txt").write_text("another session's edit\n")  # not handed off
        item, outcome, note = land.pickup(self.repo())[0]
        self.assertEqual(outcome, "held")
        self.assertIn("a.txt", note)
        self.assertEqual(git(self.root, "show", "main:a.txt"), "a")  # nothing landed under W-7's message
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["skipped"])  # said once
        self.assertIn("handed off", "\n".join(land.queue_lines(self.repo())))

    def test_handoffs_naming_one_file_land_together_under_both_messages(self):
        (self.root / "a.txt").write_text("first\n")
        land.handoff(self.repo(), ["a.txt"], "W-7: first", by="Cowork")
        (self.root / "a.txt").write_text("second\n")
        (self.root / "b.txt").write_text("also\n")
        land.handoff(self.repo(), ["a.txt", "b.txt"], "W-8: second\n\nCo-Authored-By: X <x@example.com>", by="Cowork")
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["landed", "landed"])
        self.assertEqual(git(self.root, "show", "main:a.txt"), "second")
        self.assertEqual(git(self.root, "show", "main:b.txt"), "also")
        msg = git(self.root, "log", "-1", "--format=%B", "main")
        self.assertTrue(msg.startswith("W-8: second"))
        self.assertIn("W-7: first", msg)
        self.assertIn("Co-Authored-By: X", git(self.root, "log", "-1", "--format=%(trailers)", "main"))
        self.assertEqual(len(git(self.root, "log", "--first-parent", "--format=%H", "main").split()), 2)  # one landing
        self.assertEqual(land.handoffs(self.repo()), [])

    def test_a_held_handoff_lands_once_the_edit_is_handed_off_too(self):
        (self.root / "a.txt").write_text("one\n")
        land.handoff(self.repo(), ["a.txt"], "W-7: one", by="Cowork")
        (self.root / "a.txt").write_text("two\n")
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["held"])
        land.handoff(self.repo(), ["a.txt"], "W-9: two", by="Claude Code")
        self.assertEqual([r for _, r, _ in land.pickup(self.repo())], ["landed", "landed"])
        self.assertEqual(git(self.root, "show", "main:a.txt"), "two")

    def test_a_handoff_the_last_pickup_did_not_land_is_flagged(self):
        (self.root / "a.txt").write_text("x\n")
        land.handoff(self.repo(), ["a.txt"], "W-7: x")
        (self.repo().state / "pickup.last").write_text("{}\n".format(time.time() + 60))
        self.assertIn("MISSED", "\n".join(land.queue_lines(self.repo())))


if __name__ == "__main__":
    unittest.main()
