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
import json
import os
import re
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
    try:
        git.run(["worktree", "add", "-q", "-b", branch, str(wt), main_sha], repo.root)
    except git.GitError:
        # SR-LAW-8: two starts of one item at once — git's ref lock let one win.
        if git.ok(["rev-parse", "--verify", "--quiet", "refs/heads/" + branch], repo.root) or wt.exists():
            raise LockmasterError("{} was started by another session at the same moment".format(item))
        raise
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


def submit(repo, change, message="", out=None, keep=False):
    """Commit the claimed paths in the worktree and queue the change. With
    `keep` (an auto-landing, decision 20) the change stays open after it lands."""
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
            if keep and not change["message"]:
                wip = "{}: {} (landed at the end of a turn)".format(change["item"], ", ".join(sorted(mine)[:6]) + (
                    " and {} more".format(len(mine) - 6) if len(mine) > 6 else ""))
            else:
                wip = change["message"] or "{}: {}".format(change["item"], ", ".join(change["paths"]))
            git.run(["commit", "-q", "--no-verify", "-m", wip], wt)
    if others:
        _say(out, "left behind, outside the claim (not committed): " + ", ".join(others))
    change["status"] = QUEUED
    change["reason"] = ""
    change["keep"] = bool(keep)
    change["queued_at"] = time.time()
    repo.save(change)
    return change


# ---------------------------------------------------------------- run

def run(repo, out=None):
    """Land queued changes, one at a time, until none is queued. Returns the
    number landed, or None when another lander holds the lock."""
    landed = 0
    try:
        from lockmaster import drivers
        healed = drivers.heal(repo)  # decision 10: a driver registered on another surface is re-pointed here
        if healed:
            _say(out, "merge drivers re-pointed at this machine: " + ", ".join(healed))
    except Exception:  # noqa: BLE001 — a driver that stays stale only means a plain conflict
        pass
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
    keep = bool(change.get("keep"))
    change["status"] = LANDING
    repo.save(change)
    try:
        sha, left, unclaimed = land(repo, change)
    except Red as e:
        if keep:
            return _held(repo, change, str(e), out)
        return _red(repo, change, str(e), out)
    except Exception as e:  # noqa: BLE001 — a bug is red, never a half-landing
        if keep:
            return _held(repo, change, "lockmaster failed while landing: {}".format(e), out)
        return _red(repo, change, "lockmaster failed while landing: {}".format(e), out)
    if keep:
        # Decision 20: an auto-landing keeps the change open; its worktree follows main.
        note = _follow(repo, change, sha)
        change.update(status=OPEN, keep=False, landed=sha, base=sha, reason="", held="", message="",
                      left_behind=left + unclaimed, landed_at=time.time(),
                      landings=(change.get("landings") or []) + [sha], cleanup=[note] if note else [])
        repo.save(change)
        _say(out, "landed {} as {} on {} (the change stays open)".format(item, sha[:10], repo.main))
        if left or unclaimed:
            _say(out, "  left behind, outside the claim: " + ", ".join(left + unclaimed))
        if note:
            _say(out, "  note: " + note)
        now_mod.write_if_present(repo)
        return True
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


def _held(repo, change, reason, out):
    """Decision 20: an auto-landing that cannot land is held, not red. The
    change stays open with the reason, for its own session to fix; nothing goes
    to the decider and the next turn's end tries again."""
    change.update(status=OPEN, keep=False, held=reason, held_key=pending_key(repo, change), held_at=time.time())
    repo.save(change)
    _say(out, "held: {} — {}".format(change["item"], reason))
    _say(out, "  Nothing on {} was changed; it lands at the end of a turn once this is fixed in {}.".format(
        repo.main, change["worktree"]))
    return False


