"""W-03 DoD 3 — each structural driver merges two branches that both added
rows, in a scratch repo, with no conflict; a true conflict still conflicts
(SR-ARCHITECTURE decision 10)."""
import unittest

from support import ScratchCase, git

from lockmaster.merge import merge_lines

WORKLOG = "# WORKLOG\n\n---\n\n## 2026-10-01 — first\n\n- done\n"
QUEUE = "# OPEN-WORK\n\n| item | what |\n|---|---|\n| W-01 | one |\n\n## end\n"
LESSONS = "# LESSONS\n\n- one\n"


def lines(s):
    return s.splitlines(True)


class Engine(unittest.TestCase):
    def test_newest_first_puts_the_landing_change_on_top(self):
        base = lines("h\n---\nold\n")
        ours = lines("h\n---\nmain-entry\nold\n")
        theirs = lines("h\n---\nchange-entry\nold\n")
        self.assertEqual("".join(merge_lines("append-newest-first", base, ours, theirs)),
                         "h\n---\nchange-entry\nmain-entry\nold\n")

    def test_append_keeps_landing_order(self):
        base = lines("a\n")
        self.assertEqual("".join(merge_lines("append", base, lines("a\nb\n"), lines("a\nc\n"))), "a\nb\nc\n")

    def test_table_rows_keeps_a_row_both_added_once(self):
        base = lines("|h|\n|r1|\n")
        merged = merge_lines("table-rows", base, lines("|h|\n|r1|\n|x|\n|r2|\n"), lines("|h|\n|r1|\n|x|\n|r3|\n"))
        self.assertEqual("".join(merged), "|h|\n|r1|\n|x|\n|r2|\n|r3|\n")

    def test_separate_edits_both_apply(self):
        base = lines("1\n2\n3\n4\n5\n")
        merged = merge_lines("append", base, lines("one\n2\n3\n4\n5\n"), lines("1\n2\n3\n4\nfive\n"))
        self.assertEqual("".join(merged), "one\n2\n3\n4\nfive\n")

    def test_overlapping_edits_are_not_decided_here(self):
        base = lines("1\n2\n3\n")
        self.assertIsNone(merge_lines("table-rows", base, lines("1\nTWO\n3\n"), lines("1\nzwei\n3\n")))
        self.assertIsNone(merge_lines("append", base, lines("1\n2\n"), lines("1\n2\n3\nnew\n")))


class InPlainGit(ScratchCase):
    """The drivers installed by `lockmaster drivers`, run by a plain `git merge`."""

    files = {"work/WORKLOG.md": WORKLOG, "work/OPEN-WORK.md": QUEUE, "work/LESSONS.md": LESSONS,
             "lockmaster.toml": '[merge]\n"work/WORKLOG.md" = "append-newest-first"\n'
                                '"work/OPEN-WORK.md" = "table-rows"\n"work/LESSONS.md" = "append"\n'}

    def setUp(self):
        super().setUp()
        code, out, err = self.cli("drivers")
        self.assertEqual(code, 0, err)
        self.assertIn("merge=lockmaster-table-rows", (self.root / ".gitattributes").read_text())
        self.commit("attributes")

    def branch_edit(self, name, edits):
        git(self.root, "checkout", "-q", "-b", name, "main")
        for rel, fn in edits.items():
            p = self.root / rel
            p.write_text(fn(p.read_text()))
        self.commit(name)
        git(self.root, "checkout", "-q", "main")

    def test_two_branches_adding_rows_never_conflict(self):
        add_entry = lambda who: lambda t: t.replace("---\n\n", "---\n\n## 2026-10-25 — {}\n\n- x\n\n".format(who))
        add_row = lambda who: lambda t: t.replace("| W-01 | one |\n", "| W-01 | one |\n| {} | new |\n".format(who))
        add_lesson = lambda who: lambda t: t + "- {}\n".format(who)
        for who in ("left", "right"):
            self.branch_edit(who, {"work/WORKLOG.md": add_entry(who), "work/OPEN-WORK.md": add_row(who),
                                   "work/LESSONS.md": add_lesson(who)})
        git(self.root, "merge", "-q", "--no-edit", "left")
        r = git(self.root, "merge", "--no-edit", "right", check=False)
        self.assertEqual(git(self.root, "status", "--porcelain"), "", r)
        worklog = (self.root / "work/WORKLOG.md").read_text()
        self.assertLess(worklog.index("right"), worklog.index("left"))  # the incoming entry on top
        self.assertIn("| left | new |\n| right | new |", (self.root / "work/OPEN-WORK.md").read_text())
        self.assertTrue((self.root / "work/LESSONS.md").read_text().endswith("- left\n- right\n"))

    def test_a_true_conflict_still_conflicts(self):
        self.branch_edit("left", {"work/OPEN-WORK.md": lambda t: t.replace("| one |", "| uno |")})
        self.branch_edit("right", {"work/OPEN-WORK.md": lambda t: t.replace("| one |", "| eins |")})
        git(self.root, "merge", "-q", "--no-edit", "left")
        r = __import__("subprocess").run(["git", "merge", "--no-edit", "right"], cwd=str(self.root),
                                         capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        text = (self.root / "work/OPEN-WORK.md").read_text()
        self.assertIn("<<<<<<<", text)
        self.assertIn("uno", text)
        self.assertIn("eins", text)
        git(self.root, "merge", "--abort")

    def test_drivers_rewrite_only_their_own_block(self):
        attrs = self.root / ".gitattributes"
        attrs.write_text("*.png binary\n" + attrs.read_text())
        self.cli("drivers")
        self.cli("drivers")
        text = attrs.read_text()
        self.assertTrue(text.startswith("*.png binary\n"))
        self.assertEqual(text.count("lockmaster:begin"), 1)


if __name__ == "__main__":
    unittest.main()
