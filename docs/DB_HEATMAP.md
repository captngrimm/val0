# Val0 DB Heat Map

Purpose:
Track which Val0 encrypted DB tables are safe, risky, critical, reset-sensitive, or preserve-only.

Live DB:
- /opt/val0/val0_memory.enc.db

## Heat Legend

| Heat | Meaning | Handling |
|---|---|---|
| 🟢 Low | Safe/read-only or derived/debug data | Low risk |
| 🔵 Medium-low | Useful state, generally reversible | Can update carefully |
| 🟡 Medium | User memory/state, reset-sensitive | Confirm before mutation |
| 🟠 High | Complex workflow data or cross-linked state | Manual inspection before mutation |
| 🔴 Critical | Legal, deadline, external action, destructive risk | Never casually modify |
| ⚫ Preserve | Audit/history/trace logs | Preserve unless explicitly archiving |

## Table Heat Map

| Table | Heat | Domain | Why it matters | Reset handling |
|---|---:|---|---|---|
| messages | 🟡 | Conversation | Recent context/session memory | Delete only in confirmed reset |
| user_facts | 🟡 | Persistent memory | Names, preferences, email, facts | Delete carefully |
| memory_items | 🟡 | Classified memory | Voice/text memory buckets | Delete carefully |
| memory_entries | 🟡 | Memory | General entries | Delete carefully |
| notes | 🟡 | Notes | User notes | Confirm before delete |
| reminders | 🔴 | Time commitments | Pending reminders can matter | Never delete casually |
| tasks | 🟠 | Work tracking | Active tasks / commitments | Confirm |
| commitments | 🟠 | Promises/follow-ups | May drive nudges/follow-up | Confirm |
| cases | 🔴 | Legal/cases | Legal MVP core | Never delete casually |
| case_notes | 🔴 | Legal/case notes | Case record | Never delete casually |
| case_events | 🔴 | Legal deadlines/events | Case-critical dates | Never delete casually |
| case_summaries | 🟠 | Derived legal summary | Can be regenerated, but useful | Prefer regenerate over delete |
| reminders | 🔴 | Reminders/deadlines | Time-sensitive commitments | Never casually delete |
| chat_prefs | 🔵 | Preferences | Voice mode, active case | Reset possible |
| pm_current_focus | 🔵 | PM/cockpit | Current focus | Safe to update |
| pm_decisions | 🟡 | PM history | Decision history | Preserve unless reset |
| daily_logs | 🟡 | Daily reports | User summaries | Confirm |
| milestones | 🟢 | Project trace | Build/product milestones | Preserve |
| audit_log | ⚫ | Audit trace | Operational history | Preserve |
| action_logs | ⚫ | Action trace | Operational history | Preserve |
| legal_audit_log | ⚫ | Legal audit | Legal trace | Preserve |
| processed_events | 🟢 | Dedupe/system | Prevents duplicate processing | Inspect before reset |
| user_settings | 🔵 | Preferences | Proactive mode/settings | Safe with confirmation |
| watchdog_alerts | 🟢 | Alerts | System monitoring | Preserve or archive |

## Reset Policy

For fresh-user testing:
1. Prefer simulated mode first.
2. Do not delete legal/case tables unless explicitly testing legal reset.
3. Preserve audit logs by default.
4. For destructive reset:
   - backup first
   - dry-run counts first
   - explicit confirmation
   - delete only approved chat_id rows
   - log what was deleted

## Next Design Target

Create safe command:
- /test_fresh_start

Purpose:
Simulate new-user onboarding without deleting data.

Later destructive command:
- /reset_me_confirm

Only after backup + dry-run.