def _follow(repo, change, sha):
    """Bring a kept change's branch, in its worktree, up to the landing `sha`.
    Returns a note when it could not (nothing is lost either way)."""
    wt = Path(change["worktree"])
    if not wt.is_dir():
        return ""
    tip = git.out(["rev-parse", "HEAD"], wt)
    if git.ok(["merge-base", "--is-ancestor", tip, sha], wt):
        args = ["merge", "-q", "--ff-only", sha]
    else:  # committed paths outside the claim stayed on the branch: merge main in
        args = ["merge", "-q", "--no-edit", "--no-verify", "-m",
                "lockmaster: {} follows {} after a landing".format(change["item"], repo.main), sha]
    code, o, e = git.run(args, wt, check=False)
    if code == 0:
        return ""
    if git.ok(["rev-parse", "--verify", "--quiet", "MERGE_HEAD"], wt):
        git.run(["merge", "--abort"], wt, check=False)
    return "{} was not brought up to {}: {}".format(wt, repo.main, ((e or o).strip().splitlines() or ["git refused"])[0])


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
        blocking = _accept_identical(Path(holder["path"]), m0, sha)
        code, o, e = git.run(["merge", "-q", "--ff-only", sha], holder["path"], check=False)
    else:
        blocking = []
        code, o, e = git.run(["update-ref", "refs/heads/" + repo.main, sha, m0], repo.root, check=False)
    if code == 0:
        return None
    if git.out(["rev-parse", repo.main], repo.root) != m0:
        return "moved"
    said = (e or o).strip()
    if blocking:
        said = "uncommitted edits there to {} differ from this landing".format(", ".join(blocking)) + (
            "\n" + said if said else "")
    return "{}'s checkout at {} refused the fast-forward:\n  {}".format(
        repo.main, holder["path"] if holder else "-", (said or "git gave no reason").replace("\n", "\n  "))


def _accept_identical(checkout, m0, sha):
    """SR-ARCHITECTURE decision 8a. Uncommitted edits in main's checkout to paths
    this landing changes would stop the fast-forward. Where every such edit is
    byte-for-byte what the landing holds — the usual case when edits made in
    the checkout are landed by `save` — they are staged, which loses nothing
    and lets git take the fast-forward. Returns the paths whose edits differ;
    when there are any, nothing is staged and the checkout is left as it was."""
    touched = set(_changed_in(checkout, m0, sha))
    if not touched:
        return []
    raw = git.run(["status", "--porcelain", "-z", "--untracked-files=all", "--no-renames"], checkout)
    same, differ = [], []
    for entry in filter(None, raw.split("\0")):
        xy, path = entry[:2], entry[3:]
        if path not in touched:
            continue
        full = checkout / path
        code, want, _ = git.run(["rev-parse", "--verify", "--quiet", "{}:{}".format(sha, path)], checkout,
                                check=False)
        want = want.strip() if code == 0 else None
        if full.is_file() and not full.is_symlink():
            have = git.out(["hash-object", "--path", path, "--", path], checkout)
        else:
            have = None if not full.exists() else "?"
        staged_other = xy[0] not in (" ", "?") and xy[1] not in (" ",)
        if have == want and have != "?" and not staged_other:
            same.append(path)
        else:
            differ.append(path)
    if differ:
        return sorted(differ)
    if same:
        git.run(["add", "-A", "--"] + [":(literal)" + p for p in same], checkout)
    return []


def _changed_in(cwd, a, b):
    raw = git.run(["diff", "--name-only", "-z", "--no-renames", a, b], cwd)
    return [p for p in raw.split("\0") if p]


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
    waiting = handoffs(repo)
    if not rows and not waiting:
        return ["no changes"]
    out = []
    last = last_pickup(repo)
    for h in waiting:
        note = "; last try: " + h["reason"].splitlines()[0] if h.get("reason") else ""
        if not note and last and (h.get("created") or 0) < last:
            note = "; MISSED by the pickup at " + time.strftime("%Y-%m-%d %H:%M", time.localtime(last))
        out.append("{:<10} {:<9} {}  (from {}, {}{})".format(
            h["item"], "handoff", ", ".join(h["paths"]), h.get("by", "?"),
            time.strftime("%Y-%m-%d %H:%M", time.localtime(h.get("created") or 0)), note))
    for c in rows:
        line = "{:<10} {:<9} {}".format(c["item"], c["status"], ", ".join(c["paths"]))
        if c["status"] == LANDED and c.get("landed"):
            line += "  → " + c["landed"][:10]
        out.append(line)
        if c["status"] == RED and c.get("reason"):
            out.append("           " + c["reason"].splitlines()[0])
        if c["status"] == OPEN and c.get("held"):
            out.append("           held: " + c["held"].splitlines()[0])
        for k in c.get("cleanup") or []:
            out.append("           kept: " + k)
    return out


