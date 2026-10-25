"""The `lockmaster` command — SR-ARCHITECTURE decision 14.

Python >= 3.9, standard library only (decision 2). Exit codes: 0 done, 1 a
change went red or a check found a problem, 2 refused or misused.
"""
import argparse
import os
import sys

from lockmaster import __version__

# command -> what it does (decision 14's table)
COMMANDS = {
    "start": "branch + worktree + claim for a work item",
    "claim": "widen the claim: claim add <path>…",
    "submit": "commit the claimed paths, join the queue, start landing",
    "run": "land queued changes, one at a time",
    "queue": "what is waiting, landed or red",
    "status": "live sessions, changes, worktrees, disk use; --now prints work/NOW.md",
    "abandon": "drop a change; remove its worktree only if nothing is lost",
    "doctor": "stale locks, orphan worktrees, unmerged branches, kit mismatch",
    "install": "install the kit into a repository, pinned",
    "regen": "rebuild the generated files lockmaster.toml lists",
    "drivers": "register the structural merge drivers; write .gitattributes from [merge]",
    "merge-driver": "what git runs for a structural merge (installed by `drivers`)",
}


def _parser():
    p = argparse.ArgumentParser(prog="lockmaster",
                                description="Lands AI-agent changes into main one at a time, without ever losing work.")
    p.add_argument("--version", action="version", version="lockmaster " + __version__)
    sub = p.add_subparsers(dest="command", metavar="<command>")

    s = sub.add_parser("start", help=COMMANDS["start"])
    s.add_argument("item")
    s.add_argument("--paths", nargs="+", required=True, metavar="PATH")

    s = sub.add_parser("claim", help=COMMANDS["claim"])
    s.add_argument("action", choices=["add"])
    s.add_argument("paths", nargs="+")
    s.add_argument("--item")

    s = sub.add_parser("submit", help=COMMANDS["submit"])
    s.add_argument("-m", "--message", default="")
    s.add_argument("--item")
    s.add_argument("--no-run", action="store_true", help="queue only; do not start landing")

    sub.add_parser("run", help=COMMANDS["run"])
    sub.add_parser("queue", help=COMMANDS["queue"])

    s = sub.add_parser("status", help=COMMANDS["status"])
    s.add_argument("--now", action="store_true", help="print work/NOW.md as it should be")
    s.add_argument("--write-now", action="store_true", help="write work/NOW.md")

    s = sub.add_parser("abandon", help=COMMANDS["abandon"])
    s.add_argument("--item")

    sub.add_parser("doctor", help=COMMANDS["doctor"])

    s = sub.add_parser("install", help=COMMANDS["install"])
    s.add_argument("repo", nargs="?", default=".")
    s.add_argument("--backup", action="store_true",
                   help="move each file the kit would replace aside to <file>.pre-lockmaster")

    sub.add_parser("regen", help=COMMANDS["regen"])
    sub.add_parser("drivers", help=COMMANDS["drivers"])

    s = sub.add_parser("merge-driver", help=COMMANDS["merge-driver"])
    s.add_argument("args", nargs=argparse.REMAINDER)
    return p


def main(argv=None):
    from lockmaster.config import ConfigError
    from lockmaster.repo import LockmasterError

    args = _parser().parse_args(argv)
    if not args.command:
        _parser().print_help()
        return 0
    try:
        return _dispatch(args)
    except (LockmasterError, ConfigError) as e:
        print("lockmaster {}: {}".format(args.command, e), file=sys.stderr)
        return 2


def _out(text):
    print(text)


def _dispatch(args):
    from lockmaster import land
    from lockmaster.repo import Repo

    if args.command == "merge-driver":
        from lockmaster import merge
        return merge.main(args.args)
    if args.command == "install":
        from lockmaster import install
        install.install(args.repo, backup=args.backup, out=_out)
        return 0

    repo = Repo(os.getcwd())
    if args.command == "start":
        change, overlaps = land.start(repo, args.item, args.paths, os.environ.get("CLAUDE_SESSION_ID", ""))
        print("started {} on {}: work in {}".format(change["item"], change["branch"], change["worktree"]))
        print("claim: " + ", ".join(change["paths"]))
        for other, path in overlaps:
            print("note: {} also claims {} — whichever lands second may go red".format(other, path))
        return 0
    if args.command == "claim":
        change = land.claim_add(repo, repo.current_change(args.item), args.paths)
        print("claim of {}: {}".format(change["item"], ", ".join(change["paths"])))
        return 0
    if args.command == "submit":
        change = land.submit(repo, repo.current_change(args.item), args.message, out=_out)
        print("queued " + change["item"])
        if args.no_run:
            return 0
        land.run(repo, out=_out)
        return 1 if repo.load(change["item"])["status"] == "red" else 0
    if args.command == "run":
        land.run(repo, out=_out)
        return 0
    if args.command == "queue":
        print("\n".join(land.queue_lines(repo)))
        return 0
    if args.command == "abandon":
        land.abandon(repo, repo.current_change(args.item), out=_out)
        return 0
    if args.command == "status":
        from lockmaster import now, status
        if args.write_now:
            print("work/NOW.md " + ("written" if now.write_if_present(repo) else "not kept here"))
            return 0
        if args.now:
            sys.stdout.write(status.now_text(repo))
            return 0
        print("\n".join(status.report(repo)))
        return 0
    if args.command == "doctor":
        from lockmaster import doctor
        problems = doctor.check(repo)
        print("\n".join(problems) if problems else "all well")
        return 1 if problems else 0
    if args.command == "regen":
        from lockmaster import generated
        done = generated.regen(repo.toplevel, repo.config)
        print("rebuilt: " + (", ".join(done) if done else "nothing — lockmaster.toml lists no [generated] paths"))
        return 0
    if args.command == "drivers":
        from lockmaster import drivers
        changed = drivers.install(repo)
        print("merge drivers registered in .git/config"
              + ("; .gitattributes written — commit it" if changed else ""))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
