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

**A ball on every row, always one:** 🔴 blocked on the decider, directly or through another item · 🟣 gated on a named date, directly or through another item · 🟡 waiting on another item · 🟢 no blockers.
**Optional, after the ball:** 🧨 broken or getting worse · 🔺 do first (the decider only). Full legend: [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rules 20–34.

---

## Blocked on the decider

| what the decider decides | filed |
|---|---|
| 🔴 **Rule the five proposed laws** — L3 never lose work, L4 zero runtime dependencies, L5 git stays the store, L6 one tool on PyPI and npm, L7 no model in the lander; each with a recommendation ([W-01](open/W-01-rule-the-laws.md)) | 2026-10-25 |
| ↳ **blocks:** W-08 (the npm form waits on L6) | |
| 🔴 **Three design forks** — does `run` start by itself after `submit`; does a red change stop the queue or get skipped; private until 0.1.0 or public now ([W-02](open/W-02-design-forks.md)) | 2026-10-25 |
| ↳ **blocks:** W-04, and through it W-05, W-07 | |
| 🔴 **Hold the name** — create the npm org `lockmaster` and publish a stub 0.0.1 to npm and PyPI from your accounts; neither registry reserves a name otherwise ([W-08](open/W-08-hold-the-name.md)) | 2026-10-25 |
| ↳ **blocks:** W-08 itself; nothing else in the queue | |

---

## Open items

### build

🟢 **W-03** `agent` Generated files rebuilt, never merged, and the three structural merge drivers (worklog, queue table, lessons), usable from plain git before the lander exists. Filed by Arpit (Cowork). [detail](open/W-03-generated-files-and-merge-drivers.md)

🟢 **W-06** `agent` `lockmaster install <repo>`: install a pinned `kit/` into a repository and wire its settings; replaces `scripts/bootstrap.py` and fux's `install-agent-hooks.py`. Filed by Arpit (Cowork). [detail](open/W-06-install.md)

🔴 **W-04** `agent` The core loop — `start`, `claim add`, `submit`, `run`, `queue` — landing one change at a time, as SR-ARCHITECTURE decisions 4–11 state; waiting on W-02's forks. Filed by Arpit (Cowork). [detail](open/W-04-core-loop.md)

🔴 **W-05** `agent` The claim hook (warns on a write outside the claim) and the block-main hook (refuses an agent's commit or push to `main`); waiting on W-04. Filed by Arpit (Cowork). [detail](open/W-05-claim-and-block-main-hooks.md)

🔴 **W-07** `agent` `lockmaster status`, and `work/NOW.md` as its generated view instead of a file hooks edit; waiting on W-04. Filed by Arpit (Cowork). [detail](open/W-07-status.md)

🔴 **W-08** `arpit` Hold the name: npm org `lockmaster`, a stub 0.0.1 on npm and PyPI from Arpit's accounts; the npm form waits on L6 (W-01). Filed by Arpit (Cowork). [detail](open/W-08-hold-the-name.md)

### testing

🟡 **W-09** `agent` Adopt lockmaster in fux, sheetpane and codelaw: each gets the kit by `lockmaster install` and a `lockmaster.toml`; their hand-copied hooks retire; waiting on W-06. Filed by Arpit (Cowork). [detail](open/W-09-adopt-in-three-repos.md)

### record update

🔴 **W-01** `arpit` Rule the five proposed laws L3–L7; each accepted one becomes its own `SR-LAW-n` record, a SR-LAWS row and a `CLAUDE.md` line. Filed by Arpit (Cowork). [detail](open/W-01-rule-the-laws.md)

🔴 **W-02** `arpit` Three design forks SR-ARCHITECTURE leaves open: auto-run after `submit`, red stops or skips the queue, private until 0.1.0 or public now. Filed by Arpit (Cowork). [detail](open/W-02-design-forks.md)

### research

---
