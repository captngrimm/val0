# CLIENT_GCAL_OAUTH_CALLBACK_ARCHITECTURE_V0

Purpose:
Decide where the Google Calendar OAuth callback should live before implementing live token exchange.

---

## Recommendation

Use a small HTTP sidecar service for OAuth callback.

Do not embed the OAuth HTTP callback inside the Telegram bot.

---

## Why sidecar

### Separation of concerns

Telegram bot:
- handles chat
- handles client UX
- stores internal agenda/reminders
- reports calendar connection status

OAuth sidecar:
- receives Google OAuth callback
- validates state
- exchanges code for token in later phase
- stores refresh token per client
- returns success/failure page

This avoids mixing long-polling Telegram behavior with public HTTP callback behavior.

---

## Proposed service

Name:
val0-gcal-oauth.service

Possible file:
tools/gcal_oauth_sidecar.py

Framework:
FastAPI or Flask

Preferred:
FastAPI, because Val0 already has FastAPI patterns/dependencies elsewhere and cleaner validation.

Port:
Start internal/private first:
- 127.0.0.1:8080

Public exposure:
Only after reverse proxy/TLS decision.

Current redirect URI in skeleton:
http://omfgeeks.com:8080/oauth2callback

This is acceptable for skeleton/testing only.
Before production, review:
- HTTPS
- domain
- firewall
- Google OAuth redirect config
- whether raw port 8080 should remain public

---

## Phase plan

### Phase A — Preview-only sidecar

Endpoint:
GET /oauth2callback

Behavior:
- accepts state/code
- validates state using parse_client_oauth_state
- confirms whether code is present
- does not exchange token
- does not store token
- does not log code/token
- returns safe HTML/plain text result

Goal:
Verify routing/callback shape safely.

### Phase B — Token exchange controlled test

Only after Phase A passes.

Behavior:
- validate state
- exchange code using read-only scope
- verify refresh_token exists
- store refresh_token under:
  /etc/val0/clients/<client_id>/gcal/refresh_token
- chmod 600
- write calendar_id=primary if absent
- no token logs
- return safe success page

### Phase C — Telegram UX

Add route:
“Val, conecta mi Google Calendar”

Behavior:
- explain read-only first
- generate auth link
- do not oversell
- tell user callback must complete
- after connected, status route shows connected/read-only

### Phase D — Agenda merge read-only

Only after token exists.

Behavior:
- agenda summary can show internal Val agenda + Google Calendar read-only events
- clearly label sources
- no write/sync
- no dedup automation yet

---

## Security rules

1. No refresh token logs.
2. No callback URL logs containing code.
3. No global /etc/val0/gcal token for Karen/client flows.
4. Client token path only:
   /etc/val0/clients/<client_id>/gcal/refresh_token
5. Token file mode 600.
6. Directory mode 700 if practical.
7. Read-only scope first.
8. No write scope in Phase 1.
9. No event create/update/delete from OAuth callback.
10. Disconnect/revoke plan before production.

---

## Open decisions

1. FastAPI or Flask final choice.
2. Port and reverse proxy.
3. HTTPS before real client test.
4. How to store one-time state.
5. How Telegram gets notified after successful connection.
6. Whether to copy client_secret.json per client or reference app-level secret.
7. Whether to rotate the exposed legacy google_oauth/client secret before live OAuth.

---

## Recommendation for next build step

Implement Phase A preview-only sidecar:

- tools/gcal_oauth_sidecar.py
- GET /health
- GET /oauth2callback
- uses render_client_oauth_callback_preview
- no token exchange
- no token storage
- no secrets in logs

Then add systemd service only after local smoke test passes.

