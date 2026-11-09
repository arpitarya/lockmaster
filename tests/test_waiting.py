"""W-10 — a dirty `main` checkout: the landing waits, never red, and lands by
itself once the checkout's edits clear; `status`, `doctor` and the claim hook
show the clash first; the live ledger never makes a landing wait
(SR-ARCHITECTURE decisions 8, 8a and 11; SR-LAW-9 decision 4)."""
import json
import subprocess
import sys
from pathlib import Path

from support import NO_X, ROOT, ScratchCase, git, toml_str

from lockmaster import doctor, land, status
from lockmaster.repo import LANDED, OPEN, QUEUED, RED, WAITING

HOOKS = ROOT / "kit" / "claude" / "hooks"


class Waiting(ScratchCase):
    def start(self, item, *paths, session="s-1"):
        change, _ = land.start(self.repo(), item, list(paths), session)
        return Path(change["worktree"])

    def submit(self, item, message=None):
        land.submit(self.repo(), self.repo().load(item), message or item + ": change")
        land.run(self.repo())
        return self.repo().load(item)

    def main_file(self, name):
        return git(self.root, "show", "main:" + name)

    # -------------------------------------------------------- steps 1, 2 and 5

    def test_a_differing_checkout_edit_makes_the_landing_wait_and_names_it(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("someone else's\n")
        c = self.submit("W-1")
        self.assertEqual(c["status"], WAITING)  # not red: the cause clears by itself
        self.assertIn("a.txt", c["reason"])
        self.assertIn("uncommitted edits", c["reason"])
        self.assertEqual(self.main_file("a.txt"), "a")
        self.assertEqual((self.root / "a.txt").read_text(), "someone else's\n")  # never touched (L3)
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "")  # nothing staged either
        self.assertIn("a.txt", "\n".join(land.queue_lines(self.repo())))

    def test_it_lands_with_no_resubmit_once_the_edit_is_undone(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("someone else's\n")
        self.submit("W-1")
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], WAITING)  # still there: still waiting
        git(self.root, "checkout", "--", "a.txt")  # the other session undoes its edit
        land.run(self.repo())
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], LANDED)
        self.assertEqual(self.main_file("a.txt"), "mine")
        self.assertEqual((self.root / "a.txt").read_text(), "mine\n")  # the checkout moved with main
        self.assertEqual(git(self.root, "for-each-ref", "refs/lockmaster/"), "")  # the kept commit is let go

    def test_it_lands_once_the_checkout_holds_the_same_edit(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("draft\n")
        self.submit("W-1")
        (self.root / "a.txt").write_text("mine\n")  # the same edit, made in the checkout too (decision 8a)
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)

    def test_waiting_does_not_run_the_checks_again(self):
        count = Path(self._tmp.name) / "checks-ran"
        (self.root / "lockmaster.toml").write_text("[checks]\ncount = {}\n".format(toml_str("echo x >> {}".format(count))))
        self.commit("config")
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("theirs\n")
        self.submit("W-1")
        for _ in range(3):
            land.run(self.repo())
        self.assertEqual(count.read_text().count("x"), 1)
        git(self.root, "checkout", "--", "a.txt")
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)
        self.assertEqual(count.read_text().count("x"), 1)  # fast-forwarded the checked commit

    def test_main_moving_while_it_waits_redoes_the_landing_on_the_new_main(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("theirs\n")
        self.submit("W-1")
        w2 = self.start("W-2", "b.txt")
        (w2 / "b.txt").write_text("other\n")
        self.assertEqual(self.submit("W-2")["status"], LANDED)  # a change behind a waiting one still lands
        self.assertEqual(self.repo().load("W-1")["status"], WAITING)
        git(self.root, "checkout", "--", "a.txt")
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)
        self.assertEqual(self.main_file("a.txt"), "mine")
        self.assertEqual(self.main_file("b.txt"), "other")  # redone on the new main, not from the stale base

    def test_an_edit_that_does_not_overlap_lands_at_once(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "b.txt").write_text("unrelated\n")
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(git(self.root, "status", "--porcelain"), "M b.txt")

    def test_other_refusals_stay_red(self):
        (self.root / "lockmaster.toml").write_text("[checks]\nno-x = {}\n".format(NO_X))
        self.commit("config")
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("x\n")
        (self.root / "a.txt").write_text("theirs\n")
        self.assertEqual(self.submit("W-1")["status"], RED)  # the check failed first: a real reason

    def test_an_end_of_turn_landing_waits_too_and_stays_open_when_it_lands(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("theirs\n")
        land.sync(self.repo(), session="s-1")
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], WAITING)
        self.assertEqual([i for i, _ in land.waiting_reports(self.repo(), session="s-1")], ["W-1"])
        self.assertEqual(land.waiting_reports(self.repo(), session="s-1"), [])  # said once
        git(self.root, "checkout", "--", "a.txt")
        land.sync(self.repo(), session="s-1")  # the next turn's end retries it
        c = self.repo().load("W-1")
        self.assertEqual(c["status"], OPEN)
        self.assertEqual(self.main_file("a.txt"), "mine")
        self.assertTrue(w.is_dir())

    def test_the_session_end_finishes_a_waiting_change_once_it_lands(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("theirs\n")
        land.sync(self.repo(), session="s-1")
        land.sync(self.repo(), session="s-1", final=True)
        self.assertEqual(self.repo().load("W-1")["status"], WAITING)
        git(self.root, "checkout", "--", "a.txt")
        land.run(self.repo())
        self.assertEqual(self.repo().load("W-1")["status"], LANDED)
        self.assertFalse(w.exists())

    def test_a_resubmitted_waiting_change_is_landed_afresh(self):
        w = self.start("W-1", "a.txt")
        (w / "a.txt").write_text("mine\n")
        (self.root / "a.txt").write_text("theirs\n")
        self.submit("W-1")
        (w / "a.txt").write_text("theirs\n")  # the agent adopts the checkout's edit
        self.assertEqual(self.submit("W-1")["status"], LANDED)
        self.assertEqual(self.main_file("a.txt"), "theirs")

    # -------------------------------------------------------- the ledger (2026-11-05)

    def test_the_ledger_never_makes_a_landing_wait(self):
        self.write_files(self.root, {"work/NOW.md": "# NOW\n"})
        self.commit("ledger")
        w = self.start("W-1", "a.txt", "work")
        (w / "a.txt").write_text("mine\n")
        (w / "work" / "NOW.md").write_text("# NOW\n\nthe worktree's copy\n")
        (self.root / "work" / "NOW.md").write_text("# NOW\n\nthe live row\n")  # a hook wrote it meanwhile
        c = self.submit("W-1")
        self.assertEqual(c["status"], LANDED, c.get("reason"))
        self.assertEqual(self.main_file("a.txt"), "mine")
        self.assertEqual(self.main_file("work/NOW.md"), "# NOW\n\nthe live row")  # the checkout's is the newest
        self.assertIn("the live row", (self.root / "work" / "NOW.md").read_text())  # re-rendered, not lost
        msg = git(self.root, "log", "-1", "--format=%B", "main")
        self.assertIn("Lockmaster-Change: W-1", msg)
        self.assertEqual(len(git(self.root, "log", "-1", "--format=%P", "main").split()), 2)  # parents kept

    def test_save_lands_although_the_ledger_moved_after_its_copy(self):
        self.write_files(self.root, {"work/NOW.md": "# NOW\n"})
        self.commit("ledger")
        (self.root / "a.txt").write_text("edited in place\n")
        (self.root / "work" / "NOW.md").write_text("# NOW\n\na row\n")
        real = land._copy_in

        def copy_then_ledger_moves(repo, wt, dirty):
            real(repo, wt, dirty)
            (self.root / "work" / "NOW.md").write_text("# NOW\n\na row\nthe new worktree's row\n")
        land._copy_in = copy_then_ledger_moves
        try:
            c = land.save(self.repo(), ["a.txt", "work/NOW.md"], "W-2: a")
        finally:
            land._copy_in = real
        self.assertEqual(c["status"], LANDED, c.get("reason"))
        self.assertEqual(self.main_file("a.txt"), "edited in place")

    # -------------------------------------------------------- step 3

    def test_status_and_doctor_show_the_overlap_before_the_landing(self):
        self.start("W-1", "a.txt")
        (self.root / "a.txt").write_text("theirs\n")
        self.assertEqual(land.checkout_overlaps(self.repo()), [("W-1", OPEN, ["a.txt"])])
        self.assertIn("claimed by W-1", "\n".join(status.report(self.repo())))
        self.assertTrue(any("W-1" in p and "a.txt" in p for p in doctor.check(self.repo())))
        git(self.root, "checkout", "--", "a.txt")
        self.assertEqual(land.checkout_overlaps(self.repo()), [])

    def test_the_ledger_is_not_an_overlap(self):
        self.write_files(self.root, {"work/NOW.md": "# NOW\n"})
        self.commit("ledger")
        self.start("W-1", "work")
        (self.root / "work" / "NOW.md").write_text("# NOW\n\nlive\n")
        self.assertEqual(land.checkout_overlaps(self.repo()), [])

    # -------------------------------------------------------- step 4

    def hook(self, path):
        r = subprocess.run([sys.executable, str(HOOKS / "claim-guard.py")], capture_output=True, text=True,
                           input=json.dumps({"tool_name": "Edit", "cwd": str(self.root),
                                             "tool_input": {"file_path": str(path)}}))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["systemMessage"] if r.stdout.strip() else None

    def test_the_claim_hook_warns_on_a_checkout_edit_a_change_claims(self):
        w = self.start("W-1", "a.txt", "work")
        msg = self.hook(self.root / "a.txt")
        self.assertIn("W-1 claims `a.txt`", msg)
        self.assertIn(str(w), msg)
        self.assertIsNone(self.hook(self.root / "b.txt"))  # nobody claims it
        self.assertIsNone(self.hook(self.root / "work" / "NOW.md"))  # the ledger is always edited there
