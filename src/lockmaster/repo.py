"""The repository, lockmaster's state and the land lock — SR-ARCHITECTURE decisions 3, 4 and 7.

State lives at `$(git rev-parse --git-common-dir)/lockmaster/`: shared by every
worktree, never committed, gone with the clone. A change is one JSON file in
`changes/`; the land lock is a `mkdir` mutex holding the lander's pid.
"""
import fnmatch
import json
import os
import re
import shlex
import stat
import time
from pathlib import Path

from lockmaster import config as config_mod
from lockmaster import git

ITEM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
WORKTREES_DIR = ".claude/worktrees"

# A change's status, in the order it moves through them.
OPEN, QUEUED, LANDING, LANDED, RED, ABANDONED = "open", "queued", "landing", "landed", "red", "abandoned"
LIVE = (OPEN, QUEUED, LANDING, RED)

# SR-ARCHITECTURE decision 18: the hooks that can refuse a step. A repository's
# post-* hooks (a re-index, a notification) are side effects of a person's or an
# agent's own git step; lockmaster's steps leave them out. What a landing must
# produce, it produces through [generated].
GATE_HOOKS = ("applypatch-msg", "pre-applypatch", "pre-commit", "pre-merge-commit",
              "prepare-commit-msg", "commit-msg", "pre-rebase", "pre-push")
FORWARDER = """#!/bin/sh
# Written by lockmaster (SR-ARCHITECTURE decision 18): while lockmaster runs git,
# the repository's gate hooks run and its post-* hooks do not. Rewritten each run.
hook={}
[ -x "$hook" ] || exit 0
exec "$hook" "$@"
"""


class LockmasterError(Exception):
    """A refusal lockmaster explains to the person or agent who asked."""


class Repo:
    def __init__(self, cwd="."):
        cwd = Path(cwd).resolve()
        code, top, _ = git.run(["rev-parse", "--show-toplevel"], cwd, check=False)
        if code != 0:
            raise LockmasterError("not inside a git repository: " + str(cwd))
        self.cwd = cwd
        self.toplevel = Path(top.strip())
        common = Path(git.out(["rev-parse", "--git-common-dir"], cwd))
        self.common = (cwd / common).resolve() if not common.is_absolute() else common
        # The primary worktree is the first `git worktree list` entry.
        self.root = Path(git.worktrees(cwd)[0]["path"])
        self.state = self.common / "lockmaster"
        self.changes_dir = self.state / "changes"
        self._gate_hooks_only()
        self.config = config_mod.load(self.root / config_mod.FILENAME)
        self.main = self.config.main

    def _gate_hooks_only(self):
        """Point every git step lockmaster runs at forwarders for the repository's
        gate hooks only (decision 18)."""
        git.HOOKS = []
        code, val, _ = git.run(["config", "--get", "core.hooksPath"], self.root, check=False)
        real = Path(os.path.expanduser(val.strip())) if code == 0 and val.strip() else self.common / "hooks"
        if not real.is_absolute():
            real = self.root / real
        hooks = self.state / "hooks"
        try:
            hooks.mkdir(parents=True, exist_ok=True)
            for name in GATE_HOOKS:
                f = hooks / name
                text = FORWARDER.format(shlex.quote(str(real / name)))
                if not f.is_file() or f.read_text(encoding="utf-8") != text:
                    f.write_text(text, encoding="utf-8")
                f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            return  # cannot write the forwarders: run the repository's hooks as they are
        git.HOOKS = ["-c", "core.hooksPath=" + str(hooks)]

    # ------------------------------------------------------------ changes

    def change_path(self, item):
        return self.changes_dir / (item + ".json")

    def load(self, item):
        try:
            with open(str(self.change_path(item)), encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None

    def save(self, change):
        self.changes_dir.mkdir(parents=True, exist_ok=True)
        change["updated"] = time.time()
        path = self.change_path(change["item"])
        tmp = path.with_name(path.name + ".tmp{}".format(os.getpid()))
        tmp.write_text(json.dumps(change, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(path))

    def changes(self):
        if not self.changes_dir.is_dir():
            return []
        out = []
        for f in sorted(self.changes_dir.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
        return out

    def current_change(self, item=None):
        """The change named `item`, or the one whose worktree holds the cwd."""
        if item:
            change = self.load(item)
            if change is None:
                raise LockmasterError("no change " + item + " — `lockmaster start " + item + " --paths …` first")
            return change
        here = os.path.realpath(str(self.cwd))
        for change in self.changes():
            wt = os.path.realpath(change.get("worktree", ""))
            if change["status"] in LIVE and (here == wt or here.startswith(wt + os.sep)):
                return change
        raise LockmasterError("not inside a change's worktree; name the item (--item W-nn)")

    def worktree_for(self, item):
        return self.root / WORKTREES_DIR / item

    def exclude_worktrees(self):
        """Keep `.claude/worktrees/` out of the primary checkout's status,
        locally (`info/exclude`), so no tracked file has to change."""
        info = self.common / "info"
        info.mkdir(exist_ok=True)
        exclude = info / "exclude"
        text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        line = "/" + WORKTREES_DIR + "/"
        if line not in text.split("\n"):
            with exclude.open("a", encoding="utf-8") as fh:
                fh.write(("" if text.endswith("\n") or not text else "\n") + line + "\n")


# ---------------------------------------------------------------- claims

def norm(path):
    p = path.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/") if p not in ("", "/") else p


def claimed(path, claims):
    """A path is claimed when a claim names it, a directory above it, or a glob matching it."""
    path = norm(path)
    for c in claims:
        c = norm(c)
        if c in ("", ".", "*", "**"):
            return True
        if path == c or path.startswith(c + "/"):
            return True
        if any(ch in c for ch in "*?[") and (fnmatch.fnmatchcase(path, c) or fnmatch.fnmatchcase(path, c + "/*")):
            return True
    return False


def matches(path, pattern):
    """For [generated] and [merge]: a path equals the pattern, sits under it, or matches its glob."""
    return claimed(path, [pattern])


# ---------------------------------------------------------------- the land lock

def pid_alive(pid):
    if os.name == "nt":  # os.kill(pid, 0) would send CTRL_C_EVENT on Windows
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


class LandLock:
    """Decision 7: one lander at a time. A `mkdir` mutex; its `pid` file names
    the holder. A lock whose holder is dead is stale: it is moved aside
    (atomically, so only one lander wins it) and taken."""

    def __init__(self, repo):
        self.dir = repo.state / "land.lock"
        self.held = False

    def holder(self):
        try:
            return int((self.dir / "pid").read_text().strip())
        except (OSError, ValueError):
            return None

    def stale(self):
        if not self.dir.is_dir():
            return False
        pid = self.holder()
        if pid is None:
            # Created but no pid yet: stale only once it is old.
            try:
                return time.time() - self.dir.stat().st_mtime > 60
            except OSError:
                return False
        return not pid_alive(pid)

    def acquire(self):
        self.dir.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                self.dir.mkdir()
            except FileExistsError:
                if not self.stale():
                    return False
                aside = self.dir.with_name("land.lock.stale.{}.{}".format(os.getpid(), int(time.time())))
                try:
                    os.rename(str(self.dir), str(aside))
                except OSError:
                    return False
                for f in aside.iterdir():
                    f.unlink()
                aside.rmdir()
                continue
            (self.dir / "pid").write_text(str(os.getpid()))
            self.held = True
            return True
        return False

    def release(self):
        if not self.held:
            return
        try:
            (self.dir / "pid").unlink()
        except OSError:
            pass
        try:
            self.dir.rmdir()
        except OSError:
            pass
        self.held = False
