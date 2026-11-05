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
| 🔴 **Hold the name on PyPI** — the release pipeline and 0.0.1 are ready: add the trusted publishers and the two GitHub environments (CONTRIBUTING.md §Releasing), then push `main` and the tag `v0.0.1`; and keep or delete the empty npm org `@lockmaster` ([W-08](open/W-08-hold-the-name.md)) | 2026-10-25 |
| ↳ **blocks:** nothing else in the queue | |

---

## Open items (6)

### build (5)

🔴 **W-08** `arpit` Hold the name on PyPI: the pipeline and 0.0.1 are ready; Arpit adds the trusted publishers and environments, then pushes the tag `v0.0.1`. Keep or delete the npm org `@lockmaster`. Filed by Arpit (Cowork). [detail](open/W-08-hold-the-name.md)

🟢 **W-10** `agent` A dirty `main` checkout: a refused fast-forward waits and lands once the edits clear, not red; `status`/`doctor` and a kit hook warn first. Identical edits and named paths came with W-11. Filed by Arpit (Cowork). [detail](open/W-10-dirty-main-checkout.md)

🟢 **W-13** `agent` Prove L8 with real concurrent processes: built (`tests/test_parallel.py`; three breaches found and fixed) and handed off — close it once the next Claude Code session lands it. Arpit ruled L8 on 2026-11-05. Filed by Cowork (Opus 5.5). [detail](open/W-13-prove-parallel-requests.md)

🟡 **W-14** waits on **W-10** `agent` Meet L9: a handoff lands only what was handed over, at the next Claude Code session's start (no background job, Arpit 2026-11-05). Built; decision 4 is W-10's. Filed by Cowork (Opus 5.5). [detail](open/W-14-cowork-and-claude-code-unattended.md)

🟢 **W-15** `agent` Enforce L10 in every repository: `install` creates any missing work file, `doctor` names a missing or stale one, a kit Stop hook flags a session that touched none of WORKLOG, INTERVIEW or OPEN-WORK. Arpit ruled L10 on 2026-11-05. Filed by Cowork (Opus 5.5). [detail](open/W-15-work-files-current-everywhere.md)

### testing (1)

🟢 **W-09** `agent` Adopt lockmaster in fux, sheetpane, codelaw and milo: codelaw and fux land for real; milo's and sheetpane's adoption was never committed and lands with W-11's handoff in the next Claude Code session there. Filed by Arpit (Cowork). [detail](open/W-09-adopt-in-three-repos.md)

### record update (0)

### research (0)

---
