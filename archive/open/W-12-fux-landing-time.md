---
type: Handoff
name: W-12
description: "Cowork, 2026-10-28, reviewing the queue: W-09 step 4's measurement is in — fux's one landing took 599 s. W-09 said a landing of minutes goes back to Arpit."
item: W-12
filed: 2026-10-28
filed_by: "Cowork (Opus 5.5)"
updated: 2026-11-05
updated_by: "Cowork (Opus 5.5), closed — ruled A, keep"
ball: none
closed: 2026-11-05
---

# W-12 — fux's landing takes ten minutes: keep, move or switch off the rebuild

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The measurement: fux's one landing, **fux W-304** on 2026-10-26, went from queued to landed in **599 s** — `[generated]` rebuilds `.fux/index` and `llms*.txt` in a fresh landing worktree with no runtime cache, then three checks | the cost is known | ✅ 2026-10-28 (read off fux's change record in `.git/lockmaster/changes/`) |
| 2 | Arpit rules one of the three options below | fux's landings are affordable | ✅ 2026-11-05 — **A, keep** |
| 3 | The ruled option built in fux's `lockmaster.toml` (and in lockmaster, if option B needs it) | done | ✅ nothing to build: A is what fux's `[generated]` already does. Not re-checked today — fux's folder was not connected to this session |

**Arpit, 2026-11-05 (Cowork):** *"keep rebuilding on every landing"* — option A. The ten-minute landing is an accepted cost ([B-007](../../work/BACKLOG.md)).

**Model:** NONE — nothing to build.

## Why it matters now

Since W-11 every Claude Code turn that changed something in fux lands at its end. The landing runs in the background, so no turn waits, but each one holds fux's land lock for about ten minutes: changes queue behind it, and a fast session lands behind its own previous turn. W-09's own note said: *"if it is minutes, the fork goes back to Arpit."*

## The options

| | option | gives | costs |
|---|---|---|---|
| A | **Keep** — rebuild `.fux/index` on every landing (Arpit, 2026-10-26: *"Rebuild on landing"*) | `main`'s index is always `main`'s docs | ten minutes a landing; a queue in a busy fux |
| B | **Move** — take `.fux/index` out of `[generated]`; rebuild it in fux's own CI, or nightly, and land that as a change | landings take seconds | `main`'s index trails its docs until the next rebuild |
| C | **Switch off end-of-turn landing in fux** — `[land] auto = "off"`; fux lands on `lockmaster submit` only | nothing else changes | fux keeps the old problem W-11 fixed: finished work waits for someone to submit it |

**Recommendation:** first split the 599 s — how much is `fux ingest --no-fetch` and how much the checks — with one timed landing on the Mac; if the index is most of it, B. The number alone does not say which part is slow.

## Definition of done

- Arpit's ruling recorded here, with his words.
- fux's `lockmaster.toml` carries it — it already does; no second timed landing needed, since nothing changed.

## Record affected

fux's own `lockmaster.toml` and the record there that owns it; lockmaster's [SR-ARCHITECTURE](../../records/0101_architecture.md) decision 20 names this item.

## Reference

- [W-09](../../work/open/W-09-adopt-in-three-repos.md) step 4 · [W-11](W-11-land-every-turn-and-cowork-handoff.md)
