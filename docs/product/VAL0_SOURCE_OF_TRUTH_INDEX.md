# Val0 Source-of-Truth Index

## Purpose

This index points future sessions to the files and commands that define current Val0 state. It is a source-of-truth map, not a runtime component.

## Operational State

- ValPrime checkpoint / continuity: operational cockpit and recovery spine.
- Forge docs: durable operational and product docs.
- OPEL/event logs: event and audit trail.

## Technical State

- Repo docs: architecture, product, and ops decisions.
- Smokes: executable regression truth for current behavior.
- Current branch: `val0-post-m41-conversationality-memory-lab-2026-05-25`.
- Git status: inspect with `git status -sb` before changes.
- Full smoke runner: `python3 scripts/quality/karen_rc_full_smoke.py --keep-going`.

## Karen RC

- `docs/product/KAREN_RC_STATUS_MAP.md`
- `scripts/quality/karen_rc_full_smoke.py`
- Karen-specific smokes under `scripts/quality/karen_*`.

## Router

- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`
- `docs/architecture/ROUTER_*`
- `core/intent_router_v2.py`
- `scripts/diagnostics/intent_router_v2_sample_harness.py`
- `scripts/diagnostics/intent_router_v2_coverage_report.py`
- `scripts/ops/router_shadow_mode.sh`

Intent Router v2 shadow mode is OFF by default. It should be enabled only for short observation windows.

## OCR

- `docs/product/OCR_SPIKE_01_REGISTRO_PUBLICO.md`
- `core/document_ocr_runtime.py`
- `scripts/diagnostics/karen_ocr_spike_01.py`
- `scripts/quality/karen_ocr_runtime_smoke.py`
- `scripts/quality/karen_document_watermark_guard_smoke.py`
- `scripts/quality/karen_saved_summary_watermark_guard_smoke.py`

OCR for Registro Publico / watermark PDFs is v1 operational, with conservative on-demand behavior and page limits.

## Obsidian

- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`
- `/home/forge/valeria_vault`

Role: visual second brain / graph / library view, not source of truth and not runtime.

## Markdown docs inventory / value map

- `docs/product/VAL0_DOCS_VALUE_MAP.md`
- `scripts/diagnostics/markdown_docs_inventory.py`

Use the value map and inventory diagnostic to identify active source-of-truth docs, roadmap docs, architecture reports, ops playbooks, parking-lot ideas, client/private state, historical reports, possible stale/duplicate docs, and unknown docs that need review.

## Dynamic Roadmap Intake

- `docs/product/ROADMAP_01_DYNAMIC_INTAKE_DESIGN.md`
- `docs/product/ROADMAP_02_VALPRIME_SIGNAL_PROTOCOL.md`
- `docs/product/ROADMAP_03_SIGNAL_REGISTRY_STORAGE_DESIGN.md`
- `docs/product/ROADMAP_SIGNAL_SCHEMA_V0.md`
- `docs/product/ROADMAP_INTAKE_RESPONSE_TEMPLATE.md`
- `docs/product/ROADMAP_NEWSLETTER_INTAKE_PROMPT.md`

Use these for future newsletter/article/idea intake. They define how to evaluate signals against Val0 source-of-truth docs without auto-updating the roadmap or interrupting the active sprint without approval. ValPrime is the roadmap keeper; intake chat should emit copy-pasteable `/roadmap_signal` blocks for manual review, and ValPrime should eventually append those records into a roadmap signal registry. Current phase remains manual/design. There is no Notion dependency.

## New Chat Recovery

- `docs/ops/NEWCHAT_01_RECOVERY_PROTOCOL.md`
- `docs/ops/NEWCHAT_BRIDGE_PROMPT.md`
- `scripts/diagnostics/new_chat_recovery_brief.py`
- ValPrime `/continuity` or natural "new chat bundle"

Use these to recover a new Val0 cockpit without relying on memory. ValPrime continuity provides the human/operational bundle; repo diagnostics verify technical state.

## Commands

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
python3 scripts/diagnostics/new_chat_recovery_brief.py
python3 scripts/diagnostics/intent_router_v2_sample_harness.py
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
python3 scripts/diagnostics/markdown_docs_inventory.py
bash scripts/ops/router_shadow_mode.sh status
bash scripts/ops/router_shadow_mode.sh enable
bash scripts/ops/router_shadow_mode.sh disable
bash scripts/ops/router_shadow_mode.sh logs
```

Use `enable` only for intentional, short shadow-observation windows. Disable shadow mode after testing.
