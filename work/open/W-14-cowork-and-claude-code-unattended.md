---
type: Handoff
name: W-14
description: "Arpit, 2026-11-05: L9 — Cowork and Claude Code in parallel with no manual step. Pickup landed the paths' content at pickup time, not at handoff time; handoffs land at the next Claude Code session's start (ruled 2026-11-05, no background job)."
item: W-14
filed: 2026-11-05
filed_by: "Cowork (Opus 5.5), on Arpit's ruling of L9"
updated: 2026-11-05
updated_by: "Cowork (Opus 5.5): steps 1–3 built on the no-background-job ruling; step 4 waits on W-10"
ball: agent
---

# W-14 — meet L9: what lands from a handoff is what was handed over

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | No background job: the next Claude Code session's start lands handoffs (its hook runs `pickup`) — the decider's ruling. A pickup stamps when it ran; `queue` marks a handoff it left with no reason `MISSED` | [SR-LAW-9](../../records/0011_LAW-9-cowork-and-claude-code-together.md) decision 2 and its veto check | ✅ |
| 2 | A handoff records each file's digest; a file edited after it and not handed off again holds it, named once; handoffs naming a common file land together under all their messages | decision 3 | ✅ |
| 3 | SR-ARCHITECTURE decision 19 rewritten to match; tests in `tests/test_parallel.py` | the design agrees with the law | ✅ |
| 4 | Register's `built` for SR-LAW-9 → `yes` once [W-10](W-10-dirty-main-checkout.md) lands (decision 4) | the law is met | ⏳ waits on W-10 |

**Arpit, 2026-11-05:** *"lock master should handle cowork and claude code in parallel without manual intervention."* Asked whether a `launchd` job should land handoffs: *"no background job, when ever next time the claude code starts it can go ahead and commit it."*

**Model:** Sonnet.

## Definition of done

- A path edited after its handoff is held and named, not landed under the handoff's message. ✅
- No handoff survives a pickup with no reason given. ✅
- W-10 landed; SR-LAW-9 `built: yes`.

## Record affected

[SR-LAW-9](../../records/0011_LAW-9-cowork-and-claude-code-together.md); [SR-ARCHITECTURE](../../records/0101_architecture.md) decision 19.
