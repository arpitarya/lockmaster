"""`lockmaster doctor` — SR-ARCHITECTURE decision 14: stale locks, orphan
worktrees, unmerged branches, and an installed kit that does not match this
lockmaster's. Read-only: it says what is wrong and what to type, and fixes nothing.
"""
import os

from lockmaster import __version__
from lockmaster import git
from lockmaster import install as install_mod
from lockmaster.merge import DRIVERS
from lockmaster.repo import LANDING, LIVE, WORKTREES_DIR, LandLock


def check(repo):
    """One line per problem found; empty when all is well."""
    out = []
    lock = LandLock(repo)
    if lock.stale():
        out.append("stale land lock {} (holder {} is not running) — the next `lockmaster run` takes it over".format(
            lock.dir, lock.holder() or "unknown"))
    landing = repo.state / "landing"
    if landing.is_dir():
        for d in sorted(landing.iterdir()):
            out.append("a landing worktree was left behind: {} — `git worktree remove` it once you have "
                       "looked".format(d))

    changes = repo.changes()
    live = [c for c in changes if c["status"] in LIVE]
    for c in live:
        if not os.path.isdir(c["worktree"]):
            out.append("change {} is {} but its worktree {} is gone — `lockmaster abandon --item {}`".format(
                c["item"], c["status"], c["worktree"], c["item"]))
        if c["status"] == LANDING and not lock.dir.is_dir():
            out.append("change {} was landing when its lander stopped — `lockmaster run` queues it again".format(
                c["item"]))

    # A landed or abandoned change whose cleanup kept something: kept on purpose, nothing lost.
    kept = [c for c in changes if c["status"] not in LIVE and c.get("cleanup")
            and (os.path.isdir(c["worktree"]) or git.ok(["rev-parse", "--verify", "--quiet",
                                                         "refs/heads/" + c["branch"]], repo.root))]
    for c in kept:
        out.append("change {} is {}, and its cleanup kept: {} — look, then `git worktree remove` and "
                   "`git branch -d` by hand, or the decider rules (SR-WORK-CLEANUP decision 3)".format(
                       c["item"], c["status"], "; ".join(c["cleanup"])))

    owned = {os.path.realpath(c["worktree"]) for c in live + kept}
    root_wt = os.path.realpath(str(repo.root / WORKTREES_DIR))
    for t in git.worktrees(repo.root):
        p = os.path.realpath(t["path"])
        if p.startswith(root_wt + os.sep) and p not in owned:
            out.append("orphan worktree {} [{}]: no live change owns it".format(t["path"], t["branch"] or "detached"))

    live_branches = {c["branch"] for c in live + kept}
    for b in git.out(["for-each-ref", "--format=%(refname:short)", "refs/heads/lm/"], repo.root).split():
        if b in live_branches:
            continue
        if git.ok(["merge-base", "--is-ancestor", b, repo.main], repo.root):
            out.append("branch {} is in {} and no change owns it — `git branch -d {}`".format(b, repo.main, b))
        else:
            out.append("unmerged branch {}: no live change owns it and its commits are not in {} — "
                       "the decider rules (SR-WORK-CLEANUP decision 3)".format(b, repo.main))

    if repo.config.merge:
        missing = [d for d in DRIVERS
                   if not git.ok(["config", "--get", "merge.lockmaster-{}.driver".format(d)], repo.root)]
        if missing:
            out.append("merge drivers not registered ({}) — `lockmaster drivers`".format(", ".join(missing)))

    out += kit_problems(repo.root)
    return out


def kit_problems(root):
    lock = install_mod.read_lock(root)
    if not lock:
        if (root / ".claude" / "hooks").is_dir():
            return ["the kit in .claude/ was not installed by `lockmaster install` (no {})".format(install_mod.LOCK)]
        return []
    out = []
    try:
        kit = install_mod.find_kit()
    except Exception:  # noqa: BLE001 — no kit to compare against is not a problem of the repo
        kit = None
    if lock.get("version") != __version__:
        out.append("installed kit is from lockmaster {}, this is {} — `lockmaster install {}`".format(
            lock.get("version"), __version__, root))
    elif kit is not None and lock.get("kit") != install_mod.kit_digest(kit):
        out.append("installed kit {} differs from this lockmaster's {} — `lockmaster install {}`".format(
            (lock.get("kit") or "?")[:12], install_mod.kit_digest(kit)[:12], root))
    for rel, digest in sorted(lock.get("files", {}).items()):
        f = root / rel
        if not f.is_file():
            out.append("installed file missing: " + rel)
        elif install_mod.sha(f) != digest:
            out.append("installed file edited by hand: {} — edit the kit, then reinstall".format(rel))
    return out
