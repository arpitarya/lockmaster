"""W-18 — SR-ARCHITECTURE decision 15: `install` scaffolds the rest of the work
system a repository lacks — AGENTS.md, docs/GLOSSARY.md, the generic records,
the rest of work/, archive/ and the work system's scripts — never overwriting
a file, never mixing its records into a register the repository already has,
and leaving a tree whose own checks pass."""
import json
import re
import subprocess
import sys
from pathlib import Path

from support import ROOT, ScratchCase

from lockmaster import doctor, install

SCAFFOLD = ROOT / "kit" / "scaffold"
EVERY = sorted(p.relative_to(SCAFFOLD).as_posix().replace("_archive/", "archive/", 1)
               for p in SCAFFOLD.rglob("*")
               if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store")
# a link that names a shape, not a file: a template's slot, or archive/open/ before anything has closed
PLACEHOLDER = re.compile(r"<|W-nn|NNNN|archive/open/$")


class Scaffold(ScratchCase):
    def install(self):
        code, out, err = self.cli("install", str(self.root))
        self.assertEqual(code, 0, out + err)
        return out

    def test_a_fresh_install_scaffolds_every_file(self):
        out = self.install()
        for rel in EVERY:
            self.assertTrue((self.root / rel).is_file(), rel)
        self.assertIn("work system scaffolded", out)
        lock = json.loads((self.root / ".claude" / "lockmaster.lock").read_text())
        self.assertFalse(set(EVERY) & set(lock["files"]))  # the project's papers, not kit files

    def test_an_existing_file_is_never_overwritten(self):
        self.write_files(self.root, {"AGENTS.md": "mine\n", "docs/GLOSSARY.md": "my terms\n"})
        self.install()
        self.assertEqual((self.root / "AGENTS.md").read_text(), "mine\n")
        self.assertEqual((self.root / "docs" / "GLOSSARY.md").read_text(), "my terms\n")
        out = self.install()  # a second install creates nothing
        self.assertNotIn("scaffolded", out)

    def test_a_register_of_its_own_gets_none_of_the_kit_records(self):
        self.write_files(self.root, {"records/0052_WORK-environments.md": "ours\n"})
        self.install()
        self.assertEqual(sorted(p.name for p in (self.root / "records").iterdir()), ["0052_WORK-environments.md"])
        self.assertFalse((self.root / "scripts").exists())  # its checks would read the kit's register
        self.assertTrue((self.root / "AGENTS.md").is_file())  # the rest still arrives

    def test_the_scaffolded_tree_passes_its_own_checks(self):
        self.write_files(self.root, {"CLAUDE.md": "# CLAUDE.md\n"})
        self.install()
        for script in ("check-work-system.py", "check-open-work-inbox.py"):
            r = subprocess.run([sys.executable, str(self.root / "scripts" / script)], cwd=str(self.root),
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, script + ": " + r.stdout + r.stderr)
        self.assertEqual(doctor.check(self.repo()), [])
        self.assertTrue((self.root / ".git" / "hooks" / "commit-msg").is_symlink())  # the guard is wired
        self.commit("install")  # and lets the install itself through

    def test_every_link_in_the_scaffold_resolves(self):
        self.install()
        bad = []
        for rel in EVERY:
            if not rel.endswith(".md"):
                continue
            path = self.root / rel
            text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for m in re.finditer(r"\]\(([^)\s]+)\)", text):
                link = m.group(1).split("#")[0]
                if not link or re.match(r"^[a-z]+:", link) or PLACEHOLDER.search(link) or link.endswith("CLAUDE.md"):
                    continue
                if not (path.parent / link).exists():
                    bad.append("{} -> {}".format(rel, link))
        self.assertEqual(bad, [])

    def test_no_bare_lockmaster_item_id(self):
        # In a consumer, lockmaster's W-nn is another project's item: `**lockmaster W-nn**` (rule 23b).
        for rel in EVERY:
            if rel.endswith(".md"):
                text = (SCAFFOLD / rel.replace("archive/", "_archive/", 1)).read_text(encoding="utf-8")
                bare = re.findall(r"(?<!lockmaster )(?<!fux )\bW-\d+\b", text)
                self.assertEqual(bare, [], rel)

    def test_the_inbox_template_carries_its_date(self):
        self.install()
        text = (self.root / "work" / "OPEN-WORK.md").read_text()
        self.assertNotIn("{{installed}}", text)
        self.assertRegex(text, r"\*Empty since \d{4}-\d{2}-\d{2}")
