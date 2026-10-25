---
type: Handoff
name: W-08
description: "Arpit, 2026-10-25: hold `lockmaster` on npm and PyPI — checked free that day, but no registry reserves a name without a publish."
item: W-08
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: arpit
---

# W-08 — hold the name on npm and PyPI

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Create the npm org: `npm org create lockmaster` (fails if a user already owns the scope) | `@lockmaster/*` is ours | 🔴 decider decides |
| 2 | Publish a stub 0.0.1 of `lockmaster` to PyPI from this repo (`python3 -m build`, `twine upload`) | the PyPI name is ours | 🔴 decider decides |
| 3 | Publish a stub 0.0.1 of `lockmaster` to npm, in the form L6 rules | the npm name is ours | 🔴 decider decides |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** NONE — the decider's accounts and two-factor; an agent prepares the stubs.

## Goal

`lockmaster` is ours on npm (package and scope) and on PyPI before anyone else takes it.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · npm org | `npm org ls lockmaster` lists the decider | ⏳ |
| 2 · PyPI | `pip index versions lockmaster` shows 0.0.1 | ⏳ |
| 3 · npm | `npm view lockmaster version` shows 0.0.1 | ⏳ |

## Blockers

The decider's accounts; the npm form waits on L6 (W-01).

## Record affected

no SR affected until L6 is ruled; then SR-ARCHITECTURE's distribution decision.

## Hazards

- PyPI can refuse a first upload whose name is too similar to an existing project; that would only show at upload.
- A stub must say plainly that it is a placeholder.

## Reference

- [W-01](W-01-rule-the-laws.md)