# ---------------------------------------------------------------- auto-landing (decision 20)

def _tip(repo, change):
    code, sha, _ = git.run(["rev-parse", "--verify", "--quiet", "refs/heads/" + change["branch"]], repo.root,
                           check=False)
    return sha.strip() if code == 0 else ""


def _merge_base(repo, a, b):
    """The merge base of a and b, or "" when they share no history."""
    code, sha, _ = git.run(["merge-base", a, b], repo.root, check=False)
    return sha.strip() if code == 0 else ""


def _dirty_digest(wt, paths):
    """A digest of the uncommitted edits to `paths` under `wt`."""
    import hashlib
    h = hashlib.sha256()
    for p in sorted(paths):
        f = Path(wt) / p
        h.update(p.encode("utf-8", "surrogateescape") + b"\0")
        try:
            h.update(f.read_bytes() if f.is_file() else b"<gone>")
        except OSError:
            h.update(b"<unreadable>")
    return h.hexdigest()[:16]


def _generated(repo, path):
    return any(matches(path, g) for g in repo.config.generated)


def _claimed_dirty(repo, change):
    """The worktree's uncommitted claimed paths; generated files are rebuilt, never landed."""
    wt = Path(change["worktree"])
    if not wt.is_dir():
        return []
    return [p for p in status_paths(wt) if claimed(p, change["paths"]) and not _generated(repo, p)]


def pending_key(repo, change):
    """What the change holds that is not on main yet, as one short key: the
    branch tip and a digest of its claimed uncommitted edits."""
    return "{}:{}".format(_tip(repo, change)[:12],
                          _dirty_digest(change["worktree"], _claimed_dirty(repo, change)))


def pending(repo, change):
    """True when the change holds claimed work that is not on main: claimed
    uncommitted edits, or a claimed path the branch changed whose content is
    not main's. A path already on main — landed, even if the worktree could
    not follow — is not pending."""
    if not Path(change["worktree"]).is_dir():
        return False
    if _claimed_dirty(repo, change):
        return True
    tip = _tip(repo, change)
    if not tip:
        return False
    m = git.out(["rev-parse", "--verify", repo.main + "^{commit}"], repo.root)
    base = _merge_base(repo, m, tip)
    if not base:
        return False
    mine = [p for p in _changed(repo, base, tip) if claimed(p, change["paths"]) and not _generated(repo, p)]
    if not mine:
        return False
    differs = set(_changed(repo, m, tip))
    return any(p in differs for p in mine)


def _inside(path, top):
    a, b = os.path.realpath(str(path)), os.path.realpath(str(top))
    return a == b or a.startswith(b + os.sep)


def _mine(change, session, cwd):
    """A change is this session's by its recorded id; only a change with no
    recorded session is matched by the session's working directory."""
    if change.get("session"):
        return bool(session) and change["session"] == session
    return bool(cwd) and _inside(cwd, change["worktree"])


def adopt(repo, worktree, session=""):
    """Make a worktree lockmaster did not create — `claude --worktree`, an
    agent's isolated worktree — a change of its own, so it lands like one. Its
    claim is everything it changed; it is widened on every landing, because
    the worktree is that session's alone. lockmaster never removes it. Returns
    None for the primary checkout, a lockmaster worktree, one a live change
    already holds, or a branch with no history in common with main."""
    t = next((t for t in git.worktrees(repo.root) if _inside(worktree, t["path"])
              and os.path.realpath(t["path"]) != os.path.realpath(str(repo.root))), None)
    if t is None or not t["branch"] or t["branch"] == repo.main or t["branch"].startswith("lm/"):
        return None
    if repo.change_holding(t["path"]) is not None:
        return None
    base = _merge_base(repo, repo.main, t["branch"])
    if not base:
        return None
    item = re.sub(r"[^A-Za-z0-9._-]+", "-", "wt-" + t["branch"].split("/")[-1]).strip("-.")
    n, base_item = 2, item
    while repo.load(item) is not None:
        item, n = "{}-{}".format(base_item, n), n + 1
    change = {"item": item, "branch": t["branch"], "worktree": t["path"], "paths": [], "base": base,
              "status": OPEN, "created": time.time(), "session": session, "reason": "", "adopted": True,
              "message": "", "queued_at": None, "landed": None, "left_behind": []}
    _widen(repo, change)
    repo.save(change)
    return change


