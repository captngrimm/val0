# Karen Google Calendar Read-Only PASS — 2026-05-22

## Scope

Val0 branch: `karen-client-zero-mvp-2026-05-25`

Karen agenda dashboard now includes Google Calendar read-only visibility plus Val internal agenda sections.

## Confirmed Telegram PASS

### Today

User:

`Val, ¿qué tengo hoy?`

Confirmed:

- Shows `📅 Agenda de hoy`
- Shows `🌐 Google Calendar · solo lectura`
- Shows `📌 Agenda interna de Val`
- Shows polished internal empty-state copy:
  - `No encontré recordatorios ni términos internos para hoy.`
- Shows safety line:
  - `Modo: lectura solamente. No creé, cambié ni borré eventos.`

### Tomorrow

User:

`Val, ¿qué tengo mañana?`

Confirmed:

- Shows `📅 Agenda de mañana`
- Shows Google Calendar read-only section
- Shows internal reminders/tasks section
- Does not create, edit, or delete events

### Next 7 days

User:

`Val, ¿qué tengo esta semana?`

Confirmed:

- Shows `📅 Agenda de los próximos 7 días`
- Shows Google Calendar event:
  - `2026-05-27 · (no title)`
- Shows internal agenda section
- Does not create, edit, or delete events

### Calendar connection status

User:

`Val, ¿puedes ver mi calendario?`

Confirmed:

- Provider: Google Calendar
- Status: connected
- Read: enabled
- Write: disabled for safety
- Calendar: primary

## Safety boundaries

- Google Calendar is read-only.
- Val0 must not create, change, or delete calendar events.
- Current token may belong to Frank/lab and must be replaced with Karen's real Google account token before real production use with Karen.
- Correct bot service: `val0-bot.service`.
- Do not use old `val0.service`; it is not the real bot and may be broken/restarting due to missing `RESEND_API_KEY`.
- OAuth sidecar: `val0-gcal-oauth.service`.
- OAuth exchange mode should remain preview-only unless doing controlled reauth.

## Relevant commits

- `dd39081` Record Google Calendar OAuth full circuit pass
- `457ceee` Fix Google Calendar refresh token newline storage
- `fcae276` Add Google Calendar OAuth fresh access token diagnostic
- `bf068ca` Add Karen Google Calendar read-only agenda dashboard
- `167af88` Prioritize Karen agenda dashboard over document routes
- `056b77c` Route second Karen agenda shield to Google Calendar dashboard
- `4beb5d3` Normalize Karen agenda queries with Val prefix punctuation

## Next milestone options

1. Replace lab/Frank Google token with Karen's real Google Calendar token.
2. Polish agenda UX and empty states.
3. Continue Karen delivery prep for 2026-05-26.
