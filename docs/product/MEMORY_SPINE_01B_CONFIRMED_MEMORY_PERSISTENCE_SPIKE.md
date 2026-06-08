# MEMORY-SPINE-01B Confirmed Memory Persistence Spike

Purpose: document the fixture-only persistence spike for confirmed intake memory objects.

This is experimental and disabled by default. It does not add Telegram runtime activation, production database writes, profile persistence, schema migrations, calendar/task/reminder behavior, production config, or client data writes.

## 1. Scope

MEMORY-SPINE-01B creates a safe experimental spine for confirmed memories using fake fixture data only.

Allowed behavior:

- create a memory_candidate from fake onboarding data
- promote it only after explicit consent
- write confirmed fixture memory to temp/test storage
- build a fixture memory_index_entry catalog
- include privacy_boundary, sensitivity, retrieval_tags, and audit_event

Forbidden behavior:

- no live client writes
- no production DB writes
- no clients directory writes
- no runtime activation in Telegram
- no real user/profile persistence
- no calendar, task, or reminder creation

## 2. Feature Flag

The feature is disabled by default.

The code exposes a small flag helper for future experiments:

```text
VAL0_MEMORY_SPINE_EXPERIMENTAL=1
```

No runtime path reads this flag in this lane. There is no automatic integration.

## 3. Fixture Storage

Fixture writes are restricted to:

- tmp/memory_spine_spike/
- tests/fixtures/memory_spine/

The smoke writes fake data under:

```text
tmp/memory_spine_spike/smoke/
```

Path guards reject clients paths and production database-looking paths.

## 4. Object Model

The spike aligns with MEMORY-SPINE-01A concepts:

- memory_candidate
- confirmed memory as workflow_profile
- privacy_boundary
- memory_index_entry
- audit_event

Required fields include:

- client_id / user_id
- memory_type
- title
- summary
- source
- confidence
- consent_status
- confirmed_by_user
- sensitivity
- status
- created_at / updated_at
- linked_workflow
- retrieval_tags

## 5. Consent Safeguards

Confirmed fixture memory cannot be written unless:

- consent_status is confirmed
- confirmed_by_user is true
- source object is a memory_candidate

Rejected states:

- proposed consent
- declined consent
- missing confirmed_by_user
- unconfirmed memory_candidate writes

## 6. Privacy Safeguards

The spike rejects secret-like raw data in summary/title fields.

It is intentionally limited to fake IDs such as:

```text
fixture_user_001
fixture_client_001
```

It does not include real Karen data, real Ale data, or any client-specific profile.

## 7. Smoke Coverage

`scripts/quality/memory_spine_persistence_spike_smoke.py` verifies:

- feature disabled by default
- fake onboarding memory_candidate creation
- failed confirm/save without explicit confirmed consent
- fixture-only confirmed memory write
- fixture memory index creation
- privacy_boundary / sensitivity / consent fields
- audit_event presence
- no clients writes
- protected live data not staged
- no production DB touch
- no runtime activation

## 8. Limitations

This is a spike, not production memory.

Missing by design:

- no Telegram route
- no profile writes
- no production persistence
- no migrations
- no retrieval helper wired into runtime
- no delete/update command
- no real client data

The next real implementation should require a separate design review before touching runtime or persistent stores.
