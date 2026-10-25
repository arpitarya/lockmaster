---
type: Queue
description: "The single live work queue, three lanes, plus the Blocked-on-the-decider inbox. The list only — its rules live in the record below."
governed_by: SR-WORK-OPEN-QUEUE
governed_by_path: records/0051_WORK-open-queue.md
---

# OPEN-WORK — what is still open

**This file is the LIST, plus the legend below.** Everything else — what the
queue is, an item's lifecycle, the shape of a row, ball precedence, ordering,
how the inbox works, and what every session owes — is stated once in
**[SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md)** and is not repeated
here. Read that record before changing anything below it.

**A ball on every row, always one:** 🔴 blocked on the decider, directly or through another item · 🟣 gated on a named date, directly or through another item · 🟡 waiting on another item, named right after the id — `waits on **W-mm**`, or `**<project> W-mm**` for another project's · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (the decider only). Full legend: [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rules 20–34.

---

## Blocked on the decider

| what the decider decides | filed |
|---|---|
| 🔴 **Hold the name on PyPI** — publish a placeholder 0.0.1 of `lockmaster` to PyPI from your account (L6: Python only, no npm); and keep or delete the empty npm org `@lockmaster`, created a minute before your npm ruling ([W-08](open/W-08-hold-the-name.md)) | 2026-10-25 |
| ↳ **blocks:** nothing else in the queue | |

---

## Open items

### build

🔴 **W-08** `arpit` Hold the name on PyPI: a placeholder 0.0.1 of `lockmaster` from Arpit's account; npm is dropped (L6), and the empty npm org `@lockmaster` is his to keep or delete. Filed by Arpit (Cowork). [detail](open/W-08-hold-the-name.md)

### testing

🟢 **W-09** `agent` Adopt lockmaster in fux, sheetpane and codelaw: each gets the kit by `lockmaster install` and a `lockmaster.toml`; their hand-copied hooks retire. Filed by Arpit (Cowork). [detail](open/W-09-adopt-in-three-repos.md)

### record update

### research

---
