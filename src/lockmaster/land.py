"""The core loop — SR-ARCHITECTURE decisions 4-8 and 11.

    start    branch lm/<item> + a worktree under .claude/worktrees/ + the claim
    claim    widen the claim
    submit   commit the claimed paths in the worktree, join the queue, start `run`
    run      take the land lock; land queued changes oldest first
    abandon  drop a change; remove its worktree and branch only if nothing is lost

A landing (decision 8): the claimed paths' diff against the merge base becomes
one commit; it is cherry-picked onto the latest `main` in a fresh worktree;
generated files are rebuilt; the checks run; the result is committed with a
`Lockmaster-Change:` trailer and `main` is fast-forwarded to it. When the whole
branch landed, the landing commit also records the branch tip as a parent, so
git itself can prove the branch merged and `git branch -d` removes it
(SR-LAW-3 decision 2). Anything outside the claim is left behind and reported.

Red (decision 11): a conflict, a failed rebuild or check, or a refused commit
stops that change — marked red with the reason — and the next queued change
lands. `main` moves only by fast-forward, at the very end, so a crash at any
earlier point leaves `main` untouched and the change still queued.
"""
import os
import subprocess
import time
from datetime import date
from pathlib import Path

from lockmaster import git
from lockmaster import generated
from lockmaster import now as now_mod
from lockmaster.repo import (ABANDONED, ITEM_RE, LANDED, LANDING, LIVE, OPEN, QUEUED, RED,
                             LandLock, LockmasterError, claimed, matches, norm)

TRAILER = "Lockmaster-Change"
MAIN_TRIES = 3

# SR-WORK-CLEANUP decision 1(c): the only ignored files a worktree removal may
# take with it. The same list as the kit's worktree-cleanup.py.
BUILD_OUTPUT = {
    "target", "node_modules", "dist", "build", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".cache",
    ".turbo", ".next", ".parcel-cache", "coverage", ".coverage", ".lockmaster",
    "htmlcov", ".eggs", "runtime", ".codelaw",  # fux's and codelaw's rulings, joined in the kit (W-09)
    ".DS_Store",
}


class Red(LockmasterError):
    """This change cannot land as it is; nothing was changed."""


def _say(out, text):
    if out:
        out(text)


# ---------------------------------------------------------------- start / claim

def start(repo, item, paths, session=""):
    if not ITEM_RE.match(item or ""):
        raise LockmasterError("an item id is letters, digits, `.`, `_` or `-` (got `{}`)".format(item))
    if not paths:
        raise LockmasterError("name the paths this change may touch: --paths <path>…")
    old = repo.load(item)
    if old and old["status"] in LIVE:
        raise LockmasterError("{} already has a {} change at {}".format(item, old["status"], old["worktree"]))
    branch = "lm/" + item
    if git.ok(["rev-parse", "--verify", "--quiet", "refs/heads/" + branch], repo.root):
        raise LockmasterError("branch {} already exists; land, abandon or rename it first".format(branch))
    main_sha = git.out(["rev-parse", "--verify", repo.main + "^{commit}"], repo.root)
    wt = repo.worktree_for(item)
    if wt.exists():
        raise LockmasterError("{} already exists; it is not lockmaster's to reuse".format(wt))
    repo.exclude_worktrees()
    git.run(["worktree", "add", "-q", "-b", branch, str(wt), main_sha], repo.root)
    claims = sorted({norm(p) for p in paths})
    overlaps = []
    for other in repo.changes():
        if other["item"] != item and other["status"] in LIVE:
            for p in claims:
                for q in other["paths"]:
                    if claimed(p, [q]) or claimed(q, [p]):
                        overlaps.append((other["item"], q))
    change = {"item": item, "branch": branch, "worktree": str(wt), "paths": claims, "base": main_sha,
              "status": OPEN, "created": time.time(), "session": session, "reason": "",
              "message": "", "queued_at": None, "landed": None, "left_behind": []}
    repo.save(change)
    return change, overlaps