def _widen(repo, change):
    """An adopted change claims whatever its worktree changed, generated files aside."""
    wt = Path(change["worktree"])
    tip = _tip(repo, change)
    changed = []
    if tip:
        base = _merge_base(repo, repo.main, tip)
        changed = _changed(repo, base, tip) if base else []
    dirty = status_paths(wt) if wt.is_dir() else []
    change["paths"] = sorted(set(change["paths"]) | {norm(p) for p in changed + dirty if not _generated(repo, p)})


def _finish(repo, change, out=None):
    """The session ended and the change holds nothing new: it is done. Landed
    (kept) before → LANDED; never landed anything → abandoned. Either way the
    worktree and branch go only if nothing in them can be lost."""
    if change.get("landings"):
        change.update(status=LANDED, landed=change["landings"][-1], keep=False)
        change["cleanup"] = cleanup(repo, change)
        repo.save(change)
        _say(out, "finished {}: landed earlier as {}".format(change["item"], change["landed"][:10]))
        for k in change["cleanup"]:
            _say(out, "  kept: " + k)
        now_mod.write_if_present(repo)
    else:
        abandon(repo, change, out=out)


def sync(repo, session="", cwd=None, final=False, adopt_cwd=True, out=None):
    """Land, now, every open change of this session that holds work not on
    main — at the end of a turn (kept: the change stays open and its worktree
    follows main) or at the end of the session (`final`: an ordinary submit,
    then cleanup; a change with nothing new is finished). Returns the changes
    it queued. Lands nothing on a surface that cannot commit."""
    from lockmaster import surface
    if not repo.config.auto_land:
        return []
    ok_, why = surface.can_commit(repo)
    if not ok_:
        _say(out, "not landing here: " + why)
        return []
    # SR-LAW-8: two end-of-turn landings of one session never run at once. A
    # turn's end skips while one is running (the next turn retries); the
    # session's end waits for it.
    lock = LandLock(repo, "sync.{}.lock".format(re.sub(r"[^A-Za-z0-9._-]", "_", session or "-")))
    deadline = time.time() + 3600
    while not lock.acquire():
        if not final:
            _say(out, "an end-of-turn landing of this session is already running; it lands this turn's work")
            return []
        if time.time() > deadline:
            _say(out, "gave up waiting for this session's other landing")
            return []
        time.sleep(1)
    try:
        return _sync(repo, session, cwd, final, adopt_cwd, out)
    finally:
        lock.release()


def _sync(repo, session, cwd, final, adopt_cwd, out):
    targets = []
    for c in repo.changes():
        if c["status"] != OPEN:
            continue
        if c.get("adopted") and not Path(c["worktree"]).is_dir():
            abandon(repo, c)  # its owner removed the worktree; the branch goes only if merged
            continue
        if _mine(c, session, cwd):
            targets.append(c)
    if adopt_cwd and cwd and not any(_inside(cwd, c["worktree"]) for c in targets):
        c = adopt(repo, cwd, session)
        if c is not None:
            targets.append(c)
    queued = []
    for c in targets:
        if c.get("adopted"):
            _widen(repo, c)
            repo.save(c)
        if not pending(repo, c):
            if final and not c.get("adopted"):
                _finish(repo, c, out=out)
            continue
        keep = not final or bool(c.get("adopted"))
        submit(repo, c, "", out=out, keep=keep)
        queued.append(c["item"])
    if queued:
        run(repo, out=out)
    return queued


def held_reports(repo, session="", cwd=None):
    """(item, reason) for each of this session's held changes not reported yet
    for what it holds now; marks them reported."""
    out = []
    for c in repo.changes():
        if c["status"] != OPEN or not c.get("held") or not _mine(c, session, cwd):
            continue
        key = c.get("held_key") or ""
        if c.get("held_reported") == key:
            continue
        c["held_reported"] = key
        repo.save(c)
        out.append((c["item"], c["held"]))
    return out


# ---------------------------------------------------------------- save, handoff, pickup (decision 19)

