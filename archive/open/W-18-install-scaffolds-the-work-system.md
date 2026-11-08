---
type: Handoff
name: W-18
description: "Arpit, 2026-11-08: everything milo was missing — records, AGENTS.md, the full work/ — becomes part of lockmaster, so every repository it is installed in gets it."
item: W-18
filed: 2026-11-08
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-11-08
updated_by: "Cowork (Opus 5.5): built and closed in the same change"
ball: done
---

# W-18 — `install` scaffolds the whole work system

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `kit/scaffold/` — AGENTS.md, the glossary, the generic records, the rest of `work/`, `archive/README.md`, the three work-system scripts | one source for what milo had to be given by hand | ✅ |
| 2 | `install` writes each scaffold file a repository lacks; `records/` and `scripts/` only where there is no register | a new repository gets the whole system; fux, codelaw, sheetpane are untouched | ✅ |
| 3 | the inbox template carries its date, so a fresh install passes its own checks | `check-work-system.py`, `check-open-work-inbox.py`, `doctor` and the guard all green on a scratch install | ✅ `tests/test_scaffold.py` |
| 4 | reaches other repositories with the next release | milo was given the same files by hand today | ⏳ the next release (after W-17) |

**Arpit, 2026-11-08:** *"All these things should be part of Lock Master as well"* — the records directory, `AGENTS.md`, the work directory set up from the latest lockmaster; *"no need for ci for now"*.

**Model:** Opus: a kit change that writes into other repositories.

## Goal

A repository lockmaster is installed in gets the whole work system, not only the six work files.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · scaffold | every file in `kit/scaffold/` is written where missing, never over an existing one | ✅ |
| 2 · no mixing | a repository with its own `records/` gets none of the kit's records or scripts | ✅ |
| 3 · green | the scaffolded tree passes its own checks | ✅ |
| 4 · packaged | every `kit/scaffold` directory is in `pyproject.toml` | ✅ `tests/test_packaging.py` |

## Blockers

None.

## Record affected

SR-ARCHITECTURE decision 15.

## Hazards

- `install` now writes `work/NOW.md`, so the NOW ledger runs in every new install; a repository that wants none deletes it (`tests/test_hooks.py` `WithoutTheWorkSystem`).
- The kit's records are copies of lockmaster's own, with lockmaster's item ids written `**lockmaster W-nn**`; they drift from lockmaster's when lockmaster's change, and a repository keeps the copy it was given.

## Reference

- `src/lockmaster/install.py` — `scaffold_files`
- `tests/test_scaffold.py`
