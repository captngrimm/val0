=====================================================================
VAL0 — COGNITIVE OPERATIONS CORE
=====================================================================

Operational Roadmap
Last Updated: 2026-03-21

Mission:
Val0 is a deterministic cognitive operations engine.

It began with legal workflow hardening, but its architecture is designed
to support a broader class of entity-linked cognitive workflows.

Core scope includes:

- Deterministic entity-linked execution
- Structured memory spine (canonical + derived)
- Unified timeline retrieval
- Discipline automation
- Operational CLI control
- Advisory reasoning layers (non-authoritative)
- Controlled personality rendering
- Future standalone interface

Principle:
Deterministic core first.
Advisory reasoning second.
Personality last.

Revenue stability first.
Architecture second.
Ambition third.

=====================================================================
SYSTEM PHILOSOPHY
=====================================================================

Val0 is not a chatbot-first system.

Val0 is:

1. deterministic storage
2. deterministic retrieval
3. deterministic operations
4. optional advisory reasoning on top
5. controlled rendering last

The model may help:

- phrase
- summarize
- ask clarifying questions
- generate advisory analysis

The model may NOT:

- create facts
- silently mutate deterministic records
- alter deadlines or reminders
- override DB truth
- write to memory

LLM is strictly:
- last-stage
- non-authoritative
- non-mutating

=====================================================================
ARCHITECTURAL DIRECTION — S.O.U.L.
=====================================================================

S.O.U.L. = Synthetic Organic Universal Link

Concept:

A persistent cognitive layer connecting humans,
structured data, and machine reasoning.

Val0 acts as the operational S.O.U.L. instance
for a specific user.

Responsibilities:

- capture intent
- preserve structured memory
- link entities
- coordinate workflows
- assist reasoning (advisory only)

Val0 remains deterministic at its core.

Future systems may allow multiple S.O.U.L. instances
connected through controlled, permissioned exchange.

Default:
NO cross-user data sharing.

=====================================================================
MULTI-TENANT MODEL
=====================================================================

Core abstraction:

- chat_id = tenant (user)
- case_id = unit of work (case, deal, project, etc.)

Rules:

- All operations must be scoped by chat_id
- No cross-tenant leakage
- Same client names across tenants are isolated

This enables Val0 to expand beyond legal workflows.

=====================================================================
CURRENT STATE — VERIFIED LIVE
=====================================================================

Deterministic engine operational.
Encrypted storage active (SQLCipher).
Reminder engine stable.
Reminder cancellation deterministic.
Case notes + voice ingestion live.
Semantic recall operational (advisory only).
Ops CLI stable.

Isolation:

- DM + group isolation verified
- chat-scoped operations enforced

Reminder Runner:

- stable delivery
- no stuck rows
- restart-safe

=====================================================================
MVP 1.1 — DETERMINISTIC GATES (LIVE)
=====================================================================

Implemented:

- Case summary gate (DB deterministic)
- Due today gate
- Due range gate
- Strict CASE:<id> enforcement
- Deterministic dedupe
- Conflict detection logging
- No LLM participation

=====================================================================
MVP 1.2 — GOOGLE CALENDAR MERGE (LIVE)
=====================================================================

- Read-only merge
- DB priority on conflicts
- No mutation of canonical records

=====================================================================
MVP 1.3 — DISCIPLINE LAYER (LIVE)
=====================================================================

- Reminder creation + cancellation
- Voice note ingestion
- Deterministic dedupe
- Case-linked notes

=====================================================================
SPRINT 10 — COURT DAY TIMELINE (LIVE)
=====================================================================

- Natural query support
- Deterministic timeline rendering

=====================================================================
SPRINT 12 — ENTITY TIMELINE BACKBONE (LIVE)
=====================================================================

Primitive:

parent_ref

Capabilities:

- entity-linked notes
- entity-linked reminders
- timeline queries by entity/day

No persistent timeline table.
All timelines built at query time.

=====================================================================
PHASE 2 — CASE SUMMARY MEMORY (IN PROGRESS)
=====================================================================

New derived layer:

case_summaries

Purpose:

- fast cockpit rendering
- structured case snapshot
- future LLM context injection

Properties:

- keyed by (chat_id, case_id)
- deterministic only
- fully rebuildable
- NOT source of truth

Update triggers:

- event insert
- note insert
- undo/delete operations

NOT updated during:

- detection
- suggestion
- disambiguation

Constraints:

- no pipeline changes
- no LLM usage
- no mutation of canonical tables

=====================================================================
PIPELINE PROTECTION (CRITICAL)
=====================================================================

Must NEVER be altered:

- routing order in _process_text_pipeline
- deterministic detection before LLM fallback
- confirmation flows
- disambiguation behavior
- insert semantics

This is the system's core integrity boundary.

=====================================================================
NEXT TARGETS
=====================================================================

Phase 2 Completion:

- summary refresh hooks wired everywhere
- cockpit summary section added
- undo consistency verified

Sprint — Timeline UX polish:

- formatting clarity
- source labeling

=====================================================================
APRIL LAUNCH TARGET — MIGUEL MVP
=====================================================================

Target Window:

April 1 – April 10, 2026

Goal:

Daily operational assistant for real-world use.

Required:

- deterministic timelines
- reminder engine stable
- case notes working
- summary layer functional
- daily briefing
- encrypted DB stable

Launch definition:

System is used daily without fallback to manual tracking.

=====================================================================
PHASE 0.7 — PRIME BRIDGE (PARALLEL)
=====================================================================

Frank  
 ↓  
ValPrime  
 ↓  
Val0

Rules:

- Prime is optional
- Prime cannot mutate deterministic records
- Prime outputs advisory packets only

=====================================================================
PHASE 9 — ADVISORY LAYER
=====================================================================

Outputs must separate:

FACTS  
UNKNOWN  
INFERENCE  
OPTIONS  
NEXT QUESTIONS  

No mutation allowed.

=====================================================================
CHANGE CONTROL
=====================================================================

All structural changes must:

1. be documented here first
2. preserve determinism
3. remain testable