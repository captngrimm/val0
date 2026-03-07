# Sprint09 — Case Event Conflict Detection

## Objective
Detect and warn when multiple legal events are scheduled for the same day.

This builds on Sprint08 deterministic deadline extraction and case event creation.

## Behavior
When a user message contains:

- a valid case identifier (CASE / expediente)
- a deterministic deadline phrase (e.g., "vence mañana", "audiencia mañana")

Val will:

1. Store the message as a case note
2. Create a case_event with deadline_date
3. Query for other events on the same date
4. Warn if a conflict exists

Example response:

⚠️ Boss, ya tienes otra diligencia ese mismo día (2026-03-08):

• Expediente 524242024 — CASE:524242024 vence mañana

## Technical Changes

### bot.py
Added conflict detection block after case_event insertion:

SELECT ce.event_text, ce.deadline_date, c.expediente
FROM case_events ce
JOIN cases c ON c.id = ce.case_id
WHERE ce.chat_id = ?
AND ce.deadline_date = ?
AND ce.id != ?

### Flow control
`_maybe_capture_case_note()` now returns:

True → deterministic reply already sent  
False → pipeline continues

`_process_text_pipeline()` now short-circuits when True.

### Duplicate execution fix
Removed duplicate call to `_maybe_capture_case_note()` from `handle_text()`.

This prevented:

- duplicate case events
- duplicate conflict warnings
- race conditions

## Result
Deterministic legal event detection with immediate same-day conflict warnings.