=====================================================================
VAL0 — COGNITIVE OPERATIONS CORE
=====================================================================

Operational Roadmap
Last Updated: 2026-03-08

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

Pending:

- Daily 08:00 summary push
- Overdue escalation tagging
- Reminder state audit timeline
- Timezone enforcement

=====================================================================
SPRINT 10 — COURT DAY TIMELINE (LIVE)
=====================================================================

Implemented:

- Natural query support:
  - qué tengo mañana
  - mañana tribunales

- Deterministic timeline rendering
- Case event grouping

Remaining cleanup:

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
SPRINT 12.1 — TIMELINE OUTPUT NORMALIZATION (NEXT)
=====================================================================

Goal:

Improve timeline readability.

Example target format:

📅 2026-03-08
- 09:00 | evento     | audiencia
- 12:30 | nota       | juez sugirió conciliación
- 15:00 | recordatorio | revisar expediente

Rendering only.

No storage changes.

=====================================================================
SPRINT 12.2 — CASE NOTE WRITE PATH
=====================================================================

Goal:

Allow deterministic case notes linked to entity timelines.

Example command:

nota caso 524242024: juez sugirió conciliación

Stored as:

entity_type = note
parent_ref  = CASE:<id>

Visible in:

qué tengo del caso <id>

=====================================================================
SPRINT 12.3 — SOURCE TRACE
=====================================================================

Goal:

Expose origin of timeline entries.

Example:

- event
- reminder
- note
- transcript

This improves trust and supports advisory reasoning.

=====================================================================
PHASE 0.4 — ORCHESTRATION SURFACE (ACTIVE)
=====================================================================

Goal:

Prevent founder drift and maintain operational truth.

Includes:

- Case cockpit
- State board
- Bug intake pipeline
- Timeline snapshot view

LLM may summarize but cannot author facts.

=====================================================================
PHASE 0.5 — MEMORY SPINE (ACTIVE)
=====================================================================

Live tables:

- case_notes
- chat_prefs
- memory_entries
- reminders.entity_type
- reminders.parent_ref

Memory is advisory only.

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

Prime must never be required for Val0 to operate.

---------------------------------------------------------------------
Prime Responsibilities
---------------------------------------------------------------------

Founder copilot
Voice interface
AI worker node
Development monitor

---------------------------------------------------------------------
Prime Implementation Stages
---------------------------------------------------------------------

Prime v0 — Voice Shell

- push-to-talk
- speech-to-text
- LLM response
- voice output

Prime v1 — Dev Copilot

- sprint monitoring
- roadmap reminders
- drift detection
- daily dev briefing

Prime v2 — Worker Node

Forge jobs:

- transcription
- embeddings generation
- document indexing
- memory consolidation

Prime v3 — Packet Export

Prime generates advisory packets:

packet_id
sources[]
facts[]
summaries[]
open_questions[]

Val0 ingests packets into advisory tables only.

Prime may never mutate deterministic tables.

=====================================================================
PHASE 1 — HARDENING (ACTIVE)
=====================================================================

Remaining tasks:

- reminder state audit timeline
- GCAL conflict surfacing
- deadline normalization guardrails
- rollback playbook

Hard rule:

No scope expansion that risks deterministic stability.

=====================================================================
PHASE 2 — DISCIPLINE AUTOMATION
=====================================================================

Remaining:

- daily summary push
- overdue detection
- escalation tagging
- timezone enforcement

=====================================================================
PHASE 2.5 — OPS CONTROL LAYER
=====================================================================

Implemented:

- val0ctl ops
- DB integrity check
- service health check

Planned:

- val0ctl doctor
- automated repair tools

=====================================================================
PHASE 4 — MIGUEL UX SIMPLIFICATION
=====================================================================

Goal:

Zero friction courtroom workflow.

Needs:

- clean case timeline
- case notes
- daily brief
- quick case query

=====================================================================
PHASE 5 — VOICE / PERSONALITY ARCHITECTURE
=====================================================================

Two-pass response system.

1) deterministic response pack
2) LLM renderer

Renderer may add tone but not facts.

=====================================================================
PHASE 8 — TRANSCRIPT INGESTION
=====================================================================

Future pipeline:

recording
→ transcription
→ linked note
→ advisory extraction

Potential entities:

CASE
PERSON
CLIENT
PROJECT

=====================================================================
PHASE 9 — ADVISORY ANALYSIS LAYER
=====================================================================

Allows pattern detection and hypothesis generation.

Outputs must separate:

FACTS
UNKNOWN
INFERENCE
OPTIONS
NEXT QUESTIONS

Advisory layer cannot modify deterministic records.

=====================================================================
CURRENT PRIORITY
=====================================================================

1. Sprint 12.1 timeline formatting
2. Sprint 12.2 case notes
3. Sprint 12.3 source trace
4. Phase 1 hardening
5. Phase 4 Miguel UX simplification

Prime development must not delay these tasks.

=====================================================================
CHANGE CONTROL
=====================================================================

Every structural modification must:

1. Be reflected here
2. Be committed clearly
3. Preserve determinism
4. Be CLI-testable