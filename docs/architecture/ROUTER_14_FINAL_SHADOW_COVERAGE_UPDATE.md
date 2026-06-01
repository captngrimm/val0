# ROUTER-14 Final Shadow Coverage Update

## Summary

ROUTER-13 ran a live Intent Router v2 shadow observation window, then shadow mode was disabled. Karen RC full smoke passed 24/24 after disable.

ROUTER-13 reconfirmed lanes that were already counted as covered by ROUTER-12. This final update keeps the coverage numbers honest: no additional final-gap intents are marked covered without evidence.

No runtime behavior changed.

## ROUTER-13 Observation Results

| Input | Predicted intent | Actual intent | Handler | Match | Coverage effect |
| --- | --- | --- | --- | --- | --- |
| `Val resume el último documento` | `document_summary` | `document_summary` | `maybe_handle_document_summary_query` | `match=True` | Already covered; reconfirmed. |
| `Val elimina el evento 1` | `gcal_delete` | `gcal_delete` | `maybe_handle_karen_gcal_event_number_delete` | `match=True` | Already covered; reconfirmed. |
| `Val qué recordatorios tengo` | `reminder_query` | `reminder_query` | `maybe_handle_karen_reminder_management` | `match=True` | Already covered; reconfirmed. |
| `elimina el recordatorio 1` | `reminder_delete` | `reminder_delete` | `maybe_handle_karen_reminder_management` | `match=True` | Already covered; reconfirmed. |
| `Val recuérdame cumpleaños de Miguel el lunes 1 de junio a las 10am` | `reminder_create` | `reminder_create` | `maybe_handle_karen_natural_weekday_reminder` | `match=True` | Already covered; reconfirmed. |

## Updated Coverage Counts

The current coverage diagnostic should remain:

- `COVERED`: 11
- `NEEDS_LIVE_OBSERVATION`: 4
- `NEEDS_ACTUAL_LABEL`: 0
- `SHADOW_ONLY`: 2

Covered lanes:

- `task_query`
- `agenda_query`
- `destructive_confirmation`
- `document_ocr`
- `document_summary`
- `gcal_create`
- `gcal_delete`
- `reminder_create`
- `reminder_query`
- `reminder_delete`
- `case_status`

## Remaining Unobserved Gaps

These lanes still need clean shadow observation before any migration proposal:

- `pending_action_reply`
- `reminder_update`
- `task_complete`
- `task_delete`

Shadow-only lanes remain:

- `memory_capture_candidate`
- `llm_fallback`

## Operational Note

Shadow mode was disabled after the ROUTER-13 observation window. Karen RC full smoke passed 24/24 afterward. This report is documentation only and does not change routing, handlers, or user-facing behavior.
