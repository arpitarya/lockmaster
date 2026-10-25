---
type: Handoff
name: W-01
description: "Arpit, 2026-10-25: lockmaster's repo set up with L0–L2; five more laws are proposed and need his ruling."
item: W-01
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: none
closed: 2026-10-25
---

# W-01 — rule the five proposed laws

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The decider reads the five proposals below | what binds lockmaster beyond L0–L2 | ✅ ruled 2026-10-25 |
| 2 | An agent writes each accepted law as its own `SR-LAW-n` record | one home per law (L0) | ✅ `0005`–`0009` |
| 3 | SR-LAWS gets its rows, `CLAUDE.md` its lines, the register its rows | the law is findable | ✅ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet once ruled: five short records in the shape of SR-LAW-2.

## Ruling

**Arpit, 2026-10-25 (Cowork):** *"All the blockers, I accept whatever is said over there."* — then, on L6: *"I want this to be Python only project. I don't believe we need npm."*

- **L3, L4, L5, L7 accepted** as proposed → SR-LAW-3, SR-LAW-4, SR-LAW-5, SR-LAW-7.
- **L6 changed:** not *PyPI and npm* but **Python only, PyPI only** → SR-LAW-6.

## Goal

Every rule lockmaster cannot break is a law, ruled by the decider, in one record each.

| proposed | text | why | recommendation |
|---|---|---|---|
| **L3** | lockmaster never loses work: no landing, cleanup or abandon discards a commit, an unsaved file or a branch not already in `main`; never `--force`, `branch -D`, `reset --hard`, `clean`; what would lose data stops red for the decider | the product's whole promise; already the rule for cleanup (SR-WORK-CLEANUP, ruled 2026-10-24) | **accept** |
| **L4** | zero runtime dependencies — Python standard library only | it installs into every repo and runs in hooks; nothing to resolve, nothing to audit | **accept** |
| **L5** | git stays the store — every landing is a plain git commit, readable with git alone; lockmaster keeps no history of its own | lockmaster can be removed without losing anything | **accept** |
| **L6** | one tool, two registries — `lockmaster` on PyPI and on npm, the same version, identical behaviour | the name was checked free on both (2026-10-25); hosts are Python and Node repos | **accept, and pick the npm form:** (a) a thin npm launcher that runs the Python package — recommended; (b) a second implementation in Node |
| **L7** | no model in the lander — lockmaster never calls an AI model; agents call lockmaster | determinism: the same queue lands the same way every time | **accept** |

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · ruled | each of L3–L7 accepted, changed or rejected, in the decider's words | ✅ |
| 2 · written | one `SR-LAW-n` record per accepted law; SR-LAWS, the register and `CLAUDE.md` updated in the same change | ✅ |

## Blockers

The decider's ruling (inbox).

## Record affected

SR-LAWS decision 1; SR-ARCHITECTURE decisions 2, 11 and its Consequences.

## Hazards

- A law outranks every record (L0): write each one narrowly — what it forbids, not how it is built.

## Reference

- [SR-LAWS](../../records/0001_LAWS.md) · [SR-ARCHITECTURE](../../records/0101_architecture.md)
