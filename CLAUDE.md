# CLAUDE.md — the agent contract for lockmaster

This file is binding. It carries **pointers, never rules**: every rule lives in
exactly one record under [`records/`](records/README.md) and nothing here
restates one ([SR-LAW-0](records/0002_LAW-0-authority.md)). Read this, then
[`work/INTERVIEW.md`](work/INTERVIEW.md), before your first substantive change.

## Law zero — the records are always up to date

Stated once in [SR-LAW-0](records/0002_LAW-0-authority.md) decision 1a — three
obligations; the third cannot be enforced and is the only thing covering
coherence. The gate for the first two is [SR-WORK-OWNERSHIP](records/0058_WORK-ownership.md)
decisions 3 and 6. Install its `commit-msg` hook once:

```bash
ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg
```

## Triage first — a human-blocked queue stops the session

**Before any work, read [`work/OPEN-WORK.md`](work/OPEN-WORK.md)** and ask: *is
any item agent-closable right now?* If none is, the session's **first** output
is the blocked-on-the-decider list and it then **stops**. What the first output must
name, the inbox, the 5-day rule, the `↳ blocks:` sub-row and which balls an
agent may pick from are [SR-WORK-OPEN-QUEUE](records/0051_WORK-open-queue.md)
rules 32–34 and 39–45. **Claude Code never picks from the `research` section**
(rule 37a). **Two strikes → a gate**: [SR-WORK-SESSION](records/0054_WORK-session.md)
decision 13.

## Where the state of play lives

| you want | read |
|---|---|
| what to work on next | [`work/OPEN-WORK.md`](work/OPEN-WORK.md) — **the single live queue** |
| the queue explained one item at a time, with a recommendation, rulings written back | `/docket` — [`.claude/skills/docket/SKILL.md`](.claude/skills/docket/SKILL.md) |
| what has been named and nobody is doing | [`work/BACKLOG.md`](work/BACKLOG.md) |
| the judgment behind the current state | [`work/INTERVIEW.md`](work/INTERVIEW.md) |
| what has actually shipped | [`work/IMPLEMENTATION.md`](work/IMPLEMENTATION.md) |
| the spec for anything | [the register](records/README.md) |
| a closed fork and its reopen-trigger | [`work/compare/`](work/compare/README.md) |
| a word you don't recognise | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
| why a command fails on *this* machine | [`work/MACHINE.md`](work/MACHINE.md) |
| the stages a feature moves through | [SR-WORK-LIFECYCLE](records/0053_WORK-lifecycle.md) |
| what a session owes before it ends, and how long an answer may be | [SR-WORK-SESSION](records/0054_WORK-session.md) |
| what `work/NOW.md` holds — only what is live | [SR-WORK-NOW](records/0061_WORK-now.md) |
| what happens to worktrees and lock files when a session ends | [SR-WORK-CLEANUP](records/0062_WORK-cleanup.md) |
| what a task owes the documentation | [SR-WORK-DOCS](records/0055_WORK-docs.md) |
| what to do when you cannot proceed without the decider | [SR-WORK-BLOCKERS](records/0056_WORK-blockers.md) |
| whether a claim may be grounded in an archived doc | [SR-WORK-ARCHIVE](records/0057_WORK-archive.md) |
| which record owns a module | [`records/README.md`](records/README.md) §Ownership |
| which file governs what | [SR-WORK-GOVERNANCE](records/0059_WORK-governance.md) |
| the whole set of rules about how work is done | the **WORK** records `0051`–`0062` |
| what lockmaster is and how a landing works | [SR-ARCHITECTURE](records/0101_architecture.md) |

Any work item that starts, finishes, blocks or is descoped updates
`OPEN-WORK.md` **in the same change as the work**. The record is the spec;
OPEN-WORK is the state; `IMPLEMENTATION.md` is the record of what landed.

## The laws

Each law is stated in exactly one record and is **not restated here**:

