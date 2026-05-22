# CLIENT_GCAL_OAUTH_CALLBACK_SAFETY_V0

Purpose:
Define the safety rules for Google Calendar OAuth callback/token exchange before implementing any live token storage.

---

## Current sealed state

Existing safe pieces:

- Client GCal OAuth auth-link skeleton exists.
- Auth link uses Google Calendar read-only scope.
- Auth state includes client prefix:
  - client:<client_id>:<random>
- No token exchange is implemented yet.
- No refresh token writing is implemented yet.
- Client GCal read module only reads from:
  - /etc/val0/clients/<client_id>/gcal/
- Legacy global calendar write is disabled and guarded.

---

## Non-negotiable rules

### 1. Validate state

Callback must reject requests unless state matches expected format:

client:<client_id>:<random>

Rules:
- client_id must sanitize to known/safe client id.
- unknown client ids must be rejected.
- missing state must be rejected.
- malformed state must be rejected.
- state should be one-time-use when persistent state store exists.

### 2. Read-only first

Allowed scope in Phase 1:

https://www.googleapis.com/auth/calendar.readonly

Blocked in Phase 1:
- https://www.googleapis.com/auth/calendar
- write/update/delete scopes
- broad account scopes

### 3. Store token per client only

Karen token path:

/etc/val0/clients/karen/gcal/refresh_token

Required structure:

/etc/val0/clients/<client_id>/gcal/
  client_secret.json
  refresh_token
  calendar_id

Never write user refresh tokens to:
- /etc/val0/gcal/
- repo files
- logs
- Telegram messages
- Launchpad output

### 4. File permissions

Token files must be:
- owner: root
- group: root
- mode: 600

Directories should be:
- owner: root
- group: root
- mode: 700 if practical

### 5. No token logging

Callback must never print:
- access_token
- refresh_token
- full credentials JSON
- authorization code
- request URL containing code

Logs may include:
- client_id
- status success/failure
- token stored yes/no
- scope validated yes/no
- safe token path metadata only

### 6. Calendar ID handling

Default calendar_id may be:
- primary

Later, client may choose a specific calendar id.

Calendar id path:
- /etc/val0/clients/<client_id>/gcal/calendar_id

### 7. Disconnect / revoke path

Before Production, must support:
- remove local token
- mark calendar disconnected
- explain how user can revoke access in Google account security settings

### 8. No auto-write

Callback only enables read-only status.

It must not:
- create Google Calendar events
- sync internal Val events automatically
- edit/delete anything
- migrate reminders

### 9. User-facing confirmation

After successful callback, user-facing message should say:

“Google Calendar conectado en modo solo lectura. Val puede mostrar tus eventos junto con tu agenda interna, pero no va a crear, cambiar ni borrar eventos.”

### 10. Evidence log

A successful Phase 1 test must record:
- client id
- connected status
- read-only mode
- no global credential use
- service restart persistence
- agenda display with GCal read-only events if test calendar has events

---

## Callback implementation sketch

Endpoint:
GET /oauth2callback

Steps:
1. Receive state and code.
2. Validate state.
3. Extract client_id from state.
4. Confirm client_id is allowed.
5. Exchange code with Google using read-only scope.
6. Confirm refresh_token exists.
7. Create client gcal dir.
8. Store refresh_token to client path with mode 600.
9. Store app client_secret copy or reference according to final deployment policy.
10. Store calendar_id default as primary if absent.
11. Return safe success page.
12. Do not print secrets.

---

## Open implementation questions

1. Should callback live inside existing bot process, a small FastAPI/Flask sidecar, or existing dashboard service?
2. Should client_secret.json be copied per client or referenced from app-level config?
3. Where should one-time OAuth state be stored?
   - file
   - SQLite
   - temporary signed state only
4. How do we authenticate that the user starting OAuth is actually Karen?
5. Should the auth link be short-lived?
6. How do we display success/failure back inside Telegram?

---

## Phase 1 exit criteria

OAuth callback can move from Lab to controlled test only when:

- state validation implemented
- token storage path is per-client
- token file permissions are enforced
- no secrets in logs
- read-only scope verified
- disconnect plan documented
- smoke test proves Karen status changes from not_connected to connected
- no legacy /etc/val0/gcal token used for Karen
