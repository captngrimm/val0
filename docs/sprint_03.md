# Sprint 03 — Reminder Reliability + Operational Guardrails

Updated: 2026-03-05

## Goal

Stabilize reminder UX and debugging capability before expanding automation.

Focus:

* human-readable time display
* deterministic state audit
* guardrails preventing long-term reminder misuse

Reminder system is now operational; this sprint makes it **production-grade and debuggable.**

---

# A) Local Time Display Normalization

## Problem

Reminder confirmations and listings sometimes show mixed formats
(UTC vs local formatting inconsistencies).

## Requirements

* All user-facing times display **local time only**
* Use the existing local formatting helper
* `/reminders` output must be consistent with confirmation messages

### Files Likely Affected

* `core/reminders_mvp.py`
* `core/ops_cmds.py`

### Tests

DM:

Recuérdame probar en 1 minuto

Confirmation should show:

Listo, Boss. Te lo recuerdo a las 3:14 PM.

Then:

/reminders 5

Should show the **same local format**.

---

# B) Reminder State Audit Timeline

## Problem

If a reminder fails or behaves oddly, debugging is slow.

## Goal

Record deterministic state transitions.

States:

pending
sending
sent
cancelled
failed

## Requirements

Every state change must generate an immutable audit entry.

Example transitions:

pending → sending
sending → sent
sending → failed
pending → cancelled

### Audit Entry Format

action: REMINDER_STATE_CHANGE
payload:

rid=<id>
old=<state>
new=<state>
timestamp=<utc>

### Files Likely Affected

ReminderRunner module
memory_store.py (if helper added)

### Tests

Create reminder → wait for fire → verify audit entry exists.

Cancel reminder → verify transition logged.

---

# C) 7-Day Reminder Guardrail

## Problem

Reminders can become long-term storage if users say:

“Recuérdame en 3 semanas.”

That pollutes the reminder system.

## Rule

Reminders are **short-term operational nudges**.

If requested reminder exceeds **7 days**, Val0 must refuse deterministic creation.

### Response

Example:

Eso está a más de 7 días.
Por ahora los recordatorios son para tareas cercanas.

### Implementation

Detect in grammar parsing stage.

If computed `due_at` exceeds:

now + 7 days

Return deterministic message instead of inserting reminder.

### Tests

DM:

Recuérdame pagar renta en 10 días

Expected:

Refusal message.

No reminder inserted in DB.

---

# Definition of Done

Reminder confirmations show consistent local time.

State transitions recorded in audit log.

Reminder creation rejected when >7 days.

Service remains stable (no crash loops).

val0ctl ops returns green.

Git clean.

---

# Known Follow-ups (Future Sprints)

Daily summary push (Phase 2 automation)

Overdue escalation engine

Calendar suggestion for long-term tasks

User nickname preference store

Bug intake pipeline (Phase 0.4 orchestration)

---

END OF SPRINT 03
