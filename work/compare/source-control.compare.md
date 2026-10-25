---
type: Compare
description: "Should agent-heavy work on one laptop keep git, build its own source control as Anthropic did, add a lander on top of git, or move to Jujutsu?"
date: 2026-10-25
---

# Source control for many agents on one machine

> **Verdict:** decided · **git, with lockmaster landing changes onto `main` one at a time** · confidence: high for today's scale · reopen-trigger below.

## Context

Anthropic replaced git for its monorepo with **Scion** (announced
2026-10-13): changesets in a write-ahead log, commits and merges on a server,
sparse clients, no merge queue, about 30,000 merges a day by September 2026.
Its authors call it "by no means a suitable replacement for git for general
use." The question here is narrower: several agents on **one laptop** keep
colliding in **one checkout** — swept commits, conflicting generated files,
worktrees filling the disk, work stranded on branches.

## Options

| | option | what it changes |
|---|---|---|
| A | git as it is, plus rules in the records | nothing mechanical; the collisions recur |
| B | a new system in Scion's mould | everything — server, client, review, CI |
| C | **git + lockmaster** | one lander; claims; generated files rebuilt; worktrees removed |
| D | Jujutsu (`jj`) over git | conflicts stored rather than blocking; an operation log |

## Matrix

| | stops swept commits | stops generated-file conflicts | stops worktree pile-up | keeps every tool working | cost |
|---|---|---|---|---|---|
| A | no | no | partly (cleanup hooks) | yes | none |
| B | yes | yes | yes | **no** — forge, CI, registries all change | very high |
| C | **yes** (claims) | **yes** (rebuilt) | **yes** (removed on landing) | **yes** — every landing is a git commit | low |
| D | partly | no | no | mostly | agents know git far better than `jj` |

## Consequences

C is SR-ARCHITECTURE. D stays open as backlog row B-003: it composes with C
(lockmaster could drive `jj`) if git's conflict handling becomes the limit.

## References

- [Redesigning source control at Anthropic](https://www.anthropic.com/engineering/redesigning-source-control) · [SR-ARCHITECTURE](../../records/0101_architecture.md)

## Reopen-trigger

A repository here passes **500 landings a day**, or its working tree passes
**the L2 budget on a fresh clone**, or the median wait in `lockmaster queue`
passes **10 minutes**.
