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

    from lockmaster import land
    for item, st, paths in land.checkout_overlaps(repo):  # W-10 step 3
        out.append("main's checkout has uncommitted edits to {} that change {} ({}) claims — its landing "
                   "waits until they are committed elsewhere, saved (`lockmaster save`) or undone".format(
                       ", ".join(paths), item, st))
    for c in live:
        if c["status"] == "waiting":
            out.append("change {} is waiting: {}".format(c["item"], (c.get("reason") or "").splitlines()[0]))

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
            out.append("orphan worktree {} [{}]: no live change owns it".format(os.path.normpath(t["path"]), t["branch"] or "detached"))

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
        from lockmaster import drivers as drivers_mod
        stale = drivers_mod.stale(repo)
        if stale:
            out.append("merge drivers registered with another machine's paths ({}) — the next landing re-points "
                       "them, or `lockmaster drivers`".format(", ".join(stale)))

    out += kit_problems(repo.root)
    out += work_problems(repo)
    return out


# SR-LAW-10 / W-15: this many landings on main with no WORKLOG.md change reads as drift.
STALE_LANDINGS = 10


def work_problems(repo):
    """A missing work file, and a worklog main has moved past (SR-LAW-10). Only
    where the kit is installed; whether a lesson, a machine quirk or a backlog
    row should have been written is judgment, never checked here."""
    if not install_mod.read_lock(repo.root):
        return []
    out = []
    missing = [f for f in install_mod.WORK_FILES if not (repo.root / "work" / f).is_file()]
    if missing:
        out.append("work file{} missing: {} — `lockmaster install {}` creates {} (SR-LAW-10)".format(
            "s" * (len(missing) > 1), ", ".join("work/" + f for f in missing), repo.root,
            "them" if len(missing) > 1 else "it"))
    if "WORKLOG.md" not in missing:
        n = landings_since_worklog(repo)
        if n is not None and n > STALE_LANDINGS:
            out.append("work/WORKLOG.md is stale: {} commits on {} since it last changed (more than {}) — "
                       "each session appends an entry (SR-LAW-10)".format(n, repo.main, STALE_LANDINGS))
    return out


def landings_since_worklog(repo):
    """First-parent commits on main since the last one that changed work/WORKLOG.md;
    None when main has no commit that did."""
    code, last, _ = git.run(["log", "-1", "--format=%H", repo.main, "--", "work/WORKLOG.md"], repo.root, check=False)
    last = last.strip()
    if code != 0 or not last:
        return None
    code, n, _ = git.run(["rev-list", "--count", "--first-parent", last + ".." + repo.main], repo.root, check=False)
    return int(n.strip()) if code == 0 and n.strip().isdigit() else None


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
