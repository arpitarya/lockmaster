#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit|NotebookEdit) — SR-ARCHITECTURE decision 5.

A write inside a lockmaster change's worktree to a path outside its claim is
WARNED, not refused: the hook prints the claim and the path, to the session
and to the person watching. Only claimed paths land; the rest is left behind,
so the agent should know before it writes, not after it submits.

A write in the primary checkout to a path a live change claims is WARNED too
(W-10): that uncommitted edit would make the change's landing wait. Edit it in
the change's worktree, or land it with `lockmaster save`. `work/NOW.md`, the
live ledger, is left out: it is always edited there.

The claim is read from lockmaster's state, `$(git rev-parse
--git-common-dir)/lockmaster/changes/<item>.json`. A write anywhere else (a
worktree that is no change's) is not this hook's business.
Standard library only; it does not need lockmaster installed.
"""
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

LIVE = ("open", "queued", "landing", "waiting", "red")
LEDGER = "work/NOW.md"


def norm(path):
    p = path.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/") if p not in ("", "/") else p


def claimed(path, claims):
    """The same rule as lockmaster's repo.claimed: a claim names the path, a
    directory above it, or a glob matching it."""
    path = norm(path)
    for c in map(norm, claims):
        if c in ("", ".", "*", "**") or path == c or path.startswith(c + "/"):
            return True
        if any(ch in c for ch in "*?[") and (fnmatch.fnmatchcase(path, c) or fnmatch.fnmatchcase(path, c + "/*")):
            return True
    return False


def git(args, cwd):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _locate(file_path):
    """(live changes, the worktree's top, its path there, whether it is the primary checkout)."""
    d = file_path.parent
    while not d.is_dir() and d != d.parent:
        d = d.parent
    top = git(["rev-parse", "--show-toplevel"], str(d))
    common = git(["rev-parse", "--git-common-dir"], str(d))
    if not top or not common:
        return [], None, None, False
    common = Path(common) if os.path.isabs(common) else Path(d) / common
    changes = common / "lockmaster" / "changes"
    if not changes.is_dir():
        return [], None, None, False
    live = []
    for f in sorted(changes.glob("*.json")):
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if c.get("status") in LIVE:
            live.append(c)
    real_top = os.path.realpath(top)
    rel = norm(os.path.join(os.path.relpath(os.path.realpath(str(file_path.parent)), real_top), file_path.name))
    listing = git(["worktree", "list", "--porcelain"], str(d)) or ""
    first = listing.splitlines()[0][len("worktree "):] if listing.startswith("worktree ") else ""
    return live, real_top, rel, bool(first) and os.path.realpath(first) == real_top


def change_for(file_path):
    """(change, path relative to its worktree) when `file_path` is inside a live change's worktree."""
    live, top, rel, _ = _locate(file_path)
    for c in live:
        if os.path.realpath(c.get("worktree", "")) == top:
            return c, rel
    return None, None


def claimants_in_checkout(file_path):
    """(path, [live changes claiming it]) when `file_path` is in the primary checkout."""
    live, top, rel, primary = _locate(file_path)
    if not primary or rel == LEDGER or rel.startswith(".claude/worktrees/"):
        return rel, []
    return rel, [c for c in live if os.path.realpath(c.get("worktree", "")) != top
                 and claimed(rel, c.get("paths", []))]


def main():
    try:
        hook = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    tool_input = hook.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw:
        return 0
    p = Path(raw)
    if not p.is_absolute():
        p = Path(hook.get("cwd") or os.getcwd()) / p
    change, rel = change_for(p)
    if change is None:
        rel, others = claimants_in_checkout(p)
        if not others:
            return 0
        msg = ("lockmaster: {} claims `{}`; edit it in its worktree ({}) or land this edit through lockmaster "
               "(`lockmaster save`). Left uncommitted here, it makes {} wait to land.").format(
            " and ".join(c["item"] for c in others), rel,
            ", ".join(c.get("worktree", "?") for c in others), "that change" if len(others) == 1 else "them")
    elif claimed(rel, change.get("paths", [])):
        return 0
    else:
        msg = ("lockmaster: `{}` is outside the claim of {} ({}). It will be left behind, not landed. "
               "If it belongs to this change: `lockmaster claim add {}`.").format(
            rel, change["item"], ", ".join(change.get("paths", [])) or "nothing claimed", rel)
    print(json.dumps({"systemMessage": msg,
                      "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
