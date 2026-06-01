# ROUTER-16 Pending Context + Task Create Update

## Summary

ROUTER-15 live shadow observation found one useful mismatch and one missing diagnostic intent:

- `Eliminarla del listado` was predicted as `llm_fallback` while the legacy task-delete clarification consumed it as `pending_action_reply`.
- `Val registra tarea: router prueba completar` and `Val registra tarea: router prueba eliminar` were predicted as `llm_fallback`, while the legacy runtime correctly created tasks.

ROUTER-16 fixes those gaps in shadow diagnostics only. It does not route messages through Intent Router v2 and does not change runtime behavior.

## What Changed

- `classify_intent_shadow` now recognizes explicit task creation as `task_create`.
- The shadow hook can pass a lightweight pending state for Karen task-delete clarification when that context already exists.
- With pending task-delete context, follow-up phrases like `Eliminarla del listado`, `eliminarla`, `bórrala`, `quitarla`, and `sácala del listado` classify as `pending_action_reply`.
- Without pending context, those orphan follow-up phrases intentionally remain fallback rather than being treated as commands. This is the safer design because the phrase is only meaningful when a prior task-delete clarification exists.

## Coverage Impact

`task_create` is now part of the diagnostic coverage report.

Expected status:

- `task_create`: `NEEDS_LIVE_OBSERVATION`
- `pending_action_reply`: still `NEEDS_LIVE_OBSERVATION`, but the specific task-delete follow-up mismatch is fixed when pending context is supplied.

## Safety

- Shadow mode remains default OFF.
- No live route order changed.
- No task creation/deletion behavior changed.
- No client data was modified by this diagnostics update.
