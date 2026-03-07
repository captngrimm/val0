# Sprint09 — Case Event Conflict Detection

Updated: 2026-03-07

## Goal

Detect and warn immediately when a newly created legal event lands on a day
that already has another legal event for the same chat.

This sprint builds on Sprint08 live case event creation.

---

## Problem

Val could already:

- capture case notes
- create `case_events`
- persist deadline dates

But she did not yet warn the user when two legal events landed on the same day.

That meant users could create conflicting court-day obligations without immediate feedback.

---

## Behavior

When a user sends a message that:

- contains a valid case identifier
- contains a deterministic deadline phrase

Val now:

1. stores the note in `case_notes`
2. creates the `case_event`
3. queries existing `case_events` for the same `chat_id` and `deadline_date`
4. warns if another event already exists that day

Example warning:

⚠️ Boss, ya tienes otra diligencia ese mismo día (2026-03-08):

• Expediente 524242024 — CASE:524242024 vence mañana

This is warn-but-allow behavior.
The event is still inserted.

---

## Technical Changes

### `bot.py`

Inside `_maybe_capture_case_note(...)`:

- after `insert_case_event(...)`
- query same-day events from `case_events`
- exclude the newly inserted event by `id`
- if conflicts exist, send deterministic warning

SQL shape:

```sql
SELECT ce.event_text, ce.deadline_date, c.expediente
FROM case_events ce
JOIN cases c ON c.id = ce.case_id
WHERE ce.chat_id = ?
  AND ce.deadline_date = ?
  AND ce.id != ?
ORDER BY ce.id ASC
LIMIT 5
Flow Control Fix

_maybe_capture_case_note(...) now returns:

True when it already sent a deterministic conflict warning

False otherwise

_process_text_pipeline(...) now short-circuits if the function returns True.

This prevents the model/conversational layer from replying after the deterministic legal layer already handled the message.

Duplicate Execution Fix

A duplicate call to _maybe_capture_case_note(...) in handle_text(...) was removed.

Before fix:

duplicate case-event processing

duplicate warnings

noisy reply stacking

After fix:

one legal pass

one warning

cleaner deterministic routing

Validation

Confirmed live behavior:

Message:
CASE:524242024 audiencia mañana

Response:
single deterministic same-day warning

DB state confirmed:

existing event: CASE:524242024 vence mañana

new event: CASE:524242024 audiencia mañana

same deadline_date

warning triggered correctly

Definition of Done

same-day legal conflicts trigger immediate warning

event still inserts

duplicate warning path removed

conversational follow-up suppressed after deterministic warning

service remains stable

Follow-On

Sprint10:
Court-Day Timeline

Next step is to render all same-day legal events in a clean agenda/timeline view
so Val can show the shape of the day, not just warn on conflicts.

END OF SPRINT 09