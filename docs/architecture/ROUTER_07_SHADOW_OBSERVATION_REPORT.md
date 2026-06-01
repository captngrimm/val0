# ROUTER-07 Shadow Observation Report

## Purpose

This report captures the first real predicted-vs-actual Intent Router v2 shadow observation results for Karen RC.

It establishes a baseline before any router refactor. Intent Router v2 remained shadow-only during the observation window, so no messages were routed through it and no user-facing behavior changed.

## Observation Window Summary

- Date/time: 2026-05-31 late evening Panama time.
- Shadow mode was temporarily enabled with `VAL0_INTENT_ROUTER_V2_SHADOW=true`.
- Shadow mode was disabled after the observation window.
- Karen RC full smoke passed after disable:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

## Results

| Input | Predicted intent | Actual intent | Handler | Match | Notes |
| --- | --- | --- | --- | --- | --- |
| `Val que tareas tengo activas?` | `task_query` | `task_query` | `maybe_handle_karen_task_query_hard_gate` | `match=True` | Task hard gate aligned with router prediction. |
| `Val, qué tengo mañana?` | `agenda_query` | `agenda_query` | agenda dashboard route | `match=True` | Current agenda dashboard handled the query. |
| `Val agenda prueba sombra mañana a las 10am` | `gcal_create` | `gcal_create` | `try_appointment_save_natural` | `match=True` | Google Calendar create route aligned. |
| `cancelar` | `destructive_confirmation` | `destructive_confirmation` | pending GCal confirmation route | `match=True` | Cancel was consumed by the pending confirmation route. |
| `Recuérdame en 10 minutos prueba sombra` | `reminder_create` | `reminder_create` | `handle_reminder_gate` | `match=True` | Relative reminder route aligned. |
| `Val resume con OCR el último documento` | `document_ocr` | `document_ocr` | `maybe_handle_document_ocr_query` | `match=True` | Earlier clean observation confirmed OCR route alignment. |
| `Qué tengo guardado del caso del terreno` | `case_status` | `case_status` | `maybe_handle_karen_case_status` | `match=True` | Case status route aligned. |

## Interpretation

- Direct utility lanes are ready for more shadow measurement.
- Router predictions are currently aligned with legacy handlers for the tested commands.
- No behavior change occurred during this observation window.
- Shadow logs are useful for future refactor planning because they show where current legacy routing agrees with the planned priority model.

## Known Gaps

- More voice-transcription variants need observation.
- More destructive actions need observation:
  - task delete
  - reminder delete
  - Google Calendar delete
- More document flows need observation:
  - normal document summary
  - numbered document summary
  - latest document OCR
- Memory-capture and LLM fallback paths still need observation.
- A later batch observation harness should read sanitized logs and summarize match/mismatch patterns.

## Next Recommended Router Steps

- ROUTER-08: Expand shadow sample set with delete/reminder/document variants.
- ROUTER-09: Shadow actual-label coverage for remaining high-value routes.
- ROUTER-10: First shadow-only migration candidate proposal, with no runtime behavior changes.
