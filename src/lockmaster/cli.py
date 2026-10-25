"""The `lockmaster` command — SR-ARCHITECTURE decision 14.

A stub: it names every command and the work item that builds it, and builds
none of them yet. Python >= 3.9, standard library only (decision 2).
"""
import argparse
import sys

from lockmaster import __version__

# command -> (what it does, the work item that builds it)
COMMANDS = {
    "start": ("branch + worktree + claim for a work item", "W-04"),
    "claim": ("widen the claim: claim add <path>", "W-04"),
    "submit": ("queue the change", "W-04"),
    "run": ("land queued changes, one at a time", "W-04"),
    "queue": ("what is waiting, landed or red", "W-04"),
    "status": ("live sessions, worktrees, disk use; work/NOW.md's source", "W-07"),
    "abandon": ("drop a change; remove its worktree only if nothing is lost", "W-04"),
    "doctor": ("stale locks, orphan worktrees, unmerged branches", "W-06"),
    "install": ("install a pinned kit into a repository", "W-06"),
    "regen": ("rebuild the generated files lockmaster.toml lists", "W-03"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="lockmaster",
        description="Lands AI-agent changes into main one at a time, without ever losing work.",
    )
    parser.add_argument("--version", action="version", version="lockmaster " + __version__)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    for name, (what, item) in COMMANDS.items():
        sub.add_parser(name, help=what + "  [not built: " + item + "]")
    args, _ = parser.parse_known_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    what, item = COMMANDS[args.command]
    print("lockmaster " + args.command + ": not built yet — " + item + " in work/OPEN-WORK.md builds it.",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
