"""`lockmaster status` — SR-ARCHITECTURE decision 14: what is live, from git
and lockmaster's state, never from a hand-edited file.

    sessions   work/NOW.md's In flight rows, with each one's last heartbeat
    changes    every live change: status, branch, worktree, claim
    worktrees  every git worktree, and the change it belongs to
    disk       the project's size against work/MACHINE.md's budget (SR-LAW-2)
"""
import json
import os
import re
import time
from pathlib import Path

from lockmaster import git
from lockmaster import now as now_mod
from lockmaster.repo import LIVE

BUDGET_RE = re.compile(r"^\|\s*budget\s*\|\s*([0-9.]+)\s*GB", re.M)


def disk_bytes(root):
    total = 0
    for d, dirs, files in os.walk(str(root)):
        for f in files:
            try:
                total += os.lstat(os.path.join(d, f)).st_size
            except OSError:
                pass
    return total


def budget_gb(root):
    try:
        m = BUDGET_RE.search((Path(root) / "work" / "MACHINE.md").read_text(encoding="utf-8"))
    except OSError:
        return None
    return float(m.group(1)) if m else None


def heartbeat(root, sid):
    f = Path(root) / ".claude" / ".sessions" / (re.sub(r"[^A-Za-z0-9_.-]", "_", sid) + ".json")
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("beat")
    except (OSError, ValueError):
        return None


def ago(t):
    s = int(time.time() - t)
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return "{}{} ago".format(s // n, unit)
    return "{}s ago".format(s)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "{:.1f} {}".format(n, unit) if unit != "B" else "{} B".format(n)
        n /= 1024.0


def report(repo):
    lines = []
    now_file = now_mod.now_path(repo.root)
    lines.append("sessions")
    if now_file.is_file():
        _, flight, _ = now_mod.parse(now_file.read_text(encoding="utf-8"))
        for r in flight:
            sid = r[0].strip("`")
            beat = heartbeat(repo.root, sid)
            lines.append("  {} · {} · started {} · {} · {}".format(
                sid, r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "",
                (r[3] if len(r) > 3 and r[3] else "(working on: empty)"),
                "heartbeat " + ago(beat) if beat else "no heartbeat"))
        if not flight:
            lines.append("  none")
    else:
        lines.append("  (no work/NOW.md)")

    lines.append("changes")
    live = [c for c in repo.changes() if c["status"] in LIVE]
    for c in sorted(live, key=lambda c: c["item"]):
        lines.append("  {} {} {} {} · claims {}".format(c["item"], c["status"], c["branch"], c["worktree"],
                                                       ", ".join(c["paths"])))
        if c.get("reason"):
            lines.append("    " + c["reason"].splitlines()[0])
    if not live:
        lines.append("  none")

    lines.append("worktrees")
    by_path = {os.path.realpath(c["worktree"]): c for c in live}
    for t in git.worktrees(repo.root):
        c = by_path.get(os.path.realpath(t["path"]))
        label = "main checkout" if os.path.realpath(t["path"]) == os.path.realpath(str(repo.root)) else (
            "change " + c["item"] if c else "not a live change's")
        lines.append("  {} [{}] {}".format(t["path"], t["branch"] or "detached", label))

    size, gb = disk_bytes(repo.root), budget_gb(repo.root)
    if gb:
        lines.append("disk\n  {} of the {:g} GB budget ({:.0f} %)".format(human(size), gb, 100.0 * size / (gb * 1024 ** 3)))
    else:
        lines.append("disk\n  {} (no budget row in work/MACHINE.md)".format(human(size)))
    return lines


def now_text(repo):
    path = now_mod.now_path(repo.root)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return now_mod.render(text, repo.root)
