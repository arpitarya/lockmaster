---
type: Handoff
name: W-02
description: "Arpit, 2026-10-25: the three open questions the lockmaster design doc ended on."
item: W-02
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: arpit
---

# W-02 — three design forks

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The decider rules the three forks below | W-04 can build the loop | 🔴 decider decides |
| 2 | An agent writes each ruling into SR-ARCHITECTURE | the record says what is true | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** NONE until ruled; then Sonnet for the record edit.

## Goal

SR-ARCHITECTURE leaves three things open. Each has a recommendation:

| fork | options | recommendation |
|---|---|---|
| **auto-run** | (a) `submit` starts `run` when no lander holds the lock; (b) `run` only when someone runs it | **(a)** — nobody forgets to land; the lock still keeps it to one |
| **a red change** | (a) it stops the queue until fixed; (b) it is set aside and the next change lands | **(b)** — one bad change should not hold up the rest; red goes to the inbox either way |
| **visibility** | (a) private until 0.1.0; (b) public now | **(a)** — public when the core loop works; the name is held by W-08 either way |

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · ruled | the three forks decided, in the decider's words | ⏳ |
| 2 · recorded | SR-ARCHITECTURE decisions 6–8 say what was ruled | ⏳ |

## Blockers

The decider's ruling (inbox).

## Record affected

SR-ARCHITECTURE decisions 6–8.

## Hazards

- A red change set aside must still be visible: `lockmaster queue` shows it until it lands or is abandoned.

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md)
