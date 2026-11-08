---
type: Handoff
name: W-16
description: "Arpit, 2026-11-08: every repository runs the published lockmaster package, not the checkout beside it; milo's trackers move to its root work/."
item: W-16
filed: 2026-11-08
filed_by: "Arpit (Claude Code, Opus 5.5)"
updated: 2026-11-08
updated_by: "Claude Code (Opus 5.5): closed — milo at its root, the kit from the package in every repository"
ball: done
---

# W-16 — every repository consumes the published package

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The kit's hooks (`auto-land.py`, `now-ledger.py`) find lockmaster in the `lockmaster` command's environment, never in `../lockmaster/src`; the `landing` skill says so; `dist/` rebuilt | a repository runs only a release | ✅ `963c3e5` |
| 2 | `uv tool install` the 0.0.1 wheel on the Mac — the same bytes W-08 uploads | the `lockmaster` command | ✅ `uv tool install` — `~/.local/share/uv/tools/lockmaster` |
| 3 | milo: `git mv tv-movies/work/{OPEN-WORK,INTERVIEW,WORKLOG,IMPLEMENTATION}.md work/`, links and merge rules re-pointed, the kit installed from the command (adds the missing work files) | milo's work files at its root | ✅ milo `2e14f57` (the Cowork session's uncommitted #21–#25, landed for it first), `de3be12` (the move; 48 files re-linked) |
| 4 | codelaw, fux, sheetpane: the kit reinstalled and `lockmaster drivers` run from the command | their hooks and merge drivers come from the release | ✅ codelaw `5ca829a`, fux `ddd49f5`, sheetpane `b1de5c8` |
| 5 | Once W-08 is on PyPI: `uv tool install --reinstall lockmaster` from PyPI | the command is the published one | ⤵ moved to W-08 step 1e |

**Arpit, 2026-11-08:** *"setup lockmaster for milo at root migrate whatever it on the list to root"* — reverses 2026-11-07's *"Leave milo alone"* — and *"setup milo as a package in all the repo's from her on we publish the package then have all consumer consume it"* (read as: lockmaster, the package being published).

## Goal

A change to lockmaster reaches another repository only by a release (SR-ARCHITECTURE decision 17).

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 | `tests/test_kit_hooks.py` — the command's environment found, a checkout beside the repository never used | ✅ |
| 2 | In milo, codelaw, fux and sheetpane, `lockmaster doctor` from the installed command is clean and the merge drivers name the command's `merge.py` | ✅ 2026-11-08 — codelaw's doctor names three earlier kept branches, nothing new |
| 3 | milo's `tv-movies/work/` is gone; `work/` holds the six files | ✅ |

## Record affected

SR-ARCHITECTURE decision 17; SR-LAW-10 (milo).

## Hazards

- milo's checkout holds uncommitted edits from September–October (root `CLAUDE.md`, `README.md`, `PLAN.md`, `tv-movies/server/…`) and an untracked `apps/`: none is touched; the move names only its own paths.
- A hook run by an interpreter other than the command's imports the package across Python versions; it is pure Python ≥ 3.9 (L4), so that holds.
