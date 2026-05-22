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


---

## Safety audit update — 2026-05-21

Finding:
Existing legacy GCal infrastructure uses global paths:

- /etc/val0/gcal/client_secret.json
- /etc/val0/gcal/refresh_token
- /etc/val0/gcal/calendar_id

Existing write toggle was enabled at systemd level:

- VAL0_CALENDAR_WRITE_ENABLED=true

Action:
Global calendar write was disabled through systemd drop-in:

- /etc/systemd/system/val0-bot.service.d/zz-gcal-write.conf
- VAL0_CALENDAR_WRITE_ENABLED=false

Interpretation:
This does not implement client OAuth. It only reduces risk while client-specific read-only OAuth is designed.

Rule reinforced:
Karen/client calendar work must not use legacy global /etc/val0/gcal credentials.

---

## Callback safety design update

Before implementing token exchange, use:

docs/lab/gcal/CLIENT_GCAL_OAUTH_CALLBACK_SAFETY_V0.md

Rule:
No live callback/token storage until callback safety rules are implemented:
- validate state
- read-only scope only
- store refresh token per client
- chmod 600
- no token logging
- disconnect/revoke path
- no auto-write

---

## Callback architecture update

Use:

docs/lab/gcal/CLIENT_GCAL_OAUTH_CALLBACK_ARCHITECTURE_V0.md

Decision:
OAuth callback should live in a small sidecar service, not inside the Telegram bot.

Next safe build:
Phase A preview-only sidecar:
- /health
- /oauth2callback
- validate state/code presence
- no token exchange
- no token storage
- no secret logs

---

## Preview sidecar systemd update — 2026-05-21

Service installed:
val0-gcal-oauth.service

Mode:
Preview-only / Phase A

Bind:
127.0.0.1:8080

Endpoints:
- /health
- /oauth2callback

Verification:
- service active/running
- /health OK
- bad state rejected
- no secret/code echo
- local-only listener confirmed

Rule:
Do not expose publicly and do not send auth links to clients until callback/token exchange safety is complete.

---

## Access log safety update — 2026-05-21

Finding:
Sidecar access logs initially included full request URLs, which can include OAuth callback code query parameters.

Action:
Disabled Uvicorn access logs for val0-gcal-oauth.service using:

--no-access-log

Verification:
A fake callback code was not found in new journal logs after restart.

Rule:
Live token exchange must not proceed if OAuth authorization codes can appear in service logs.

---

## Public HTTPS callback update — 2026-05-21

Public callback domain:
https://auth.holaval.com/oauth2callback

Status:
HTTPS enabled and verified.

Infrastructure:
- DNS auth.holaval.com -> 167.172.239.59
- Nginx reverse proxy public 80/443
- Sidecar local-only on 127.0.0.1:8080
- Snap Certbot used because APT Certbot was broken by Python/OpenSSL package conflict

Verification:
- HTTPS /health OK
- HTTPS /oauth2callback safe rejection OK
- no fake OAuth code echoed
- no fake OAuth code found in Nginx logs
- no fake OAuth code found in sidecar journal

Rule:
Before token exchange, update VAL0_GCAL_OAUTH_REDIRECT_URI and Google Cloud OAuth redirect settings to the exact HTTPS callback URL.
