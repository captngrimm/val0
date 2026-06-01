# ROUTER-09 Coverage Gap Report

## Summary

ROUTER-08 expanded the Intent Router v2 shadow sample harness to 47 representative Karen phrases. The harness now covers direct utilities, destructive actions, documents/OCR, case/finca/legal context, voice-prefix variants, pending replies, and fallback language.

ROUTER-09 compares that sample coverage with actual legacy handler labels and the first clean shadow observation report. This is not a router refactor. Intent Router v2 remains shadow-only and default OFF.

## Current Coverage

The current strongest coverage is where all of these are true:

1. classifier coverage
2. actual handler labels
3. sample harness coverage
4. at least one clean shadow observation
5. Karen RC full smoke passing

Current `COVERED` lanes from the first observation window:

- `task_query`
- `agenda_query`
- `gcal_create`
- `destructive_confirmation`
- `reminder_create`
- `document_ocr`
- `case_status`

## Coverage Status Meanings

- `COVERED`: classifier, actual label, sample coverage, and at least one clean observation exist.
- `SHADOW_ONLY`: classifier/sample coverage exists, but this should remain diagnostic or fallback-only for now.
- `NEEDS_ACTUAL_LABEL`: sample/classifier coverage exists, but the legacy runtime handler does not yet report an actual label.
- `NEEDS_LIVE_OBSERVATION`: classifier and actual label exist, but a clean shadow observation has not been recorded yet.

## Needs Actual Labels Or Observation

These lanes should be observed or labeled before any migration proposal:

- `task_delete`
- `task_complete`
- `reminder_query`
- `reminder_delete`
- `reminder_update`
- `gcal_delete`
- `document_summary`
- `memory_capture_candidate`
- `llm_fallback`

Suggested next observations:

- task delete
- task complete
- reminder query
- reminder delete
- reminder update
- Google Calendar delete
- normal document summary
- numbered document summary
- memory capture candidate
- LLM fallback

## Refactor Rule

Router migration should only start with lanes that have:

1. classifier coverage
2. actual handler labels
3. sample harness coverage
4. at least one clean shadow observation
5. Karen RC full smoke passing

Until then, keep Intent Router v2 in diagnostics/shadow mode. Do not route messages through it.

## Diagnostic Command

Use:

```bash
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
python3 scripts/diagnostics/intent_router_v2_coverage_report.py --json
```

The script reads the sample harness, scans observer labels, checks the ROUTER-07 observation report, and writes a local copy under `tmp/router_coverage/`.

## ROUTER-10 Update

ROUTER-10 adds the missing actual labels for:

- `pending_action_reply`
- `reminder_query`
- `reminder_delete`
- `reminder_update`
- `task_complete`

After this label-only change, those lanes should move from `NEEDS_ACTUAL_LABEL` to `NEEDS_LIVE_OBSERVATION`. The next step is a short shadow observation window for those intents. This is still not a router refactor and introduces no behavior change.

## ROUTER-12 Update

ROUTER-12 records a clean follow-up shadow observation for:

- `document_summary`
- `gcal_delete`
- `reminder_query`
- `reminder_delete`

Those lanes should now move to `COVERED`. Remaining `NEEDS_LIVE_OBSERVATION` gaps are `pending_action_reply`, `reminder_update`, `task_complete`, and `task_delete`.
