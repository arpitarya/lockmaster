"""scripts/release.py — the tag, __version__ and CHANGELOG agree before
anything is published (SR-ARCHITECTURE decision 17)."""
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

from support import ROOT

spec = importlib.util.spec_from_file_location("release", ROOT / "scripts" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

LOG = """# Changelog

## [Unreleased]

### Added

- a thing

## [0.0.1] - 2026-10-01

- the first
"""


class Release(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "src" / "lockmaster").mkdir(parents=True)
        (self.root / "src/lockmaster/__init__.py").write_text('"""x"""\n\n__version__ = "0.0.1"\n')
        (self.root / "CHANGELOG.md").write_text(LOG)

    def tearDown(self):
        self._tmp.cleanup()

    def test_prepare_bumps_the_version_and_cuts_the_changelog(self):
        release.prepare("0.1.0", self.root, today=date(2026, 10, 26))
        self.assertEqual(release.current(self.root), "0.1.0")
        log = (self.root / "CHANGELOG.md").read_text()
        self.assertIn("## [Unreleased]\n\n## [0.1.0] - 2026-10-26\n\n### Added\n\n- a thing\n", log)
        self.assertEqual(release.section(log, "Unreleased"), "")
        self.assertEqual(release.check("v0.1.0", self.root), "0.1.0")

    def test_prepare_refuses_an_older_version_or_an_empty_unreleased(self):
        with self.assertRaises(release.ReleaseError):
            release.prepare("0.0.1", self.root)
        release.prepare("0.0.2", self.root)
        with self.assertRaises(release.ReleaseError):
            release.prepare("0.0.3", self.root)  # [Unreleased] is empty now

    def test_check_refuses_a_tag_that_disagrees(self):
        for tag in ("0.0.1", "v0.0.2", "vbanana"):
            with self.subTest(tag):
                with self.assertRaises(release.ReleaseError):
                    release.check(tag, self.root)
        self.assertEqual(release.check("v0.0.1", self.root), "0.0.1")

    def test_pre_releases_order_before_the_release(self):
        self.assertLess(release.key("0.1.0rc1"), release.key("0.1.0"))
        self.assertLess(release.key("0.1.0a2"), release.key("0.1.0b1"))

    def test_this_repository_agrees_with_itself(self):
        version = release.current()
        self.assertTrue(release.section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), "Unreleased") is not None)
        release.key(version)


if __name__ == "__main__":
    unittest.main()
