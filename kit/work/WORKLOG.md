---
type: Log
description: "Append-only per-session trail, newest first."
---

# WORKLOG — the append-only session log

Written by `lockmaster install` (lockmaster's law L10). Every session appends
**one entry before it ends** — a chat-only session counts. Never edit a past
entry; newest on top.

**Entry format:**

```
## YYYY-MM-DD — <one-line title>  ·  <surface> (<model>)

- **Asked:** *<the ask>*
- **Done:** <what landed, with commit shas where they exist>
- **Decided / left open:** <rulings taken; forks put to the decider>
- **Mistakes:** <what went wrong, or "none">
- **Next:** <the single next step>
```

---