- **L0** — SRs are the only source of truth; Law records outrank every other record — [SR-LAW-0](records/0002_LAW-0-authority.md)
- **L1** — a retired record is archived, never deleted — [SR-LAW-1](records/0003_LAW-1-retired-records-archived.md)
- **L2** — `work/MACHINE.md`'s budget section is always followed — 5 GB of disk per project, all agents combined; every GB past it needs the decider's approval — [SR-LAW-2](records/0004_LAW-2-machine-budget.md)
- **L3** — lockmaster never loses work — never a forced git operation; what would lose data stops red for the decider — [SR-LAW-3](records/0005_LAW-3-never-lose-work.md)
- **L4** — zero runtime dependencies — the Python standard library alone — [SR-LAW-4](records/0006_LAW-4-zero-dependencies.md)
- **L5** — git stays the store — every landing is a plain git commit; lockmaster keeps no history of its own — [SR-LAW-5](records/0007_LAW-5-git-stays-the-store.md)
- **L6** — Python only — one package, on PyPI and nowhere else; no npm — [SR-LAW-6](records/0008_LAW-6-python-only.md)
- **L7** — no model in the lander — lockmaster never calls an AI model — [SR-LAW-7](records/0009_LAW-7-no-model-in-the-lander.md)

[SR-LAWS](records/0001_LAWS.md) assigns the handles and routes each to its
record; that is all it does. Add a law by adding a record in the law range and
a line here, on the decider's ruling named in the record.

## Documentation (required)

Three rule groups, one home — [SR-WORK-DOCS](records/0055_WORK-docs.md): how a
doc is written (decisions 1–5); who may edit the agent-steering files, this one
included, and under what two obligations (6–8 — **read before editing
`CLAUDE.md`**); the documents every task updates before it is done (10). The
registry is [SR-WORK-REGISTRY](records/0060_WORK-registry.md) §3.

**The shared memory between sessions is [`work/`](work/README.md)**; `docs/`
holds what the project *is*. Read `work/README.md` once; it is the map.

## Session continuity (required)

The worklog entry (a chat-only session counts), the interview kept current
*during* the session, `work/NOW.md` ([SR-WORK-NOW](records/0061_WORK-now.md)), the transition markers and
how long an answer may be — [SR-WORK-SESSION](records/0054_WORK-session.md).

## Blockers stop the session (required)

A blocker is a file — [`work/BLOCKED.json`](work/BLOCKED.json) — and the
session stops. Its shape, the four values, the prohibition on working around
one and the hooks that enforce it — [SR-WORK-BLOCKERS](records/0056_WORK-blockers.md).

## Archive is not evidence

One archive, [`archive/`](archive/README.md), at the repo root. What may be
named, what may never be cited — [SR-WORK-ARCHIVE](records/0057_WORK-archive.md).

## Hard-won build knowledge

Dated lessons live in [`work/LESSONS.md`](work/LESSONS.md), newest first.
Three that bind hard enough to name here: **re-derive `git status` right before
staging** — concurrent sessions commit too; **ground truth over prose** — a doc
repeating another doc is not a second source; **a loaded machine produces a
clean, localised anomaly** that reads like a finding — say what you are
running.

## Layout

```
work/        THE SHARED MEMORY between sessions — start at work/README.md
records/     THE STANDING RECORDS — the register, the template, the laws, the WORK records, SR-ARCHITECTURE
docs/        WHAT THE PROJECT IS — the glossary
archive/     THE ONE ARCHIVE — everything retired, mirroring the live tree
src/         THE TOOL — the `lockmaster` package, Python ≥ 3.9, standard library only
tests/       scratch-repo tests, one per decision as it is built
kit/         WHAT LOCKMASTER INSTALLS — kit/claude → .claude/, kit/github → .github/
scripts/     the commit guard and the work-system checks
.claude/     installed from kit/claude by `lockmaster install .` — edit kit/, never the copy
.github/     installed from kit/github by `lockmaster install .`, plus workflows/release.yml — lockmaster's own release pipeline, edited here
lockmaster.toml  this repo's own landing rules: its checks and merge drivers
```

**Dogfooding.** lockmaster is built with the work system it will install.
Change a hook in `kit/claude/hooks/`, then run
`PYTHONPATH=src python3 -m lockmaster install .` to install it here; an edit
made only in `.claude/` is reported by `lockmaster doctor` and overwritten by
the next install. Once the kit is installed, an agent session cannot commit to
`main`: work goes through `lockmaster start` / `submit`
([SR-ARCHITECTURE](records/0101_architecture.md) decision 12).
