# CLIENT_CALENDAR — Karen / Val Personal

Purpose:
Track Karen's calendar integration status and rules.

---

## Status

provider:
google_calendar

connection_status:
not_connected

calendar_id:
pending

token_ref:
pending private server path

read_enabled:
planned

write_enabled:
planned, but not enabled until Karen explicitly authorizes it

---

## Intended use

Karen's Google Calendar should be the visible source for fixed appointments and events, such as:

- appointment with Nora
- lawyer meeting
- calls
- document delivery date
- family/admin appointments
- school/family/work events with date/time

Val0 should keep the context around those events:

- which case/project it belongs to
- what documents are needed
- what questions to ask
- what happened after the event
- follow-up tasks and reminders

---

## Privacy boundary

Karen's calendar must be independent from Frank's calendar and from any other client calendar.

No global Val0 calendar should be used as Karen's calendar.

---

## Current known gap

The legacy/global Google Calendar token is invalid and should not be repaired as the final Karen solution.

Before enabling Karen calendar access:
1. Create client-specific calendar token path.
2. Authorize Karen's Google account or chosen calendar account.
3. Verify read access.
4. Only then enable Agenda Bridge for Karen.

