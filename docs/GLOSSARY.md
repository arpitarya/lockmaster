---
type: Glossary
description: "Recurring terms, defined once."
---

# Glossary

| term | meaning |
|---|---|
| Standing Record (SR) | a maintained specification in `records/`, cited by name; see the register |
| Law | a rule that outranks every other record; `SR-LAW-n` |
| W-nn | an open work item — a queue row plus a detail file |
| B-nnn | a backlog row — named, unclaimed, no file |
| ball | the one marker every queue row opens with: 🔴 🟣 🟡 🟢 |
| blocker tag | `waits on **W-mm**`, right after a 🟡 row's id: the item it waits on — `**<project> W-mm**` when that item is another project's (SR-WORK-OPEN-QUEUE rule 23b) |
| blocker | `work/BLOCKED.json` with a decision other than `PROCEED` |
| veto condition | the checkable condition under which a decision reopens |
| change | one agent's unit of work: a work-item id, its claimed paths, a branch `lm/<item>` and a worktree; SR-ARCHITECTURE decision 4 |
| claim | the paths a change may touch; only they land; SR-ARCHITECTURE decisions 4–5 |
| landing | putting one queued change onto `main` — claimed paths, generated files rebuilt, checks, a fast-forward commit; SR-ARCHITECTURE decision 8 |
| lander | whoever holds the land lock and is landing; there is only ever one per repo; SR-ARCHITECTURE decision 7 |
| generated file | a file rebuilt by a command on landing, never merged; listed in `lockmaster.toml` `[generated]` |
| structural merge | a merge driver that knows a file's shape (worklog entries, queue rows, lessons), so two additions never conflict |
| red | a change that cannot land as it is — a conflict, a failed rebuild or check, a refused commit; set aside so the next change lands, it waits for its agent, then the decider; SR-ARCHITECTURE decision 11 |
| land lock | the `mkdir` mutex in lockmaster's state directory that keeps landings to one at a time; a dead holder's lock is taken over; SR-ARCHITECTURE decision 7 |
| left behind | what a change's branch or worktree holds outside its claim: never landed, reported, and keeps the worktree and branch from being removed; SR-ARCHITECTURE decision 5 |
| lockmaster.lock | `.claude/lockmaster.lock` in an installed repository: the kit's version, digest and file hashes, checked by `lockmaster doctor`; SR-ARCHITECTURE decision 15 |
| kit | what lockmaster installs into a repository — `kit/claude` → `.claude/`, `kit/github` → `.github/` |
