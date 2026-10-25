"""`lockmaster install <repo>` — SR-ARCHITECTURE decisions 14 and 15.

    kit/claude/**  ->  <repo>/.claude/**   hooks made executable
    kit/github/**  ->  <repo>/.github/**
    kit/claude/settings.json is MERGED into <repo>/.claude/settings.json: the
        kit's hook entries replace the ones a previous install wrote; the
        repo's own entries and keys are kept
    <repo>/.claude/lockmaster.lock  records the version, the kit's digest and
        each installed file's hash, so `lockmaster doctor` sees a mismatch
    the merge drivers, when the repo has a lockmaster.toml

An existing file the kit would replace, and which a previous install did not
write, is never overwritten silently: the install stops and names it, or with
--backup moves it aside to `<file>.pre-lockmaster` first (SR-LAW-3).
"""
import hashlib
import json
import os
import stat
from pathlib import Path

from lockmaster import __version__
from lockmaster import git
from lockmaster.repo import LockmasterError

LOCK = ".claude/lockmaster.lock"
SETTINGS = ".claude/settings.json"
TREES = (("claude", ".claude"), ("github", ".github"))


def find_kit():
    """The kit this lockmaster carries: $LOCKMASTER_KIT, the package's own
    copy, or the source checkout's kit/."""
    env = os.environ.get("LOCKMASTER_KIT")
    here = Path(__file__).resolve().parent
    for cand in ([Path(env)] if env else []) + [here / "kit", here.parents[1] / "kit"]:
        if (cand / "claude").is_dir():
            return cand
    raise LockmasterError("cannot find the kit (set LOCKMASTER_KIT to a kit/ directory)")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def kit_files(kit):
    """(source path, installed relative path) for every kit file but settings.json."""
    out = []
    for sub, dest in TREES:
        base = kit / sub
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_dir() or "__pycache__" in f.parts or f.name == ".DS_Store":
                continue
            rel = (Path(dest) / f.relative_to(base)).as_posix()
            if rel != SETTINGS:
                out.append((f, rel))
    return out


def kit_digest(kit):
    h = hashlib.sha256()
    for f, rel in kit_files(kit) + [(kit / "claude" / "settings.json", SETTINGS)]:
        if f.is_file():
            h.update(rel.encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def read_lock(target):
    try:
        return json.loads((Path(target) / LOCK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _commands(settings):
    return {h.get("command") for groups in settings.get("hooks", {}).values()
            for g in groups for h in g.get("hooks", []) if h.get("command")}


def merge_settings(current, kit_settings, managed_before):
    """The kit's hook entries, then the repo's own; every other key of the
    repo's settings kept. `managed_before` are the commands a previous install
    wrote, so a hook the kit dropped leaves too."""
    managed = set(managed_before) | _commands(kit_settings)
    merged = dict(current)
    for key, value in kit_settings.items():
        if key != "hooks" and key not in merged:
            merged[key] = value
    hooks = {}
    events = list(kit_settings.get("hooks", {})) + [e for e in current.get("hooks", {})
                                                     if e not in kit_settings.get("hooks", {})]
    for event in events:
        own = []
        for g in current.get("hooks", {}).get(event, []):
            kept = [h for h in g.get("hooks", []) if h.get("command") not in managed]
            if kept:
                own.append(dict(g, hooks=kept))
        groups = list(kit_settings.get("hooks", {}).get(event, [])) + own
        if groups:
            hooks[event] = groups
    merged["hooks"] = hooks
    return merged


def install(target, backup=False, out=print):
    target = Path(target).resolve()
    if git.run(["rev-parse", "--show-toplevel"], target, check=False)[0] != 0:
        raise LockmasterError("not a git repository: {}".format(target))
    kit = find_kit()
    old = read_lock(target)
    old_files = old.get("files", {})
    plan = kit_files(kit)

    conflicts = []
    for src, rel in plan:
        dst = target / rel
        if dst.exists():
            cur = sha(dst)
            if cur != sha(src) and old_files.get(rel) != cur:
                conflicts.append(rel)
    if conflicts and not backup:
        raise LockmasterError(
            "these files exist and were not written by a lockmaster install; nothing was changed:\n  "
            + "\n  ".join(conflicts)
            + "\nrun again with --backup to move each aside to <file>.pre-lockmaster first")
    for rel in conflicts:
        dst = target / rel
        aside, n = dst.with_name(dst.name + ".pre-lockmaster"), 1
        while aside.exists():
            aside, n = dst.with_name("{}.pre-lockmaster.{}".format(dst.name, n)), n + 1
        os.rename(str(dst), str(aside))
        out("  moved aside: {} -> {}".format(rel, aside.relative_to(target).as_posix()))

    files = {}
    for src, rel in plan:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)
        if "hooks" in Path(rel).parts and dst.suffix in (".sh", ".py"):
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        files[rel] = sha(dst)

    # A file an earlier kit installed and this one does not: removed only if untouched.
    for rel, digest in old_files.items():
        dst = target / rel
        if rel not in files and dst.is_file():
            if sha(dst) == digest:
                dst.unlink()
                out("  removed (no longer in the kit): " + rel)
            else:
                out("  kept, edited by hand and no longer in the kit: " + rel)

    kit_settings = json.loads((kit / "claude" / "settings.json").read_text(encoding="utf-8"))
    settings_path = target / SETTINGS
    current = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.is_file() else {}
    merged = merge_settings(current, kit_settings, old.get("settings", []))
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    if not settings_path.is_file() or settings_path.read_text(encoding="utf-8") != text:
        settings_path.write_text(text, encoding="utf-8")

    lock = {"version": __version__, "kit": kit_digest(kit), "files": files,
            "settings": sorted(_commands(kit_settings))}
    (target / LOCK).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out("installed kit {} into {}: {} files, settings merged".format(lock["kit"][:12], target, len(files)))

    from lockmaster.repo import Repo
    from lockmaster import drivers
    repo = Repo(target)
    if (target / "lockmaster.toml").is_file():
        if drivers.install(repo):
            out("  .gitattributes: lockmaster's [merge] block written — commit it")
        out("  merge drivers registered in .git/config")
    _guard(repo, out)
    return lock


def _guard(repo, out):
    """The commit guard, when the repository carries scripts/sr-guard.sh (SR-WORK-OWNERSHIP decision 6)."""
    guard = repo.root / "scripts" / "sr-guard.sh"
    if not guard.is_file():
        return
    guard.chmod(guard.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    hooks = repo.common / "hooks"
    hooks.mkdir(exist_ok=True)
    link = hooks / "commit-msg"
    if link.is_symlink() or link.exists():
        return
    os.symlink(os.path.relpath(str(guard), str(hooks)), str(link))
    out("  commit guard: .git/hooks/commit-msg -> scripts/sr-guard.sh")
