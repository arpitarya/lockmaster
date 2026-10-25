"""Installing the structural merge drivers — SR-ARCHITECTURE decision 10.

Each driver is registered in the repository's `.git/config` as
`merge.lockmaster-<driver>`, and `.gitattributes` gets one line per
`lockmaster.toml` `[merge]` path, inside a block lockmaster owns. Usable from
plain git: `git merge` and `git cherry-pick` call the drivers too.
"""
import shlex
import sys
from pathlib import Path

from lockmaster import git
from lockmaster.merge import DRIVERS

BEGIN = "# lockmaster:begin — written by `lockmaster drivers` from lockmaster.toml [merge]; edit that, not this"
END = "# lockmaster:end"


def driver_command(name):
    script = Path(__file__).with_name("merge.py").resolve()
    return "{} {} {} %O %A %B %P".format(shlex.quote(sys.executable), shlex.quote(str(script)), name)


def attributes_block(merge):
    lines = [BEGIN]
    for path, driver in merge.items():
        if any(c.isspace() for c in path):
            raise ValueError("a [merge] path with whitespace cannot go into .gitattributes: " + path)
        lines.append("{} merge=lockmaster-{}".format(path, driver))
    return lines + [END]


def write_attributes(root, merge):
    """Replace lockmaster's block in `.gitattributes` (or add it); everything
    else in the file is kept as it is. Returns True when the file changed."""
    path = Path(root) / ".gitattributes"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = old.splitlines()
    if BEGIN.split(" —")[0] in "\n".join(lines):
        start = next(i for i, l in enumerate(lines) if l.startswith(BEGIN.split(" —")[0]))
        end = next((i for i in range(start, len(lines)) if lines[i] == END), len(lines) - 1)
        lines = lines[:start] + lines[end + 1:]
    while lines and not lines[-1].strip():
        lines.pop()
    block = attributes_block(merge) if merge else []
    new_lines = lines + ([""] if lines and block else []) + block
    new = "\n".join(new_lines) + ("\n" if new_lines else "")
    if new == old:
        return False
    if new:
        path.write_text(new, encoding="utf-8")
    elif path.exists():
        path.write_text("", encoding="utf-8")
    return True


def install(repo):
    """Register every driver in .git/config; write .gitattributes from [merge]."""
    for name in DRIVERS:
        key = "merge.lockmaster-" + name
        git.run(["config", key + ".name", "lockmaster " + name + " (SR-ARCHITECTURE decision 10)"], repo.root)
        git.run(["config", key + ".driver", driver_command(name)], repo.root)
    changed = write_attributes(repo.root, repo.config.merge)
    return changed
