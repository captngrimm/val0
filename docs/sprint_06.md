# Sprint 06 — GCAL Conflict Surfacing

Updated: 2026-03-06


## Validation Status

Implemented and runtime-stable.

Verified:

- due_today still works
- due_range still works
- DB due items still render correctly after merge return-shape change
- no bot crash introduced

Pending live validation:

- user-facing conflict block requires a real CASE-bound Google Calendar event
  on the same date as a DB deadline with a differing time and/or title

Current status:

Sprint06 deployed and stable.
Conflict surfacing logic awaits live mismatch confirmation.

## Goal

Expose deterministic Google Calendar vs DB deadline discrepancies to the user
inside due query responses.

This sprint does **not** add advisory reasoning, travel feasibility, or
automatic outreach.

It only surfaces factual conflicts already detected by the merge layer.

The objective is simple:

If the system detects that a calendar event disagrees with the DB for the same
case and date, the user should see a clear warning.

---

# A) Problem

The merge layer already detects conflicts between:

- deterministic DB deadlines
- Google Calendar events

These conflicts are currently logged only in merge diagnostics.

That is useful for operators, but not useful enough for the user.

If Val knows a case has conflicting schedule data, Val should say so.

---

# B) Scope

This sprint is limited to **user-visible conflict surfacing** for due queries.

Affected due gates:

- `try_due_today()`
- `try_due_range()`

Conflict categories already available from the merge layer:

- time mismatch
- title mismatch
- both

No new DB tables are introduced.

No reminder logic is touched.

No calendar mutation occurs.

---

# C) Design Rules

## Rule 1 — DB remains authoritative

If DB and GCAL disagree:

- DB data is not overwritten
- GCAL data is not written back
- merge remains read-only

Val only surfaces the discrepancy.

---

## Rule 2 — Conflict visibility must be deterministic

If the merge engine detects a conflict, the same conflict should be rendered
consistently in due query responses.

No model interpretation is required.

---

## Rule 3 — User language, not operator language

The user should not see internal merge jargon like:

- conflict_total
- title hash
- collision sample

Instead, Val should say something like:

Ojo: encontré una discrepancia entre expediente y calendario.

---

# D) Merge Layer Change

## File

`core/due_merge.py`

## Current state

`merge_due_items()`:

- normalizes DB items
- optionally fetches GCAL events
- detects conflicts
- logs conflict stats
- dedupes results
- returns merged items only

## Required change

`merge_due_items()` must return structured conflict data in addition to items.

Recommended return shape:

```python
{
  "items": [...],
  "conflicts": [...]
}

Conflict object shape:

{
  "case_id": str,
  "due_date": str,
  "db_due_local": str,
  "gcal_due_local": str,
  "db_title": str,
  "gcal_title": str,
  "kind": "time" | "title" | "both"
}

This preserves determinism while making conflicts renderable.

E) Due Gate Change
File

core/case_mvp.py

Required change

Both due gates must consume the new merge result shape.

Current pattern:

items = merge_due_items(...)

New pattern:

merged = merge_due_items(...)
items = merged["items"]
conflicts = merged["conflicts"]

Rendering behavior:

render due items exactly as before

if conflicts exist, append a conflict warning block

Affected functions:

try_due_today()

try_due_range()

F) Conflict Rendering
File

core/case_mvp.py

Add a deterministic helper to render conflicts.

Suggested helper:

_render_due_conflicts(conflicts)

Expected style:

⚠️ Ojo: encontré discrepancias entre expediente y calendario

CASE:104
• expediente: 2026-03-06 09:00 — Audiencia preliminar
• calendario: 2026-03-06 10:30 — Audiencia preliminar

Rules:

concise

human-readable

factual only

no suggestions yet

no inferred travel logic

no social prioritization

G) Non-Goals

This sprint does not include:

travel feasibility analysis

“you won’t make it” reasoning

contact prioritization

auto-drafted messages

assistant-to-assistant communication

WhatsApp integration

calendar writes

reminder/calendar schema merge

Those belong to later advisory or action-layer sprints.

H) Tests
Test 1 — No conflict

DB and GCAL match for same case/date.

Expected:

due items render normally

no conflict block shown

Test 2 — Time mismatch

DB deadline time and GCAL event time differ for same case/date.

Expected:

due items render normally

conflict block appears

DB remains authoritative

Test 3 — Title mismatch

DB title and GCAL title differ for same case/date.

Expected:

due items render normally

conflict block appears

Test 4 — GCAL disabled

VAL0_GCAL_ENABLED=0

Expected:

DB-only behavior

no conflict block

no crash

Test 5 — GCAL fetch failure

Credentials/API failure.

Expected:

DB-only result still returned

no crash

no user-facing stack trace

I) Definition of Done

Due gates still return merged due items normally.

Conflicts are visible to the user in natural language.

DB remains authoritative.

GCAL remains read-only.

No schema changes introduced.

No reminder subsystem changes introduced.

Service remains stable.

Git clean.

J) Follow-On Candidates

After this sprint, the next logical advisory-facing candidates are:

travel feasibility warnings

scheduling impossibility detection

action suggestions

draft outreach to affected contacts

controlled contact-action layer

These belong above the deterministic merge layer and must not weaken the
deterministic core.

END OF SPRINT 06