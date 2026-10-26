"""W-06 — `lockmaster install <repo>` and `lockmaster doctor`
(SR-ARCHITECTURE decisions 14 and 15)."""
import json
import os
import re
import unittest

from support import ROOT, ScratchCase

from lockmaster import install

OWN_HOOK = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo the repo's own hook"}]}


class Install(ScratchCase):
    def install(self, *extra):
        return self.cli("install", str(self.root), *extra)

    def settings(self):
        return json.loads((self.root / ".claude/settings.json").read_text())

    def test_a_fresh_repo_gets_the_kit_and_every_hook_resolves(self):
        code, out, err = self.install()
        self.assertEqual(code, 0, err)
        for src, rel in install.kit_files(install.find_kit()):
            self.assertEqual((self.root / rel).read_bytes(), src.read_bytes(), rel)
        self.assertFalse((self.root / ".github").exists())  # a repository's CI is its own (decision 16)
        for groups in self.settings()["hooks"].values():
            for g in groups:
                for h in g["hooks"]:
                    m = re.search(r"\$CLAUDE_PROJECT_DIR/(\.claude/hooks/[^\" ]+)", h["command"])
                    self.assertTrue(m, h["command"])
                    hook = self.root / m.group(1)
                    self.assertTrue(hook.is_file(), hook)
                    self.assertTrue(os.access(str(hook), os.X_OK), hook)

    def test_the_repos_own_hooks_survive_an_install_and_a_reinstall(self):
        (self.root / ".claude").mkdir()
        (self.root / ".claude/settings.json").write_text(json.dumps(
            {"permissions": {"allow": ["Bash(ls)"]}, "hooks": {"PreToolUse": [OWN_HOOK]}}))
        self.install()
        first = self.settings()
        self.install()
        again = self.settings()
        self.assertEqual(first, again)
        self.assertIn(OWN_HOOK, again["hooks"]["PreToolUse"])
        self.assertEqual(again["permissions"], {"allow": ["Bash(ls)"]})
        kit = json.loads((install.find_kit() / "claude/settings.json").read_text())
        n_kit = sum(len(v) for v in kit["hooks"].values())
        self.assertEqual(sum(len(v) for v in again["hooks"].values()), n_kit + 1)

    def test_a_file_lockmaster_did_not_write_is_never_overwritten_silently(self):
        hook = self.root / ".claude/hooks/inject-inbox.sh"
        hook.parent.mkdir(parents=True)
        hook.write_text("the repo's own hook\n")
        code, _, err = self.install()
        self.assertEqual(code, 2)
        self.assertIn(".claude/hooks/inject-inbox.sh", err)
        self.assertEqual(hook.read_text(), "the repo's own hook\n")
        self.assertFalse((self.root / ".claude/settings.json").exists())
        code, out, err = self.install("--backup")
        self.assertEqual(code, 0, err)
        self.assertEqual((hook.parent / "inject-inbox.sh.pre-lockmaster").read_text(), "the repo's own hook\n")

    def test_the_repos_own_ci_is_never_touched(self):
        ci = self.root / ".github/workflows/ci.yml"
        ci.parent.mkdir(parents=True)
        ci.write_text("the repo's own CI\n")
        code, _, err = self.install()
        self.assertEqual(code, 0, err)
        self.assertEqual(ci.read_text(), "the repo's own CI\n")
        self.assertFalse((ci.parent / "ci.yml.pre-lockmaster").exists())

    def test_the_version_is_pinned_and_doctor_reports_a_mismatch(self):
        self.install()
        lock = json.loads((self.root / install.LOCK).read_text())
        self.assertEqual(lock["kit"], install.kit_digest(install.find_kit()))
        code, out, _ = self.cli("doctor")
        self.assertEqual(code, 0, out)
        lock["version"] = "0.0.0-older"
        (self.root / install.LOCK).write_text(json.dumps(lock))
        code, out, _ = self.cli("doctor")
        self.assertEqual(code, 1)
        self.assertIn("installed kit is from lockmaster 0.0.0-older", out)

    def test_doctor_reports_a_hand_edited_hook(self):
        self.install()
        hook = self.root / ".claude/hooks/block-main.py"
        hook.write_text(hook.read_text() + "# edited\n")
        code, out, _ = self.cli("doctor")
        self.assertEqual(code, 1)
        self.assertIn("edited by hand: .claude/hooks/block-main.py", out)


if __name__ == "__main__":
    unittest.main()
