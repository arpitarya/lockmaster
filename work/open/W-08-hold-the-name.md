---
type: Handoff
name: W-08
description: "Arpit, 2026-10-25: hold `lockmaster` on PyPI — checked free that day, but PyPI reserves a name only with a publish. npm dropped by L6."
item: W-08
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Claude Code (Opus 5.5): the release pipeline built, 0.0.1 prepared"
ball: arpit
---

# W-08 — hold the name on PyPI

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The release pipeline and 0.0.1 prepared: `.github/workflows/release.yml`, `scripts/release.py`, `__version__` 0.0.1, CHANGELOG cut | a tag publishes, no token stored | ✅ 2026-10-25 (Claude Code) |
| 1a | The decider adds the pending trusted publishers on pypi.org and test.pypi.org and the `testpypi` / `pypi` GitHub environments (CONTRIBUTING.md §Releasing) | the pipeline may publish | 🔴 decider decides |
| 1b | The decider pushes `main` and the tag: `git tag -a v0.0.1 -m "lockmaster 0.0.1" && git push origin main v0.0.1`, then approves the `pypi` environment | the PyPI name is ours | 🔴 decider decides |
| 2 | Keep or delete the npm org `@lockmaster` — created 2026-10-25 in Chrome a minute before L6 was ruled; it holds nothing | no loose end on npm | 🔴 decider decides |

**Arpit, 2026-10-25:** *"to create an npm org, you go ahead and do it … for lock master and lock hyphen master, both of them."* — then, before `lock-master` was created: *"I want this to be Python only project. I don't believe we need npm."*

**Model:** NONE — the decider's PyPI and GitHub accounts; the build, the pipeline and the version are prepared (2026-10-25).

## Goal

`lockmaster` is ours on PyPI before anyone else takes it. Nothing is published to npm ([SR-LAW-6](../../records/0008_LAW-6-python-only.md)).

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · PyPI | `pip index versions lockmaster` shows 0.0.1 | ⏳ |
| 2 · npm org | the decider has said keep or delete `@lockmaster`; `lock-master` was never created | ⏳ |

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
