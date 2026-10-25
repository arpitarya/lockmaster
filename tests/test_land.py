"""W-04 — the core loop on a scratch repo (SR-ARCHITECTURE decisions 4-8, 11).

DoD 1 happy path · DoD 2 claims · DoD 3 red · DoD 4 cleanup, plus the two
hazards: two landers at once, and a lander that dies mid-landing.
"""
import os
import sys
import unittest
from pathlib import Path

from support import ScratchCase, git

from lockmaster import land
from lockmaster.repo import LANDED, LANDING, QUEUED, RED, LandLock

PY = sys.executable


class Loop(ScratchCase):
    def start(self, item, *paths):
        change, _ = land.start(self.repo(), item, list(paths))
        return Path(change["worktree"])

    def submit(self, item, message="", run=True):
        repo = self.repo()
        land.submit(repo, repo.load(item), message)
        if run:
            land.run(repo)
        return self.repo().load(item)

    def first_parents(self):
        return git(self.root, "rev-list", "--first-parent", "main").split()

    # -------------------------------------------------------- DoD 1

    def test_two_changes_from_two_worktrees_land_one_after_the_other(self):
        w1, w2 = self.start("W-1", "a.txt"), self.start("W-2", "b.txt")
        (w1 / "a.txt").write_text("a\nfrom W-1\n")
        (w2 / "b.txt").write_text("b\nfrom W-2\n")
        before = git(self.root, "rev-parse", "main")
        self.assertEqual(self.submit("W-1", "W-1: a")["status"], LANDED)
        self.assertEqual(self.submit("W-2", "W-2: b")["status"], LANDED)
        chain = self.first_parents()
        self.assertEqual(chain[2], before)  # two new commits on main, each fast-forwarded onto the last
        for sha, item in zip(chain[:2], ("W-2", "W-1")):
            self.assertEqual(git(self.root, "log", "-1", "--format=%(trailers:key=Lockmaster-Change,valueonly)", sha),
                             item)
        self.assertEqual((self.root / "a.txt").read_text(), "a\nfrom W-1\n")  # main's checkout moved too
        self.assertEqual((self.root / "b.txt").read_text(), "b\nfrom W-2\n")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_submit_from_the_worktree_lands_through_the_cli(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("changed\n")
        code, out, err = self.cli("submit", "-m", "W-1: a", cwd=w)
        self.assertEqual(code, 0, out + err)
        self.assertIn("landed W-1", out)
        code, out, _ = self.cli("queue")
        self.assertIn("W-1        landed", out)

    # -------------------------------------------------------- DoD 2

    def test_a_file_outside_the_claim_is_left_behind_and_reported(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("claimed\n")
        (w / "b.txt").write_text("not claimed, committed by the agent\n")
        self.commit("agent commits both", cwd=w)
        (w / "stray.txt").write_text("not claimed, never committed\n")
        change = self.submit("W-1")
        self.assertEqual(change["status"], LANDED)
        self.assertEqual(sorted(change["left_behind"]), ["b.txt", "stray.txt"])
        self.assertEqual(git(self.root, "show", "main:b.txt"), "b")
        self.assertNotIn("stray.txt", git(self.root, "ls-tree", "-r", "--name-only", "main"))
        # Nothing lost: the worktree and branch stay, holding what did not land.
        self.assertTrue((w / "stray.txt").exists())
        self.assertIn("lm/W-1", git(self.root, "branch", "--list", "lm/W-1"))
        self.assertTrue(change["cleanup"])

    def test_a_directory_claim_covers_what_is_under_it(self):
        self.write_files(self.root, {"docs/x.md": "x\n"})
        self.commit("docs")
        w = self.start("W-1", "docs/")
        (w / "docs" / "y.md").write_text("y\n")
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(git(self.root, "show", "main:docs/y.md"), "y")

    def test_claim_add_widens_the_claim(self):
        w = self.start("W-1", "a.txt")
        (w / "b.txt").write_text("now claimed\n")
        code, out, err = self.cli("claim", "add", "b.txt", cwd=w)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(git(self.root, "show", "main:b.txt"), "now claimed")

    # -------------------------------------------------------- DoD 3

    def test_a_conflicting_change_goes_red_and_nothing_is_lost(self):
        w1, w2 = self.start("W-1", "a.txt"), self.start("W-2", "a.txt")
        (w1 / "a.txt").write_text("one\n")
        (w2 / "a.txt").write_text("two\n")
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        main_before = git(self.root, "rev-parse", "main")
        change = self.submit("W-2")
        self.assertEqual(change["status"], RED)
        self.assertIn("conflicts with main in: a.txt", change["reason"])
        self.assertEqual(git(self.root, "rev-parse", "main"), main_before)
        self.assertEqual((w2 / "a.txt").read_text(), "two\n")
        self.assertEqual(git(self.root, "show", "lm/W-2:a.txt"), "two")
        self.assertEqual(git(self.root, "worktree", "list", "--porcelain").count("landing"), 0)

    def test_a_red_change_is_set_aside_and_the_next_lands(self):
        w1, w2, w3 = self.start("W-1", "a.txt"), self.start("W-2", "a.txt"), self.start("W-3", "b.txt")
        (w1 / "a.txt").write_text("one\n")
        (w2 / "a.txt").write_text("two\n")
        (w3 / "b.txt").write_text("three\n")
        self.submit("W-1")
        self.submit("W-2", run=False)
        self.submit("W-3", run=False)
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-2")["status"], RED)
        self.assertEqual(self.repo().load("W-3")["status"], LANDED)

    def test_a_red_change_fixed_and_resubmitted_lands(self):
        w1, w2 = self.start("W-1", "a.txt"), self.start("W-2", "a.txt")
        (w1 / "a.txt").write_text("one\n")
        (w2 / "a.txt").write_text("two\n")
        self.submit("W-1")
        self.assertEqual(self.submit("W-2")["status"], RED)
        git(w2, "merge", "-q", "main", check=False)  # the agent resolves: takes both
        (w2 / "a.txt").write_text("one\ntwo\n")
        self.commit("resolved", cwd=w2)
        self.assertEqual(self.submit("W-2")["status"], LANDED)
        self.assertEqual(git(self.root, "show", "main:a.txt"), "one\ntwo")

    def test_a_failed_check_is_red(self):
        self.write_files(self.root, {"lockmaster.toml": '[checks]\nfails = "exit 7"\n'})
        self.commit("config")
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        change = self.submit("W-1")
        self.assertEqual(change["status"], RED)
        self.assertIn("check `fails`", change["reason"])

    def test_checks_and_generated_files_run_in_the_landing(self):
        self.write_files(self.root, {
            "gen.py": "open('ALL.txt','w').write(open('a.txt').read() + open('b.txt').read())\n",
            "ALL.txt": "a\nb\n",
            "lockmaster.toml": "[checks]\nok = '\"{0}\" -c \"pass\"'\n"
                               "[generated]\n\"ALL.txt\" = '\"{0}\" gen.py'\n".format(PY),
        })
        self.commit("generated")
        w1, w2 = self.start("W-1", "a.txt", "ALL.txt"), self.start("W-2", "b.txt")
        (w1 / "a.txt").write_text("A\n")
        (w1 / "ALL.txt").write_text("a hand-made version that must not land\n")
        (w2 / "b.txt").write_text("B\n")
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(self.submit("W-2")["status"], LANDED)
        self.assertEqual(git(self.root, "show", "main:ALL.txt"), "A\nB")

    def test_structural_merges_apply_during_a_landing(self):
        self.write_files(self.root, {"work/WORKLOG.md": "# log\n\n---\n\n## old\n",
                                     "lockmaster.toml": '[merge]\n"work/WORKLOG.md" = "append-newest-first"\n'})
        self.commit("worklog")
        self.cli("drivers")
        self.commit("attributes")
        w1, w2 = self.start("W-1", "work/WORKLOG.md"), self.start("W-2", "work/WORKLOG.md")
        for w, who in ((w1, "one"), (w2, "two")):
            p = w / "work" / "WORKLOG.md"
            p.write_text(p.read_text().replace("---\n\n", "---\n\n## {}\n\n".format(who)))
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(self.submit("W-2")["status"], LANDED)
        log = git(self.root, "show", "main:work/WORKLOG.md")
        self.assertLess(log.index("## two"), log.index("## one"))

    def test_main_checkout_with_local_edits_to_a_landed_path_is_red_not_overwritten(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("landing\n")
        (self.root / "a.txt").write_text("the decider's unsaved edit\n")
        change = self.submit("W-1")
        self.assertEqual(change["status"], RED)
        self.assertEqual((self.root / "a.txt").read_text(), "the decider's unsaved edit\n")

    # -------------------------------------------------------- DoD 4

    def test_a_landed_changes_worktree_and_branch_are_removed(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        change = self.submit("W-1")
        self.assertEqual(change["cleanup"], [])
        self.assertFalse(w.exists())
        self.assertEqual(git(self.root, "branch", "--list", "lm/*"), "")
        self.assertEqual(len(git(self.root, "worktree", "list").splitlines()), 1)
        code, out, _ = self.cli("doctor")
        self.assertEqual(code, 0, out)

    def test_abandon_removes_only_what_loses_nothing(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("unsaved\n")
        code, out, _ = self.cli("abandon", "--item", "W-1")
        self.assertEqual(code, 0)
        self.assertIn("kept", out)
        self.assertEqual((w / "a.txt").read_text(), "unsaved\n")
        w2 = self.start("W-2", "b.txt")
        self.cli("abandon", "--item", "W-2")
        self.assertFalse(w2.exists())
        self.assertEqual(git(self.root, "branch", "--list", "lm/W-2"), "")

    # -------------------------------------------------------- hazards

    def test_a_second_lander_waits_its_turn(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        repo = self.repo()
        held = LandLock(repo)
        self.assertTrue(held.acquire())
        try:
            land.submit(repo, repo.load("W-1"))
            self.assertIsNone(land.run(repo))
            self.assertEqual(self.repo().load("W-1")["status"], QUEUED)
        finally:
            held.release()
        land.run(repo)
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)

    def test_a_dead_landers_lock_and_change_are_taken_over(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        repo = self.repo()
        land.submit(repo, repo.load("W-1"))
        change = repo.load("W-1")
        change["status"] = LANDING  # the lander died here; main was never moved
        repo.save(change)
        lock = LandLock(repo)
        lock.dir.mkdir(parents=True)
        (lock.dir / "pid").write_text("999999")
        self.assertIn("stale land lock", self.cli("doctor")[1])
        self.assertEqual(land.run(repo), 1)
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)


class OneBuildOutputList(unittest.TestCase):
    def test_the_lander_and_the_kits_cleanup_share_one_list(self):
        # SR-WORK-CLEANUP decision 1(c): the list grows only by the decider's ruling — in both places at once.
        import importlib.util
        from support import ROOT
        spec = importlib.util.spec_from_file_location("wc", ROOT / "kit/claude/hooks/worktree-cleanup.py")
        wc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wc)
        self.assertEqual(land.BUILD_OUTPUT, wc.BUILD_OUTPUT)


if __name__ == "__main__":
    unittest.main()
