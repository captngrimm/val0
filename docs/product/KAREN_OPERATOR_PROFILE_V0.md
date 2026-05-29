# Karen Operator Profile v0

Status: founder-beta / client-zero learning profile  
Scope: Karen Val0 Personal OS behavior and UX preferences  
Last updated: 2026-05-29

## Purpose

This document captures Karen's live feedback and emerging Personal OS preferences.

This is not runtime configuration yet. It is a product/UX source of truth for future settings, personalization, and client-specific operator behavior.


## Active Name / Vocative

Current preferred vocative:

- Tany

Previous/legacy vocative:

- previous legacy nickname

Rule:
Val should address Karen as Tany going forward and should not revert to the previous legacy nickname unless Karen explicitly asks.

## Core Mental Model

Karen wants Val to behave like a practical personal operator:

- understand natural language
- avoid technical/slash commands
- show numbered lists
- let the user act by number
- explain clearly what belongs to Google Calendar vs Val
- confirm before destructive actions
- avoid repeating internal/debug labels
- work naturally from voice and text when possible

## Agenda Model

Agenda should be divided into clear sections:

### Eventos de Google Calendar

Meaning:
- real calendar appointments/events
- stored in Google Calendar
- Google handles native notifications
- Val can read them
- Val can create them after confirmation
- Val can delete them by number after confirmation

Preferred label:

📅 Eventos de Google Calendar

Example actions:
- Val, agenda cita con Nora mañana a las 3pm
- Val, elimina el evento 1
- Val, qué tengo mañana?

### Recordatorios de Val

Meaning:
- reminders managed by Val
- Val sends Telegram reminder
- separate from Google Calendar
- should be numbered
- should support natural actions by number

Preferred label:

⏰ Recordatorios de Val

Example actions:
- Val, recuérdame mañana a las 9 llamar al juzgado
- Val, qué recordatorios tengo?
- Val, elimina el recordatorio 1
- Val, recordatorios vencidos
- Val, elimina el recordatorio vencido 1

Important:
If a reminder shows a time conflict, be honest.

Example:
09:00 · ir a la Boutique a las 12md ⚠️ texto menciona otra hora

Meaning:
Val will trigger at 09:00, but the reminder text mentions 12md, so the user should confirm the intended time.

### Tareas de Val

Meaning:
- pending actions managed by Val
- may or may not have dates
- not the same as Google Calendar events
- should be numbered
- can be marked done
- deletion/destructive behavior should be careful

Preferred label:

📌 Tareas de Val

Example actions:
- Val, registra tarea: pedir cotización al topógrafo
- Val, qué tareas activas tengo?
- Val, marca la tarea 1 como hecha
- Val, elimina la tarea 1

Important:
If a reminder-looking phrase was stored as a task, label it clearly rather than hiding it.

Example:
⚠️ Posible recordatorio guardado como tarea

## Document Workflow Preferences

Karen wants documents to work without depending on captions.

Preferred flow:

1. User uploads document.
2. User says:
   - Val, resume este documento
   - Val, qué fue lo último que subí?
   - Val, sugiere nombre para este documento
3. Val should resolve "este documento" to the latest uploaded document when safe.
4. If several documents were uploaded recently, Val should ask which one.
5. Document inventory should be numbered by upload date/newest first.

Preferred commands:
- Val, qué documentos tengo?
- Val, resume el documento 1
- Val, sugiere nombre para el documento 1
- Val, guarda ese nombre

Document list should help avoid long ugly filenames.

If a filename is illegible, Val can suggest a cleaner name and tags.

## Naming / Metadata Preferences

Karen values:
- readable document names
- upload dates
- suggested tags
- practical importance
- clear document numbering
- original filename preserved when an alias/name is saved

Do not physically rename files unless explicitly supported and confirmed.

For now:
- save alias/metadata
- keep original file intact
- show "Original: filename.pdf" when useful

## Voice vs Text

Karen expects voice and text to behave similarly.

Testing rule:
- First try voice naturally.
- If voice fails, repeat the exact same command by text.
- This helps identify whether the failure is voice transcription or Val logic.

Voice should eventually support the same natural commands as typed text:
- resume este documento
- qué tengo mañana
- qué recordatorios tengo
- elimina el recordatorio 1
- marca la tarea 1 como hecha

## UX / Copy Preferences

Avoid:
- slash commands
- internal IDs
- technical terms
- "Modo: lectura solamente" in normal routine views
- commands that Val cannot actually execute
- stale names/context such as wrong user names or old pending actions

Prefer:
- short explanations
- numbered lists
- natural action examples
- clear confirmation before deletion
- updated list after deletion when practical
- honest fallback when a feature is not implemented

Examples:

Good:
Listo. Eliminé de Google Calendar: Cita con Nora — viernes 3:00 PM.

Good:
No pude crear el evento en Google Calendar. No lo marqué como creado.

Good:
Todavía no puedo editar ese recordatorio directamente. Puedo eliminarlo y crear uno nuevo con la hora correcta. ¿Quieres que lo haga?

Bad:
Modo: lectura solamente. No creé, cambié ni borré eventos.

Bad:
Usa /rmd <id>.

Bad:
Confirming a stale action from a previous context.

## Confirmation Rules

For destructive or external-write actions:
- ask confirmation first
- bind confirmation to the specific pending action
- never use stale pending actions
- after success, clear pending action

Applies to:
- deleting Google Calendar events
- creating Google Calendar events
- deleting reminders
- potentially deleting tasks

## Google Calendar Policy

Google Calendar owns:
- calendar events
- appointments
- native notifications

Val owns:
- interpretation
- agenda summary
- context
- reminders by Telegram
- tasks
- document preparation
- follow-up suggestions

Do not auto-mirror every Google Calendar event into Val reminders by default.

Future optional setting:
- "Also remind me by Telegram before Google Calendar events"
Default should be OFF.

## Known Current Capabilities

As of M5G:

- Val reads Google Calendar events.
- Val creates Google Calendar events after confirmation.
- Val deletes Google Calendar events by visible number after confirmation.
- Google Calendar events appear under "Eventos de Google Calendar".
- Val reminders appear under "Recordatorios de Val".
- Val tasks appear under "Tareas de Val".
- Document no-caption latest-document flow works.
- Numbered document references work.
- Reminder vencidos cleanup works.
- Routine read-only footer removed.

## Known Caveats

- Direct reminder editing may still use honest fallback.
- Voice routing may still expose transcription/intake issues.
- Document OCR/manual review still has limits.
- CLIENT_GROCERY.md remains an intentional uncommitted local file during this branch.
- Karen-specific hardcoded warning literal_karen remains known tech debt before multi-client expansion.

## Product Value

Karen's testing is defining the first real Personal OS operator profile.

This profile should later become:
- client preferences
- UX defaults
- safe action policies
- memory/workspace behavior
- per-client roadmap expectations
- onboarding/tutorial content

Karen is not only testing features; she is shaping the operating model.
