---
type: Handoff
name: W-05
description: "Arpit, 2026-10-25: build step 3 of the lockmaster design."
item: W-05
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: arpit
---

# W-05 — the claim hook and the block-main hook

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `kit/claude/hooks/claim-guard`: a write outside the session's claim is warned | agents stay inside their claim | ⏳ |
| 2 | `kit/claude/hooks/block-main`: an agent's commit or push to `main` is refused | only lockmaster writes to `main` | ⏳ |
| 3 | Wired in `kit/claude/settings.json`; installed here by bootstrap | both live in this repo | ⏳ |

**Arpit, 2026-10-25:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out."*

**Model:** Sonnet: two small hooks against a settled contract.

## Goal

An agent cannot quietly step outside its claim, and cannot commit to `main` behind lockmaster's back.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · claim | a write outside the claim prints the claim and the path, in the hook's output | ⏳ |
| 2 · main | `git commit` on `main` and `git push origin main` from an agent session are refused; lockmaster's own landing passes | ⏳ |

## Blockers

W-04 (the claim and the landing must exist).

## Record affected

SR-ARCHITECTURE decisions 5 and 12.

## Hazards

- The decider must still be able to commit to `main` by hand: the hook binds agent sessions only.

## Reference

- [SR-ARCHITECTURE](../../records/0101_architecture.md)
