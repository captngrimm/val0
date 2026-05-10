# KAREN REMINDER DUE-TIME V0 PASS

## Date
2026-05-10

## Branch
karen-client-zero-mvp-2026-05-25

## Status
PASS básico.

## Context

Karen/Frank tested whether Val reminders actually send a Telegram message when due.

Earlier issue:
- reminder creation worked
- but no message arrived because the reminder runner/job was not scheduled

Fix:
- scheduled `_reminder_tick` via JobQueue run_repeating

## Validated input

Val, recuérdame en 2 minutos revisar los documentos del caso del terreno.

## Immediate response

Val replied:

Listo. Te lo recuerdo en 2 minuto(s).

## Due-time result

After the due time, Val sent a Telegram message:

revisar los documentos del caso del terreno

## Result

PASS básico.

The reminder engine can now:
- create reminder
- wait until due
- send reminder message in Telegram

## Remaining polish

- User-facing reminder message is too bare/raw.
- Should render as something like:
  ⏰ Recordatorio: revisar los documentos del caso del terreno
- Future actions:
  - mark done
  - snooze
  - reschedule
  - optional Google Calendar integration for stronger phone-level notifications

## Product implication

For Karen MVP, reminders can be described as working in beta/basic form.

Important legal reminders should still have Google Calendar/phone alarm backup until more reliability testing passes.
