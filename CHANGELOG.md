# Changelog

All notable changes to lockmaster. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- The core loop (2026-10-25): `start`, `claim add`, `submit` (which starts
  landing), `run`, `queue`, `abandon` — claimed paths only, landed one at a
  time onto `main` by fast-forward with a `Lockmaster-Change:` trailer; a red
  change is set aside with its reason; worktree and branch removed only when
  nothing is lost.
- `lockmaster.toml` (2026-10-25): `[main]`, `[checks]`, `[generated]`,
  `[merge]`, read the same on Python 3.9 and 3.11+.
- Generated files rebuilt, never merged (`lockmaster regen`), and three
  structural merge drivers — `append-newest-first`, `table-rows`, `append` —
  usable from plain git (`lockmaster drivers`) (2026-10-25).
- `lockmaster status` (with `--now` for `work/NOW.md`), `lockmaster doctor`,
  and `lockmaster install <repo>`, which merges the kit's hooks into a
  repository's settings and pins the kit (2026-10-25).
- Two kit hooks (2026-10-25): `claim-guard.py` warns on a write outside the
  claim; `block-main.py` refuses an agent's commit or push to `main`.
- The repository: the design of record (SR-ARCHITECTURE), the work system
  (2026-10-25).
