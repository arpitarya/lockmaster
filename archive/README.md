# `archive/` — the one archive, and where each thing went

**There is exactly ONE archive directory, and it is this one, at the repo
root.** Anything archived is moved here, into a directory mirroring where it
came from. This README is the **map**: every archived doc gets a row naming its
**live successor**.

## Archive is not evidence

A doc in here may be *named*. It may never be *cited as backing a live claim*
— nothing guarantees an archived file was not overwritten after it was
retired. Entries are frozen; **relative links inside them are not repaired**.
Rules: [SR-WORK-ARCHIVE](../records/0057_WORK-archive.md).

## Layout — the archive mirrors the live tree

| directory | holds |
|---|---|
| `open/` | closed work items' detail files, byte for byte |
| `records/` | retired records (L1) |
| `compare/` | decided forks whose triggers were ported into a record |
| `proposals/` | implemented or rejected proposals |
| `scripts/` | retired scripts |

## `open/`

| file | closed | where the live answer lives now |
|---|---|---|
| [W-01-rule-the-laws.md](open/W-01-rule-the-laws.md) | 2026-10-25 — ruled: L3, L4, L5, L7 accepted; L6 changed to Python only | [SR-LAW-3](../records/0005_LAW-3-never-lose-work.md) … [SR-LAW-7](../records/0009_LAW-7-no-model-in-the-lander.md); [SR-LAWS](../records/0001_LAWS.md) |
| [W-02-design-forks.md](open/W-02-design-forks.md) | 2026-10-25 — ruled: auto-run, red set aside, private until 0.1.0 | [SR-ARCHITECTURE](../records/0101_architecture.md) decisions 6, 11, 17 |
| [W-03-generated-files-and-merge-drivers.md](open/W-03-generated-files-and-merge-drivers.md) | 2026-10-25 — built: `lockmaster.toml`, `regen`, the three merge drivers | [SR-ARCHITECTURE](../records/0101_architecture.md) decisions 9, 10, 13 · `src/lockmaster/` |
| [W-04-core-loop.md](open/W-04-core-loop.md) | 2026-10-25 — built: start, claim, submit, run, queue, abandon | [SR-ARCHITECTURE](../records/0101_architecture.md) decisions 3–8, 11 · `src/lockmaster/land.py` |
| [W-05-claim-and-block-main-hooks.md](open/W-05-claim-and-block-main-hooks.md) | 2026-10-25 — built: `claim-guard.py`, `block-main.py` | [SR-ARCHITECTURE](../records/0101_architecture.md) decisions 5, 12 · `kit/claude/hooks/` |
| [W-06-install.md](open/W-06-install.md) | 2026-10-25 — built: `lockmaster install`, `doctor`; `bootstrap.py` retired | [SR-ARCHITECTURE](../records/0101_architecture.md) decisions 14, 15 · `src/lockmaster/install.py` |
| [W-07-status.md](open/W-07-status.md) | 2026-10-25 — built: `lockmaster status`, NOW.md as its view | [SR-ARCHITECTURE](../records/0101_architecture.md) decision 14 · [SR-WORK-NOW](../records/0061_WORK-now.md) |

## `records/`

| file | retired | successor |
|---|---|---|

## `scripts/`

| file | retired | successor |
|---|---|---|
| [bootstrap.py](scripts/bootstrap.py) | 2026-10-25 — W-06 | `lockmaster install .` ([`src/lockmaster/install.py`](../src/lockmaster/install.py), [SR-ARCHITECTURE](../records/0101_architecture.md) decision 15); the checks it ran are CI's |

## `backlog/`

| id | closed | what absorbed it |
|---|---|---|
| B-005 | 2026-10-25 — the wheel carries `kit/` | `pyproject.toml` `[tool.setuptools]`; `tests/test_packaging.py`; the release workflow's "the wheel carries the kit" and verify steps |
