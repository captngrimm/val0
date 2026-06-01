# Val0 Session Startup Checklist

Use this checklist at the start of a new Val0/Karen/Router session.

## Inspect Current Status

```bash
git status -sb
git log --oneline -12
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
bash scripts/ops/router_shadow_mode.sh status
```

The full smoke should pass before runtime work. Shadow mode should be OFF unless an intentional short observation window is in progress.

## Check Source-of-Truth Docs

- `docs/product/VAL0_MASTER_MILESTONE_MAP.md`
- `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`
- `docs/product/KAREN_RC_STATUS_MAP.md`
- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`
- latest `docs/architecture/ROUTER_*`
- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`

## Decision Rules

- If full smoke fails: stop and triage.
- If repo is dirty: inspect before proceeding.
- If shadow is ON unexpectedly: disable unless actively observing.
- If changing runtime: run full smoke before and after.
- If doing router work: prefer shadow/docs/smokes before behavior changes.
- If testing destructive actions: use test data only.
- Do not commit client dirty data accidentally.
- Do not start broad router refactor until the M45 observation lane is ready.
