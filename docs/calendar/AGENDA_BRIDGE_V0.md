# AGENDA_BRIDGE_V0 — Val0

Purpose:
Define the first safe calendar bridge for client-specific agenda lookup.

---

## Principle

Read before write.

Agenda Bridge v0 should first answer calendar questions safely before creating events.

---

## Supported first queries

- Val, qué tengo hoy?
- Val, qué tengo mañana?
- Val, qué tengo esta semana?
- Val, qué cita tengo para el 28?
- Val, qué tengo para el 28 de mayo?
- Val, tengo algo el 28?

---

## Data sources

Agenda Bridge v0 should merge:

1. Client Google Calendar events, if connected.
2. Val0 local reminders from encrypted DB.
3. Client/case appointment notes, only as secondary context.
4. Clear empty-state response if nothing is found.

---

## Empty-state response

If no event/reminder is found:

"No veo nada guardado para esa fecha. Si esa cita existe, dime fecha y hora y la guardo."

If calendar is not connected:

"Todavía no tengo conectado tu calendario. Puedo revisar recordatorios internos, pero para ver tu agenda real necesito conectar Google Calendar."

---

## Write behavior

Writing events is not part of the first bridge unless explicitly enabled.

Future write flow:
- user asks to create event
- Val confirms date/time/title
- Val writes to that client's calendar
- Val stores context in Val0 memory
- Val optionally creates follow-up/reminder

---

## Privacy requirement

Never use a global calendar as a client calendar.

Every calendar operation must resolve through client_id first.

