"""The package ships the kit (SR-ARCHITECTURE decision 15): every kit/
directory is a package in pyproject.toml, with its files as package data,
and the version has one source."""
import re
import unittest

from support import ROOT

from lockmaster import __version__


class Packaging(unittest.TestCase):
    def setUp(self):
        self.pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    def test_every_kit_directory_is_listed_and_carries_its_files(self):
        dirs = [ROOT / "kit"] + sorted(d for d in (ROOT / "kit").rglob("*")
                                       if d.is_dir() and d.name != "__pycache__")
        for d in dirs:
            name = "lockmaster." + ".".join(d.relative_to(ROOT).parts)
            with self.subTest(name):
                self.assertIn('"{}",'.format(name), self.pyproject)
                self.assertIn('"{}" = ["*"]'.format(name), self.pyproject)

    def test_every_listed_kit_package_has_its_directory(self):
        # A kit/ directory removed but still listed breaks the build (setuptools refuses it).
        for name in re.findall(r'"(lockmaster\.kit[a-z.]*)",', self.pyproject):
            with self.subTest(name):
                self.assertTrue((ROOT / "kit").joinpath(*name.split(".")[2:]).is_dir(), name)

    def test_the_version_has_one_source(self):
        self.assertIn('version = { attr = "lockmaster.__version__" }', self.pyproject)
        project = self.pyproject.split("[project]", 1)[1].split("\n[", 1)[0]
        self.assertNotRegex(project, r'(?m)^version\s*=')  # no second, static version
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+([ab]\d+|rc\d+)?$")


if __name__ == "__main__":
    unittest.main()
