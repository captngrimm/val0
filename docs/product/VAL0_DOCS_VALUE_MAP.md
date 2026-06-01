# Val0 Docs Value Map

## Purpose

This map prevents scattered markdown docs from becoming forgotten, duplicated, or conflicting.

Val0 now has many markdown files across product docs, architecture docs, ops docs, client notes, and historical reports. The rule is simple: preserve useful material, but know which files are active source-of-truth and which are snapshots, parking-lot ideas, or private client state.

## Active Source-of-Truth Docs

These are source-of-truth docs for current orientation and should be checked before relying on scattered older markdown.

- `docs/product/VAL0_MASTER_MILESTONE_MAP.md`  
  Current macro map for M42-M50 and active lane M45.
- `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`  
  Current index of operational, technical, Karen RC, Router, OCR, and Obsidian truth sources.
- `docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md`  
  Session-start recovery checklist and decision rules.
- `docs/product/KAREN_RC_STATUS_MAP.md`  
  Karen RC status map.
- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`  
  Intent Router v2 architecture and migration order.
- Latest `docs/architecture/ROUTER_*` reports  
  Router observation and coverage audit trail.
- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`  
  Obsidian / `valeria_vault` role clarification.

These are the first files to inspect when deciding current Val0 direction.

## Supporting Docs

- OCR docs, especially `docs/product/OCR_SPIKE_01_REGISTRO_PUBLICO.md`, explain Registro Publico / watermark PDF feasibility and limits.
- Router reports document shadow observations, sample coverage, actual-label coverage, and remaining observation gaps.
- Ops playbooks such as `docs/ops/ROUTER_05_SHADOW_OBSERVATION_PLAYBOOK.md` explain safe operational procedures.
- Obsidian role docs clarify future visual second brain possibilities without making Obsidian runtime truth.
- Founder-beta, roadmap, onboarding, and product docs may still contain useful offer language, product packaging, or future feature ideas.

## Client / Private Docs

Files under `clients/*` may contain client state, working notes, or test artifacts.

Treat these as `CLIENT_PRIVATE_OR_STATE`, not product truth, unless explicitly reviewed. Do not commit, move, summarize externally, or use them as source-of-truth casually.

## Historical / Stale Docs

Some markdown reports are snapshots from a specific day, milestone, or test pass. They are useful for audit and history, but they should not override current source-of-truth docs.

Likely historical material includes old handoffs, dated readiness reports, demo checklists, and older milestone notes. Possible stale or duplicate docs should be marked for review before any cleanup.

## Cleanup Policy

- Use no automatic deletion.
- Never delete docs automatically.
- Mark candidates for review first.
- If duplicated, prefer current source-of-truth docs.
- If client state, do not commit or move casually.
- If parking-lot idea, preserve it or link it from a parking lot index.
- If a doc is historical, keep it as audit material unless an explicit cleanup task says otherwise.

## Inventory Categories

The diagnostic inventory uses these categories:

- `ACTIVE_SOURCE_OF_TRUTH`
- `ACTIVE_ROADMAP`
- `ARCHITECTURE_REPORT`
- `OPS_PLAYBOOK`
- `PARKING_LOT`
- `CLIENT_PRIVATE_OR_STATE`
- `HISTORICAL_REPORT`
- `POSSIBLE_STALE_OR_DUPLICATE`
- `UNKNOWN_REVIEW`

Run:

```bash
python3 scripts/diagnostics/markdown_docs_inventory.py
python3 scripts/diagnostics/markdown_docs_inventory.py --json
```

## Next Recommended

- DOCS-AUDIT-02: review stale/duplicate candidates.
- DOCS-AUDIT-03: create docs index or navigation README.
- DOCS-AUDIT-04: optional Obsidian export/sync index later.
