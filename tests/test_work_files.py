"""W-15 — SR-LAW-10: the six work files are present and kept current in every
repository lockmaster is installed in: `install` creates a missing one,
`doctor` names a missing or stale one, and the kit's Stop hook tells a session
that changed files but none of WORKLOG, INTERVIEW or OPEN-WORK, once."""
import json
import subprocess
import sys

from support import ScratchCase, git

from lockmaster import doctor, install

SIX = install.WORK_FILES


class WorkFiles(ScratchCase):
    def install(self):
        code, out, err = self.cli("install", str(self.root))
        self.assertEqual(code, 0, out + err)
        return out

    # -------------------------------------------------------- step 1

    def test_a_fresh_install_leaves_all_six(self):
        out = self.install()
        for name in SIX:
            self.assertTrue((self.root / "work" / name).is_file(), name)
        self.assertIn("work files created", out)
        lock = json.loads((self.root / ".claude" / "lockmaster.lock").read_text())
        self.assertFalse(any(rel.startswith("work/") for rel in lock["files"]))  # the project's papers, not kit files

    def test_an_existing_work_file_is_never_overwritten(self):
        self.write_files(self.root, {"work/WORKLOG.md": "my own log\n"})
        self.install()
        self.assertEqual((self.root / "work" / "WORKLOG.md").read_text(), "my own log\n")
        self.install()  # a second install creates nothing and changes nothing
        self.assertEqual((self.root / "work" / "WORKLOG.md").read_text(), "my own log\n")

    def test_the_machine_template_carries_a_budget_lockmaster_reads(self):
        self.install()
        from lockmaster import status
        self.assertEqual(status.budget_gb(self.root), 5.0)

    # -------------------------------------------------------- step 2

    def test_doctor_names_a_missing_work_file(self):
        self.install()
        (self.root / "work" / "LESSONS.md").unlink()
        problems = doctor.check(self.repo())
        self.assertTrue(any("work/LESSONS.md" in p and "missing" in p for p in problems), problems)

    def test_doctor_says_nothing_where_the_kit_is_not_installed(self):
        self.assertEqual(doctor.work_problems(self.repo()), [])

    def test_doctor_names_a_worklog_main_has_moved_past(self):
        self.install()
        self.commit("install")
        self.assertEqual(doctor.work_problems(self.repo()), [])
        for i in range(doctor.STALE_LANDINGS + 1):
            self.write_files(self.root, {"a.txt": "{}\n".format(i)})
            self.commit("change {}".format(i))
        problems = doctor.work_problems(self.repo())
        self.assertTrue(any("WORKLOG.md is stale" in p for p in problems), problems)
        log = self.root / "work" / "WORKLOG.md"
        log.write_text(log.read_text() + "\n## an entry\n")
        self.commit("worklog")
        self.assertEqual(doctor.work_problems(self.repo()), [])

    # -------------------------------------------------------- step 3

    def hook(self, mode, **payload):
        payload.setdefault("session_id", "s-1")
        r = subprocess.run([sys.executable, str(self.root / ".claude" / "hooks" / "work-files.py"), mode],
                           input=json.dumps(payload), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def wrote(self, path):
        return self.hook("edit", tool_name="Edit", cwd=str(self.root), tool_input={"file_path": str(path)})

    def test_a_session_that_touched_no_work_file_is_told_once(self):
        self.install()
        self.wrote(self.root / "src" / "thing.py")
        out = self.hook("stop")
        self.assertEqual(out["decision"], "block")
        self.assertIn("src/thing.py", out["reason"])
        self.assertIn("work/WORKLOG.md", out["reason"])
        self.assertIsNone(self.hook("stop"))  # told once

    def test_a_session_that_updated_a_work_file_stops_freely(self):
        self.install()
        self.wrote(self.root / "src" / "thing.py")
        self.wrote(self.root / "work" / "WORKLOG.md")
        self.assertIsNone(self.hook("stop"))

    def test_edits_in_a_changes_worktree_count_as_the_same_files(self):
        self.install()
        wt = self.root / ".claude" / "worktrees" / "W-1"
        self.wrote(wt / "src" / "thing.py")
        self.wrote(wt / "work" / "OPEN-WORK.md")
        self.assertIsNone(self.hook("stop"))

    def test_only_work_files_or_nothing_written_never_blocks(self):
        self.install()
        self.assertIsNone(self.hook("stop"))
        self.wrote(self.root / "work" / "NOW.md")
        self.assertIsNone(self.hook("stop"))

    def test_a_stop_already_continuing_for_a_hook_never_blocks_again(self):
        self.install()
        self.wrote(self.root / "src" / "thing.py")
        self.assertIsNone(self.hook("stop", stop_hook_active=True))

    def test_the_notes_live_in_gits_directory_not_the_tree(self):
        self.install()
        self.commit("install")
        self.wrote(self.root / "src" / "thing.py")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertTrue(list((self.root / ".git" / "lockmaster" / "sessions").glob("*.work-files.json")))

    def test_the_hook_is_wired_into_the_kits_settings(self):
        self.install()
        settings = json.loads((self.root / ".claude" / "settings.json").read_text())
        commands = [h["command"] for groups in settings["hooks"].values() for g in groups for h in g["hooks"]]
        self.assertTrue(any("work-files.py\" stop" in c for c in commands))
        self.assertTrue(any("work-files.py\" edit" in c for c in commands))
