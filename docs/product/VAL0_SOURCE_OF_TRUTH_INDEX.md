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

## Commands

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
python3 scripts/diagnostics/intent_router_v2_sample_harness.py
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
bash scripts/ops/router_shadow_mode.sh status
bash scripts/ops/router_shadow_mode.sh enable
bash scripts/ops/router_shadow_mode.sh disable
bash scripts/ops/router_shadow_mode.sh logs
```

Use `enable` only for intentional, short shadow-observation windows. Disable shadow mode after testing.
