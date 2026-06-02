# Time Intelligence Layer

## Purpose

The time intelligence layer extracts reusable natural Spanish time parsing out of Karen-specific reminder code without changing current runtime behavior.

Karen reminder routes still call the existing compatibility helpers in `bot.py`. Those helpers now delegate to `core/time_intelligence.py`.

## Module Plan

- `core/time_intelligence.py`
  - reusable natural Spanish clock parsing
  - reusable relative-duration parsing
  - no-date future-today inference
  - ambiguous same-day AM-to-PM rollover
  - title time-phrase stripping
  - display preference enum/design helper
- `bot.py`
  - keeps Karen-specific wrappers and route behavior
  - keeps Karen-specific date/title extraction
  - keeps UTC storage and confirmation behavior
- `scripts/quality/karen_reminder_time_parser_smoke.py`
  - covers both compatibility wrappers and reusable parser behavior

## Supported Inputs

Relative durations:

- `media hora`
- `una hora`
- `una hora y media`
- `N minutos`
- `N horas`

Clock times:

- `9:20`
- `9 y 20`
- `3 de la tarde`
- `10 de la noche`
- `13:30`

Inference rules:

- If a no-date resolved time is still future today, infer today.
- If an ambiguous today time already passed and PM is still reasonable, roll forward to PM.
- Do not silently change explicit AM/PM, daypart, or 24h times.

## Display Preference Design

Internal storage remains normalized datetime/UTC. User-facing display can be rendered with a preference:

- `12h`
- `24h`
- `natural_spanish`

Do not force a global display preference. Confirmation copy should reflect the stored value.

## Migration Notes

- Existing Karen wrappers remain in `bot.py` for compatibility.
- Existing smokes should stay green before any runtime behavior changes.
- Future clients can import `core.time_intelligence` directly instead of copying Karen-specific parser code.
- Any future route migration must keep client isolation and avoid hardcoded chat IDs.

## Runtime Note

This extraction does not refactor the router, does not restart runtime, and does not change reminder storage.