def claim_add(repo, change, paths):
    if change["status"] not in LIVE:
        raise LockmasterError("{} is {}; its claim is closed".format(change["item"], change["status"]))
    change["paths"] = sorted(set(change["paths"]) | {norm(p) for p in paths})
    repo.save(change)
    return change


# ---------------------------------------------------------------- submit

def status_paths(worktree):
    """Every path `git status` reports in `worktree` (both sides of a rename)."""
    raw = git.run(["status", "--porcelain", "-z", "--untracked-files=all"], worktree)
    parts, out, i = raw.split("\0"), [], 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.append(entry[3:])
        if entry[0] in "RC":
            out.append(parts[i])
            i += 1
    return out


def submit(repo, change, message="", out=None):
    """Commit the claimed paths in the worktree and queue the change."""
    if change["status"] in (LANDED, ABANDONED):
        raise LockmasterError("{} is already {}".format(change["item"], change["status"]))
    if change["status"] == LANDING:
        raise LockmasterError("{} is landing right now".format(change["item"]))
    wt = Path(change["worktree"])
    if not wt.is_dir():
        raise LockmasterError("{}'s worktree {} is gone".format(change["item"], wt))
    dirty = status_paths(wt)
    mine = [p for p in dirty if claimed(p, change["paths"])]
    others = sorted(set(dirty) - set(mine))
    if message:
        change["message"] = message
    if mine:
        git.run(["add", "-A", "--"] + [":(literal)" + p for p in mine], wt)
        if not git.ok(["diff", "--cached", "--quiet"], wt):
            wip = change["message"] or "{}: {}".format(change["item"], ", ".join(change["paths"]))
            git.run(["commit", "-q", "--no-verify", "-m", wip], wt)
    if others:
        _say(out, "left behind, outside the claim (not committed): " + ", ".join(others))
    change["status"] = QUEUED
    change["reason"] = ""
    change["queued_at"] = time.time()
    repo.save(change)
    return change


# ---------------------------------------------------------------- run

def run(repo, out=None):
    """Land queued changes, one at a time, until none is queued. Returns the
    number landed, or None when another lander holds the lock."""
    landed = 0
    while True:
        lock = LandLock(repo)
        if not lock.acquire():
            pid = lock.holder()
            _say(out, "a lander is already running{}; it lands queued changes in order".format(
                " (pid {})".format(pid) if pid else ""))
            return None if landed == 0 else landed
        try:
            for change in repo.changes():
                if change["status"] == LANDING:  # a lander died mid-landing; main was not moved
                    change["status"] = QUEUED
                    repo.save(change)
            while True:
                queued = sorted((c for c in repo.changes() if c["status"] == QUEUED),
                                key=lambda c: (c["queued_at"] or 0, c["item"]))
                if not queued:
                    break
                if land_one(repo, queued[0], out):
                    landed += 1
        finally:
            lock.release()
        # A change queued after the last look but before the release: go round again.
        if not any(c["status"] == QUEUED for c in repo.changes()):
            return landed


def land_one(repo, change, out=None):
    item = change["item"]
    change["status"] = LANDING
    repo.save(change)
    try:
        sha, left, unclaimed = land(repo, change)
    except Red as e:
        return _red(repo, change, str(e), out)
    except Exception as e:  # noqa: BLE001 — a bug is red, never a half-landing
        return _red(repo, change, "lockmaster failed while landing: {}".format(e), out)
    change.update(status=LANDED, landed=sha, reason="", left_behind=left + unclaimed, landed_at=time.time())
    reasons = cleanup(repo, change)
    change["cleanup"] = reasons
    repo.save(change)
    _say(out, "landed {} as {} on {}".format(item, sha[:10], repo.main))
    if left or unclaimed:
        _say(out, "  left behind, outside the claim: " + ", ".join(left + unclaimed))
    for r in reasons:
        _say(out, "  kept: " + r)
    now_mod.write_if_present(repo)
    return True


