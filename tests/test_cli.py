"""The command's contract: every command SR-ARCHITECTURE decision 14 names
exists, help exits 0, and a refusal is exit 2 with the reason on stderr."""
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from support import ScratchCase

from lockmaster.cli import COMMANDS, main


class Contract(unittest.TestCase):
    def test_decision_14_commands_exist(self):
        for name in ("start", "claim", "submit", "run", "queue", "status", "abandon", "doctor", "install",
                     "regen", "drivers"):
            self.assertIn(name, COMMANDS)

    def test_help_exits_zero(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([]), 0)


class Refusals(ScratchCase):
    def test_submit_outside_a_change_is_refused_with_its_reason(self):
        code, _, err = self.cli("submit")
        self.assertEqual(code, 2)
        self.assertIn("not inside a change's worktree", err)

    def test_a_bad_item_id_is_refused(self):
        code, _, err = self.cli("start", "../x", "--paths", "a.txt")
        self.assertEqual(code, 2)
        self.assertIn("item id", err)

    def test_starting_a_live_change_twice_is_refused(self):
        self.assertEqual(self.cli("start", "W-1", "--paths", "a.txt")[0], 0)
        code, _, err = self.cli("start", "W-1", "--paths", "a.txt")
        self.assertEqual(code, 2)
        self.assertIn("already has", err)


if __name__ == "__main__":
    unittest.main()
