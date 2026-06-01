# ROUTER-12 Post-Observation Coverage Update

## Summary

ROUTER-11 ran a clean live shadow observation window with `VAL0_INTENT_ROUTER_V2_SHADOW=true`, then shadow mode was disabled. Karen RC full smoke passed 24/24 after disable.

This report records the new observed `match=True` lanes and updates coverage expectations. No runtime behavior changed.

## ROUTER-11 Results

| Input | Predicted intent | Actual intent | Handler | Match | Notes |
| --- | --- | --- | --- | --- | --- |
| `Val resume el último documento` | `document_summary` | `document_summary` | `maybe_handle_document_summary_query` | `match=True` | Normal latest-document summary aligned. |
| `Val elimina el evento 1` | `gcal_delete` | `gcal_delete` | `maybe_handle_karen_gcal_event_number_delete` | `match=True` | Numbered Google Calendar delete route aligned. |
| `Val qué recordatorios tengo` | `reminder_query` | `reminder_query` | `maybe_handle_karen_reminder_management` | `match=True` | Reminder list route aligned. |
| `elimina el recordatorio 1` | `reminder_delete` | `reminder_delete` | `maybe_handle_karen_reminder_management` | `match=True` | Numbered reminder delete route aligned. |
| `Val recuérdame cumpleaños de Miguel el lunes 1 de junio a las 10am` | `reminder_create` | `reminder_create` | `maybe_handle_karen_natural_weekday_reminder` | `match=True` | Reminder create was already covered; this reconfirmed it with a dated Monday phrase. |

## Updated Coverage Counts

Expected coverage after ROUTER-11:

- `COVERED`: 11
- `NEEDS_LIVE_OBSERVATION`: 4
- `NEEDS_ACTUAL_LABEL`: 0
- `SHADOW_ONLY`: 2

Newly covered by ROUTER-11:

- `document_summary`
- `gcal_delete`
- `reminder_query`
- `reminder_delete`

Already covered before ROUTER-11:

- `task_query`
- `agenda_query`
- `destructive_confirmation`
- `document_ocr`
- `gcal_create`
- `reminder_create`
- `case_status`

## Remaining Live Observation Gaps

These intents still need clean shadow observation before any migration proposal:

- `pending_action_reply`
- `reminder_update`
- `task_complete`
- `task_delete`

`memory_capture_candidate` and `llm_fallback` remain `SHADOW_ONLY` for now.

## Operational Note

Shadow mode was disabled after the ROUTER-11 observation window, and Karen RC full smoke passed afterward. This update changes only diagnostics and documentation. It does not route messages through Intent Router v2 and does not change user-facing behavior.
