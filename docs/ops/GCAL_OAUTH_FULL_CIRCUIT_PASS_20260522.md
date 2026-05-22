# GCAL_OAUTH_FULL_CIRCUIT_PASS_20260522

Status:
PASS.

Client:
karen

Mode:
Google Calendar read-only.

Infrastructure confirmed:
- auth.holaval.com HTTPS callback working
- Nginx reverse proxy working
- val0-gcal-oauth sidecar working
- exchange mode gated behind VAL0_GCAL_OAUTH_EXCHANGE_ENABLED=1
- exchange mode disabled after test
- per-client token path works:
  /etc/val0/clients/karen/gcal/refresh_token
- token file mode 600
- gcal directory mode 700
- calendar_id=primary

Final smoke results:
- refresh token stored with real newline, not literal backslash-n
- CONTAINS_LITERAL_BACKSLASH_N=False
- TOKEN_REFRESH_OK=YES
- HAS_ACCESS_TOKEN=True
- EXPIRY_PRESENT=True
- GCAL_MODULE_READ_STATUS=ok
- EVENT_COUNT_NEXT_14_DAYS=1
- RECENT_SECRET_LOG_LEAK=NO

Root cause fixed:
Refresh token was previously stored with literal "\\n" characters:
refresh_token.strip() + "\\n"

Fix:
Store with real newline:
refresh_token.strip() + "\n"

Important boundary:
This is still read-only. No create/update/delete calendar actions are enabled.

Production note:
If this token was authorized using Frank's account for lab testing, replace it with Karen's real Google account before treating it as Karen production data.
