# CLIENT_CALENDAR_REGISTRY — Val0 Platform

Purpose:
Track calendar integrations per client.

This prevents Val0 from using one global Google Calendar for every client.

Privacy rule:
A client's calendar must never be mixed with another client's calendar.

---

## Current state

Val0 has a legacy/global Google Calendar configuration:

- /etc/val0/gcal/client_secret.json
- /etc/val0/gcal/refresh_token
- /etc/val0/gcal/calendar_id

Current issue:
- The global refresh token is invalid.
- This should not be treated as the final multi-client architecture.

---

## Target model

Each client should have a calendar connector record.

Example:

client_id:
karen

provider:
google_calendar

status:
not_connected / connected / needs_reauth / disabled

calendar_id:
primary

token_ref:
private server path, not stored in repo

read_enabled:
true / false

write_enabled:
false by default unless explicitly enabled

notes:
Human-visible events should live in the client's calendar.
Val0 keeps context, follow-up notes, client memory, and workflow state.

---

## Storage rule

Do not store OAuth secrets or refresh tokens in this repo.

Allowed in repo:
- client_id
- provider name
- status
- calendar_id if non-sensitive
- capability status
- setup notes
- last verification timestamp

Not allowed in repo:
- refresh_token
- access_token
- client_secret
- private credentials

---

## Calendar ownership rule

Frank calendar:
Only for Frank.

Karen calendar:
Only for Karen.

Business client calendar:
Only for that client or company account.

Val0 must resolve calendar access through client_id before reading or writing events.

---

## Event vs memory split

Google Calendar stores:
- meetings
- appointments
- calls
- delivery dates
- fixed-time events

Val0 stores:
- context
- why the event matters
- related case/project
- documents needed
- questions to ask
- post-meeting follow-up
- roadmap/client memory

---

## Agenda Bridge v0 target behavior

When client asks:
"Val, qué cita tengo para el 28?"

Val0 should:

1. Resolve client_id.
2. Check whether calendar is connected.
3. Read events from that client's calendar for the requested date.
4. Read Val0 reminders for the requested date.
5. Optionally read client/case notes that mention appointments.
6. Respond honestly:
   - show events found
   - show reminders found
   - say if calendar is not connected
   - say if nothing is found
   - never invent events

