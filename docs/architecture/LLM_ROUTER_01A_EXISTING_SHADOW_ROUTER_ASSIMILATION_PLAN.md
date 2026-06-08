# LLM Router 01A Existing Shadow Router Assimilation Plan

## 1. Purpose

This lane defines how Val0 should use the existing shadow/router infrastructure as the path toward LLM-assisted conversationality. The goal is assimilation, not reinvention: keep deterministic handlers in charge of execution, let the router/LLM propose only inside bounded shadow or classifier layers, and preserve client isolation before any runtime classifier is enabled.

This is docs/design only. It adds no runtime behavior, no bot routing changes, no DB writes, no client data writes, no production memory writes, and no calendar/task/reminder behavior changes.

## 2. Existing Router And Shadow Inventory

| Piece | Role | Current status | Notes |
| --- | --- | --- | --- |
| `core/intent_router_v2.py` | Deterministic shadow intent classifier | Shadow-only | Provides `classify_intent_shadow`; no message is routed through it. |
| `core/intent_router_v2_observer.py` | Predicted-vs-actual observation helpers | Shadow-only | Used for comparison records and diagnostics. |
| `core/conversation_router.py` | Conversational router v1 model/helpers | Diagnostic/design support | Existing pure router concepts should be reused before adding new router code. |
| `core/intent_interpreter.py` | Earlier intent interpretation utility | Runtime/diagnostic support | Existing interpreter patterns should be inventoried before any LLM classifier spike. |
| `scripts/ops/router_shadow_mode.sh` | Short-window shadow operation helper | Operational helper | Shadow mode default OFF; can enable `VAL0_INTENT_ROUTER_V2_SHADOW=true` for observation windows. |
| `scripts/diagnostics/intent_router_v2_sample_harness.py` | Curated phrase sample harness | Diagnostic | Runs sample phrases without Telegram, services, or state mutation. |
| `scripts/diagnostics/intent_router_v2_coverage_report.py` | Coverage and observation report generator | Diagnostic | Compares sample coverage, shadow classifier support, actual labels, and observation evidence. |
| `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md` | Router source-of-truth architecture | Docs-only | Defines priority order: pending actions, deterministic utilities, documents/case/memory, LLM fallback last. |
| `docs/architecture/CONVERSATIONAL_ROUTER_V1_DESIGN.md` | Conversational router design | Docs-only | States deterministic handlers execute and the LLM cannot execute tools or writes. |
| `docs/architecture/ROUTER_07_SHADOW_OBSERVATION_REPORT.md` | First live shadow observation report | Docs-only | Confirms shadow-only observation, no behavior change. |
| `docs/architecture/ROUTER_09_COVERAGE_GAP_REPORT.md` | Coverage gap report | Docs-only | Identifies covered, shadow-only, and observation-gap lanes. |
| `docs/architecture/ROUTER_12_POST_OBSERVATION_COVERAGE_UPDATE.md` | Post-observation update | Docs-only | Records clean shadow observation and disabled shadow mode afterward. |
| `docs/architecture/ROUTER_16_PENDING_CONTEXT_TASK_CREATE_UPDATE.md` | Pending context and task-create update | Docs-only plus diagnostic classifier update | Confirms pending-context fixes are shadow diagnostics only. |

## 3. Current Status Summary

- Runtime active: legacy deterministic handlers in `bot.py`, plus deterministic volatile adaptive intake from INTAKE-01B/01C.
- Shadow-only: `intent_router_v2`, `intent_router_v2_observer`, router shadow logs, sample harness comparison, coverage reporting.
- Docs-only: router marching order, conversational router design, shadow observation reports, coverage update reports.
- Diagnostic: sample harness, coverage report, observer demo scripts, shadow-mode helper status/log inspection.
- Deprecated/unknown: no piece should be deleted or bypassed in this lane; any older interpreter/router utility must be inventoried before replacement.

## 4. How Adaptive Intake Fits

INTAKE-01B and INTAKE-01C are deterministic volatile runtime lanes. They do not write memory, create tasks, create reminders, create calendar events, or call the memory spine.

They should become sample cases for a future classifier/composer:

- Trigger phrases: `no se que necesito`, `ayudame a empezar`, `estoy perdida`, `tengo demasiadas cosas`.
- Domain examples: time/day, work, documents/admin, clients/business, ideas/projects, routines.
- Work examples: `soy cajera`, `atiendo caja`, `trabajo en retail`.
- Recommendation examples: shifts, pending items, reminders, payments/dates, after-shift routine, too-broad `todo`.

