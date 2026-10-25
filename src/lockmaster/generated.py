"""Generated files are never merged, only rebuilt — SR-ARCHITECTURE decision 9.

`lockmaster.toml` `[generated]` maps a path or glob to the command that
rebuilds it. `regen` restores each such file to `main`'s version, then runs
its command; a command that fails fails the run.

A generated file with uncommitted edits is not overwritten: that would be
`checkout --` over changes (SR-LAW-3 decision 3). It is refused, by name, and
nothing is touched until it is committed or put back.
"""
import subprocess
from pathlib import Path

from lockmaster import git
from lockmaster.repo import LockmasterError, matches


class RegenError(LockmasterError):
    pass


def _tracked(worktree, ref, pattern):
    names = git.run(["ls-tree", "-r", "--name-only", "-z", ref], worktree).split("\0")
    return [n for n in names if n and matches(n, pattern)]


def regen(worktree, config, ref=None):
    """Rebuild every [generated] path in `worktree`. Returns the patterns rebuilt."""
    worktree = Path(worktree)
    ref = ref or config.main
    if not config.generated:
        return []
    restore, refused = [], []
    for pattern in config.generated:
        for name in _tracked(worktree, ref, pattern):
            if git.run(["status", "--porcelain", "--", name], worktree).strip():
                refused.append(name)
            else:
                restore.append(name)
    if refused:
        raise RegenError("generated files with uncommitted edits — commit them or put them back, "
                         "then run again: " + ", ".join(refused))
    for name in restore:
        blob = subprocess.run(["git", "show", ref + ":" + name], cwd=str(worktree),
                              capture_output=True, check=True).stdout
        target = worktree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != blob:
            target.write_bytes(blob)
    done = []
    for pattern, command in config.generated.items():
        r = subprocess.run(command, shell=True, cwd=str(worktree), capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
            raise RegenError("rebuilding `{}` with `{}` exited {}:\n  {}".format(
                pattern, command, r.returncode, "\n  ".join(tail)))
        done.append(pattern)
    return done


def stage(worktree, config):
    """Stage whatever the rebuild changed under the [generated] patterns."""
    for pattern in config.generated:
        spec = ":(glob)" + pattern if any(c in pattern for c in "*?[") else pattern
        git.run(["add", "-A", "--", spec], worktree, check=False)
