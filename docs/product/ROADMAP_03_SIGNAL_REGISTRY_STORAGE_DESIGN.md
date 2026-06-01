# ROADMAP-03 Signal Registry Storage Design

## Purpose

This design defines how roadmap signals from newsletters, ideas, client feedback, Codex findings, OPEL events, and ValPrime parking lot items should be stored and reviewed.

The goal is to make useful ideas recoverable and auditable so the user does not need to remember scattered notes manually.

The registry should support roadmap updates without letting random signals mutate the active sprint automatically.

## Registry Concept

A Roadmap Signal is a structured record.

Fields:

- `signal_id`
- `created_at`
- `source_type`
- `source_ref`
- `captured_by`
- `raw_summary`
- `distilled_signal`
- `related_milestone`
- `related_lane`
- `decision_category`
- `relevance_to_mission`
- `user_value`
- `urgency`
- `implementation_effort`
- `dependency_risk`
- `trust_or_safety_impact`
- `current_sprint_fit`
- `status`
- `review_after`
- `promoted_to`
- `rejection_reason`
- `owner`
- `next_action`
- `privacy_level`
- `evidence_refs`

## Supported Source Types

- `newsletter`
- `article`
- `user_idea`
- `client_feedback`
- `codex_finding`
- `opel_event`
- `valprime_parking_lot`
- `obsidian_note`
- `repo_doc`
- `chat_checkpoint`

## Decision Categories

Use the ROADMAP-01 / ROADMAP-02 categories:

- `NO_CHANGE`
- `PARKING_LOT`
- `ROADMAP_UPDATE_CANDIDATE`
- `ACTIVE_SPRINT_INTERRUPT`
- `RESEARCH_REQUIRED`
- `PRODUCT_POSITIONING_SIGNAL`
- `TECH_DEBT_SIGNAL`
- `CLIENT_VALUE_SIGNAL`

## Status Lifecycle

- `captured`
- `triaged`
- `parked`
- `roadmap_candidate`
- `approved`
- `rejected`
- `implemented`
- `superseded`
- `archived`

## Storage Options

### A. ValPrime Internal File/Database

Best fit for operational memory and recurring review. ValPrime is the roadmap keeper, so this is the preferred future owner.

Tradeoff: requires command implementation and storage discipline.

### B. Repo Markdown Registry

Good for transparent, versioned design records and approved roadmap decisions.

Tradeoff: public repo docs are not appropriate for sensitive client/private signals.

### C. OPEL Event Log

Good for audit trail and timestamped events.

Tradeoff: OPEL is event/audit history, not necessarily the best review queue.

### D. Obsidian Visual Layer

Good for graph view, library navigation, and human review.

Tradeoff: Obsidian is not source-of-truth and should not become split-brain storage.

### E. Future Database/Table

Good if signal volume grows and filtering/status transitions become frequent.

Tradeoff: higher implementation and migration cost.

## Recommended Phased Approach

- Phase 1: Markdown registry/design only.
- Phase 2: ValPrime command `/roadmap_signal` appends structured signal.
- Phase 3: `/roadmap_review` summarizes open signals.
- Phase 4: optional export to Obsidian.
- Phase 5: database-backed registry if signal volume grows.

No Notion dependency is required or desired.

## Proposed Initial File Layout

For design only, future files could include:

- `docs/product/ROADMAP_SIGNAL_REGISTRY.md`
- `docs/product/ROADMAP_SIGNAL_REVIEW_QUEUE.md`
- `docs/product/ROADMAP_SIGNAL_DECISION_LOG.md`

Do not create live mutable registry files until the storage owner and privacy model are confirmed.

## Recovery Behavior

Future status recovery should:

1. Check ValPrime checkpoint.
2. Check `ROADMAP_SIGNAL_REGISTRY`.
3. Check `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`.
4. Check `docs/product/VAL0_MASTER_MILESTONE_MAP.md`.
5. List open roadmap signals.
6. Recommend next action.

