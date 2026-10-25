"""The stub's contract: every command SR-ARCHITECTURE decision 14 names exists,
and none pretends to work before it is built."""
import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lockmaster.cli import COMMANDS, main  # noqa: E402


class StubContract(unittest.TestCase):
    def test_decision_14_commands_exist(self):
        for name in ("start", "claim", "submit", "run", "queue", "status", "abandon", "doctor", "install"):
            self.assertIn(name, COMMANDS)

    def test_unbuilt_command_fails_loudly(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(main(["run"]), 2)
        self.assertIn("not built yet", err.getvalue())

    def test_help_exits_zero(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
