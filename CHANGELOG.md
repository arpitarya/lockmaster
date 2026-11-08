# Changelog

All notable changes to lockmaster. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.0.3] - 2026-11-08

### Added

- `lockmaster install` scaffolds the rest of the work system a repository
  lacks: `AGENTS.md`, `docs/GLOSSARY.md`, the generic records, `work/README.md`,
  `NOW.md`, `BLOCKED.json`, `IMPLEMENTATION.md`, the `open/`, `compare/` and
  `proposals/` indexes, `archive/README.md` and the work system's scripts. A
  file that exists is never touched; a repository with its own `records/` gets
  none of the kit's records or scripts (W-18).

### Fixed

- The kit's `work/OPEN-WORK.md` template declares its empty inbox, so a fresh
  install passes `check-open-work-inbox.py` (W-18).

## [0.0.2] - 2026-11-08

### Changed

- Every repository but lockmaster runs the published package: the kit's hooks
  find lockmaster in the `lockmaster` command's own environment (`uv tool
  install lockmaster`, pipx) and no longer in a checkout beside the repository;
  the `landing` skill says the same (W-16).

## [0.0.1] - 2026-11-08

Uploaded from the decider's machine on 2026-11-08, built from `943afe6`: it
holds everything below, the 2026-10-25 cut and what landed after it.

### Added

- `lockmaster install` creates any of the six work files (`work/OPEN-WORK.md`,
  `BACKLOG.md`, `INTERVIEW.md`, `MACHINE.md`, `LESSONS.md`, `WORKLOG.md`) a
  repository lacks, from `kit/work/`, and never overwrites one; `doctor` names a
  missing one and a `WORKLOG.md` main has moved more than ten commits past; the
  kit's `work-files.py` tells a session, once at `Stop`, that changed files but
  none of WORKLOG, INTERVIEW or OPEN-WORK (W-15, SR-LAW-10).

- A landing stopped only by uncommitted edits in `main`'s checkout now
  **waits** instead of going red, and lands by itself — no resubmit, no
  second run of the checks — once they are committed, saved or undone; it is
  redone first if `main` moved. `status` and `doctor` name the overlapping
  edits before the landing, and the kit's `claim-guard.py` warns on them
  (W-10, SR-ARCHITECTURE decision 11).

- Laws L8 and L9: lockmaster handles parallel requests; Cowork and Claude Code
  work in parallel with no manual step (2026-11-05, SR-LAW-8, SR-LAW-9).
- Law L10: the work files are always up to date in every repository
  lockmaster is installed in (2026-11-05, SR-LAW-10).
- A handoff lands only what was handed over: a file edited after it, and not
  handed off again, holds it; handoffs naming a common file land together
  under all their messages; `queue` marks a handoff a pickup missed (W-14).

### Fixed

- The kit's `docket` skill no longer lists the queue's groups; it walks the
  groups each repository's queue names, so a repository with its own group
  needs no hand edit to the installed skill (W-15).

- Sessions starting at the same moment are no longer refused when git trips
  on another worktree being added (`git.worktree_add` retries it; SR-LAW-8).
- `work/NOW.md`, the live ledger, no longer stops a landing: a landing that
  changes it carries the checkout's copy (W-10, SR-ARCHITECTURE decision 8a).

- Saves in the same second no longer collide; handoffs written at once no
  longer overwrite each other; two end-of-turn landings of one session no
  longer run at once; a pickup lands a handoff written while it ran (W-13).

- A Claude Code session's changes land at the end of every turn and stay open,
  their worktree following `main`; a change that cannot land is held for its
  agent, not sent to the decider; `claude --worktree` worktrees are adopted
  (`lockmaster sync`, the kit's `auto-land.py`; 2026-10-28, W-11,
  SR-ARCHITECTURE decision 20). The landing runs in the background; what it
  did is said at the next turn's end. `[land] auto = "off"` turns it off.
- `lockmaster save -m … <path>…` lands edits made in `main`'s checkout, or —
  on a surface that cannot commit, such as the Cowork bridge — hands them off;
  `lockmaster pickup` (run by the kit's hook) lands the handoffs;
  `lockmaster can-commit` says which surface this is (W-11, decision 19).
- The kit's `landing` skill: how a change reaches `main` from Cowork or Claude Code.
- Merge drivers heal: every `lockmaster run` re-points a driver registered with
  another machine's paths, `install` on a surface that cannot commit registers
  none, and `doctor` names one (W-11, decision 10).

- lockmaster's own git steps run a repository's gate hooks (`commit-msg`,
  `pre-commit`, …) and not its `post-*` hooks (2026-10-26, W-09,
  SR-ARCHITECTURE decision 18): fux's re-index hooks no longer run inside a
  landing or in `main`'s checkout.
- Tests for the kit's disk-budget, NOW-ledger, worktree-cleanup and lock-release
  hooks, ported from fux's own (2026-10-26, W-09).

### Changed

- Uncommitted edits in `main`'s checkout identical to a landing no longer stop
  its fast-forward; differing ones are named in the red reason instead of an
  empty line (W-11, decision 8a).

- The kit's hooks read any repo's inbox heading (`## Blocked on …`), name no
  law number in the disk-budget messages, and sweep write locks past their TTL
  at Stop; worktree cleanup counts fux's and codelaw's build output
  (`htmlcov`, `.eggs`, `runtime`, `.codelaw`) (2026-10-26, W-09).

- The kit no longer carries a CI workflow (2026-10-25, W-09): it held
  lockmaster's own `ci.yml`, which `lockmaster install --backup` would have
  moved a target repository's CI aside for. A repository's CI is its own.

### Added (cut 2026-10-25)

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
- The release pipeline (2026-10-25): a `v<version>` tag is tested on three
  operating systems and two Pythons, built, checked, installed from the wheel
  and made to land a change, then published to TestPyPI and PyPI by trusted
  publishing, with a GitHub release; `scripts/release.py` cuts a version.
- The wheel carries the kit, so `lockmaster install` works from a pip install.
- Two kit hooks (2026-10-25): `claim-guard.py` warns on a write outside the
  claim; `block-main.py` refuses an agent's commit or push to `main`.
- The repository: the design of record (SR-ARCHITECTURE), the work system
  (2026-10-25).
