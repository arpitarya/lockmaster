"""Thin wrappers over the `git` command — SR-ARCHITECTURE decision 1.

Every git operation lockmaster runs goes through `run`, so the forbidden forms
of SR-LAW-3 decision 3 have one place to be kept out of. Nothing here forces.
"""
import os
import subprocess

#: `-c core.hooksPath=…` while a Repo is open: lockmaster's own git steps run the
#: repository's gate hooks and not its post-* hooks (SR-ARCHITECTURE decision 18).
HOOKS = []


class GitError(Exception):
    """A git command exited non-zero."""

    def __init__(self, args, code, out, err):
        self.args_ = args
        self.code = code
        self.out = out
        self.err = err
        super().__init__("git {} exited {}: {}".format(" ".join(args), code, (err or out).strip()))


def run(args, cwd, check=True, env=None, input=None):
    """Run `git <args>` in `cwd`; return stdout. With check=False, return
    (code, stdout, stderr) instead of raising."""
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    r = subprocess.run(["git"] + HOOKS + list(args), cwd=str(cwd), capture_output=True, text=True,
                       env=full_env, input=input)
    if not check:
        return r.returncode, r.stdout, r.stderr
    if r.returncode != 0:
        raise GitError(list(args), r.returncode, r.stdout, r.stderr)
    return r.stdout


def out(args, cwd, env=None):
    """stdout of a git command, stripped."""
    return run(args, cwd, env=env).strip()


def ok(args, cwd):
    """True when the git command exits 0."""
    return run(args, cwd, check=False)[0] == 0


def worktrees(cwd):
    """Every worktree of the repository: dicts of path, head, branch, locked."""
    trees, cur = [], None
    for line in run(["worktree", "list", "--porcelain"], cwd).splitlines() + [""]:
        if not line:
            if cur:
                trees.append(cur)
            cur = None
            continue
        key, _, val = line.partition(" ")
        if key == "worktree":
            cur = {"path": val, "head": "", "branch": "", "locked": None}
        elif cur is None:
            continue
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val[len("refs/heads/"):] if val.startswith("refs/heads/") else val
        elif key == "locked":
            cur["locked"] = val
    return trees


def dirty(cwd):
    """`git status --porcelain` lines: modified, staged, deleted or untracked."""
    return [l for l in run(["status", "--porcelain", "--untracked-files=all"], cwd).splitlines() if l]
