# Sprint 02 — Reminder Hardening + Cancel + Chat-Scoped Listing
Updated: 2026-03-02

## Scope
A) Deterministic Reminder Creator (DM only) — expanded grammar + punctuation tolerance  
B) Deterministic cancel paths (text + command)  
C) Re-enable /ops /health /reminders handlers safely  
D) Fix reminder listing isolation (no cross-chat bleed)  

## A) Reminder Creator (DM only)
### Supported grammar (deterministic)
- Verbs (tolerant):
  - "recuérdame" / "recuerdame"
  - "acuérdame" / "acuerdame"
  - "recordame"
- Time forms:
  1) "<verb> <text> en <N> minutos"
  2) "<verb> <text> en <N> horas"
  3) "<verb> <text> mañana a las <HH:MM|3pm|3:15pm>"
  4) "<verb> <text> (hoy) a las <HH:MM|6pm|6:15pm>"
- Punctuation tolerance:
  - trailing ".", "!", "?" allowed (stripped)

### Requirements
- Insert into reminders table:
  - status=pending
  - due_at_utc stored in UTC (authoritative)
- Reply deterministic confirmation
- Audit log:
  - action=CMD_REMINDER_CREATE
  - payload includes mode + due_at_utc + text

### Tests
- DM: "Acuérdame probar el sistema en 1 minuto."
- DM: "Recuérdame chequear logs en 2 horas."
- DM: "Recuérdame pagar X mañana a las 3pm"
- DM: "Recuérdame llamar a Miguel hoy a las 18:00."
- DB: rows appear with correct due_at_utc
- After due: ReminderRunner sends + marks sent/failed deterministically

## B) Cancel reminders (DM deterministic)
### Supported cancel grammar (deterministic)
- Text:
  - "cancela 23"
  - "olvida 23"
  - "borra 23"
  - optional: "recordatorio", "#"
- Command:
  - /rmd <id>  (alias for cancel)

### Requirements
- Only cancel if:
  - reminder belongs to chat_id
  - status in (pending, sending)
- Update status -> cancelled
- Audit log:
  - action=CMD_REMINDER_CANCEL
  - payload includes rid + ok

### Tests
- Create reminder, then: "cancela <id>" -> removed from pending list
- /rmd <id> works same way
- DB confirms status=cancelled

## C) Re-enable ops commands
### Requirements
- /ops, /health, /reminders register without NameError
- Keep deterministic; no model dependency
- /reminders lists only caller chat_id reminders (no cross-chat leakage)

### Tests
- DM: /ops returns green status
- DM: /health returns tick age + stats
- DM: /reminders N shows pending/sending for that chat only

## D) Isolation fix — chat-scoped reminder listing
### Requirement
- /reminders must call list_reminders_for_chat(chat_id, ...)
- Never use global list_reminders() for user-facing lists unless chat_id passed

### Tests
- Two chat_ids with pending reminders
- /reminders in DM A shows only A
- /reminders in DM B shows only B

## Definition of Done
- Service stable (no crash loop)
- Reminder creation works end-to-end
- Cancel works end-to-end (text + /rmd)
- /reminders is chat-scoped
- val0ctl ops green
- git clean
- Audit log shows CMD_REMINDER_CREATE + CMD_REMINDER_CANCEL entries

## Notes / Known follow-ups (not blocking)
- Local-time display normalization for reminder list (currently shows due_at_utc raw)
- Telemetry counters (sent/cancelled/failed per tick)
- Multi-line / multi-command parsing (single message -> multiple reminders)