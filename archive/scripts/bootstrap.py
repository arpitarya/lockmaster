#!/usr/bin/env python3
"""Install kit/ into THIS repository — SR-ARCHITECTURE decision 15.

    python3 scripts/bootstrap.py

Until `lockmaster install` exists (W-06), this is how lockmaster's own work
system is installed:

  1. kit/claude/**  ->  .claude/**   (hooks made executable; settings.local.json untouched)
  2. kit/github/**  ->  .github/**
  3. the commit guard: .git/hooks/commit-msg -> scripts/sr-guard.sh
  4. records/RULE-SINCE gets the current HEAD once a first commit exists
  5. the checks: unit tests, check-work-system.py, check-open-work-inbox.py

Edit kit/, never the installed copies: every run overwrites them. Run it on
the Mac (or any terminal) — the Cowork bridge may not write .claude/ or .github/.
Idempotent. Python >= 3.9, standard library only.
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def copy_tree(src, dst):
    n = 0
    for f in sorted(src.rglob("*")):
        if f.is_dir() or "__pycache__" in f.parts:
            continue
        out = dst / f.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(f), str(out))
        if out.suffix in (".sh", ".py") and "hooks" in out.parts:
            out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        n += 1
    return n


def main():
    print("lockmaster bootstrap — installing kit/ into " + str(ROOT))
    print("  .claude/: {} files".format(copy_tree(ROOT / "kit" / "claude", ROOT / ".claude")))
    print("  .github/: {} files".format(copy_tree(ROOT / "kit" / "github", ROOT / ".github")))
    guard = ROOT / "scripts" / "sr-guard.sh"
    guard.chmod(guard.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    code, common = git("rev-parse", "--git-common-dir")
    if code == 0:
        hooks = (ROOT / common).resolve() / "hooks"
        hooks.mkdir(exist_ok=True)
        link = hooks / "commit-msg"
        if link.is_symlink() or link.exists():
            print("  commit guard: .git/hooks/commit-msg already present — left as it is")
        else:
            os.symlink("../../scripts/sr-guard.sh", str(link))
            print("  commit guard: installed (.git/hooks/commit-msg -> scripts/sr-guard.sh)")
        since = ROOT / "records" / "RULE-SINCE"
        has_sha = any(l.strip() and not l.startswith("#") for l in since.read_text().splitlines())
        code, head = git("rev-parse", "--verify", "--quiet", "HEAD")
        if not has_sha and code == 0 and head:
            with since.open("a") as fh:
                fh.write(head + "\n")
            print("  records/RULE-SINCE: baseline " + head[:8] + " written — commit it")
        elif not has_sha:
            print("  records/RULE-SINCE: no commit yet — run this again after the first commit")
    else:
        print("  not a git repository — guard and RULE-SINCE skipped")

    print("\nchecks:")
    ok = True
    for cmd in ([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"],
                [sys.executable, "-B", "scripts/check-work-system.py"],
                [sys.executable, "-B", "scripts/check-open-work-inbox.py"]):
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        name = " ".join(cmd[2:])
        print("  {} {}".format("ok  " if r.returncode == 0 else "FAIL", name))
        if r.returncode != 0:
            ok = False
            print("    " + (r.stdout + r.stderr).strip().replace("\n", "\n    "))
    print("\nnext: git add -A && git commit -m \"lockmaster: the repository set up\" && python3 scripts/bootstrap.py"
          if ok else "\nfix the failures above, then run this again")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
