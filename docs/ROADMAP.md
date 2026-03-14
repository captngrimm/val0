=====================================================================
VAL0 — COGNITIVE OPERATIONS CORE
=====================================================================

Operational Roadmap
Last Updated: 2026-03-13

Mission:
Val0 is a deterministic cognitive operations engine.

It began with legal workflow hardening, but its architecture is designed
to support a broader class of entity-linked cognitive workflows.

Core scope includes:

- Deterministic legal execution
- Encrypted memory spine
- Unified timeline retrieval
- Discipline automation
- Operational CLI control
- Advisory reasoning layers
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

- create legal facts
- silently mutate deterministic records
- alter deadlines or reminders
- override DB truth

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
- preserve memory
- link entities
- coordinate workflows
- assist reasoning

Val0 remains deterministic at its core.

Advisory intelligence may operate on top,
but must never mutate operational records.

Future systems may allow multiple S.O.U.L. instances
connected through shared modules and services.

=====================================================================
CURRENT STATE — VERIFIED LIVE
=====================================================================

Deterministic legal engine operational.
Encrypted storage active (SQLCipher).
Google Calendar merge hardened and gated.
Reminder engine stable and verified.
Reminder cancellation deterministic (ID-based, DB-backed).
Ops commands stable (/ops /health /reminders).
Voice ingestion + case note capture live.
Semantic recall operational (advisory only).
Ops CLI control surface active.

Reminder Runner:

- Due reminders delivered live (chat_id verified)
- Blocked-user path marks reminder failed without crash
- No stuck "sending" rows
- due_now returns 0 after delivery
- APScheduler stable across restart

Isolation:

- DM + group chat isolation verified
- /reminders is chat-scoped

=====================================================================
MVP 1.1 — DETERMINISTIC LEGAL GATES (LIVE)
=====================================================================

Implemented:

- Case summary gate (DB deterministic)
- Due today gate
- Due range gate
- Strict CASE:<id> enforcement
- SQLCipher encrypted DB
- Deterministic dedupe
- Conflict detection logging
- No LLM participation

Legal gates never depend on model reasoning.

=====================================================================
MVP 1.2 — GOOGLE CALENDAR MERGE (LIVE)
=====================================================================

Implemented:

- Feature flag: VAL0_GCAL_ENABLED
- Deterministic DB + GCAL merge
- Conflict detection logging
- DB priority on collisions
- No database mutation
- OAuth isolated under /etc/val0/gcal

Merge is read-only and query-time only.

=====================================================================
MVP 1.3 — DISCIPLINE LAYER (LIVE)
=====================================================================

Implemented:

- Regex-based reminder creation
- Reminder cancellation by ID
- Reminder runner stable
- Encrypted reminder storage
- CLI injection tests
- case_notes table live
- Voice-to-note ingestion
- Deterministic dedupe index

Reminders are short-term nudges.
Calendar is the system of record.

Pending polish:

- Daily 08:00 summary push
- Overdue escalation tagging
- Reminder state audit timeline
- Timezone enforcement

=====================================================================
SPRINT 10 — COURT DAY TIMELINE (LIVE)
=====================================================================

Implemented:

Natural query support:

- qué tengo mañana
- mañana tribunales

Deterministic timeline rendering.
Case event grouping.

Remaining polish:

- formatting normalization
- clearer source labels

=====================================================================
SPRINT 12 — ENTITY TIMELINE BACKBONE (LIVE)
=====================================================================

Core primitive introduced:

parent_ref

Example:

parent_ref = CASE:524242024

Capabilities:

- entity-linked reminders
- entity-linked notes
- timeline retrieval by entity
- timeline retrieval by day

Supported queries:

qué tengo mañana  
qué tengo del caso 524242024

Timeline assembled at query time.

No persistent timeline table created.

Design rules:

- read-only merge
- deterministic retrieval
- no model mutation

=====================================================================
NEXT SPRINT TARGETS
=====================================================================

