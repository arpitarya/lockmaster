"""`work/NOW.md` as a generated view — SR-ARCHITECTURE decision 14, SR-WORK-NOW decisions 2-5.

The sessions in `## In flight` are the sessions' own (now-ledger.py adds and
closes them, a Cowork session by hand). What is computed is everything else:
a resource row whose path is gone leaves, and the file is always written in
one canonical shape. `render` is that computation; `lockmaster status --now`
prints it, every landing writes it, and the kit's now-ledger.py writes
through it, so NOW.md equals `lockmaster status --now` after each of them.
"""
import os
import re
from pathlib import Path

FLIGHT_HEAD = "| session | surface | started | working on |"
RES_HEAD = "| kind | where | host | session | created |"
# Rows whose `where` is a path on this host: dropped once the path is gone.
PATH_KINDS = {"worktree", "files", "folder", "dir", "clone", "build"}
DEFAULT_HEAD = """---
type: Pointer
description: "Only what is being worked on right now: one row per live session, plus what those sessions created and have not yet cleaned. Empty when nothing is running."
---

# NOW
"""


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(text):
    """(prose before the tables, flight rows, resource rows) — rows as cell lists."""
    head, _, _ = text.partition("## In flight")
    flight, res, section = [], [], None
    for line in text.splitlines():
        if line.startswith("## In flight"):
            section = flight
        elif line.startswith("## Resources"):
            section = res
        elif section is not None and line.startswith("|") and not line.startswith("|---"):
            c = cells(line)
            if c[0] in ("session", "kind"):
                continue
            section.append(c)
    return (head.rstrip() + "\n") if head.strip() else DEFAULT_HEAD, flight, res


def where_path(cell, root):
    m = re.search(r"`([^`]+)`", cell)
    if not m:
        return None
    p = Path(m.group(1).rstrip("/"))
    return p if p.is_absolute() else Path(root) / p


def normalise(res, root):
    return [r for r in res if not (r and r[0] in PATH_KINDS and len(r) > 1
                                   and (p := where_path(r[1], root)) is not None and not p.exists())]


def format_now(head, flight, res):
    def table(header, rows, n):
        out = [header, "|" + "---|" * n]
        out += ["| " + " | ".join((list(r) + [""] * n)[:n]) + " |" for r in rows]
        return "\n".join(out)

    return "{}\n## In flight\n\n{}\n\n## Resources this session created\n\n{}\n".format(
        head, table(FLIGHT_HEAD, flight, 4), table(RES_HEAD, res, 5))


def render(text, root):
    """NOW.md's text as it should be, given its current text."""
    head, flight, res = parse(text)
    return format_now(head, flight, normalise(res, root))


def now_path(root):
    return Path(root) / "work" / "NOW.md"


def write_if_present(repo):
    """Rewrite work/NOW.md in the primary checkout, when the repository keeps one."""
    path = now_path(repo.root)
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    new = render(text, repo.root)
    if new != text:
        tmp = path.with_name(".NOW.md.tmp")
        tmp.write_text(new, encoding="utf-8")
        os.replace(str(tmp), str(path))
    return True
