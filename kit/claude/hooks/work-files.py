#!/usr/bin/env python3
"""The work files stay current — lockmaster's SR-LAW-10 decision 4, at the source (W-15).

    edit  PostToolUse(Write|Edit|MultiEdit|NotebookEdit)  note the path this
          session wrote, relative to its own checkout or worktree
    stop  Stop  a session that wrote files outside `work/` and touched none of
          work/WORKLOG.md, work/INTERVIEW.md, work/OPEN-WORK.md is told once,
          before it stops, to update them in the same change

The notes live in git's own directory (`<git-common-dir>/lockmaster/sessions/`),
never in the tree. Whether a lesson, a machine quirk or a backlog row should
have been written is judgment; this hook does not judge it. A Stop reached
while already continuing for a Stop hook never blocks again. It never fails a
session. Python >= 3.9, standard library only; it does not need lockmaster.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHED = ("work/WORKLOG.md", "work/INTERVIEW.md", "work/OPEN-WORK.md")


def notes_file(sid):
    try:
        r = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=str(ROOT), capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    common = Path(r.stdout.strip())
    common = common if common.is_absolute() else (ROOT / common).resolve()
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in sid)
    return common / "lockmaster" / "sessions" / (safe + ".work-files.json")


def read(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"paths": []}


def write(f, notes):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".part")
    tmp.write_text(json.dumps(notes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def relative(path):
    """`path` relative to the checkout or worktree holding it — this repository's
    main checkout or one of its `.claude/worktrees/` — else None."""
    root = os.path.realpath(str(ROOT))
    full = os.path.realpath(str(path))
    if not full.startswith(root + os.sep):
        return None
    rel = os.path.relpath(full, root).replace(os.sep, "/")
    if rel.startswith(".claude/worktrees/"):
        parts = rel.split("/")
        if len(parts) < 4:
            return None
        rel = "/".join(parts[3:])
    return rel


def edit(sid, hook):
    raw = (hook.get("tool_input") or {}).get("file_path") or (hook.get("tool_input") or {}).get("notebook_path")
    f = notes_file(sid) if raw and sid else None
    if f is None:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = Path(hook.get("cwd") or os.getcwd()) / p
    rel = relative(p)
    if rel is None:
        return None
    notes = read(f)
    if rel not in notes["paths"]:
        notes["paths"].append(rel)
        write(f, notes)
    return None


def stop(sid, hook):
    f = notes_file(sid) if sid else None
    if f is None or hook.get("stop_hook_active"):
        return None
    if not any((ROOT / w).is_file() for w in WATCHED):
        return None  # no work system here yet: `lockmaster doctor` names that (SR-LAW-10 decision 6)
    notes = read(f)
    paths = notes.get("paths") or []
    outside = [p for p in paths if not p.startswith("work/")]
    if not outside or any(p in WATCHED for p in paths) or notes.get("told"):
        return None
    notes["told"] = True
    write(f, notes)
    shown = ", ".join(outside[:5]) + (" and {} more".format(len(outside) - 5) if len(outside) > 5 else "")
    return {"decision": "block", "reason": (
        "This session changed {} but none of work/WORKLOG.md, work/INTERVIEW.md or work/OPEN-WORK.md. "
        "The work files travel with the work they describe (lockmaster's L10): update the queue row, the "
        "state of play and this session's worklog entry in the same change, then stop.").format(shown)}


def main(argv):
    mode = argv[0] if argv else ""
    fn = {"edit": edit, "stop": stop}.get(mode)
    if fn is None:
        print("usage: work-files.py edit|stop", file=sys.stderr)
        return 0
    try:
        hook = json.loads(sys.stdin.read() or "{}") if not sys.stdin.isatty() else {}
    except ValueError:
        hook = {}
    try:
        result = fn(hook.get("session_id") or os.environ.get("CLAUDE_SESSION_ID", ""), hook)
    except Exception as e:  # noqa: BLE001 — never fail the session over a nudge
        print("work-files.py {}: {}".format(mode, e), file=sys.stderr)
        return 0
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
