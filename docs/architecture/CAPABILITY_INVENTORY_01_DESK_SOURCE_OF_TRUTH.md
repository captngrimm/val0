# Capability Inventory 01 Desk Source Of Truth

## Purpose

This is the short Desk map for Personal OS / LLM router / operator response work. Open this before starting new architecture lanes so existing assets are not forgotten.

## First Five Files

1. `AGENTS.md`
2. `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`
3. `docs/product/VAL0_MASTER_MILESTONE_MAP.md`
4. `docs/architecture/CAPABILITY_INVENTORY_01_FORGOTTEN_ASSETS_AUDIT.md`
5. `docs/architecture/LLM_ROUTER_01A_EXISTING_SHADOW_ROUTER_ASSIMILATION_PLAN.md`

## Router Desk

- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`
- latest `docs/architecture/ROUTER_*`
- `docs/architecture/CONVERSATIONAL_ROUTER_V1_DESIGN.md`
- `core/intent_router_v2.py`
- `core/intent_router_v2_observer.py`
- `core/conversation_router.py`
- `core/intent_interpreter.py`
- `scripts/diagnostics/intent_router_v2_sample_harness.py`
- `scripts/diagnostics/intent_router_v2_coverage_report.py`

Rule: do not rebuild the router. Expand shadow samples and observations first.

## Intake / Onboarding Desk

- `core/adaptive_intake.py`
- `core/onboarding_discovery.py`
- `docs/product/INTAKE_01A_ADAPTIVE_USER_INSIGHT_QUESTIONNAIRE_DESIGN.md`
- `docs/product/INTAKE_01B_VOLATILE_RUNTIME_ADAPTIVE_INTAKE.md`
- `docs/product/INTAKE_01C_VOLATILE_INTAKE_RECOMMENDATION.md`
- `docs/product/ONBOARDING_01G_DAILY_REVIEW_CONTENTS_SELECTION.md`
- `docs/product/ONBOARDING_01H_DEMO_POLISH_CONTEXT_BLEED_FIX.md`

Rule: current intake/onboarding state is volatile unless a future approved lane changes that.

## Memory Desk

- `docs/product/MEMORY_SPINE_01A_INTAKE_MEMORY_LIBRARY_LAYER_DESIGN.md`
- `docs/product/MEMORY_SPINE_01A_MEMORY_OBJECT_MODEL.md`
- `docs/product/MEMORY_SPINE_01B_CONFIRMED_MEMORY_PERSISTENCE_SPIKE.md`
- `core/memory_spine.py`
- `docs/architecture/INFINITE_MEMORY_LIBRARY_ARCHITECTURE_V0.md`

Rule: memory spine is disabled unless explicitly approved. Consent and deterministic writes are required.

## Response / Voice Composer Desk

- `docs/product/BOUNDED_LLM_VOICE_RENDERER_V1_DESIGN.md`
- `core/bounded_voice_renderer.py`
- `scripts/quality/bounded_voice_renderer_smoke.py`
- `scripts/diagnostics/voice_renderer_shadow_review.py`
- `scripts/quality/voice_renderer_shadow_review_smoke.py`

Rule: use bounded voice renderer validation ideas for any response composer. Composer drafts; handlers execute.

## Runtime Product Desk

- `docs/product/KAREN_RC_STATUS_MAP.md`
- `scripts/quality/karen_rc_full_smoke.py`
- `core/daily_operator.py`
- `core/document_ocr_runtime.py`
- `core/document_summary_queries.py`
- `core/case_workspace.py`
- `core/case_timeline_events.py`
- `core/client_profiles.py`

Rule: this is high-trust runtime territory. No broad refactors without full smoke and client isolation audit.

## Ops / Continuity Desk

- `docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md`
- `docs/ops/NEWCHAT_01_RECOVERY_PROTOCOL.md`
- `docs/ops/NEWCHAT_BRIDGE_PROMPT.md`
- `scripts/diagnostics/new_chat_recovery_brief.py`
- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`
- `docs/architecture/TOOL_ASSIMILATION_MAP.md`
- `scripts/diagnostics/markdown_docs_inventory.py`

Rule: ValPrime/checkpoints are the cockpit; repo docs and smokes are technical truth; Obsidian is not runtime truth.

## Current Guardrail Reminder

- Protected live data can remain dirty, but must not be staged, reset, discarded, edited, or committed.
- Shadow mode default OFF.
- Pending confirmations beat new intent.
- Deterministic handlers execute.
- LLM fallback last.
- No DB writes, client data writes, production restarts, or runtime changes in docs/audit lanes.

## Recurring Audit

Run:

```bash
python3 scripts/quality/capability_inventory_audit_smoke.py
python3 scripts/diagnostics/val0_source_of_truth_check.py
python3 scripts/diagnostics/markdown_docs_inventory.py
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
```

If this is a runtime lane, also run:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
python3 scripts/quality/client_isolation_audit.py
```
