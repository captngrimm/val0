# Intent Router v2 Marching Order

## Why This Exists

Karen RC was stabilized with tactical hard gates. That was the right short-term move: Karen needed reliable live behavior across identity, Spanish-first replies, agenda, Google Calendar, reminders, tasks, documents, watermark guards, and on-demand OCR.

Those hard gates are not the long-term architecture. They protect the RC, but they also make route order harder to reason about as features grow. Intent Router v2 is the cleanup lane after Karen RC PASS.

## Current Pain

- `bot.py` contains many route checks and priority gates.
- There are duplicated live paths for similar text handling.
- Karen-specific hard gates were added to stop urgent regressions.
- Case, memory, and document routes have previously hijacked direct utilities like tasks, reminders, and agenda.
- Voice transcription variants add prefixes, typos, and word-number variants that are currently handled tactically.
- The LLM/generic fallback can still be dangerous if it is reached before direct user commands are exhausted.

## Target Routing Order

1. Pending actions
2. Destructive confirmations
3. Direct utilities:
   - agenda
   - Google Calendar
   - reminders
   - tasks
4. Documents / OCR
5. Case/finca/legal context
6. Memory capture
7. LLM fallback

## Proposed Intent Router v2 Shape

### IntentCandidate

An `IntentCandidate` is a possible interpretation of a message.

Fields:

- `intent_type`
- `confidence`
- `source`
- `normalized_text`
- `required_context`
- `destructive`
- `client_scope`

Examples of `source`:

- deterministic matcher
- pending action context
- voice normalization
- LLM classifier fallback

### IntentDecision

An `IntentDecision` is the selected route.

Fields:

- `selected_intent`
- `handler`
- `reason`
- `blocked_by`
- `needs_confirmation`

The decision should explain why the route won, especially when it blocks another plausible route.

### RouterPriorityMap

The `RouterPriorityMap` owns the priority model:

- deterministic first
- pending/destructive actions before new intents
- direct utilities before context/memory
- LLM only fallback

The priority map should be explicit enough that a new route cannot accidentally jump ahead of tasks, reminders, agenda, or documents.

## ARCH-02 Shadow Skeleton

ARCH-02 adds `core/intent_router_v2.py` as a shadow classifier only.

- The shadow classifier exists.
- It is default OFF.
- It is enabled only with `VAL0_INTENT_ROUTER_V2_SHADOW=true`.
- It does not route messages.
- It does not remove or bypass any current Karen RC hard gate.
- It does not call external APIs or mutate state.

The goal is to compare predicted intent against the current routes before any refactor changes behavior. For now, the shadow hook can log predicted intent, confidence, reason, client, and text preview. A future step is to log predicted intent vs actual handler once handler labels are available across the existing routes.

## ARCH-03 Shadow Sample Harness

ARCH-03 adds `scripts/diagnostics/intent_router_v2_sample_harness.py`.

The harness runs curated real and representative Karen phrases through `classify_intent_shadow` without Telegram, external services, or state mutation. It prints expected vs predicted intent and can emit JSON with `--json`.

Use it to quickly inspect shadow classifier behavior before changing router rules:

```bash
python3 scripts/diagnostics/intent_router_v2_sample_harness.py
python3 scripts/diagnostics/intent_router_v2_sample_harness.py --json
```

This is still shadow-only. Passing the harness does not mean runtime behavior changed; it means the planned router prediction matches the current expected intent map for sampled phrases.

## ROUTER-04 Predicted vs Actual Handler Labels

ROUTER-04 adds shadow-only observation helpers for comparing predicted intent against the current legacy handler that actually consumed a message.

- Predicted intent comes from Intent Router v2.
- Actual intent comes from lightweight legacy handler labels.
- Logging remains gated by `VAL0_INTENT_ROUTER_V2_SHADOW=true`.
- The router is still shadow-only.
- There is no behavior change and no message is routed through Intent Router v2.

Example comparison:

```text
[INTENT_ROUTER_V2_COMPARE] predicted=task_query actual=task_query match=True confidence=0.95 handler=maybe_handle_karen_task_query_hard_gate
```

This comparison data will guide the future router refactor. Once handler labels are broad enough, we can measure mismatches before moving any lane from legacy hard gates into router-owned decisions.

## ROUTER-05 Shadow Observation Playbook

ROUTER-05 adds the operator playbook and helper command for short-window shadow observation:

