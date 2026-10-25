---
type: Register
description: "The SR register: the convention, the ownership table, and the state of every record."
---

# SRs — the decision records

**How to use this file.** The naming convention, the record shape, the
ownership table and the rules every record obeys. Read it before writing a
record, before citing one, and before adding a module under `scripts/`, `.claude/hooks/`, `kit/` or `src/`.

One record per completed feature or ruled measurement. **Every record is cited
by NAME in prose, never by number.**

## What an SR is — and what it is not

A Standing Record is a **maintained specification**, not a decision-log entry:
amended in the same change as the code (law zero); superseded records are
rewritten or deleted; retired records are archived (L1); cited by name because
the content moves; it **owns** components and carries a veto condition to check
*today*. The decision-log role lives in `work/compare/` (the fork, its verdict,
its reopen-trigger) and `work/WORKLOG.md`.

## One directory, one state

`records/` is the only home a LIVE record has. A superseded record is rewritten
or deleted in the change that supersedes it; a **retired** record is moved to
`archive/records/` with `status: archived`, a dated banner and an
`archive/README.md` row (L1), and from then on is named, never cited.

Three files here are NOT records and carry no number: this register,
`TEMPLATE.md`, and `RULE-SINCE`.

## The three kinds

Every record declares a `kind`; it answers *what would have to change for this
record to become wrong?*

| `kind` | becomes wrong when | the gate the kind selects |
|---|---|---|
| `law` | The decider rules differently | precedence: a record conflicting with a law is void in the conflicting part |
| `component` | the code changes | `scripts/sr-guard.sh` — the owning record is touched in the same change |
| `process` | the way work is done changes | it owns its enforcement — a hook or script today, a test once tests exist |

## The convention

**Path.** `records/NNNN_<short-name>.md`, on three ranges:

| range | holds | a new record takes |
|---|---|---|
| `0001`–`0050` | the **Law** records only — `0001` SR-LAWS, `0002` SR-LAW-0, `0003` SR-LAW-1, `0004` SR-LAW-2, `0005`–`0009` SR-LAW-3 to SR-LAW-7 | the next free number after the highest law |
| `0051`–`0100` | the **WORK** records only — how work is done | the next free number after the highest |
| `0101`– | every other record | the next free number after the highest |

Gaps are reservations; no placeholder files. The number is a filename ordinal,
**not an identity**. **Cite by NAME, never by number.**

### Frontmatter is the metadata, and the body never restates it

Keys, in this order: `type` · `kind` · `name` · `title` · `description` ·
`status` · `date` · `feature` · `owns` · `laws` · `timestamp` · `content_sha`;
optional `supersedes`, `ratifies`. See `TEMPLATE.md` for each value. **Quote
any value containing `: `.** The body opens at §1 and restates none of it.

### A record states what is true now. It carries no history.

No `Amended` sections. When a decision changes, rewrite the sentence in place,
in the same commit. The one exception is an argument that still binds — it
belongs in *Alternatives considered*.

### Two sections and a bibliography

**§1 — For humans**: one screen; a diagram (Mermaid and a collapsed ASCII
twin, updated together). **§2 — For agents**: Context · Decision (numbered) ·
Consequences · Alternatives considered · Reference (required) · Veto
condition. **References**: every source cited, grouped; nothing new; never an
archived document.

**The reference is grounded** — never an archived doc. **The veto condition is
a condition, not an event** — checkable today with a command.

**A record that restates a cross-cutting principle is a bug.** Each law lives
in its own `SR-LAW-n` record; every other record names it in `laws:` and moves
on.

### Records are kept current by a check, not by good intentions

| where | what it does |
|---|---|
| `scripts/sr-guard.sh` | a `commit-msg` hook: refuses a commit that changes an owned component without staging its owning record and every describer — unless the message carries `no SR affected` on its own line. Install: `ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg` |
| `records/RULE-SINCE` | the baseline commit sha from which the rule applies — the first commit's sha, written once it existed; CI replays the guard from it |

**The escape hatch is a claim in git history under your name**, not a silent
skip. What none of this proves: that a touched record is **coherent**.

Start from `TEMPLATE.md`.

---

## The register

