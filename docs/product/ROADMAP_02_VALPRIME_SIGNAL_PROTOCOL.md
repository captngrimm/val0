# ROADMAP-02 ValPrime Roadmap Signal Protocol

## Purpose

This protocol defines how newsletter/idea intake sends distilled roadmap signals to ValPrime.

ValPrime is the roadmap keeper. Not Notion.

The intake chat analyzes incoming material. ValPrime stores and reviews roadmap signals. The user approves major changes before any roadmap, sprint, or source-of-truth update.

## Roles

- Newsletter/Idea Intake Chat = analyst.
- ValPrime = roadmap keeper / operational memory.
- Repo docs = technical and product source of truth.
- OPEL / Forge docs = event and audit history.
- User = final approval.

## Proposed Manual Commands For Now

These are manual protocol commands, not implemented runtime commands yet:

- `/roadmap_signal`
- `/roadmap_review`
- `/roadmap_decision`
- `/parking_lot`
- `/checkpoint`

## `/roadmap_signal` Format

```text
/roadmap_signal
source:
date:
topic:
summary:
related_milestone:
impact:
recommendation:
reason:
suggested_action:
do_not_interrupt_current_sprint:
approval_required:
```

Example:

```text
/roadmap_signal
source: AI newsletter, summarized by intake chat
date: 2026-06-01
topic: lightweight personal memory graphs
summary: The source suggests small, user-owned memory graphs are becoming easier to build.
related_milestone: M49 Obsidian / Visual Second Brain Sync Layer
impact: Possible future architecture signal, not urgent.
recommendation: PARKING_LOT
reason: Relevant to Personal OS, but current active lane is M45 Router Coverage / Observation.
suggested_action: Save for ROADMAP-07 Obsidian export/index review.
do_not_interrupt_current_sprint: yes
approval_required: yes, before changing roadmap docs
```

## Decision Categories

- `NO_CHANGE`
- `PARKING_LOT`
- `ROADMAP_UPDATE_CANDIDATE`
- `ACTIVE_SPRINT_INTERRUPT`
- `RESEARCH_REQUIRED`
- `PRODUCT_POSITIONING_SIGNAL`
- `TECH_DEBT_SIGNAL`
- `CLIENT_VALUE_SIGNAL`

## Review Rhythm

Review is manual for now.

Suggested rhythm:

- weekly review of accumulated `/roadmap_signal` blocks
- ad hoc review only for urgent trust/safety/client blockers
- no Notion dependency

Future ValPrime command:

- `/roadmap_review` summarizes accumulated signals, groups patterns, and proposes whether anything should become a roadmap update.

## Guardrails

- No automatic roadmap changes.
- No active sprint interruption without explicit approval.
- Preserve source summary, not full copyrighted newsletter text.
- Sensitive/client data must not go into public docs.
- If signal affects current sprint, require user confirmation.
- Keep facts separate from speculation.
- If source trust is unclear, mark `RESEARCH_REQUIRED`.
- If the signal is interesting but not urgent, use `/parking_lot`.

## Future Phases

- ROADMAP-03: Roadmap signal registry storage design.
- ROADMAP-04: ValPrime `/roadmap_signal` command implementation.
- ROADMAP-05: `/roadmap_review` synthesis.
- ROADMAP-06: optional scheduler/reminder, no Notion required.
- ROADMAP-07: optional Obsidian export/view.

## Runtime Note

This protocol changes no runtime behavior. It does not integrate Notion, call external services, or implement ValPrime commands yet.