def _red(repo, change, reason, out):
    change.update(status=RED, reason=reason, red_at=time.time())
    repo.save(change)
    item = change["item"]
    short = reason.splitlines()[0][:120].replace("|", "/")
    _say(out, "\n".join([
        "red: {} — {}".format(item, reason),
        "  Nothing on {} or in {} was changed.".format(repo.main, change["worktree"]),
        "  Fix it there and run `lockmaster submit` again; queued changes behind it still land.",
        "  If you cannot fix it, put this row in the decider's inbox (SR-WORK-OPEN-QUEUE rule 42):",
        "  | 🔴 Land or drop lockmaster change {}: {} | {} |".format(item, short, date.today().isoformat()),
        "  | ↳ **blocks:** {} | |".format(item),
    ]))
    return False


def _changed(repo, base, tip):
    raw = git.run(["diff", "--name-only", "-z", "--no-renames", base, tip], repo.root)
    return [p for p in raw.split("\0") if p]


def _claimed_commit(repo, base, tip, files, item):
    """A commit on `base` whose tree is base's with `files` taken from `tip`."""
    index = repo.state / "index.{}".format(os.getpid())
    env = {"GIT_INDEX_FILE": str(index)}
    try:
        git.run(["read-tree", base], repo.root, env=env)
        listed = {}
        raw = git.run(["ls-tree", "-r", "-z", tip, "--"] + files, repo.root)
        for entry in filter(None, raw.split("\0")):
            meta, path = entry.split("\t", 1)
            mode, _, sha = meta.split(" ")
            listed[path] = (mode, sha)
        zero = "0" * len(base)
        info = []
        for f in files:
            mode, sha = listed.get(f, ("0", zero))  # mode 0 removes the entry
            info.append("{} {}\t{}".format(mode, sha, f))
        git.run(["update-index", "-z", "--index-info"], repo.root, env=env,
                input="\0".join(info) + "\0")
        tree = git.out(["write-tree"], repo.root, env=env)
    finally:
        try:
            index.unlink()
        except OSError:
            pass
    return git.out(["commit-tree", tree, "-p", base, "-m", "lockmaster: the claimed paths of " + item], repo.root)


def _message(repo, change, base, tip):
    if change.get("message"):
        msg = change["message"]
    else:
        shas = git.out(["rev-list", "--reverse", base + ".." + tip], repo.root).split()
        if len(shas) == 1:
            msg = git.out(["log", "-1", "--format=%B", shas[0]], repo.root)
        else:
            subjects = git.out(["log", "--reverse", "--format=%s", base + ".." + tip], repo.root).splitlines()
            msg = "{}: {} commits\n\n".format(change["item"], len(subjects)) + "\n".join("- " + s for s in subjects)
    return git.run(["interpret-trailers", "--trailer", "{}: {}".format(TRAILER, change["item"])],
                   repo.root, input=msg.rstrip() + "\n")


