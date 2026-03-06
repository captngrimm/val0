# Sprint 05 — Reminder State Audit Timeline

Updated: 2026-03-05

## Goal

Add deterministic audit visibility for reminder state transitions.

This sprint hardens reminder observability without changing reminder creation,
delivery semantics, or transport architecture.

The objective is simple:

Every reminder state change must leave a durable, queryable trail.

This makes reminder behavior debuggable in production and keeps the system aligned
with deterministic operations principles.

---

# A) Reminder State Transition Audit

## Problem

Reminders currently work, but state changes are not fully visible in an immutable
audit trail.

If a reminder fails, gets cancelled, or behaves unexpectedly, debugging requires
manual inspection of logs and DB state.

That is operationally weak.

## Objective

Record reminder state transitions as explicit audit entries.

Tracked reminder states:

- pending
- sending
- sent
- cancelled
- failed

Tracked transitions include at minimum:

- pending → sending
- sending → sent
- sending → failed
- pending → cancelled

No transition should occur silently.

---

# B) Audit Contract

## Action

Use a deterministic audit action:

REMINDER_STATE_CHANGE

## Payload

Payload must include:

- rid=<reminder_id>
- old=<old_state>
- new=<new_state>
- timestamp=<utc>

Example:

rid=104
old=pending
new=sending
timestamp=2026-03-05T23:08:00Z

## Rules

- Audit is written only after the underlying status update succeeds.
- No model involvement.
- No inferred states.
- No silent mutation.

---

# C) Storage Strategy

## Implementation Rule

Use the existing audit infrastructure.

Preferred destination:

audit_log

No new table should be added unless inspection proves the existing audit path
cannot support reminder transition logging cleanly.

## Design Principle

This sprint is observability hardening, not schema expansion.

Minimal patching only.

---

# D) Likely File Changes

## 1. memory_store.py

Purpose:

- add a deterministic helper for reminder state audit logging
- centralize audit insertion so runner/cancel paths remain thin

Likely helper:

log_reminder_state_change(rid, old_state, new_state)

This helper should write a structured audit row using the existing audit table.

---

## 2. Reminder runner module

Purpose:

- log pending → sending
- log sending → sent
- log sending → failed

This is the subsystem that already performs reminder delivery, so it is the
correct place to emit delivery-state transitions.

---

## 3. core/reminders_mvp.py

Purpose:

- log pending → cancelled when cancellation succeeds

Cancellation is part of the reminder control path and must be auditable.

---

# E) Required Behavioral Rules

## Rule 1 — Successful sends

When a reminder is selected for delivery:

pending → sending

If Telegram delivery succeeds:

sending → sent

Both transitions must be logged.

---

## Rule 2 — Failed sends

If Telegram delivery fails after reminder selection:

pending → sending
sending → failed

The reminder must not disappear silently.

---

## Rule 3 — Cancellation

If a valid pending reminder is cancelled:

pending → cancelled

The transition must be logged.

Cancellation of already-sent or already-cancelled reminders must remain
deterministic and must not fabricate state transitions.

---

# F) Test Plan

## Test 1 — Normal delivery

DM:

Recuérdame probar en 1 minuto

Expected operational result:

- reminder created
- runner picks it up
- message delivered
- reminder marked sent

Expected audit trail:

- pending → sending
- sending → sent

---

## Test 2 — Cancellation

Create reminder:

Recuérdame pagar luz en 2 minutos

Then cancel it.

Expected operational result:

- reminder status becomes cancelled

Expected audit trail:

- pending → cancelled

No delivery should occur after cancellation.

---

## Test 3 — Delivery failure path

Simulate Telegram failure or blocked-user path.

Expected operational result:

- reminder enters sending
- reminder becomes failed
- service does not crash

Expected audit trail:

- pending → sending
- sending → failed

---

# G) Verification Queries

Operational verification should confirm that recent reminder transitions can be
read from the audit trail.

Typical checks:

- latest reminder transition rows
- state history for a given reminder id
- correlation between reminder status and audit events

The exact SQL should be derived from the live audit_log schema before patching.

No speculative schema assumptions should be committed.

---

# H) Definition of Done

Reminder delivery still works normally.

Reminder cancellation still works normally.

Every reminder state transition is auditable.

Failed deliveries are visible in audit history.

No crash loops introduced.

No reminder architecture rewrites introduced.

Git clean.

---

# I) Non-Goals

This sprint does not include:

- daily summary push
- overdue escalation logic
- new notification channels
- WhatsApp transport
- UI changes
- reminder/calendar schema merge
- model-generated audit content

---

# J) Follow-On Candidates

After this sprint, the next logical hardening targets are:

- GCAL conflict surfacing
- merge audit visibility
- deadline normalization guardrails
- founder rollback playbook

These remain Phase 1 hardening items and should be selected after Sprint05 is
verified and documented.

---

END OF SPRINT 05