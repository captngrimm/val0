# FOUNDER_DEMO_READINESS_V1 — Val0

Purpose:
One canonical founder-demo path for Val0 after Alpha, Caso Finca, and Generic Folders.

This is not a stress test.
This is not a public launch checklist.
This is a controlled demo path to show what Val0 already does honestly.

## Current promise

Val0 is a Telegram-first personal operator in founder-beta.

Today Val0 can help with:

- agenda / reminders / tasks
- Google Calendar actions with explicit confirmation
- Caso Finca as a read-only case workspace
- document inventory inside Caso Finca
- OCR-backed summary for trusted document 1
- generic folders like Libro
- simple text notes inside folders
- warmer Karen/Tany-facing responses

Do not promise:

- perfect memory
- full autonomy
- legal conclusions
- perfect OCR
- arbitrary document attachment to folders
- folder rename/delete
- public SaaS readiness

Correct framing:

Val0 is early, but it already organizes real workflows with less friction.

## Demo path

Use this order:

1. Agenda
2. Tasks
3. Calendar create with confirmation
4. Caso Finca workspace
5. Caso Finca document list
6. Document 1 summary
7. Folder list
8. Save/read idea in Libro
9. Founder-beta close

## Pre-demo technical gate

Run before a real demo:

- cd /opt/val0
- python3 scripts/diagnostics/val0_alpha_brief.py
- python3 scripts/diagnostics/val0_source_of_truth_check.py --full
- python3 scripts/quality/karen_rc_full_smoke.py --keep-going
- python3 scripts/quality/client_fixture_smoke.py --client karen
- git diff --check
- git status --short --branch

Pass condition:

- intended head is present
- Karen RC full smoke passes
- client fixture smoke passes
- git diff check passes
- dirty files are only expected live data

Known live data:

- clients/karen/CLIENT_GROCERY.md
- clients/karen/CLIENT_FOLDERS.json

Do not reset, discard, overwrite, or casually commit those files.

## Telegram demo script

### 1. Agenda

Send:
Val, qué tengo mañana?

Expected:
Clean Spanish agenda view.

Demo point:
Val recovers immediate day/time context.

### 2. Tasks

Send:
Val, qué tareas activas tengo pendientes?

Expected:
Active task list. It must not route to Caso Finca.

Demo point:
Val tracks pending work.

### 3. Calendar create with confirmation

Send:
Val, agenda para mañana a la 1:30 PM cita con la bróker y mi mamá

Expected:
Calendar draft/preview through confirmation path.

Demo point:
Val turns natural language into calendar structure, but does not write without confirmation.

Operator note:
Stop before confirmation if you do not want a real calendar event created.

### 4. Open Caso Finca

Send:
Val, abre mi Caso Finca

Expected:
Compact read-only Caso Finca dashboard.

Demo point:
Val behaves like a living workspace, not just generic chat.

### 5. Document list

Send:
Val, muéstrame documentos del Caso Finca

Expected:
Compact document list without raw internal paths.

Demo point:
Val organizes existing document references inside a scoped case.

### 6. Document summary

Send:
Val, resume el documento 1

Expected:
Conservative OCR-backed summary with legal boundary preserved.

Demo point:
Val helps prepare review context without pretending to be a lawyer.

Safe line:
This is a reading aid, not a legal conclusion. Nora/the lawyer confirms legal effect.

### 7. Folder list

Send:
Val, lista mis carpetas

Expected:
Val lists folders like Libro.

Demo point:
Val can organize personal ideas outside the case workspace.

### 8. Save and read idea in Libro

Send:
Val, guarda esta idea en Libro: escribir una escena sobre el mercado

Then send:
Val, qué tengo en Libro?

Expected:
Val shows the saved idea under Libro.

Demo point:
Val captures lightweight personal ideas into a user-created folder.

## Close script

Val0 is still founder-beta. The point is not that it does everything yet.

The point is that it already organizes useful real workflows:
agenda, tasks, reminders, Caso Finca, document summaries, and personal folders.

The strongest next step is to pick one real workflow for the client and configure Val around that instead of pretending it should handle the whole universe on day one.

## Scoring

Score only:

- PASS
- POLISH
- BLOCKER

Track top 3 issues only.

PASS:
The person understands it and says it would help with a real workflow.

POLISH:
The flow works but tone, wording, or steps need cleanup.

BLOCKER:
Val routes wrong, exposes internals, claims legal authority, writes without confirmation, or fails the core path.

## Next lane options after demo readiness

Choose one:

1. Folder Rename/Delete Guarded v1
2. Generic Folder Add/Move Notes v2
3. Caso Finca OCR Summary v2
4. M45 Router Coverage Closeout

Do not add new features during demo rehearsal unless a trust-killer appears.
