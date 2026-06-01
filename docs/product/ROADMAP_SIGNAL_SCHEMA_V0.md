# Roadmap Signal Schema v0

This schema defines the structured shape for future `/roadmap_signal` records.

It is a design/reference schema only. It is not a runtime command implementation.

## Required Fields

```yaml
/roadmap_signal
signal_id:
created_at:
source_type:
source_ref:
captured_by:
topic:
summary:
distilled_signal:
related_milestone:
decision_category:
recommended_action:
approval_required:
```

## Optional Fields

```yaml
related_lane:
raw_summary:
impact:
reason:
suggested_action:
do_not_interrupt_current_sprint:
relevance_to_mission:
user_value:
urgency:
implementation_effort:
dependency_risk:
trust_or_safety_impact:
current_sprint_fit:
status:
review_after:
promoted_to:
rejection_reason:
owner:
next_action:
privacy_level:
evidence_refs:
```

## Allowed Source Types

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

## Allowed Decision Categories

- `NO_CHANGE`
- `PARKING_LOT`
- `ROADMAP_UPDATE_CANDIDATE`
- `ACTIVE_SPRINT_INTERRUPT`
- `RESEARCH_REQUIRED`
- `PRODUCT_POSITIONING_SIGNAL`
- `TECH_DEBT_SIGNAL`
- `CLIENT_VALUE_SIGNAL`

## Allowed Status Values

- `captured`
- `triaged`
- `parked`
- `roadmap_candidate`
- `approved`
- `rejected`
- `implemented`
- `superseded`
- `archived`

## Copy-Paste Example

```text
/roadmap_signal
source_type: newsletter
source_ref: <newsletter title/date>
topic: local-first AI memory
related_milestone: M52 Infinite Memory v0
decision_category: ROADMAP_UPDATE_CANDIDATE
impact: high
urgency: medium
effort: unknown
trust_or_safety_impact: high
summary: A newsletter suggests local-first AI memory tools are becoming more practical and may affect Val0's Personal OS direction.
recommended_action: Park for weekly ValPrime roadmap review and compare against current M45/M46 priorities.
approval_required: yes
```

## Guardrail

Store summaries and evidence references, not full copyrighted newsletter text. Do not store sensitive client data in public repo docs.
