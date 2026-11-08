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
| 2026-11-08 | W-15 (step 4) | the kit installed and landed in codelaw `794da39`; the kit's docket skill names no queue group (`a86244f`), re-landed in sheetpane `6c971b6` and fux `7e7cfe7`; a test fails on a kit skill listing queue groups | **built** — W-15 closed; milo left alone (ruled) | `tests/test_kit_hooks.py`, `tests/test_work_files.py` |
| 2026-11-07 | W-15 (step 4, in part) | the new kit (W-10, W-15) installed and landed in sheetpane `1e04930` and fux `4c135a0`; both already had all six work files | **built** — milo waits on the decider, codelaw on its live session | `lockmaster queue` in each |
| 2026-11-07 | W-09 (step 4–5) | milo's and sheetpane's adoption (the kit, `lockmaster.toml`, `.gitattributes`) landed — their first landings, milo `4a99fa8`, sheetpane `9285efc`; fux's held W-11 handoff landed the same way | **built** — W-09 closed | `lockmaster queue` in each: the handoff dropped as landed |
| 2026-11-07 | W-15 (steps 1–3) | `kit/work/` templates, `install` writes a missing work file (never overwrites); `doctor` names a missing work file and a stale `WORKLOG.md`; the kit's `work-files.py` Stop hook; SR-LAW-10 `built: yes` | **built** — the installs into the other four repositories follow | `tests/test_work_files.py` (13 tests) |
| 2026-11-07 | W-10 | status `waiting`: a landing stopped only by uncommitted edits in main's checkout keeps its checked commit and lands by itself once they clear (redone if `main` moved); `status`/`doctor` name the overlap; `claim-guard.py` warns on a checkout edit a change claims; a landing that changes `work/NOW.md` carries the checkout's copy | **built** — W-10 closed | `tests/test_waiting.py` (15 tests); the whole suite green on Python 3.9 |
| 2026-11-07 | W-14 | step 4: SR-LAW-9 decision 4 met by W-10; register `built: yes` | **built** — W-14 closed | `tests/test_parallel.py`, `tests/test_waiting.py` |
| 2026-11-05 | W-13 | `tests/test_parallel.py` (six concurrent processes per case) and its three fixes, landed in `9c747a7` | **built** — W-13 closed 2026-11-07 | `cd tests && python3 -m unittest test_parallel` green on Python 3.9, 2026-11-07 |
| 2026-10-28 | W-11 | `lockmaster sync` and the kit's `auto-land.py` (land at every `Stop`, kept open; held, not red; `claude --worktree` adopted); `save`, `handoff`, `pickup`, `can-commit` and `surface.py`; identical checkout edits accepted by the fast-forward; `[land] auto`; the `landing` skill; installed in lockmaster, codelaw, fux, milo, sheetpane; the landing in the background; merge drivers re-pointed by every `run` | **built** — W-11 closed | `tests/test_autoland.py`; 114 tests green on Python 3.9, 3.11, 3.13 |
| 2026-10-25 | W-08 (step 1) | the release pipeline (`.github/workflows/release.yml`), `scripts/release.py`, one version source, the wheel carrying `kit/` (B-005 closed), 0.0.1 cut | **built** — publishing waits on the decider's trusted-publisher setup and tag push | `tests/test_release.py`, `tests/test_packaging.py`; the built 0.0.1 wheel passes `twine check --strict` and, installed alone in a fresh venv, installs the kit and lands a change |
| 2026-10-25 | W-07 | `lockmaster status` (`--now`, `--write-now`); `lockmaster.now`, the one NOW.md renderer, written by every landing and by the kit's `now-ledger.py` | **built** — W-07 closed | `tests/test_status.py` |
| 2026-10-25 | W-06 | `lockmaster install <repo> [--backup]` and `lockmaster doctor`; `.claude/lockmaster.lock`; `scripts/bootstrap.py` archived; `records/RULE-SINCE` = first commit | **built** — W-06 closed; the wheel does not carry `kit/` yet (B-005) | `tests/test_install.py`; an install on a copy of this repo turns `scripts/check-work-system.py` green |
| 2026-10-25 | W-05 | `kit/claude/hooks/claim-guard.py` and `block-main.py`, wired in `kit/claude/settings.json` | **built** — W-05 closed; live here after `lockmaster install .` | `tests/test_hooks.py` |
| 2026-10-25 | W-04 | the core loop: `start`, `claim add`, `submit` → `run`, the land lock, landing, red set aside, cleanup, `abandon`, `queue` | **built** — W-04 closed | `tests/test_land.py`; two changes to one `WORKLOG.md` landed through this repo's own checks on a copy of it |
| 2026-10-25 | W-03 | `lockmaster.toml` reader, `lockmaster regen`, the three structural merge drivers and `lockmaster drivers` | **built** — W-03 closed | `tests/test_config.py`, `tests/test_regen.py`, `tests/test_merge.py` |
| 2026-10-25 | W-01 | L3–L7 as SR-LAW-3 … SR-LAW-7 (`0005`–`0009`); L6 changed by the decider to Python only, PyPI only; SR-LAWS, the register, `CLAUDE.md` | **ruled and recorded** — W-01 closed | the five records; `python3 scripts/check-work-system.py` |
| 2026-10-25 | W-02 | SR-ARCHITECTURE decisions 6 (auto-run), 11 (red set aside), 17 (PyPI only, private until 0.1.0) | **ruled and recorded** — W-02 closed; W-04 unblocked | `records/0101_architecture.md` |
| 2026-10-25 | setup | the work system, SR-ARCHITECTURE, W-01–W-09, `kit/`, `scripts/bootstrap.py`, the stub package | **landed** (uncommitted until the decider's first commit) | `python3 scripts/check-work-system.py` |
