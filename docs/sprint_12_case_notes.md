=====================================================================
SPRINT 12.2 — DETERMINISTIC CASE NOTES
=====================================================================

Objective
---------
Allow users to attach structured notes to a case using a deterministic
command and retrieve them in the case timeline.

Command
-------

nota caso <expediente>: <texto>

Example:

nota caso 524242024: juez sugirió conciliación

Behavior
--------

1. Command is parsed deterministically (regex).
2. Active case is set using set_active_case_id().
3. Note is inserted into case_notes table.
4. Audit log entry created with action CMD_CASE_NOTE_CREATE.
5. Timeline query returns the note.

Implementation
--------------

File: bot.py

Block added in _process_text_pipeline():

Regex:

(?is)^\s*nota\s+(?:del\s+)?(?:caso|expediente)\s+(\d{4,})\s*:\s*(.+?)\s*$

Insert:

insert_case_note(
    chat_id,
    case_id,
    note_text,
    source="text"
)

Guard Added
-----------

File: bot.py

Function: _maybe_capture_case_note()

Prevent generic note capture from intercepting the deterministic command:

if low.startswith("nota caso") or low.startswith("nota expediente"):
    return False

Bug Fix
-------

Issue:
Command failed silently.

Root cause:
bot.py missing `import re`.

Fix:
Added:

import re

Outcome
-------

Case timelines now include:

- reminders
- notes
- tasks (future)
- events (future)

Example output:

🗂️ CASE:524242024

📅 2026-03-08
- 00:31 | juez sugirió conciliación otra vez
- 15:00 | revisar el caso 524242024

Architectural Impact
--------------------

Cases now behave as deterministic containers for operational data:

CASE
 ├── reminders
 ├── notes
 ├── events
 └── tasks

This forms the foundation for:

- case cockpit
- transcript ingestion
- legal strategy analysis
- evidence tracking
- timeline reconstruction