Recovery should show what is approved, parked, rejected, implemented, and awaiting review.

## Guardrails

- No automatic sprint interruption.
- No automatic roadmap changes.
- No roadmap mutation without user approval.
- Do not store full copyrighted newsletter text; store summary/signals.
- Do not store sensitive client data in public repo docs.
- Keep private/client signals scoped.
- Every promotion needs evidence and reason.
- Keep ValPrime as roadmap keeper.
- Keep repo docs/smokes as technical source-of-truth.
- Keep OPEL / Forge docs as event and audit history.
- Keep Obsidian as optional visual layer, not authoritative storage.

## Example Signal Records

### Newsletter Signal: M52 Infinite Memory

```yaml
signal_id: RS-2026-06-01-001
created_at: 2026-06-01
source_type: newsletter
source_ref: AI newsletter, local-first memory tools
captured_by: intake_chat
raw_summary: A newsletter argues that local-first memory graphs are becoming more practical for personal AI systems.
distilled_signal: Val0 may need an Infinite Memory v0 lane after router stabilization.
related_milestone: M52 Infinite Memory v0
related_lane: memory_architecture
decision_category: ROADMAP_UPDATE_CANDIDATE
relevance_to_mission: 5
user_value: 4
urgency: 2
implementation_effort: 4
dependency_risk: 3
trust_or_safety_impact: 4
current_sprint_fit: 1
status: parked
review_after: 2026-06-15
promoted_to:
rejection_reason:
owner: ValPrime
next_action: Revisit after M45 Router Coverage / Observation.
privacy_level: public_summary
evidence_refs:
  - newsletter summary only
```

### Karen Feedback Signal: M49 Memory Library / Carpetas

```yaml
signal_id: RS-2026-06-01-002
created_at: 2026-06-01
source_type: client_feedback
source_ref: Karen live feedback summary
captured_by: ValPrime
raw_summary: Karen needs documents, tasks, and case context grouped into understandable containers.
distilled_signal: Topic containers / Carpetas may be a strong client-value lane after RC stabilization.
related_milestone: M49 Memory Library / Carpetas
related_lane: client_memory_library
decision_category: CLIENT_VALUE_SIGNAL
relevance_to_mission: 5
user_value: 5
urgency: 3
implementation_effort: 4
dependency_risk: 3
trust_or_safety_impact: 4
current_sprint_fit: 2
status: roadmap_candidate
review_after: 2026-06-08
promoted_to:
rejection_reason:
owner: ValPrime
next_action: Compare against `docs/product/CARPETAS_TOPIC_CONTAINERS_V0.md`.
privacy_level: client_private_summary
evidence_refs:
  - client-private feedback pointer only
```

### Codex Finding Signal: M45 Router Coverage

```yaml
signal_id: RS-2026-06-01-003
created_at: 2026-06-01
source_type: codex_finding
source_ref: Router coverage diagnostics
captured_by: Codex
raw_summary: Coverage report shows remaining live-observation gaps for pending_action_reply, reminder_update, task_complete, task_create, and task_delete.
distilled_signal: Continue M45 observation before broad router refactor.
related_milestone: M45 Router Coverage / Observation
related_lane: intent_router_v2
decision_category: TECH_DEBT_SIGNAL
relevance_to_mission: 4
user_value: 4
urgency: 3
implementation_effort: 2
dependency_risk: 2
trust_or_safety_impact: 5
current_sprint_fit: 5
status: triaged
review_after: 2026-06-03
promoted_to: ROUTER-17 observation plan
rejection_reason:
owner: ValPrime
next_action: Observe remaining gaps using test data only.
privacy_level: repo_public
evidence_refs:
  - scripts/diagnostics/intent_router_v2_coverage_report.py
```

## Runtime Note

This is design only. It does not implement ValPrime commands, create mutable registry files, integrate Notion, or call external services.
