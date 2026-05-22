# Karen Google Calendar Real Connection Pass — 2026-05-22

## Status

PASS: Karen's real Google Calendar is connected in read-only mode.

## Confirmed

- `client_id`: `karen`
- Provider: Google Calendar
- Status: connected
- Mode: read-only
- Calendar: `primary`
- Uses legacy/global credentials: false
- Token storage: `/etc/val0/clients/karen/gcal/refresh_token`
- Google Calendar write remains disabled.

## Verification

The previous Frank/lab token was quarantined and removed from Karen's client folder.

Karen then authorized with her real Google account. OAuth callback returned:

- Google Calendar connected
- Status: read-only
- Client: karen
- Access token diagnostic: calendar list OK

Val0 verification showed real Karen events:

- `2026-05-23 09:30` · Cita topografo
- `2026-05-25` · Cumpleaños de Cumpleaños de Caro
- `2026-05-26 09:00` · Llamar al Juzgado para averiguar si salió el Oficio
- `2026-05-28 14:00` · Capacitación gerente de sucursal

Dashboard smoke rendered Google Calendar plus internal Val agenda successfully.

## Safety

- Read-only only.
- Do not enable Google Calendar write yet.
- Internal Val reminders remain separate from Google Calendar events.
- Next possible milestone: polish agenda display labels and later design explicit opt-in Google Calendar write/sync.