def land(repo, change):
    """Land one change. Returns (landed sha, committed paths left behind,
    uncommitted paths left behind). Raises Red when it cannot land."""
    cfg = repo.config
    wt = Path(change["worktree"])
    tip = git.out(["rev-parse", "--verify", "refs/heads/" + change["branch"]], repo.root)
    for _ in range(MAIN_TRIES):
        m0 = git.out(["rev-parse", "--verify", repo.main + "^{commit}"], repo.root)
        base = git.out(["merge-base", m0, tip], repo.root)
        changed = _changed(repo, base, tip)
        mine = [p for p in changed if claimed(p, change["paths"])]
        # A generated file is rebuilt whoever changed it, so it is never left behind.
        left = [p for p in changed if p not in mine and not any(matches(p, g) for g in cfg.generated)]
        to_land = [p for p in mine if not any(matches(p, g) for g in cfg.generated)]
        unclaimed = [p for p in status_paths(wt) if not claimed(p, change["paths"])] if wt.is_dir() else []
        if not to_land:
            raise Red("nothing inside the claim changed ({} paths claimed: {})".format(
                len(change["paths"]), ", ".join(change["paths"])))
        c = _claimed_commit(repo, base, tip, to_land, change["item"])
        msg = _message(repo, change, base, tip)
        landing = repo.state / "landing" / "{}-{}".format(change["item"], int(time.time() * 1000))
        landing.parent.mkdir(parents=True, exist_ok=True)
        git.run(["worktree", "add", "-q", "--detach", str(landing), m0], repo.root)
        try:
            code, o, e = git.run(["cherry-pick", "--no-commit", c], landing, check=False)
            if code != 0:
                conflicts = git.out(["diff", "--name-only", "--diff-filter=U"], landing).split()
                raise Red("conflicts with {} in: {}".format(repo.main, ", ".join(conflicts) or (e or o).strip()))
            try:
                generated.regen(landing, cfg, ref=m0)
            except generated.RegenError as err:
                raise Red(str(err))
            generated.stage(landing, cfg)
            if git.ok(["diff", "--cached", "--quiet"], landing):
                raise Red("every claimed change is already on {}; abandon the change".format(repo.main))
            for name, command in cfg.checks.items():
                env = dict(os.environ, LOCKMASTER_LANDING="1", LOCKMASTER_CHANGE=change["item"])
                r = subprocess.run(command, shell=True, cwd=str(landing), capture_output=True, text=True, env=env)
                if r.returncode != 0:
                    tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
                    raise Red("check `{}` (`{}`) failed:\n  {}".format(name, command, "\n  ".join(tail)))
            msg_file = repo.state / "message.{}".format(os.getpid())
            msg_file.write_text(msg, encoding="utf-8")
            try:
                code, o, e = git.run(["commit", "-q", "-F", str(msg_file)], landing, check=False)
                if code != 0:
                    raise Red("the commit was refused:\n  " + (e + o).strip().replace("\n", "\n  "))
                sha = git.out(["rev-parse", "HEAD"], landing)
                if not left:
                    # The whole branch landed: say so in history, so `git branch -d` can prove it.
                    meta = git.out(["log", "-1", "--format=%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI", sha], landing)
                    an, ae, ad, cn, ce, cd = meta.split("\0")
                    env = {"GIT_AUTHOR_NAME": an, "GIT_AUTHOR_EMAIL": ae, "GIT_AUTHOR_DATE": ad,
                           "GIT_COMMITTER_NAME": cn, "GIT_COMMITTER_EMAIL": ce, "GIT_COMMITTER_DATE": cd}
                    sha = git.out(["commit-tree", sha + "^{tree}", "-p", m0, "-p", tip, "-F", str(msg_file)],
                                  landing, env=env)
            finally:
                msg_file.unlink()
            moved = _fast_forward(repo, m0, sha)
            if moved == "moved":
                continue
            if moved:
                raise Red(moved)
            return sha, left, unclaimed
        finally:
            _remove_landing(repo, landing)
    raise Red("{} kept moving during the landing; tried {} times".format(repo.main, MAIN_TRIES))


def _fast_forward(repo, m0, sha):
    """Move main from m0 to sha. None when done, "moved" when main moved
    meanwhile, else the reason it could not."""
    holder = next((t for t in git.worktrees(repo.root) if t["branch"] == repo.main), None)
    if holder:
        code, o, e = git.run(["merge", "-q", "--ff-only", sha], holder["path"], check=False)
    else:
        code, o, e = git.run(["update-ref", "refs/heads/" + repo.main, sha, m0], repo.root, check=False)
    if code == 0:
        return None
    if git.out(["rev-parse", repo.main], repo.root) != m0:
        return "moved"
    return "{}'s checkout at {} refused the fast-forward:\n  {}".format(
        repo.main, holder["path"] if holder else "-", (e or o).strip().replace("\n", "\n  "))


