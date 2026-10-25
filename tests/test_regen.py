"""W-03 DoD 2 and 4 — `lockmaster regen` rebuilds every [generated] path; a
failing command fails the run; nothing in the tool forces (SR-ARCHITECTURE
decision 9, SR-LAW-3)."""
import re
import sys
import unittest
from pathlib import Path

from support import ROOT, ScratchCase

PY = sys.executable


class Regen(ScratchCase):
    files = {
        "src.txt": "one\ntwo\n",
        "COUNT.txt": "stale\n",
        "gen.py": "n = len(open('src.txt').readlines())\nopen('COUNT.txt', 'w').write(str(n) + '\\n')\n",
        "lockmaster.toml": "[generated]\n\"COUNT.txt\" = '\"{}\" gen.py'\n".format(PY),
    }

    def test_rebuilds_each_generated_path(self):
        (self.root / "src.txt").write_text("one\ntwo\nthree\n")
        code, out, err = self.cli("regen")
        self.assertEqual(code, 0, err)
        self.assertEqual((self.root / "COUNT.txt").read_text(), "3\n")

    def test_a_failing_command_fails_the_run(self):
        (self.root / "lockmaster.toml").write_text('[generated]\n"COUNT.txt" = "exit 3"\n')
        code, out, err = self.cli("regen")
        self.assertEqual(code, 2)
        self.assertIn("exited 3", err)

    def test_uncommitted_edits_to_a_generated_file_are_refused_not_overwritten(self):
        (self.root / "COUNT.txt").write_text("hand edit\n")
        code, out, err = self.cli("regen")
        self.assertEqual(code, 2)
        self.assertIn("COUNT.txt", err)
        self.assertEqual((self.root / "COUNT.txt").read_text(), "hand edit\n")


class NoForcing(unittest.TestCase):
    def test_no_forced_git_operation_in_src_or_the_kit(self):
        bad = re.compile(r"--force|branch -D|reset --hard|git clean|push -f")
        hits = []
        for base in (ROOT / "src", ROOT / "kit" / "claude"):
            for f in base.rglob("*"):
                if f.is_file() and f.suffix in (".py", ".sh", ".json", ".md"):
                    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                        if bad.search(line):
                            hits.append("{}:{}".format(Path(f).relative_to(ROOT), n))
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
