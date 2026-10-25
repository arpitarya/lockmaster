---
type: Log
description: "What shipped, when, and how it turned out — the evidence store the queue reconciles against."
---

# IMPLEMENTATION — what has landed

A row is earned by **landing**, never by being planned. The queue reconciles
against this file before an item may be closed
([SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rule 9). Newest first.

| date | item | what landed | outcome | evidence |
|---|---|---|---|---|
| 2026-10-25 | W-07 | `lockmaster status` (`--now`, `--write-now`); `lockmaster.now`, the one NOW.md renderer, written by every landing and by the kit's `now-ledger.py` | **built** — W-07 closed | `tests/test_status.py` |
| 2026-10-25 | W-06 | `lockmaster install <repo> [--backup]` and `lockmaster doctor`; `.claude/lockmaster.lock`; `scripts/bootstrap.py` archived; `records/RULE-SINCE` = first commit | **built** — W-06 closed; the wheel does not carry `kit/` yet (B-005) | `tests/test_install.py`; an install on a copy of this repo turns `scripts/check-work-system.py` green |
| 2026-10-25 | W-05 | `kit/claude/hooks/claim-guard.py` and `block-main.py`, wired in `kit/claude/settings.json` | **built** — W-05 closed; live here after `lockmaster install .` | `tests/test_hooks.py` |
| 2026-10-25 | W-04 | the core loop: `start`, `claim add`, `submit` → `run`, the land lock, landing, red set aside, cleanup, `abandon`, `queue` | **built** — W-04 closed | `tests/test_land.py`; two changes to one `WORKLOG.md` landed through this repo's own checks on a copy of it |
| 2026-10-25 | W-03 | `lockmaster.toml` reader, `lockmaster regen`, the three structural merge drivers and `lockmaster drivers` | **built** — W-03 closed | `tests/test_config.py`, `tests/test_regen.py`, `tests/test_merge.py` |
| 2026-10-25 | W-01 | L3–L7 as SR-LAW-3 … SR-LAW-7 (`0005`–`0009`); L6 changed by the decider to Python only, PyPI only; SR-LAWS, the register, `CLAUDE.md` | **ruled and recorded** — W-01 closed | the five records; `python3 scripts/check-work-system.py` |
| 2026-10-25 | W-02 | SR-ARCHITECTURE decisions 6 (auto-run), 11 (red set aside), 17 (PyPI only, private until 0.1.0) | **ruled and recorded** — W-02 closed; W-04 unblocked | `records/0101_architecture.md` |
| 2026-10-25 | setup | the work system, SR-ARCHITECTURE, W-01–W-09, `kit/`, `scripts/bootstrap.py`, the stub package | **landed** (uncommitted until the decider's first commit) | `python3 scripts/check-work-system.py` |