def _checkout_dirty(repo, paths):
    """The uncommitted paths in main's checkout under `paths`."""
    claims = [norm(p) for p in paths]
    return [p for p in status_paths(repo.root) if claimed(p, claims)]


def _relative(repo, paths, cwd=None):
    out = []
    base = Path(cwd or repo.cwd)
    for p in paths:
        q = Path(p)
        full = q if q.is_absolute() else base / q
        try:
            rel = os.path.relpath(os.path.abspath(str(full)), os.path.realpath(str(repo.root)))
        except ValueError:
            rel = p
        if rel.startswith(".."):
            # A path given relative to the checkout root, from somewhere else.
            rel = p
        out.append(norm(rel.replace(os.sep, "/")))
    return out


def _require_main_checkout(repo):
    holder = next((t for t in git.worktrees(repo.root) if t["branch"] == repo.main), None)
    if holder is None or os.path.realpath(holder["path"]) != os.path.realpath(str(repo.root)):
        raise LockmasterError("main's checkout is not the primary checkout; save needs {} checked out at {}".format(
            repo.main, repo.root))


def _copy_in(repo, wt, dirty):
    """Copy the checkout's versions of `dirty` into the worktree `wt` (a
    deletion deletes). The worktree is lockmaster's own copy; the checkout is
    only read."""
    import shutil
    for p in dirty:
        src, dst = repo.root / p, Path(wt) / p
        if src.is_file() or src.is_symlink():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            if src.is_symlink():
                os.symlink(os.readlink(str(src)), str(dst))
            else:
                shutil.copy2(str(src), str(dst))
        elif dst.exists() or dst.is_symlink():
            dst.unlink()


def save(repo, paths, message, item=None, out=None, change=None):
    """Land uncommitted edits made directly in main's checkout: a change is
    started on the paths (or `change`, an earlier attempt, is reused), the
    checkout's edits copied into its worktree, submitted and landed; the
    checkout's identical edits are accepted by the fast-forward (decision 8a).
    Returns the change, or None when nothing under `paths` is uncommitted."""
    _require_main_checkout(repo)
    if not paths:
        raise LockmasterError("name the paths to save: lockmaster save -m \"…\" <path>…")
    dirty = _checkout_dirty(repo, paths)
    if not dirty:
        return None
    if change is None or not Path(change["worktree"]).is_dir():
        change = _start_unique(repo, item, paths)
    else:
        claim_add(repo, change, paths)
    _copy_in(repo, change["worktree"], dirty)
    change = submit(repo, change, message or "{}: {}".format(change["item"], ", ".join(dirty)), out=out)
    run(repo, out=out)
    return repo.load(change["item"])


def _start_unique(repo, item, paths):
    """Start a change for `save`. A name lockmaster chose is made unique when
    another save took it in the same second (SR-LAW-8 decision 3)."""
    session = os.environ.get("CLAUDE_SESSION_ID", "")
    if item:
        return start(repo, item, paths, session)[0]
    base = time.strftime("save-%Y%m%d-%H%M%S")
    for n in range(1, 100):
        name = base if n == 1 else "{}-{}".format(base, n)
        if repo.load(name) is not None:
            continue
        try:
            return start(repo, name, paths, session)[0]
        except LockmasterError:
            continue  # taken by a save running at the same moment
    raise LockmasterError("could not find a free name for this save after {}".format(base))


def handoffs_dir(repo):
    return repo.state / "handoffs"


def handoffs(repo):
    d = handoffs_dir(repo)
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        try:
            h = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        h["_file"] = str(f)
        out.append(h)
    return sorted(out, key=lambda h: (h.get("created") or 0, h.get("item", "")))


