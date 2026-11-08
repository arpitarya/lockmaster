---
type: Handoff
name: W-08
description: "Arpit, 2026-10-25: hold `lockmaster` on PyPI — checked free that day, but PyPI reserves a name only with a publish. npm dropped by L6."
item: W-08
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-11-08
updated_by: "Claude Code (Opus 5.5): the decider ruled a first upload from his machine; dist/ built and verified; rebuilt after W-16"
ball: arpit
---

# W-08 — hold the name on PyPI

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The release pipeline and 0.0.1 prepared: `.github/workflows/release.yml`, `scripts/release.py`, `__version__` 0.0.1, CHANGELOG cut | a tag publishes, no token stored | ✅ 2026-10-25 (Claude Code) |
| 1a | ~~The decider adds the pending trusted publishers and the `testpypi` / `pypi` GitHub environments, then pushes the tag~~ | — | ⤵ replaced 2026-11-08 by 1c–1d; trusted publishing is still how 0.1.0 and later publish |
| 1c | Claude Code builds `dist/` from `main` and runs the pipeline's checks on it: tests, lint, `twine check --strict`, every kit file in the wheel, the wheel installed alone and one change landed with it | the files to upload | ✅ 2026-11-08 (Claude Code) |
| 1d | The decider uploads 0.0.1 from his machine: `twine upload dist/*` | the PyPI name is ours | 🔴 decider decides |
| 1e | Claude Code, once 0.0.1 is on PyPI: `uv tool install --reinstall lockmaster` — the command every repository runs (W-16) comes from PyPI, not the local wheel | the published package in use | ⏳ after 1d |
| 2 | Keep or delete the npm org `@lockmaster` — created 2026-10-25 in Chrome a minute before L6 was ruled; it holds nothing | no loose end on npm | ✅ ruled 2026-11-07: kept empty, nothing published |

**Arpit, 2026-10-25:** *"to create an npm org, you go ahead and do it … for lock master and lock hyphen master, both of them."* — then, before `lock-master` was created: *"I want this to be Python only project. I don't believe we need npm."*

**Arpit, 2026-11-07:** *"the package is only for pypi"* — and on `@lockmaster`: *"Keep it empty"*.

**Arpit, 2026-11-08:** *"commit everything generate the build i will do the first publish from local"*.

**Model:** NONE — the decider's PyPI account; `dist/` is built and verified (2026-11-08).

## Goal

`lockmaster` is ours on PyPI before anyone else takes it. Nothing is published to npm ([SR-LAW-6](../../records/0008_LAW-6-python-only.md)).

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · PyPI | `pip index versions lockmaster` shows 0.0.1 | ⏳ — 2026-11-07: still *"No matching distribution found"* (pypi.org 404); no `v0.0.1` tag in the Mac clone |
| 2 · npm org | the decider has said keep or delete `@lockmaster`; `lock-master` was never created | ✅ 2026-11-07 — keep, empty |

## Blockers

The decider's PyPI account.

## Record affected

SR-LAW-6; SR-ARCHITECTURE decision 17 (a placeholder before 0.1.0).

## Hazards

- PyPI can refuse a first upload whose name is too similar to an existing project; that shows only at upload.
- The placeholder must say plainly that it is a placeholder: the repository stays private until 0.1.0 (SR-ARCHITECTURE decision 17).
- Keeping `@lockmaster` costs nothing and stops anyone else taking the scope; deleting it is an npm settings action the decider takes himself.

## Reference

- [SR-LAW-6](../../records/0008_LAW-6-python-only.md) · [W-01](../../archive/open/W-01-rule-the-laws.md)
