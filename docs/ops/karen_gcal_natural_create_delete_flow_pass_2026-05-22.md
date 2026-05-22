# Karen Google Calendar Natural Create/Delete Flow Pass — 2026-05-22

## Status

PASS: Karen can create and delete Google Calendar events through natural Telegram language with confirmation.

## Confirmed create flow

User message:

- `Val, tengo cita con Mabel mañana a las 6pm`

Val response:

- Parsed date/time/title.
- Presented draft.
- Asked for confirmation.
- On `si`, created event in Karen's real Google Calendar.
- `Val, ¿qué tengo mañana?` showed `Cita con Mabel` at 6:00 PM from Google Calendar.

## Confirmed delete flow

Initial delete route was intercepted by grocery/list delete:

- `Val borra cabalgata intensa`
- Val incorrectly treated it as supermarket cleanup.

Fix:

- Added Google Calendar delete priority gate before grocery/list delete.
- Commit: `bde46d7 Prioritize Karen Google Calendar delete over grocery delete`

Expected/confirmed behavior after fix:

- `Val borra cabalgata intensa`
- Val finds the Google Calendar event.
- Val asks for confirmation.
- On confirmation, deletes only that event_id.

## Safety boundaries

- Create requires confirmation.
- Delete requires event lookup plus confirmation.
- Delete targets a specific event_id only.
- No broad calendar cleanup.
- No edit/update flow yet.
- Legacy/global writer must not be used for Karen.

## Current milestone stack

- `45f7c06` Document Karen Google Calendar read write full pass
- `3980ce7` Add Karen Google Calendar appointment confirmation flow
- `4b4bb11` Add guarded client Google Calendar delete helpers
- `f943d49` Add Karen Google Calendar delete confirmation flow
- `bde46d7` Prioritize Karen Google Calendar delete over grocery delete

## Next product milestone

Polish UX copy and reduce rough edges:
- Say “Google Calendar” clearly when creating/deleting.
- Possibly remove jokes from production copy.
- Add audit log for created/deleted event IDs.
- Add duplicate detection before creating a same-title/same-time event.
