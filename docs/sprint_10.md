# Sprint10 — Court-Day Timeline

Updated: 2026-03-07

## Goal

Allow Val to show the full shape of a court day instead of only detecting conflicts.

Users should be able to ask things like:

- ¿Qué tengo mañana?
- ¿Qué tengo en tribunales mañana?
- agenda mañana

and receive a clean timeline of legal events.

---

## Current Limitation

Sprint09 can detect conflicts between events but only warns when a new event is created.

There is no way to **view the entire day’s schedule**.

Lawyers need a quick overview of:

- hearings
- deadlines
- filings
- other diligences

for a specific day.

---

## Target Behavior

Example output:

📅 Mañana (2026-03-08)

• Expediente 524242024 — CASE:524242024 vence mañana  
• Expediente 524242024 — CASE:524242024 audiencia mañana

⚠️ Tienes múltiples diligencias ese día.

---

## Command Patterns

Trigger phrases:

- "qué tengo mañana"
- "agenda mañana"
- "qué vence mañana"
- "mañana tribunales"

---

## Data Source

Table:

`case_events`

Query shape:

SELECT ce.event_text, ce.deadline_date, c.expediente
FROM case_events ce
JOIN cases c ON c.id = ce.case_id
WHERE ce.chat_id = ?
AND ce.deadline_date = ?
ORDER BY ce.id ASC

---

## Implementation Plan

1. Detect a “mañana” schedule query.
2. Query same-day events from `case_events`.
3. Render the results using `_render_due_grouped()`.
4. Append a conflict indicator if multiple events exist.

---

## Definition of Done

Val can show a clean timeline for:

- today
- tomorrow
- small ranges (future sprint)

No LLM required for schedule rendering.

---

## Future Extensions

Sprint11 possibilities:

- hearing times
- courtroom locations
- travel feasibility warnings
- stacked hearing detection

END OF SPRINT 10