def _write_handoff(f, h):
    h = {k: v for k, v in h.items() if k != "_file"}
    tmp = Path(f).with_name(Path(f).name + ".part")
    tmp.write_text(json.dumps(h, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def handoff(repo, paths, message, item=None, by=""):
    """Record edits in main's checkout for the next surface that can commit.
    Writes one new file (written aside, then renamed in: no file is removed),
    so it works where nothing can be deleted. Returns the handoff."""
    dirty = _checkout_dirty(repo, paths)
    if not dirty:
        return None
    item = item or time.strftime("handoff-%Y%m%d-%H%M%S")
    d = handoffs_dir(repo)
    d.mkdir(parents=True, exist_ok=True)
    h = {"paths": sorted({norm(p) for p in paths}), "files": dirty, "message": message,
         "by": by or "a surface that cannot commit", "created": time.time(),
         "digest": _dirty_digest(repo.root, dirty),
         # SR-LAW-9 decision 3: what lands is what was handed over, file by file.
         "digests": {f: _dirty_digest(repo.root, [f]) for f in dirty}}
    n, name = 2, item
    while True:
        fd = None
        if repo.load(name) is None:
            try:  # exclusive: a handoff written at the same moment never overwrites this one (SR-LAW-8)
                fd = os.open(str(d / (name + ".json")), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                pass
        if fd is not None:
            break
        name, n = "{}-{}".format(item, n), n + 1
    h["item"] = name
    with os.fdopen(fd, "w", encoding="utf-8") as fh:  # a reader that sees it half-written skips it this time
        fh.write(json.dumps(h, indent=2, sort_keys=True) + "\n")
    return h


def pickup(repo, out=None):
    """Land every handoff, oldest first, on a surface that can commit.

    Handoffs that name a common file land together, as one change under all
    their messages: the file holds the newest edit, so landing them apart would
    put it under the older message (SR-LAW-9 decision 3).

    Returns [(item, outcome, note)] per handoff — outcome `landed`; `gone`
    (nothing left to land: it is on main already, or the edits were reverted);
    `held` (a file was edited in main's checkout after it was handed off and
    not handed off again: nothing lands until it is — the note is the reason,
    given once); `red` (it could not land: the handoff keeps one change, which
    is retried with the checkout's edits once they change — the note is the
    reason, given once); `waiting` (queued behind another lander); `skipped`
    (unchanged since it went red or was held, or this surface cannot commit);
    `failed` (lockmaster itself failed on it; the handoff is kept)."""
    from lockmaster import surface
    pending_ = handoffs(repo)
    if not pending_:
        return []
    ok_, why = surface.can_commit(repo)
    if not ok_:
        _say(out, "{} handoff{} waiting: {}".format(len(pending_), "s" * (len(pending_) != 1), why))
        return [(h["item"], "skipped", "") for h in pending_]
    lock = LandLock(repo, "pickup.lock")
    if not lock.acquire():
        _say(out, "another session is picking the handoffs up")
        return []
    results, seen = [], set()
    try:
        while True:  # a handoff written while this pass ran is landed by the next (SR-LAW-8)
            groups = [g for g in _groups(handoffs(repo)) if any(h["item"] not in seen for h in g)]
            if not groups:
                break
            for group in groups:
                seen.update(h["item"] for h in group)
                try:
                    results.extend(_pickup_group(repo, group, out))
                except Exception as e:  # noqa: BLE001 — one bad handoff never stops the rest
                    _say(out, "handoff {}: lockmaster failed on it: {}".format(group[-1]["item"], e))
                    results.extend((h["item"], "failed", str(e)) for h in group)
        _write_stamp(repo)
    finally:
        lock.release()
    return results


def _write_stamp(repo):
    """When this surface last picked the handoffs up — SR-LAW-9's veto check."""
    f = repo.state / "pickup.last"
    tmp = f.with_name("pickup.last.{}".format(os.getpid()))
    tmp.write_text("{}\n".format(time.time()), encoding="utf-8")
    os.replace(str(tmp), str(f))


def last_pickup(repo):
    try:
        return float((repo.state / "pickup.last").read_text().strip())
    except (OSError, ValueError):
        return None


def _groups(hs):
    """`hs` (oldest first) split into groups that share a file, each oldest
    first; the groups ordered by their oldest member."""
    parent = list(range(len(hs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i, h in enumerate(hs):
        for f in h.get("files") or h.get("paths") or []:
            if f in owner:
                parent[find(i)] = find(owner[f])
            owner[f] = i
    groups = {}
    for i in range(len(hs)):
        groups.setdefault(find(i), []).append(hs[i])
    return sorted(groups.values(), key=lambda g: (g[0].get("created") or 0, g[0]["item"]))


def _drifted(repo, group, dirty):
    """Files edited in main's checkout since the handoff that last named them."""
    owner = {}
    for h in group:  # oldest first: the newest handoff naming a file owns it
        for f in h.get("files") or []:
            owner[f] = h
    if len(group) == 1 and "digests" not in group[0]:
        h = group[0]  # written before per-file digests: the whole handoff is the unit
        if h.get("digest") and _dirty_digest(repo.root, h.get("files") or []) != h["digest"]:
            return [f for f in h.get("files") or [] if f in dirty] or list(h.get("files") or [])
        return []
    out = []
    for f in sorted(dirty):
        d = (owner.get(f) or {}).get("digests")
        if d is not None and _dirty_digest(repo.root, [f]) != d.get(f):
            out.append(f)
    return out


_TRAILER_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*: ")


def _group_message(group):
    lead = group[-1]
    msg = (lead.get("message") or "").strip() or "{}: {}".format(
        lead["item"], ", ".join(lead.get("files") or lead["paths"]))
    if len(group) == 1:
        return msg
    note = ["Landed with the earlier handoff{} that touch{} the same files:".format(
        "s" * (len(group) > 2), "" if len(group) > 2 else "es")]
    for h in group[:-1]:
        subject = ((h.get("message") or "").strip().splitlines() or [h["item"]])[0]
        note.append("- {} (from {}): {}".format(h["item"], h.get("by", "?"), subject))
    paras = msg.split("\n\n")
    if len(paras) > 1 and all(_TRAILER_LINE.match(l) for l in paras[-1].splitlines()):
        return "\n\n".join(paras[:-1] + ["\n".join(note), paras[-1]])
    return msg + "\n\n" + "\n".join(note)


def _pickup_group(repo, group, out):
    lead = group[-1]  # the newest handoff carries the group's state
    names = [h["item"] for h in group]

    def each(outcome, note=""):
        return [(n, outcome, note if n == lead["item"] else "") for n in names]

    def drop():
        for h in group:
            try:
                Path(h["_file"]).unlink()
            except FileNotFoundError:
                pass

    def keep(**kw):
        lead.update(kw)
        _write_handoff(lead["_file"], lead)

    prior = None
    for h in reversed(group):
        if h.get("change"):
            prior = repo.load(h["change"])
            if prior is not None:
                break
    if prior and prior["status"] == LANDED:
        drop()
        return each("landed")
    if prior and prior["status"] in (QUEUED, LANDING):
        return each("waiting")
    files = sorted({f for h in group for f in (h.get("files") or h["paths"])})
    dirty = _checkout_dirty(repo, files)
    if not dirty:
        drop()
        if prior and prior["status"] in (RED, OPEN):
            abandon(repo, prior)
        _say(out, "handoff {}: nothing left uncommitted in {} — dropped".format(", ".join(names), ", ".join(files)))
        return each("gone")
    digest = _dirty_digest(repo.root, dirty)
    fixing = prior is not None and prior["status"] in (RED, OPEN)  # went red: its fix is made where it is
    if fixing and lead.get("tried") == digest:
        return each("skipped")
    if not fixing:
        drifted = _drifted(repo, group, dirty)
        if drifted:
            if lead.get("held_digest") == digest:
                return each("skipped")
            reason = ("edited in main's checkout after it was handed off, and not handed off again: {}. "
                      "It lands once that edit is handed off too (`lockmaster save`) or undone.").format(
                          ", ".join(drifted))
            keep(held_digest=digest, reason=reason)
            _say(out, "handoff {}: held — {}".format(lead["item"], reason))
            return each("held", reason)
    item = lead["item"] if repo.load(lead["item"]) is None else "{}-{}".format(lead["item"], int(time.time()))
    change = save(repo, files, _group_message(group), item=item, out=out, change=prior if fixing else None)
    if change is None:
        drop()
        return each("gone")
    if change["status"] == LANDED:
        drop()
        _say(out, "handoff {} landed as {}".format(
            ", ".join("{} from {}".format(h["item"], h.get("by", "?")) for h in group), change["landed"][:10]))
        return each("landed")
    if change["status"] in (QUEUED, LANDING):  # another lander holds the lock; it lands it
        keep(change=change["item"])
        return each("waiting")
    keep(change=change["item"], tried=digest, reason=change.get("reason", ""))
    return each("red", lead["reason"])
