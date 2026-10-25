---
type: Log
description: "Append-only per-session trail, date-grouped, newest first."
---

# WORKLOG — the append-only session log

Every session appends **one entry before it ends** — a chat-only session
counts. **Never edit a past entry; append only, newest on top.** A wrong old
entry is corrected by a new one. Distinct from `INTERVIEW.md`, which is the
*current* state of play. Rules: [SR-WORK-SESSION](../records/0054_WORK-session.md).

**Entry format:**

```
## YYYY-MM-DD — <one-line title>  ·  <surface> (<model>)

- **Asked:** *<the ask>*
- **Done:** <what landed, with commit shas where they exist>
- **Decided / left open:** <rulings taken in-session; forks put to the decider>
- **Mistakes:** <what went wrong and what was done about it, or "none">
- **Next:** <the single next step>
```

---

## 2026-10-25 — the repository set up: the work system from codelaw, the design, the first nine items  ·  Cowork (Opus 5.5)

- **Asked:** *"Here is the lock master repo. Add the necessary documents, add whatever is needed for the tool to be built out. And then I'll create a separate project in Claude Cowork as well as in Claude Code. Set up the work environment that we have in Fux, Sheetpane, and Codelaw."*
- **Done:** the work system copied from codelaw as it stood on 2026-10-25 (the WORK records `0051`–`0062`, L0, L1, the machine budget as L2, the hooks, the `docket` skill, the checks, the guard), codelaw's specifics removed; SR-ARCHITECTURE from the lockmaster design doc; W-01–W-09 and three inbox rows; the compare doc on source control; a stub package; `kit/` holding what lockmaster installs, and `scripts/bootstrap.py` to install it here — the Cowork bridge cannot write `.claude/` or `.github/`.
- **Decided / left open:** L3–L7 proposed, not ruled (W-01); three design forks (W-02); holding the name on npm and PyPI is the decider's (W-08).
- **Mistakes:** none.
- **Next:** Arpit runs `python3 scripts/bootstrap.py`, makes the first commit, and rules the inbox.
