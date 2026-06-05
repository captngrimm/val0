# Caso Finca Timeline Live Persistence Decision

## Purpose

Decide the safest live persistence path for Caso Finca timeline events before enabling real `sí, guárdalo` writes.

A-028B added deterministic draft previews. A-028C proved fixture/temp JSON event storage. A-028D connected confirmation to fixture storage only and kept live mode refusing real persistence. This decision closes the architecture gap before any live event writes.

The product goal is simple: Karen should eventually save timeline events for Caso Finca without Val touching unrelated live files, losing auditability, inventing legal meaning, or creating git contamination.

## Current State

Available today:

- Draft parser and preview in `core/case_timeline_events.py`.
- Volatile pending draft in `context.chat_data`.
- Fixture/temp JSON store for tests.
- Fixture-only confirmation handler.
- Live mode refusal: Val can prepare the draft, but does not persist real events.

Protected live files that must not be used for timeline events:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`

No live timeline event storage file exists yet, and this document does not create one.

## Options Compared

### Option 1: SQLite Table In Existing Encrypted/Local Memory DB

Summary:

- Primary event records live in a structured table, not in git-tracked client markdown/JSON files.
- Audit trail can be stored in a companion table.
- Tests can use a temp database.

Auditability:

- Strong. Each event can have immutable audit rows for create, confirm, edit, soft-delete, restore, and source changes.
- Corrections do not need to overwrite prior values silently.

Rollback / soft-delete:

- Strong. `deleted_at` plus audit rows support soft-delete and restoration.
- Future correction flows can create new audit rows without losing old state.

Client isolation:

- Strong if every row has `client_id` and `case_id`.
- Runtime queries must always filter by both fields.

Git contamination risk:

- Low. Existing DB-style runtime data should not be staged like client markdown/JSON.
- Still requires backup/ops discipline, but less risk than a new git-visible client file.

Backup / recovery:

- Good if existing DB backup strategy is reliable.
- Needs an operator diagnostic/export command for human-readable recovery.

Migration complexity:

- Medium. Requires schema/migration, temp DB smokes, and compatibility checks.
- More work than JSON, but cleaner for edits/deletes.

Operator debugging:

- Medium. Less visible than JSON, so add diagnostics:
  - timeline event list report,
  - audit trail report,
  - export to safe markdown if needed.

Live runtime safety:

- Strong with transactional writes and explicit confirmation.
- Easier to prevent partial writes.

Future multi-client generalization:

- Strong. A reusable `case_timeline_events` table can support other clients/workspaces with `client_id`, `case_id`, and source labels.

Testing without live data:

- Use temp SQLite DB path.
- Use test case IDs and fake client IDs.
- Verify no `clients/karen/*` files change.

### Option 2: New Guarded Client JSON File

Example future path:

```text
clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json
```

Auditability:

- Medium. An audit trail can be embedded per event, but edits are whole-file rewrites.

Rollback / soft-delete:

- Medium. Soft-delete is easy, but merge conflicts and accidental rewrites are risks.

Client isolation:

- Medium. File path is client-scoped, but the architecture becomes Karen-specific unless wrapped carefully.

Git contamination risk:

- High. A new client JSON file in `clients/karen` is likely to appear in `git status`.
- It would need the same “live data, do not stage” guard as `CLIENT_FOLDERS.json`.

Backup / recovery:

- Good for human inspection if not accidentally committed.
- Risky if live private details enter the repo diff.

Migration complexity:

- Low. The A-028C fixture store already proves the shape.

Operator debugging:

- Strong. Easy to read and inspect.

Live runtime safety:

- Medium. Needs lock/write discipline and careful protection against partial writes.

Future multi-client generalization:

- Medium-low. It can generalize with one file per client, but operational guardrails multiply.

Testing without live data:

- Easy with temp JSON files.
- Must continue refusing `clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json` until explicitly approved.

### Option 3: Markdown Append-Only Log

Example future path:

```text
clients/karen/CASE_TIMELINE_APPEND_LOG.md
```

Auditability:

- Medium-high for human history if append-only is respected.
- Low for structured querying unless parsed carefully.

Rollback / soft-delete:

- Weak-medium. Requires conventions like “SOFT_DELETE event N” rather than durable state.

Client isolation:

- Medium. Client path is clear, but still live client data.

Git contamination risk:

- High. Markdown live data is easy to accidentally stage or paste.

Backup / recovery:

- Human-readable, but fragile for runtime correctness.

Migration complexity:

- Low at first, high later when correction/delete flows need reliable parsing.

Operator debugging:

- Strong for reading, weak for data integrity.

Live runtime safety:

- Medium-low. Append logs are hard to query, dedupe, and sort safely.

Future multi-client generalization:

- Low-medium. Good as an export/report format, not as primary runtime storage.

Testing without live data:

- Easy with temp files, but runtime parser risks grow.

### Option 4: Hybrid SQLite Primary + Export / Report View

Summary:

- SQLite is the primary live data store.
- Markdown/JSON exports are generated reports, not source of truth.
- Exports can go under `tmp/` or an operator report path unless explicitly approved.

Auditability:

- Strong. Primary audit trail stays structured.

Rollback / soft-delete:

- Strong. SQLite handles state; exports are disposable views.

Client isolation:

- Strong if DB rows filter by `client_id` and `case_id`.

Git contamination risk:

- Low for primary data.
- Export/report paths must remain outside tracked live client files by default.

Backup / recovery:

- Strongest if paired with diagnostics and backup strategy.
- Operator can inspect generated reports without touching live source data.

Migration complexity:

- Medium-high. Requires schema plus export/report helper.

Operator debugging:

- Strong once export/report helper exists.

Live runtime safety:

- Strong. Transactional writes plus confirmation gate.

Future multi-client generalization:

- Strong. Best platform path.

Testing without live data:

- Use temp DB and temp export path.
- Smokes assert no client files changed.

## Recommendation

Use **Hybrid SQLite Primary + Export / Report View** for live v1.

Primary live event storage should be SQLite in the existing encrypted/local memory data layer, not a new git-visible client JSON file.

Why:

- Timeline events need audit trail, correction, soft-delete, and future numbered-event context.
- JSON is tempting because A-028C already proved it, but it would create another live client file likely to become dirty/staged.
- Markdown is useful for operator reports, but too fragile as primary runtime data.
- SQLite supports future multi-client workspaces better than Karen-only JSON.

The JSON fixture store remains valuable for tests and dry spikes. It should not become the live persistence path.

## Proposed SQLite Schema

Primary table:

```text
case_timeline_events
- event_id TEXT PRIMARY KEY
- client_id TEXT NOT NULL
- case_id TEXT NOT NULL
- title TEXT NOT NULL
- description TEXT NOT NULL
- event_date TEXT
- event_date_precision TEXT NOT NULL
- recorded_at TEXT NOT NULL
- source_type TEXT NOT NULL
- source_ref TEXT
- confirmation_status TEXT NOT NULL
- confidence TEXT NOT NULL
- legal_effect_status TEXT NOT NULL DEFAULT 'unknown'
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
- reason TEXT
- before_json TEXT
- after_json TEXT
- created_at TEXT NOT NULL
```

Indexes:

```text
idx_case_timeline_events_client_case
  (client_id, case_id, deleted_at)

idx_case_timeline_events_date
  (client_id, case_id, event_date_precision, event_date)

idx_case_timeline_event_audit_event
  (event_id, created_at)
```

Required enum-like values:

- `event_date_precision`: `exact`, `month_only`, `year_only`, `unknown`
- `source_type`: `user_note`, `document_metadata`, `ocr_summary`, `manual_review`, `inferred_candidate`
- `confirmation_status`: `confirmed_by_user`, `pending_confirmation`, `candidate`, `contradicted`, `rejected`
- `legal_effect_status`: `unknown`, `asks_nora`, `confirmed_by_lawyer`, `not_legal_effect`

Default for live create:

- `confirmation_status`: `confirmed_by_user` only after explicit pending-draft confirmation.
- `legal_effect_status`: `unknown`.

## Migration / Test Approach

Implementation should be a separate lane.

Suggested test strategy:

- Add a storage adapter that accepts a DB path/connection.
- Smokes use a temp SQLite DB.
- Migration smoke creates tables in temp DB only.
- Confirmation smoke writes to temp DB only.
- Live mode remains disabled until a guarded runtime storage path is explicitly enabled.
- `client_isolation_audit.py` should ensure timeline persistence does not reference `CLIENT_GROCERY.md` or `CLIENT_FOLDERS.json`.
- Add a protected staging guard that flags any staged `clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json` if such a file is ever created manually.

No test should write to:

- `clients/karen/CLIENT_GROCERY.md`
- `clients/karen/CLIENT_FOLDERS.json`
- `clients/karen/CLIENT_CASE_TIMELINE_EVENTS.json`

## Live-Write Guardrails

Live writes must require all of the following:

- Pending timeline draft exists in recent context.
- Confirmation phrase is explicit: `sí`, `sí guárdalo`, `dale`, `guardar`, etc.
- Draft is not stale.
- `client_id` and `case_id` are explicit.
- `source_type` is present.
- `event_date_precision` is present.
- `legal_effect_status` defaults to `unknown`.
- No legal-effect confirmation by default.
- No raw OCR dump in event description or audit.
- No internal IDs in user-facing output unless technical details are requested.
- Soft-delete only for deletion flow.
- Every create/update/delete has audit row.
- Runtime response states what was saved and keeps Nora/legal boundary visible.

Stale pending draft guard:

- Store `created_at`, `source_message_id`, and optional `expires_at` in pending state.
- Reject confirmation when draft is older than a short window or when newer conflicting pending action exists.
- Never let generic `sí` save an event unless the pending draft key is active and fresh.

## Protected Live-Data Guardrails

Before enabling live writes:

- Update staging/diff guidance to explicitly treat timeline event live data as protected.
- If a JSON export exists, keep it in `tmp/` by default.
- If a future client file is ever approved, add guard comments and smoke coverage before using it.
- Night Runner and client isolation checks should continue refusing staged protected live data.

## Acceptance Criteria For Future Implementation

Future live implementation must prove:

- `sí, guárdalo` writes only after a pending timeline draft.
- Saved event can be read back in the Caso Finca timeline.
- `CLIENT_GROCERY.md` and `CLIENT_FOLDERS.json` are untouched.
- No live data is accidentally committed.
- Tests use temp DB/temp JSON, not live client files.
- Soft-delete path exists before any delete command goes live.
- Audit row exists for create.
- No legal effect is marked confirmed by default.
- No raw OCR text is dumped.
- Generic confirmations do not save events without pending draft.

## Risks

- SQLite migration may touch shared DB code and needs careful compile/smoke coverage.
- Operator debugging is weaker than JSON until export/report diagnostics exist.
- Pending-state staleness matters; otherwise `sí` could confirm the wrong draft.
- Source references from documents must avoid leaking internal IDs in normal user-facing copy.
- If exports are generated into tracked paths, git contamination risk returns.

## Next Implementation Lane

Recommended:

**A-028F — Timeline Event SQLite Store Adapter + Temp DB Smokes**

Scope:

- Add SQLite adapter for timeline events.
- Create schema in temp DB for tests.
- Port A-028C/A-028D fixture-store tests to temp SQLite.
- Keep live mode refusing real persistence.
- No production migration yet unless explicitly approved after temp DB proof.

Follow-up:

**A-028G — Timeline Event Live Write Enablement With Guardrails**

Only after:

- Temp DB adapter is green.
- Migration path is reviewed.
- Stale pending draft guard is implemented.
- Client isolation and protected live-data staging guards are updated.