Sprint 12.1 — Timeline Formatting

Goal:

Improve readability of timeline output.

Example:

📅 2026-03-08
- 09:00 | evento       | audiencia
- 12:30 | nota         | juez sugirió conciliación
- 15:00 | recordatorio | revisar expediente

Rendering only.
No storage changes.

---------------------------------------------------------------------

Sprint 12.2 — Case Note Write Path

Goal:

Allow deterministic notes attached to case timelines.

Example command:

nota caso 524242024: juez sugirió conciliación

Stored as:

entity_type = note  
parent_ref  = CASE:<id>

Visible in:

qué tengo del caso <id>

---------------------------------------------------------------------

Sprint 12.3 — Source Trace

Expose origin of timeline entries.

Sources:

- event
- reminder
- note
- transcript

Improves user trust and advisory reasoning clarity.

=====================================================================
APRIL LAUNCH TARGET — MIGUEL MVP
=====================================================================

Target Window:

April 1 – April 10, 2026

Goal:

Ship the first stable operational assistant
for Miguel's daily legal workflow.

Launch Criteria:

Required:

- deterministic case timeline
- reminder engine stable
- case note write path
- timeline source labels
- daily briefing (08:00)
- encrypted DB stable
- Google Calendar merge stable
- CLI health + ops checks

Nice to Have:

- overdue escalation tagging
- formatting polish
- advisory argument builder

Non-blocking:

- Prime bridge
- advanced advisory analysis
- transcript ingestion

Launch is defined as:

Miguel successfully using Val0 as
a daily operational assistant.

=====================================================================
PHASE 0.4 — ORCHESTRATION SURFACE
=====================================================================

Purpose:

Prevent founder drift and maintain operational truth.

Includes:

- Case cockpit
- State board
- Bug intake pipeline
- Timeline snapshot view

LLM may summarize but cannot author facts.

=====================================================================
PHASE 0.5 — MEMORY SPINE
=====================================================================

Live tables:

- case_notes
- chat_prefs
- memory_entries
- reminders.entity_type
- reminders.parent_ref

Memory remains advisory only.

=====================================================================
PHASE 0.7 — PRIME BRIDGE (PARALLEL TRACK)
=====================================================================

Prime introduces a founder-focused AI layer.

Architecture:

Frank  
 ↓  
ValPrime (Forge RTX 4080)  
 ↓  
Val0 (VPS)

Val0 remains the production assistant.

Prime is optional.

Prime must never be required for Val0 operation.

---------------------------------------------------------------------

Prime Responsibilities

- founder copilot
- voice interface
- AI worker node
- development monitor

---------------------------------------------------------------------

Prime Implementation Stages

Prime v0 — Voice Shell  
Prime v1 — Dev Copilot  
Prime v2 — Worker Node  
Prime v3 — Packet Export

Prime packets may include:

packet_id  
sources[]  
facts[]  
summaries[]  
open_questions[]

Val0 may ingest packets only into advisory tables.

Prime may never mutate deterministic records.

=====================================================================
PHASE 9 — ADVISORY ANALYSIS LAYER
=====================================================================

Purpose:

Pattern detection and reasoning assistance.

Outputs must clearly separate:

FACTS  
UNKNOWN  
INFERENCE  
OPTIONS  
NEXT QUESTIONS

Advisory layer cannot modify deterministic records.

=====================================================================
PHASE 9.2 — ARGUMENT BUILDER
=====================================================================

Purpose:

Assist professionals constructing structured arguments.

Example input:

"arguments for changing school closer to mother"

Expected structure:

FACTORS  
ARGUMENTS  
COUNTERPOINTS  
QUESTIONS

Rules:

- advisory only
- no legal facts invented
- no case record mutation
- supports legal drafting workflows

=====================================================================
CHANGE CONTROL
=====================================================================

Every structural modification must:

1. be reflected here
2. be committed clearly
3. preserve determinism
4. be CLI-testable