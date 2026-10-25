"""W-03 DoD 1 — lockmaster.toml means the same on Python 3.9 and 3.11+;
anything outside the subset is a loud error (SR-ARCHITECTURE decision 13)."""
import sys
import unittest

import support  # noqa: F401 — puts src/ on the path

from lockmaster import config

GOOD = '''# lockmaster.toml
[main]
branch = "trunk"

[checks]
tests = "python3 -m unittest discover -s tests"   # a comment
'lint' = 'echo "ok"'

[generated]
"CHANGELOG.md" = "python3 scripts/changelog.py"
"docs/**" = "make docs"

[merge]
"work/WORKLOG.md" = "append-newest-first"
"work/OPEN-WORK.md" = "table-rows"
"work/LESSONS.md" = "append"
'''


class SubsetReader(unittest.TestCase):
    def test_reads_every_table(self):
        c = config.parse(GOOD)
        self.assertEqual(c.main, "trunk")
        self.assertEqual(list(c.checks), ["tests", "lint"])
        self.assertEqual(c.checks["lint"], 'echo "ok"')
        self.assertEqual(c.generated["docs/**"], "make docs")
        self.assertEqual(c.merge["work/LESSONS.md"], "append")

    def test_escapes(self):
        data = config.parse_subset('[checks]\nx = "a\\tb\\"c\\\\ \\u00e9"\n')
        self.assertEqual(data["checks"]["x"], 'a\tb"c\\ é')

    def test_defaults_without_a_file(self):
        c = config.load("/nonexistent/lockmaster.toml")
        self.assertEqual((c.main, c.checks, c.generated, c.merge), ("main", {}, {}, {}))

    def test_outside_the_subset_is_loud(self):
        bad = {
            "array": '[checks]\nx = ["a", "b"]\n',
            "integer": '[checks]\nx = 1\n',
            "dotted": '[checks]\na.b = "x"\n',
            "unknown table": '[landing]\nx = "y"\n',
            "unknown driver": '[merge]\n"a" = "union"\n',
            "main key": '[main]\nremote = "origin"\n',
            "key outside a table": 'x = "y"\n',
            "array of tables": '[[checks]]\nx = "y"\n',
            "multi-line string": '[checks]\nx = """y"""\n',
            "duplicate key": '[checks]\nx = "a"\nx = "b"\n',
            "trailing junk": '[checks]\nx = "a" b\n',
        }
        for name, text in bad.items():
            with self.subTest(name):
                with self.assertRaises(config.ConfigError):
                    config.parse(text)

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib arrives in Python 3.11")
    def test_tomllib_agrees_with_the_subset_reader(self):
        import tomllib
        self.assertEqual(tomllib.loads(GOOD), config.parse_subset(GOOD))
        self.assertEqual(config.parse(GOOD).as_dict(), config.validate(config.parse_subset(GOOD)).as_dict())


if __name__ == "__main__":
    unittest.main()
