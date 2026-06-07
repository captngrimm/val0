# MEMORY-SPINE-01A Memory Object Model

Purpose: propose object types and fields for future intake memory persistence without implementing storage now.

This is product/design only. It is not a database schema, migration, profile write, runtime route, or production configuration.

## 1. Proposed Object Types

### memory_candidate

A temporary record extracted from intake or correction before user confirmation.

Use for:

- possible user preference
- possible workflow setup
- possible privacy boundary
- possible correction pattern

Rules:

- not treated as confirmed memory
- not retrieved as a fact
- must expire or be discarded if not confirmed

### user_preference

A confirmed operational preference about how the user wants Val to communicate or behave.

Examples:

- preferred language
- preferred tone
- concise vs detailed answers
- confirmation style

### workflow_profile

A confirmed setup record for one active workflow.

Examples:

- Daily Operator
- documents/admin
- client follow-up
- ideas/projects
- routines

### intake_summary

A compact, source-aware summary of what Val heard during onboarding.

Use for:

- explaining the recommendation
- showing the user what was captured
- connecting candidate records to the intake conversation

### correction_pattern

A confirmed or pending pattern learned from user corrections.

Examples:

- "when I say daily review, include undated pending items"
- "use WhatsApp-style copy, not formal proposal copy"

### memory_index_entry

The Library Index / librarian catalog record that points to a memory object without storing every detail inline.

Use for:

- retrieval tags
- scope filtering
- status/freshness checks
- linked workflow lookup

### privacy_boundary

A confirmed rule about what Val may not save, retrieve, infer, expose, send, create, or touch.

Examples:

- no message sending without confirmation
- no legal conclusions
- do not save emotional disclosures
- do not use third-party private details as reusable memory

### audit_event

An append-only event that records consent, updates, deletion requests, retrieval decisions, or memory lifecycle changes.

Audit events are not user profile facts. They explain what happened to memory and why.

## 2. Shared Fields

Each object type should support these fields where applicable:

- id
- client_id / user_id
- memory_type
- title
- summary
- source
- confidence
- consent_status
- sensitivity
- status
- created_at
- updated_at
- expires_or_review_after
- linked_workflow
- retrieval_tags

Field intent:

- id: stable object identifier
- client_id / user_id: strict retrieval scope
- memory_type: one of the proposed object types
- title: short human-readable label
- summary: compact inspectable memory text
- source: intake answer, user confirmation, correction, operator note, document, or audit event
- confidence: low, medium, high, or confirmed
- consent_status: not_asked, proposed, granted, declined, revoked
- sensitivity: low, moderate, high, restricted
- status: candidate, proposed, confirmed, active, stale, archived, deleted
- created_at: creation timestamp
- updated_at: latest update timestamp
- expires_or_review_after: freshness/review date or null
- linked_workflow: workflow id/name or null
- retrieval_tags: scoped tags for future retrieval

## 3. Example JSON-Like Records

These examples are illustrative, not schema commitments.

### Daily Operator Workflow Profile

```json
{
  "id": "mem_workflow_daily_operator_001",
  "client_id": "client_resolved_at_runtime",
  "user_id": "user_resolved_at_runtime",
  "memory_type": "workflow_profile",
  "title": "Daily Operator pilot setup",
  "summary": "User confirmed a Daily Operator workflow with WhatsApp and notes as sources, and a daily review containing agenda, important tasks, and undated pending items.",
  "source": "confirmed intake summary",
  "confidence": "confirmed",
  "consent_status": "granted",
  "sensitivity": "moderate",
  "status": "active",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "expires_or_review_after": "2026-07-07T00:00:00Z",
  "linked_workflow": "daily_operator",
  "retrieval_tags": ["daily_review", "agenda", "tasks", "undated_pending", "workflow_profile"]
}
```

### Preferred Tone

```json
{
  "id": "mem_pref_tone_001",
  "client_id": "client_resolved_at_runtime",
  "user_id": "user_resolved_at_runtime",
  "memory_type": "user_preference",
  "title": "Preferred tone",
  "summary": "User prefers warm, direct, practical answers with brief explanations when trust or safety matters.",
  "source": "user confirmed preference",
  "confidence": "confirmed",
  "consent_status": "granted",
  "sensitivity": "low",
  "status": "active",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "expires_or_review_after": null,
  "linked_workflow": null,
  "retrieval_tags": ["tone", "communication_style", "user_preference"]
}
```

### Privacy Boundary

```json
{
  "id": "mem_boundary_no_send_001",
  "client_id": "client_resolved_at_runtime",
  "user_id": "user_resolved_at_runtime",
  "memory_type": "privacy_boundary",
  "title": "No sends or calendar writes without confirmation",
  "summary": "Val must draft first and ask before sending messages, creating reminders, or creating calendar events.",
  "source": "confirmed intake boundary",
  "confidence": "confirmed",
  "consent_status": "granted",
  "sensitivity": "moderate",
  "status": "active",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "expires_or_review_after": null,
  "linked_workflow": "daily_operator",
  "retrieval_tags": ["privacy_boundary", "confirmation_required", "no_auto_send", "no_auto_calendar"]
}
```

### Memory Candidate Pending Confirmation

```json
{
  "id": "mem_candidate_001",
  "client_id": "client_resolved_at_runtime",
  "user_id": "user_resolved_at_runtime",
  "memory_type": "memory_candidate",
  "title": "Possible workflow source preference",
  "summary": "User mentioned that most pending items live in WhatsApp and notes. This is not confirmed memory yet.",
  "source": "intake answer",
  "confidence": "medium",
  "consent_status": "proposed",
  "sensitivity": "moderate",
  "status": "proposed",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "expires_or_review_after": "2026-06-14T00:00:00Z",
  "linked_workflow": "daily_operator",
  "retrieval_tags": ["memory_candidate", "workflow_sources", "pending_confirmation"]
}
```

### Correction Pattern

```json
{
  "id": "mem_correction_daily_review_001",
  "client_id": "client_resolved_at_runtime",
  "user_id": "user_resolved_at_runtime",
  "memory_type": "correction_pattern",
  "title": "Daily review should include reminders",
  "summary": "User corrected the Daily Operator setup: daily review should include reminders in addition to agenda and tasks.",
  "source": "user correction",
  "confidence": "confirmed",
  "consent_status": "granted",
  "sensitivity": "low",
  "status": "active",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "expires_or_review_after": null,
  "linked_workflow": "daily_operator",
  "retrieval_tags": ["correction_pattern", "daily_review", "reminders"]
}
```

## 4. Rules

- no raw secrets
- no unconfirmed sensitive facts
- no global leakage
- no Karen hardcoding
- client isolation first
- memory must be inspectable and deletable
- memory must support delete/update memory operations
- candidate memory must not behave like confirmed memory
- privacy boundary records must be checked before action suggestions
- retrieval must filter by client_id / user_id before any semantic or keyword search
- stale memory must be named as stale or reviewed before strong use
- audit_event records must not become hidden user profiles

Implementation remains future work. This document only defines a design target for later persistence, indexing, retrieval, correction, and deletion behavior.