`built` says whether code implements the record's decisions — `yes`, `partly` or `no` ([SR-WORK-OWNERSHIP](0058_WORK-ownership.md) decision 9); [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md) says what landed.

| # | name | title | status | built |
|---|------|-------|--------|-------|
| [0001](0001_LAWS.md) | **SR-LAWS** | The laws have exactly one home each; this record routes the handles | accepted | yes |
| [0002](0002_LAW-0-authority.md) | **SR-LAW-0** | **L0** — records are the only source of truth; Law records outrank every other record | accepted | yes |
| [0003](0003_LAW-1-retired-records-archived.md) | **SR-LAW-1** | **L1** — a retired record is archived, never deleted | accepted | yes |
| [0004](0004_LAW-2-machine-budget.md) | **SR-LAW-2** | **L2** — `work/MACHINE.md`'s budget section is always followed — 5 GB of disk per project, all agents combined; every GB past it approved first | accepted | yes |
| [0005](0005_LAW-3-never-lose-work.md) | **SR-LAW-3** | **L3** — lockmaster never loses work — never a forced git operation; what would lose data stops red for the decider | accepted | partly |
| [0006](0006_LAW-4-zero-dependencies.md) | **SR-LAW-4** | **L4** — zero runtime dependencies — the Python standard library alone | accepted | yes |
| [0007](0007_LAW-5-git-stays-the-store.md) | **SR-LAW-5** | **L5** — git stays the store — every landing is a plain git commit; lockmaster keeps no history of its own | accepted | yes |
| [0008](0008_LAW-6-python-only.md) | **SR-LAW-6** | **L6** — Python only — one package, on PyPI and nowhere else; no npm | accepted | yes |
| [0009](0009_LAW-7-no-model-in-the-lander.md) | **SR-LAW-7** | **L7** — no model in the lander — lockmaster never calls an AI model | accepted | partly |
| [0051](0051_WORK-open-queue.md) | **SR-WORK-OPEN-QUEUE** | How `OPEN-WORK.md` works — the queue discipline in eight groups | accepted | yes |
| [0052](0052_WORK-backlog.md) | **SR-WORK-BACKLOG** | How `BACKLOG.md` works — the named-but-unclaimed in five classes | accepted | yes |
| [0053](0053_WORK-lifecycle.md) | **SR-WORK-LIFECYCLE** | How a feature travels — compare, proposal, handoff in the item file, the model line, one record | accepted | yes |
| [0054](0054_WORK-session.md) | **SR-WORK-SESSION** | What a session owes before it ends; the two-strikes rule | accepted | yes |
| [0055](0055_WORK-docs.md) | **SR-WORK-DOCS** | The documentation contract — form, steering-file edits, the documents every task updates | accepted | yes |
| [0056](0056_WORK-blockers.md) | **SR-WORK-BLOCKERS** | A blocker is a file, not a remark — `work/BLOCKED.json` and the three hooks | accepted | yes |
| [0057](0057_WORK-archive.md) | **SR-WORK-ARCHIVE** | One archive; named, never cited | accepted | yes |
| [0058](0058_WORK-ownership.md) | **SR-WORK-OWNERSHIP** | `owns` and `describes`, and the commit guard | accepted | yes |
| [0059](0059_WORK-governance.md) | **SR-WORK-GOVERNANCE** | The governance map — which file governs what; no counts | accepted | yes |
| [0060](0060_WORK-registry.md) | **SR-WORK-REGISTRY** | The doc registry — rules in §2, the table in §3 | accepted | yes |
| [0061](0061_WORK-now.md) | **SR-WORK-NOW** | `work/NOW.md` holds only what is live — a row per session; what a session leaves becomes a work item | accepted | yes |
| [0062](0062_WORK-cleanup.md) | **SR-WORK-CLEANUP** | Worktrees, lock files and session leftovers — cleaned automatically when nothing is lost; red, blocked on the decider, when something would be | accepted | yes |
| [0101](0101_architecture.md) | **SR-ARCHITECTURE** | lockmaster lands agent changes into main one at a time, on plain git — claims, the queue, landing, generated files, structural merges, the kit | accepted | partly |

---

## Ownership — which record owns which component