def _remove_landing(repo, landing):
    """The landing worktree is lockmaster's own. Whatever is in it is
    committed to its detached HEAD first, so even a failed attempt loses
    nothing, then the worktree is removed the safe way."""
    if landing.is_dir():
        if git.dirty(landing):
            git.run(["add", "-A"], landing, check=False)
            git.run(["commit", "-q", "--no-verify", "-m", "lockmaster: what a red landing attempt held"],
                    landing, check=False)
        git.run(["worktree", "remove", str(landing)], repo.root, check=False)
    git.run(["worktree", "prune"], repo.root, check=False)


# ---------------------------------------------------------------- cleanup

def main_holder(repo):
    t = next((t for t in git.worktrees(repo.root) if t["branch"] == repo.main), None)
    return Path(t["path"]) if t else repo.root


def cleanup(repo, change):
    """SR-WORK-CLEANUP decisions 1-2, now rather than at session end: remove
    the change's worktree and branch only when nothing in them can be lost.
    Returns why anything was kept (empty when both went)."""
    wt, kept = Path(change["worktree"]), []
    if wt.is_dir():
        d = git.dirty(wt)
        if d:
            kept.append("worktree {}: {} uncommitted file{}".format(wt, len(d), "s" * (len(d) != 1)))
        ign = git.run(["status", "--porcelain", "--ignored", "--untracked-files=normal"], wt)
        for line in ign.splitlines():
            if line.startswith("!! "):
                rel = line[3:].rstrip("/")
                if not any(part in BUILD_OUTPUT for part in Path(rel).parts):
                    kept.append("worktree {}: ignored `{}` is not build output".format(wt, rel))
        if not kept:
            code, _, e = git.run(["worktree", "remove", str(wt)], repo.root, check=False)
            if code != 0:
                kept.append("worktree {}: git refused to remove it: {}".format(wt, e.strip()))
    if not kept and git.ok(["rev-parse", "--verify", "--quiet", "refs/heads/" + change["branch"]], repo.root):
        code, _, e = git.run(["branch", "-d", change["branch"]], main_holder(repo), check=False)
        if code != 0:
            kept.append("branch {}: not all of it is in {} — {}".format(
                change["branch"], repo.main, e.strip().splitlines()[0] if e.strip() else "git refused"))
    git.run(["worktree", "prune"], repo.root, check=False)
    return kept


def abandon(repo, change, out=None):
    if change["status"] == LANDING:
        raise LockmasterError("{} is landing right now".format(change["item"]))
    if change["status"] in (LANDED, ABANDONED):
        raise LockmasterError("{} is already {}".format(change["item"], change["status"]))
    change["status"] = ABANDONED
    change["abandoned_at"] = time.time()
    kept = cleanup(repo, change)
    change["cleanup"] = kept
    repo.save(change)
    _say(out, "abandoned " + change["item"])
    for k in kept:
        _say(out, "  kept: " + k)
    if kept:
        _say(out, "  Nothing was removed that is not in {}; the decider rules on what is kept "
                  "(SR-WORK-CLEANUP decision 3).".format(repo.main))
    now_mod.write_if_present(repo)
    return kept


# ---------------------------------------------------------------- queue

def queue_lines(repo):
    order = {LANDING: 0, QUEUED: 1, RED: 2, OPEN: 3, LANDED: 4, ABANDONED: 5}
    rows = sorted(repo.changes(), key=lambda c: (order.get(c["status"], 9), c.get("queued_at") or 0, c["item"]))
    if not rows:
        return ["no changes"]
    out = []
    for c in rows:
        line = "{:<10} {:<9} {}".format(c["item"], c["status"], ", ".join(c["paths"]))
        if c["status"] == LANDED and c.get("landed"):
            line += "  → " + c["landed"][:10]
        out.append(line)
        if c["status"] == RED and c.get("reason"):
            out.append("           " + c["reason"].splitlines()[0])
        for k in c.get("cleanup") or []:
            out.append("           kept: " + k)
    return out
