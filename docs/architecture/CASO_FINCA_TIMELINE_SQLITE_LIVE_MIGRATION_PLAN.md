# Caso Finca Timeline SQLite Live Migration Plan

## Purpose

Plan the production SQLite migration and live-write enablement for Caso Finca timeline events without enabling it yet.

A-028B through A-028I proved the safe fixture loop:

- draft preview
- fixture confirmation
- temp SQLite save
- temp SQLite read/render
- temp SQLite export diagnostic

This document defines the reviewed path from fixture proof to production migration. It does not enable live persistence.

## Current Position

Live behavior today:

- Val can prepare a Caso Finca timeline event draft.
- Val can store to temp JSON or temp SQLite only when a test fixture path is explicitly provided.
- Live/default confirmation refuses real persistence.
- No production DB migration has been applied.
- No Telegram route reads production SQLite timeline events.

Protected live files:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`

These files must not be reset, discarded, casually staged, or casually committed. Timeline events must not be stored in either file.

## Proposed Production Schema Source

Primary table:

```text
case_timeline_events
- event_id TEXT PRIMARY KEY
- client_id TEXT NOT NULL
- case_id TEXT NOT NULL
- title TEXT NOT NULL
- description TEXT
- event_date TEXT
- event_date_precision TEXT NOT NULL
- recorded_at TEXT NOT NULL
- source_type TEXT NOT NULL
- source_ref TEXT
- confirmation_status TEXT NOT NULL
- confidence TEXT
- legal_effect_status TEXT NOT NULL
- created_by TEXT NOT NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
- deleted_at TEXT
```

Audit table:

```text
case_timeline_event_audit
- audit_id TEXT PRIMARY KEY
- event_id TEXT NOT NULL
- client_id TEXT NOT NULL
- case_id TEXT NOT NULL
- action TEXT NOT NULL
- actor TEXT NOT NULL
- timestamp TEXT NOT NULL
- before_json TEXT
- after_json TEXT
- reason TEXT
```

Indexes:

- `idx_case_timeline_events_client_case`
- `idx_case_timeline_events_date`
- `idx_case_timeline_event_audit_event`

## Migration Approach

1. Run temp DB smokes first.
2. Backup the production encrypted/local memory DB.
3. Apply schema idempotently.
4. Verify schema exists.
5. Run an export diagnostic against an empty/no-op production timeline view.
6. Keep live feature disabled.
7. Only after operator review, enable a feature/config gate for one client/case.

No migration lane should combine schema migration and live Telegram writes unless explicitly approved after review.

## Required Feature / Config Gate

Future intended gate:

```text
CASE_TIMELINE_SQLITE_LIVE_ENABLED=false
```

Current implementation state:

- `is_live_timeline_sqlite_enabled()` returns `False`.
- There is no runtime production enablement path.
- Non-temp SQLite paths are refused by the current adapter.

Future enablement must be explicit and reviewed. Do not silently wire environment flags into production writes without a separate lane and smoke coverage.

## Required Client / Case Allowlist

Initial live allowlist must be narrow:

```text
client_id: karen
case_id: CASE:KAREN-LAND-001
alias: caso_finca
```

No other client/workspace should be accepted until multi-client tests exist.

## Required Runtime Path

Future live path:

1. User creates draft.
2. Draft is stored in pending state with timestamp/message metadata.
3. User confirms explicitly.
4. Runtime checks:
   - live flag enabled,
   - client/case allowlisted,
   - schema ready,
   - pending draft fresh,
   - no conflicting pending action,
   - source/date precision present.
5. Write event row.
6. Write audit row.
7. Reply with safe event-added summary.
8. Timeline read can show the new event.

## Refusal Behavior When Disabled

When disabled, Val must continue to say:

- real timeline saving is not enabled yet,
- draft can be prepared,
- no real Karen memory is touched,
- Nora/la abogada confirms legal effect.

Generic confirmations must not save events without a pending timeline draft.

## Rollback Plan

If migration is applied but live writes are not enabled:

- Leave schema in place; it is inert.
- Keep feature flag disabled.
- No event rows should exist unless seeded by an approved test.

If live writes are enabled and a problem appears:

- Disable feature flag immediately.
- Stop write path.
- Export timeline/audit report.
- Soft-delete incorrect event rows rather than hard-delete.
- Use audit rows to reconstruct what happened.

## Backup Plan

Before production migration:

- Record current git head.
- Record DB path.
- Create encrypted/local DB backup using the established Val0 backup method.
- Verify backup exists.
- Do not copy DB contents into repo docs.

## Operator Verification Commands

Before migration:

```bash
python3 scripts/quality/caso_finca_timeline_event_sqlite_store_smoke.py
python3 scripts/quality/caso_finca_timeline_event_sqlite_confirmation_smoke.py
python3 scripts/quality/caso_finca_timeline_event_sqlite_read_smoke.py
python3 scripts/quality/caso_finca_timeline_sqlite_export_smoke.py
python3 scripts/quality/client_isolation_audit.py
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
git diff --check
```

After migration, before enablement:

```bash
python3 scripts/diagnostics/caso_finca_timeline_sqlite_export.py --db-path <approved-prod-db-path> --client-id karen --case-id caso_finca
python3 scripts/quality/client_isolation_audit.py
git status --short --branch
```

Do not run production DB export commands from this plan until the production DB path and operator approval are explicit.

## Smoke Tests Required Before Enabling Live

Required:

- Default live guard smoke proves disabled state.
- Temp SQLite confirmation smoke remains green.
- Temp SQLite read/export smokes remain green.
- Migration smoke proves schema idempotency on a temp DB.
- Production DB dry-run/backup smoke exists.
- Client isolation audit passes.
- Karen RC full smoke passes.

## What Must Never Be Staged / Committed

Never stage or commit:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`
- any future `clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json`
- production DB files
- DB backups
- raw OCR bodies or private client document text

Generated reports should default to `tmp/` or an operator-only report path.

## Legal / Safety Boundaries

- Val organizes and summarizes.
- Val does not confirm legal effect.
- `legal_effect_status` defaults to `unknown`.
- Nora/la abogada confirms legal effect.
- OCR-derived events require OCR caveat.
- Soft-delete only for deletes.
- Every write/edit/delete needs an audit row.

## Decision Point Before Enablement

Before live writes:

1. Confirm schema/migration reviewed.
2. Confirm DB backup.
3. Confirm feature gate and allowlist.
4. Confirm stale pending draft guard.
5. Confirm export diagnostic works.
6. Confirm client isolation and Karen RC smokes pass.
7. Operator explicitly approves live enablement.

## Recommended Next Lane

**A-028K — Timeline SQLite Migration Dry-Run Smoke**

Scope:

- Temp DB migration runner/smoke only.
- Idempotent schema creation proof.
- No production DB migration.
- No live Telegram persistence.
