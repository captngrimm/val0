# GCAL_OAUTH_PREVIEW_SIDECAR_SYSTEMD_20260521

Status:
Installed and running on Val0.

Service:
val0-gcal-oauth.service

Service file:
/etc/systemd/system/val0-gcal-oauth.service

Purpose:
Run the Google Calendar OAuth callback preview-only sidecar.

Current mode:
Preview-only / Phase A.

Endpoints:
- GET /health
- GET /oauth2callback

Bind:
127.0.0.1:8080

Important:
The service is local-only. It is not publicly exposed.

Current behavior:
- validates OAuth callback state/code shape
- rejects bad state
- rejects missing code
- does not exchange token
- does not store token
- does not echo authorization code
- does not log secrets intentionally

ExecStart:
PYTHONPATH=/opt/val0 /opt/val0/.venv/bin/python -m uvicorn tools.gcal_oauth_sidecar:app --host 127.0.0.1 --port 8080

Verification:
- uvicorn_available=True
- fastapi_available=True
- systemd active/running
- /health returned OK val0-gcal-oauth preview-only
- bad-state callback rejected safely
- SECRET_ECHO_FAIL=NO
- ss showed listener on 127.0.0.1:8080 only

Next safe steps:
1. Keep sidecar local-only until reverse proxy/TLS decision.
2. Do not send OAuth link to Karen yet.
3. Add Telegram connection UX only when callback flow decision is clear.
4. Before live token exchange:
   - validate state
   - store token per client only
   - chmod 600
   - avoid logging code/token
   - confirm read-only scope
   - create disconnect/revoke plan

---

## Access log safety update — 2026-05-21

Finding:
Uvicorn access logs were logging full callback URLs, including query parameters.

Risk:
OAuth callback URLs may include authorization codes. Logging full URLs could expose sensitive OAuth authorization codes in journal logs.

Action:
Updated systemd ExecStart for val0-gcal-oauth.service to include:

--no-access-log

Current ExecStart:
PYTHONPATH=/opt/val0 /opt/val0/.venv/bin/python -m uvicorn tools.gcal_oauth_sidecar:app --host 127.0.0.1 --port 8080 --no-access-log

Verification:
- systemd daemon-reload completed
- val0-gcal-oauth.service restarted successfully
- service active/running
- callback with fake code returned safe rejection
- journal check for new fake code returned LOG_LEAK_FIXED=YES

Rule:
Do not proceed to live OAuth token exchange unless access logging remains disabled or callback logs are safely redacted.
