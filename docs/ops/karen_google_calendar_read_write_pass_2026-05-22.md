# Karen Google Calendar Read/Write Full Pass — 2026-05-22

## Status

PASS: Karen's real Google Calendar is connected for read and guarded write.

## Confirmed flow

1. Frank/lab calendar token was removed from Karen client folder.
2. Karen authorized her real Google account.
3. Google Calendar read-only worked with Karen's real calendar.
4. Karen then authorized write scope.
5. Read initially broke due to scope mismatch after write authorization.
6. Val0 was patched to support reading after write-scope authorization.
7. Client-scoped write skeleton was tested:
   - dry run returned `dry_run`
   - real write with gates off returned `blocked`
8. Write gates were enabled:
   - global gate: `VAL0_CLIENT_GCAL_WRITE_ENABLED=true`
   - client gate: `/etc/val0/clients/karen/gcal/write_enabled=true`
9. Val0 created a real Google Calendar event in Karen's calendar:
   - Title: `Cabalgata Intensa`
   - Date/time: 2026-05-23 20:00 America/Panama
   - Duration: 15 minutes
10. Karen queried Val afterward:
   - `Val, ¿qué tengo mañana?`
   - Val showed:
     - `Sat 23/05 9:30 AM · Cita topografo`
     - `Sat 23/05 8:00 PM · Cabalgata Intensa`

## Safety state

- Google Calendar write is client-scoped.
- Legacy/global writer must not be used for Karen.
- Agenda query remains read-only.
- Real event creation must stay behind explicit confirmation.
- Agenda interna de Val remains separate from Google Calendar.
- Next product milestone: natural flow
  `Val, registra cita...` → parsed event draft → user confirms → create event in Google Calendar.

## Current commits involved

- `c34eddf` Add client-scoped Google Calendar write skeleton
- `6eefff6` Fix client Google Calendar write OAuth callback scopes
- `a74db90` Support Google Calendar reads after write auth

## Notes

The test event was intentionally humorous and should be deleted later if Karen prefers.
