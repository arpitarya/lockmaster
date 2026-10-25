#!/usr/bin/env python3
"""Cut and verify a lockmaster release — SR-ARCHITECTURE decision 17.

    python3 scripts/release.py prepare 0.1.0   # bump __version__, cut CHANGELOG's [Unreleased] into [0.1.0]
    python3 scripts/release.py check v0.1.0    # CI: the tag, __version__ and a CHANGELOG section agree
    python3 scripts/release.py notes v0.1.0    # CI: that version's CHANGELOG section, for the GitHub release

The version has one source, `src/lockmaster/__init__.py`; pyproject.toml reads
it. A release is the tag `v<version>` pushed to GitHub: `.github/workflows/
release.yml` tests, builds, verifies and publishes it (TestPyPI, then PyPI).
Python >= 3.9, standard library only.
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)((?:a|b|rc)\d+)?$")
INIT_RE = re.compile(r'^__version__ = "([^"]+)"$', re.M)


class ReleaseError(Exception):
    pass


def current(root=ROOT):
    m = INIT_RE.search((root / "src" / "lockmaster" / "__init__.py").read_text(encoding="utf-8"))
    if not m:
        raise ReleaseError("no `__version__ = \"…\"` line in src/lockmaster/__init__.py")
    return m.group(1)


def key(version):
    m = VERSION_RE.match(version)
    if not m:
        raise ReleaseError("not a release version (X.Y.Z, optionally aN, bN or rcN): " + version)
    pre = m.group(4) or ""
    rank = {"a": 0, "b": 1, "r": 2}.get(pre[:1], 3)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), rank, int(re.sub(r"\D", "", pre) or 0))


def section(changelog, version):
    """The body of `## [version]` in CHANGELOG.md, or None."""
    m = re.search(r"^## \[{}\][^\n]*\n(.*?)(?=^## \[|\Z)".format(re.escape(version)), changelog, re.M | re.S)
    return m.group(1).strip() if m else None


def prepare(version, root=ROOT, today=None):
    old = current(root)
    if key(version) <= key(old):
        raise ReleaseError("{} is not newer than the current {}".format(version, old))
    log_path = root / "CHANGELOG.md"
    log = log_path.read_text(encoding="utf-8")
    if section(log, version) is not None:
        raise ReleaseError("CHANGELOG.md already has a [{}] section".format(version))
    unreleased = section(log, "Unreleased")
    if not unreleased:
        raise ReleaseError("CHANGELOG.md's [Unreleased] section is empty: nothing to release")
    stamp = (today or date.today()).isoformat()
    log = re.sub(r"^## \[Unreleased\][^\n]*\n.*?(?=^## \[|\Z)",
                 "## [Unreleased]\n\n## [{}] - {}\n\n{}\n\n".format(version, stamp, unreleased),
                 log, count=1, flags=re.M | re.S)
    log_path.write_text(log.rstrip("\n") + "\n", encoding="utf-8")
    init = root / "src" / "lockmaster" / "__init__.py"
    init.write_text(INIT_RE.sub('__version__ = "{}"'.format(version), init.read_text(encoding="utf-8")),
                    encoding="utf-8")
    return old


def check(tag, root=ROOT):
    if not tag.startswith("v"):
        raise ReleaseError("a release tag is v<version> (got {})".format(tag))
    version = tag[1:]
    key(version)
    have = current(root)
    if have != version:
        raise ReleaseError("tag {} but src/lockmaster/__init__.py says {}".format(tag, have))
    if not section((root / "CHANGELOG.md").read_text(encoding="utf-8"), version):
        raise ReleaseError("CHANGELOG.md has no non-empty [{}] section".format(version))
    return version


def main(argv):
    if len(argv) != 2 or argv[0] not in ("prepare", "check", "notes"):
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    mode, arg = argv
    try:
        if mode == "prepare":
            old = prepare(arg)
            print("{} -> {}: src/lockmaster/__init__.py and CHANGELOG.md updated.".format(old, arg))
            print("Next: commit both (the decider, or through `lockmaster submit`), then\n"
                  "  git tag -a v{0} -m \"lockmaster {0}\" && git push origin main v{0}".format(arg))
        elif mode == "check":
            print("release {} checks out".format(check(arg)))
        else:
            print(section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), check(arg)))
    except ReleaseError as e:
        print("release: " + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
