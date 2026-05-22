# CLIENT_GCAL_OAUTH_LAB_PLAN_V0

Purpose:
Plan a safe per-client Google Calendar OAuth connection flow for Val0/Valdía without mixing client accounts or writing calendar events too early.

---

## Core rule

Each client calendar must be isolated.

Never use Frank/global/legacy Google Calendar credentials for Karen or any other client.

---

## Current status

Karen:
- Google Calendar is not connected.
- Val can currently use internal agenda only.
- Internal agenda supports:
  - natural appointment save
  - date lookup
  - anchored reminder before appointment
  - richer agenda list

Existing boundary message:
Google Calendar todavía no está conectado para Karen; esto es solo agenda interna de Val.

---

## Target architecture

Per client:

- client_id: karen
- config path: /etc/val0/clients/karen/gcal/
- token path: /etc/val0/clients/karen/gcal/refresh_token
- credential/config metadata: client-scoped
- no shared calendar token
- no global write access

---

## OAuth phases

### Phase 0 — Lab design only

No OAuth live.
No token creation.
No calendar read/write.

Deliverables:
- architecture doc
- risk checklist
- command plan
- user consent copy
- read-only test criteria

### Phase 1 — Read-only connection

Goal:
Let Karen authorize Val to read calendar events.

Allowed:
- read upcoming events
- show events alongside internal Val agenda
- never modify calendar

Blocked:
- creating events
- editing events
- deleting events

Success criteria:
- token stored under Karen-only path
- `Val, puedes ver mi calendario?` returns connected/read-only status
- `Val, qué tengo en agenda?` can show internal agenda + Google Calendar read-only events
- no Frank calendar data appears

### Phase 2 — Write candidate / explicit confirmation

Goal:
Create events only after explicit user confirmation.

Allowed:
- draft an event proposal
- ask for confirmation
- then create event

Blocked:
- silent event creation
- auto-sync all internal events
- deleting/updating without confirmation

Success criteria:
- “Val, tengo cita con Nora...” creates internal event first
- Val asks whether to add to Google Calendar
- event creation requires explicit “sí, agrégalo al calendario”
- event output includes calendar event ID/audit note

### Phase 3 — Sync rules

Goal:
Decide how internal agenda and Google Calendar should coexist.

Open questions:
- Should internal agenda be source of truth?
- Should GCal be source of truth?
- Should Val maintain both with parent_ref mapping?
- How to avoid duplicate events?
- How to handle edits/reschedules?

---

## Privacy / safety checklist

Before enabling live OAuth:

1. Confirm client identity.
2. Confirm client-specific token path.
3. Confirm scopes.
4. Confirm read-only first.
5. Confirm no global legacy token is used.
6. Confirm logs do not expose tokens.
7. Confirm revoke instructions exist.
8. Confirm calendar output never mixes client data.
9. Confirm write actions require explicit confirmation.
10. Confirm rollback/disconnect command.

---

## Recommended scopes

Start with read-only scope.

Read-only:
- calendar events read

Write scope only later:
- calendar event create/update

Do not request broad scopes unless needed.

---

## User consent copy draft

Spanish-first:

“Para conectar tu Google Calendar, Val necesita permiso para leer tus eventos y mostrarte tu agenda junto con lo que ya tienes guardado en Val. Primero será solo lectura: Val no va a crear, cambiar ni borrar eventos sin pedirte confirmación explícita.”

---

## First implementation target

Command/phrase:
“Val, conecta mi Google Calendar”

Response:
- explains permission
- gives auth link
- says read-only first
- says events remain client-private
- stores token only under client-specific path after callback

---

## Lab exit criteria

This can move from Lab to Production only when:

- Karen-specific token path works
- read-only calendar status works
- calendar read returns expected events
- Frank/global calendar is never queried
- service restart preserves token
- disconnect/revoke process exists
- evidence log records test PASS

