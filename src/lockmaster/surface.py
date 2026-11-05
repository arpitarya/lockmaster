"""Can this surface commit? — SR-ARCHITECTURE decision 19.

A landing writes git's lock files and removes them, creates worktrees and
prunes the ones whose paths are gone. Two surfaces cannot do that safely:

- **a shell that cannot unlink** (the Cowork bridge until the decider allows
  deletes): git's own lock files are left behind and every git write fails;
- **a checkout mounted from elsewhere** (the Cowork bridge sees the Mac's
  repository under another path): the host's worktrees look missing from
  here, so a `git worktree prune` here would cut them off.

On such a surface lockmaster commits nothing: `lockmaster save` hands the
edits to the next surface that can (`handoff`, `pickup` in land.py).

`home` is the primary checkout's path on the surface that commits, kept at
`<git-common-dir>/lockmaster/home`. When it is not yet written, it is read off
the worktree paths of lockmaster's own changes.
"""
import os
from pathlib import Path

from lockmaster import git
from lockmaster.repo import WORKTREES_DIR

PROBE = "probe"
HOME = "home"


def can_unlink(repo):
    """Write a probe file in the state directory and remove it. The probe has
    one fixed name, so a surface that cannot remove it leaves one file, never
    a pile."""
    repo.state.mkdir(parents=True, exist_ok=True)
    probe = repo.state / PROBE
    try:
        probe.write_text("lockmaster probe\n", encoding="utf-8")
    except OSError:
        return False
    try:
        probe.unlink()
    except OSError:
        return False
    return True


def recorded_home(repo):
    """The primary checkout's path where lockmaster committed, or None."""
    try:
        text = (repo.state / HOME).read_text(encoding="utf-8").strip()
        if text:
            return text
    except OSError:
        pass
    tail = Path(WORKTREES_DIR).parts
    for change in repo.changes():
        wt = Path(change.get("worktree") or "")
        parts = wt.parts
        if len(parts) > len(tail) + 1 and parts[-len(tail) - 1:-1] == tail:
            return str(Path(*parts[:-len(tail) - 1]))
    return None


def foreign(repo):
    """The reason this checkout is another host's, seen through a mount; or None.

    Only evidence counts: git lists worktrees that do not exist here, outside
    this checkout, under the recorded home or at a `.claude/worktrees/` path —
    the ones a prune from this surface would cut off. A worktree of this
    checkout's own that was deleted by hand is not evidence."""
    here = os.path.realpath(str(repo.root))
    home = recorded_home(repo)
    if home and os.path.realpath(home) == here:
        home = None
    marker = "/" + WORKTREES_DIR + "/"
    cut = []
    for t in git.worktrees(repo.root):
        p = t["path"]
        if os.path.isdir(p) or os.path.realpath(p) == here or p.startswith(here + "/"):
            continue
        if (home and (p == home or p.startswith(home.rstrip("/") + "/"))) or marker in p:
            cut.append(p)
    if not cut:
        return None
    where = home or os.path.dirname(cut[0].split(marker)[0] + "/") or cut[0]
    return ("this checkout ({}) is {} seen from another machine; {} of its worktree{} would be "
            "cut off by a landing here").format(here, where, len(cut), "s" * (len(cut) != 1))


def can_commit(repo):
    """(True, "") on a surface that may land; else (False, the reason)."""
    if not can_unlink(repo):
        return False, "this shell cannot remove files, so git cannot commit here"
    why = foreign(repo)
    if why:
        return False, why
    home = repo.state / HOME
    try:
        if not home.is_file():  # written once: a later surface never moves it
            home.write_text(os.path.realpath(str(repo.root)) + "\n", encoding="utf-8")
    except OSError:
        pass
    return True, ""