- Playbook: `docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md`
- Helper: `scripts/ops/router_shadow_mode.sh`

The helper can temporarily enable `VAL0_INTENT_ROUTER_V2_SHADOW=true` through a systemd drop-in, inspect shadow/actual/compare logs, and disable the drop-in again. This remains short-window observation only:

- Shadow mode is default OFF.
- There is no behavior change.
- No message is routed through Intent Router v2.
- The comparison logs guide future refactor work; they do not directly change runtime behavior.

## ROUTER-07 Shadow Observation Report

ROUTER-07 records the first clean real shadow observation pass:

- Report: `docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md`
- Tested lanes included task query, agenda query, Google Calendar create, destructive confirmation/cancel, reminder create, document OCR, and case status.
- The observed predicted-vs-actual pairs were `match=True`.
- Karen RC full smoke passed after shadow mode was disabled.
- There was no behavior change.

## ROUTER-08 Expanded Shadow Sample Set

ROUTER-08 expands `scripts/diagnostics/intent_router_v2_sample_harness.py` with dangerous and ambiguous real-world phrases before any router refactor.

- Coverage now includes task delete/complete, reminder query/delete/update, Google Calendar delete variants, pending confirmations, numbered document references, OCR requests, case/finca variants, voice-prefix typo examples, and LLM fallback samples.
- The harness remains diagnostics-only.
- It does not call Telegram, Google Calendar, OCR, memory, or live services.
- There is no behavior change and no message is routed through Intent Router v2.

## ROUTER-09 Coverage Gap Report

ROUTER-09 adds `docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md` and `scripts/diagnostics/intent_router_v2_coverage_report.py`.

The report compares sample-harness coverage, shadow classifier coverage, actual legacy handler labels, and clean observation evidence. It identifies which lanes are `COVERED`, `SHADOW_ONLY`, `NEEDS_ACTUAL_LABEL`, or `NEEDS_LIVE_OBSERVATION` before any router migration proposal.

This remains diagnostics-only. There is no behavior change.

## ROUTER-10 Missing Actual Labels

ROUTER-10 adds shadow-only actual labels for previously unlabeled legacy routes:

- `pending_action_reply`
- `reminder_query`
- `reminder_delete`
- `reminder_update`
- `task_complete`

The next step is live shadow observation for these intents. This remains observer-only; no message is routed through Intent Router v2 and there is no behavior change.

## Migration Plan

### Phase 0: Freeze RC Behavior

- Keep current Karen RC behavior frozen.
- Maintain `scripts/quality/karen_rc_full_smoke.py`.
- Do not start route refactors unless the full RC smoke is passing.

### Phase 1: Inventory Current Routes

- Run `python3 scripts/diagnostics/route_inventory.py`.
- Identify duplicate routes, old fallback routes, and routes that exist in more than one live path.
- Mark which routes are Karen-specific, reusable, or legacy.

### Phase 2: Shadow Mode Router

- Introduce a router wrapper in shadow mode.
- Log predicted intent vs actual handled route.
- Do not change behavior.
- Use the logs to find mismatches before moving handlers.

### Phase 3: Migrate One Lane At A Time

Move lanes into the router in this order:

1. tasks
2. reminders
3. agenda/GCal
4. documents
5. case/finca
6. memory

Each lane needs lane-specific smokes before and after migration.

### Phase 4: Remove Obsolete Hard Gates

- Remove old hard gates only after lane smokes and live Karen checks pass.
- Keep fallbacks honest during the transition.
- Do not remove a guard just because the new router compiles.

## Guardrails

- No route can write/delete without explicit confirmation.
- Pending actions always beat new intents.
- Memory capture must never beat direct user commands.
- Case/finca must never beat agenda/tasks/reminders/docs.
- Documents/OCR must never trigger on random short replies like `sí`, `hoy`, or `ok`.
- LLM fallback must be last.

## Testing Requirements

Router refactor cannot begin unless:

- `python3 scripts/quality/karen_rc_full_smoke.py --keep-going` passes.
- Route inventory exists.
- Each migrated lane has lane-specific smokes.
- Live Karen behavior is not regressed.

## Operational Note

After Karen RC PASS, shift from stabilization hard gates to Intent Router v2. Do not add major features until the router/refactor plan exists unless an urgent Karen client blocker appears.
