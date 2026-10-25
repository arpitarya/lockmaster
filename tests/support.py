"""Scratch repositories for the tests: a real git repo in a temp directory,
with the user's global and system git config shut out so their hooks and
settings cannot change the result."""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
ROOT = SRC.parent

ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd, *args, check=True):
    r = subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError("git {} failed: {}".format(" ".join(args), r.stderr))
    return r.stdout.strip()


class ScratchCase(unittest.TestCase):
    """Each test gets `self.root`, a repo on `main` with one commit."""

    files = {"a.txt": "a\n", "b.txt": "b\n"}

    def setUp(self):
        self._env = {k: os.environ.get(k) for k in ENV}
        os.environ.update(ENV)
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(os.path.realpath(self._tmp.name)) / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        self.write_files(self.root, self.files)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    @staticmethod
    def write_files(base, files):
        for rel, text in files.items():
            p = Path(base) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def commit(self, message="change", cwd=None):
        cwd = cwd or self.root
        git(cwd, "add", "-A")
        git(cwd, "commit", "-q", "-m", message)
        return git(cwd, "rev-parse", "HEAD")

    def repo(self):
        from lockmaster.repo import Repo
        return Repo(self.root)

    def cli(self, *argv, cwd=None):
        """Run `lockmaster <argv>` in-process from `cwd`; (exit code, stdout, stderr)."""
        from lockmaster.cli import main
        os.chdir(str(cwd or self.root))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        os.chdir(self._cwd)
        return code, out.getvalue(), err.getvalue()
