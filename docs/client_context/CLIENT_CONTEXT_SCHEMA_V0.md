# Client Context Schema v0

Purpose:
Give each client Val a structured context layer without leaking data across clients.

## Files per client

- CLIENT_PROFILE.md
- CLIENT_ROADMAP.md
- CLIENT_IDEAS.md
- CLIENT_STATUS.md

## Design rules

1. Client data is isolated.
2. ValPrime/admin may coordinate roadmap and checkpoints.
3. Client Val may read only its own client context.
4. Reusable capabilities are shared as code/patterns, not private data.
5. Context should be easy to ingest later into larger memory systems.

## Future database fields

- client_id
- client_type
- domain
- intent
- raw_text
- normalized_text
- entities
- due_at
- followup_at
- source
- confidence
- status
- created_at
- updated_at
