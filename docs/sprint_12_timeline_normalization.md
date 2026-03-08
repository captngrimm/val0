=====================================================================
SPRINT 12.3 — TIMELINE NORMALIZATION + SOURCE TRACE
=====================================================================

Objective
---------
Clean up case timeline rendering so outputs are readable, trustworthy,
and ready for cockpit-style use.

Problem
-------
Current output is structurally correct but visually noisy.

Examples:

- 07:43 | 524242024: CASE:524242024 vence mañana
- 00:31 | 524242024: juez sugirió conciliación otra vez
- 15:00 | 524242024: revisar el caso 524242024

Goal
----
Normalize all case timeline items into source-labeled rows.

Target style:

📅 2026-03-08
- 07:43 | evento       | vence mañana
- 00:31 | nota         | juez sugirió conciliación otra vez
- 15:00 | recordatorio | revisar el caso 524242024

Scope
-----
Rendering only.

No storage changes.
No schema changes.
No reminder runner changes.
No timeline merge logic changes.

Sources
-------
Current source types:

- reminder
- note
- event

Normalization Rules
-------------------
1. event
   - strip CASE:<id> prefix
   - strip expediente repetition when obvious
   - preserve event meaning

2. note
   - show raw note text only
   - no case-id prefix in display row

3. reminder
   - show reminder text only
   - no entity prefix in display row

4. preserve:
   - time
   - date grouping
   - item order

Implementation Direction
------------------------
File: core/case_mvp.py

Primary target:
- try_timeline_for_case()

Rendering should map source → label:

- reminder    → recordatorio
- note        → nota
- event       → evento

Future Use
----------
This normalized timeline becomes the visual base for:

- case cockpit
- source trace
- transcript items
- advisory summaries

Definition of Done
------------------
The query:

qué tengo del caso 524242024

returns a clean, source-labeled timeline without duplicated case text.