The future classifier may propose labels such as `adaptive_intake_start`, `adaptive_intake_domain_work`, or `adaptive_intake_work_recommendation`, but deterministic handlers execute the actual response path.

## 5. How Memory Spine Fits

MEMORY-SPINE-01B remains disabled. The LLM/router cannot write memory. A future memory save requires:

- explicit user consent
- a proposed memory record the user can inspect
- deterministic write path
- client isolation
- audit event
- delete/update memory command

No classifier, response composer, or LLM fallback may directly create a memory candidate, confirmed memory, workflow profile, profile write, DB write, or production memory write. Memory writes must stay behind explicit consent and deterministic code.

## 6. Assimilation Doctrine

1. Borg existing tools first.
2. Build only the missing trust layer / operator layer.
3. Do not duplicate router logic.
4. Keep current deterministic handlers as the execution layer.
5. Use existing sample harness and coverage reporting before creating new diagnostics.
6. Treat adaptive intake as new sample coverage, not as a reason to build a parallel router.
7. Keep shadow mode default OFF unless an intentional observation window is running.

## 7. Proposed Next Sequence

1. LLM-ROUTER-01B: shadow sample expansion for adaptive intake phrases.
   - Add INTAKE-01B/01C examples to the existing sample harness.
   - Add expected labels without changing runtime behavior.

2. LLM-CLASSIFIER-01: controlled JSON classifier spike, shadow only.
   - The classifier returns structured labels, confidence, entities, and rationale.
   - It cannot execute tools, write memory, create/delete calendar events, create reminders, or mutate client files.

3. OPERATOR-RESPONSE-01: response composer v1, no side effects.
   - Composer drafts bounded Spanish-first replies.
   - Deterministic handlers still own state transitions and actions.

4. MEMORY-SPINE-01C: confirmed memory save proposal flow, disabled until approved.
   - Propose save records only after user consent.
   - Runtime write path remains disabled until reviewed and approved.

## 8. Safety Rules

- Pending confirmations beat new intent.
- Deterministic high-trust routes beat LLM.
- LLM fallback last.
- Deterministic handlers execute; LLM/router may only propose.
- LLM cannot execute tools, write memory, create/delete calendar events, create reminders, mutate client files, write DB rows, or change production config.
- No DB writes.
- No client data writes.
- Feature flag default OFF for shadow/LLM classifier lanes.
- Client isolation first: no cross-client contamination, no reusable logic with client-specific paths, names, chat IDs, or private data.

## 9. Risk Table

| Risk | Failure mode | Mitigation |
| --- | --- | --- |
| Route hijack | LLM or new classifier steals agenda/tasks/documents/intake from deterministic handlers | Pending confirmations and deterministic high-trust routes win before classifier/fallback. |
| Stale context | Short reply like `si`, `todo eso`, or `eliminarla` is interpreted under the wrong old state | Pending state must be explicit and consumed/cleared deterministically. |
| Duplicate bot process | Two workers reply or mutate state independently | Keep process/deployment checks outside classifier work; do not enable new runtime flags without ops procedure. |
| Hallucinated action | LLM says it saved, created, deleted, or remembered something | LLM cannot execute; composer must forbid action claims unless deterministic handler reports completion. |
| Cross-client contamination | Client-specific copy, paths, or context leak into reusable router behavior | Client isolation audit, no hardcoded client data, resolver-owned identity, sample fixtures only. |
| Privacy leakage | Classifier logs too much raw sensitive text | Shadow records should minimize text preview and avoid secrets; future logs need privacy review. |
| Overconfident classification | Ambiguous user message becomes a wrong route | Confidence thresholds, clarify-first behavior, and deterministic fallback to safe questions. |

## 10. Acceptance Criteria Before Runtime LLM Classifier

- Existing sample harness covers new adaptive intake phrases.
- Shadow observation is clean for the new labels.
- Actual handler labels are available for intake/onboarding paths.
- Karen RC smoke green.
- Client isolation audit green.
- Feature flag default OFF.
- No DB writes and no client data writes.
- No LLM execution of tools, memory writes, calendar events, reminders, or client-file mutation.

## 11. Non-Goals

- No router replacement.
- No bot.py refactor in this lane.
- No core runtime edits in this lane.
- No production memory persistence.
- No direct LLM tool execution.
- No autonomous Personal OS behavior.
