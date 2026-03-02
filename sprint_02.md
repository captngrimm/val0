# Sprint 02 — Reminder Creator + Ops Commands Re-enable
Updated: 2026-02-28

## Scope
A) Deterministic Reminder Creator (DM only)
B) Re-enable /ops /health /reminders handlers safely

## A) Reminder Creator (DM only)
### Requirements
- Parse Spanish trigger: "Recuérdame <text> en <N> minutos"
- Insert into reminders table (status=pending, due_at_utc UTC)
- Reply deterministic confirmation
- Audit log:
  - action=CMD_REMINDER_CREATE
  - payload includes parsed due + text

### Tests
- DM: "Recuérdame probar el sistema en 1 minuto."
- DB: row appears in reminders with due_at_utc ~ now+60s
- After due: ReminderRunner sends + marks sent

## B) Re-enable ops commands
### Requirements
- /ops, /health, /reminders should register without NameError
- Keep deterministic, no model dependency

### Tests
- DM: /ops returns status
- DM: /health returns tick age
- DM: /reminders shows pending/sending

## Definition of Done
- val0ctl ops green
- git clean
- reminder creation works end-to-end
- handlers enabled and working
