# Karen Google Calendar Read-Only Tech Pass — 2026-05-22

## Status

PASS: Karen client-scoped Google Calendar read-only connection is technically working.

## Confirmed

- `client_id`: `karen`
- Provider: Google Calendar
- Mode: read-only
- Calendar: `primary`
- Token storage: `/etc/val0/clients/karen/gcal/refresh_token`
- Uses legacy/global credentials: false
- Calendar write remains disabled via `VAL0_CALENDAR_WRITE_ENABLED=false`
- `val0-bot.service` is active
- `val0-gcal-oauth.service` is active
- Dashboard renders Google Calendar section plus internal Val agenda.

## Observed Dashboard Output

Weekly dashboard showed:

- Google Calendar read-only section
- `2026-05-27 · Evento sin título`
- Internal Val agenda:
  - `17:00 | recordatorio | Cita con Mabel, tema Libro Finca 10082.`

## Safety Notes

- This is read-only only.
- Do not enable Google Calendar write yet.
- Before telling Karen this is definitely her real Google account, confirm with Karen that the visible event on `2026-05-27` belongs to her calendar, or run a controlled reauth with her present.
- No tokens or secrets are stored in repo.
- Client token path is file-based under `/etc/val0/clients/karen/gcal/`.

## Related Commits

- `7be6465` Add Val0 service Python helper
- `89bd1a8` Improve Karen appointment title cleanup
- `4fffce5` Document Karen Google Calendar read-only pass
- `dd39081` Record Google Calendar OAuth full circuit pass