**This table is the answer, not a judgement call.** Which components it must
name, and how it agrees with each record's `owns:`, is
[SR-WORK-OWNERSHIP](0058_WORK-ownership.md) decision 2. Most specific wins; a
carve-out is justified by a *different decision*. A component with no decision
yet is owned by an open `W-nn`.

<!-- OWNERSHIP-TABLE-START -->

| component | owner | note |
|---|---|---|
| `scripts/sr-guard.sh` | SR-WORK-OWNERSHIP | the guard is the executable form of decisions 3 and 6 |
| `scripts/release.py` | SR-ARCHITECTURE | decision 17: cuts and checks a release |
| `.github/workflows/release.yml` | SR-ARCHITECTURE | decision 17: the release pipeline; lockmaster's own, not part of the kit |
| `scripts/check-open-work-inbox.py` | SR-WORK-OPEN-QUEUE | rule 45a's check |
| `scripts/check-work-system.py` | SR-WORK-OPEN-QUEUE | the row, inbox and lost-id checks; it also runs the ownership, registry and archive checks |
| `.claude/hooks/guard-open-work-inbox.sh` | SR-WORK-OPEN-QUEUE | rule 45a, in-session |
| `.claude/hooks/inject-inbox.sh` | SR-WORK-BLOCKERS | decision 7 |
| `.claude/hooks/stop-if-blocked.sh` | SR-WORK-BLOCKERS | decision 7 |
| `.claude/hooks/session-lock.sh` | SR-WORK-BLOCKERS | decision 7 |
| `.claude/hooks/release-locks.sh` | SR-WORK-CLEANUP | decisions 8–9 |
| `.claude/hooks/worktree-cleanup.py` | SR-WORK-CLEANUP | decisions 1–6 |
| `.claude/hooks/require-progress.sh` | SR-WORK-SESSION | decision 5 |
| `.claude/hooks/now-ledger.py` | SR-WORK-NOW | decisions 2–5 |
| `.claude/hooks/disk-budget.py` | SR-LAW-2 | decision 4 |
| `.claude/hooks/claim-guard.py` | SR-ARCHITECTURE | decision 5: warns on a write outside a change's claim |
| `.claude/hooks/block-main.py` | SR-ARCHITECTURE | decision 12: refuses an agent's commit or push to `main` |
| `kit` | SR-ARCHITECTURE | decision 15: the hooks, settings, skill and CI lockmaster installs; `.claude/` and `.github/` here are installed copies of it |
| `src` | SR-ARCHITECTURE | decisions 1–14: the `lockmaster` package |
| `tests` | SR-ARCHITECTURE | scratch-repo tests for every decision as it is built |
| `pyproject.toml` | SR-ARCHITECTURE | decision 2: the package, Python ≥ 3.9, no dependencies |
| `lockmaster.toml` | SR-ARCHITECTURE | decision 13: this repository's own checks and merge drivers |

<!-- OWNERSHIP-TABLE-END -->

## Describes — which record's subject REACHES INTO a component it does not own

Ownership stays one record per component; **describes is any number**, and the
guard demands the owner **and every describer**. Every row states its reason.
A component may be narrowed to symbols: `` `path::name,name` ``.

<!-- DESCRIBES-TABLE-START -->

| component | describer | why |
|---|---|---|
| `scripts/check-work-system.py` | SR-WORK-OWNERSHIP | decision 2: its `owns:` ↔ Ownership-table check |
| `scripts/check-work-system.py` | SR-WORK-REGISTRY | decisions 5–8: its registry check |
| `scripts/check-work-system.py` | SR-WORK-ARCHIVE | decision 1: its one-`archive/` check |
| `kit/claude/hooks/worktree-cleanup.py` | SR-WORK-CLEANUP | decisions 1–6: the installed copy's source |
| `kit/claude/hooks/release-locks.sh` | SR-WORK-CLEANUP | decisions 8–9: the installed copy's source |
| `kit/claude/hooks/now-ledger.py` | SR-WORK-NOW | decisions 2–5: the installed copy's source |
| `kit/claude/hooks/disk-budget.py` | SR-LAW-2 | decision 4: the installed copy's source |

<!-- DESCRIBES-TABLE-END -->
