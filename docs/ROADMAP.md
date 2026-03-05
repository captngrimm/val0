=====================================================================
VAL0 — COGNITIVE OPERATIONS CORE
=====================================================================

Operational Roadmap
Last Updated: 2026-03-05

Mission:
Val0 is a deterministic cognitive operations engine.
It began with legal workflow hardening, but its scope includes:

- Deterministic legal execution
- Discipline automation
- Encrypted memory spine
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
- Due reminders delivered live (chat_id verified).
- Blocked-user path marks reminder failed without crash.
- No stuck "sending" rows.
- due_now returns 0 after delivery.
- APScheduler stable across restart.
- Schema verified: due_at_utc authoritative (stored UTC, displayed local).

Isolation:
- DM + group chat isolation verified.
- /reminders is chat-scoped (no cross-chat leakage).

Memory Spine (Minimal):
- memory_entries table present.
- Deterministic insert verified.
- Keyword recall verified.
- Date-range recall verified.
- Advisory only — never mutates deterministic systems.

Hard Rules:
- No LLM involvement in legal gates.
- No silent DB mutation.
- All merge logic is query-time only.
- All automation auditable via logs/audit tables.

Primary control surface:
val0ctl ops

Systemd:
sudo systemctl status val0-bot.service

=====================================================================
MVP 1.1 — DETERMINISTIC LEGAL GATES (LIVE)
=====================================================================

- Case summary gate (DB deterministic)
- Due today gate
- Due range gate
- Strict CASE:<id> enforcement
- SQLCipher encrypted DB
- Short-circuit pipeline confirmed
- Conflict detection logging
- Deterministic dedupe
- Log-safe hashing
- No LLM participation

Hard rule:
Legal gates never depend on model reasoning.

=====================================================================
MVP 1.2 — GOOGLE CALENDAR MERGE (LIVE, HARDENED)
=====================================================================

- Feature flag: VAL0_GCAL_ENABLED
- Timezone control: VAL0_TZ
- Unbound GCAL events disabled by default
- Deterministic DB + GCAL merge
- Conflict detection logging
- DB priority on collisions
- No database mutation
- No model involvement
- OAuth isolated under /etc/val0/gcal

Merge is read-only and query-time only.

=====================================================================
MVP 1.3 — DISCIPLINE LAYER (LIVE, STABLE)
=====================================================================

Live:
- Deterministic reminder creation (regex-based)
- Regex punctuation tolerance
- Reminder cancellation by ID (DB-backed)
- Reminder runner (APScheduler stable)
- Deterministic tick logging
- Encrypted reminder storage
- CLI injection testable
- case_notes table live
- Active case binding per user
- Voice-to-note ingestion (text + voice)
- /reminders is chat-scoped (no cross-chat listing)
- Deterministic dedupe enforced (unique index for active reminders)
- Multi-reminder VN splitting supported (deterministic)

Design principle:
Reminders are short-term operational nudges.
Calendar is the system of record for long-term commitments.

Operational boundary:
Reminders should normally not exceed ~7 days.
Longer commitments should migrate to calendar events.

Pending:
- Daily 08:00 summary push
- Overdue escalation tagging
- Reminder state audit log (state-change timeline)
- Per-user timezone enforcement
- Local-time display normalization in all user-facing outputs
- Per-user friendly address/nickname store (optional)

=====================================================================
PHASE 0.4 — ORCHESTRATION SURFACE (ACTIVE)
=====================================================================

Objective:
Stop founder drift and create a stable operational truth layer.

Scope:
- Case Cockpit view (CASE:<id> snapshot)
- State Board (LIVE / PARTIAL / PLANNED)
- Bug Intake pipeline
- Repro Capture Template
- Timeline view for case/chat history

Rules:
- Storage deterministic
- LLM may phrase summaries but cannot author facts
- All entries must map to DB rows and audit logs

=====================================================================
PHASE 0.5 — MEMORY SPINE (ACTIVE)
=====================================================================

Baseline schema operational.

Live:
- case_notes
- chat_prefs
- memory_entries

Constraints:
Advisory only.
Never overrides deterministic systems.

Pending:
- Memory audit visibility
- Memory health verification

=====================================================================
PHASE 0.7 — PRIME BRIDGE (DEV LEVERAGE MODULE)
=====================================================================

Objective:
Introduce VAL PRIME as an optional local compute accelerator.

VAL0 (VPS):
- production assistant
- deterministic workflows
- legal execution
- reminders
- user interaction

VAL PRIME (Local machine / 4080 "Forge"):
- project monitoring
- nightly ingestion jobs
- transcript processing
- embeddings generation
- long-term memory consolidation

Operational Modes:

Prime Lite
- runs without GPU
- tracks roadmap progress
- monitors project drift
- generates developer briefings

Prime Forge
- GPU available
- speech-to-text
- embeddings
- clustering
- bug aggregation

Non-negotiables:

VAL0 must remain fully operational without PRIME.

PRIME may:
- generate summaries
- produce bug clusters
- propose memory entries
- generate development reports

PRIME may NOT:
- modify deterministic tables
- mutate legal deadlines
- alter reminders directly

Integration Model:

Prime → Export Packets → Val0

Export Packet v1 schema:

- packet_id
- chat_id / user scope
- sources[]
- facts[]
- summaries[]
- bug_reports[]
- open_questions[]

Val0 ingestion rules:

- packets stored in advisory tables only
- ingestion logged via audit_log
- no deterministic mutation allowed

Purpose:

Allow local compute acceleration without introducing system dependency.

=====================================================================
PHASE 1 — HARDENING (ACTIVE)
=====================================================================

Live:
- audit_log populated
- legal_audit_log present
- reminder dedupe enforced

Remaining:
- Reminder state audit timeline
- Merge audit table
- GCAL conflict surfacing
- Deadline normalization guardrails
- Founder rollback playbook

Hard rule:
No scope expansion that risks deterministic stability.

=====================================================================
PHASE 2 — DISCIPLINE AUTOMATION
=====================================================================

Remaining:
- Daily summary auto-push
- Overdue detection engine
- Escalation tagging
- Push toggles
- Timezone enforcement

=====================================================================
PHASE 2.5 — OPERATIONAL CONTROL LAYER
=====================================================================

Implemented:
- val0ctl ops
- DB integrity check
- Git dirty detection
- Service health verification

Planned:
- val0ctl doctor
- val0ctl fix reminders
- val0ctl fix gcal
- controlled dry-run repair tools

=====================================================================
PHASE 2.6 — MAINTENANCE HARNESS
=====================================================================

Observability layer:

- token spend metrics
- latency tracking
- correction capture
- weekly system snapshot

=====================================================================
PHASE 3 — CONTROLLED SYNC (OPTIONAL)
=====================================================================

Calendar event snapshot system.

=====================================================================
PHASE 4 — MIGUEL UX SIMPLIFICATION
=====================================================================

Goal:
Zero friction courtroom workflow.

=====================================================================
PHASE 5 — VOICE / PERSONALITY ARCHITECTURE
=====================================================================

Two-pass system.

1) Deterministic answer
2) Renderer layer

Renderer Contract:

Val0 produces a structured Response Pack containing:

- grounded_facts
- memory_refs
- actions_taken
- constraints
- risk_flags
- options
- next_questions
- tone_mode
- formatting

LLM Renderer Rules:

- May NOT introduce operational facts outside grounded_facts
- Must cite memory_refs when referencing stored data
- May add tone/personality only
- Must surface risk_flags explicitly

Purpose:
Maintain conversational voice without allowing hallucination to alter system truth.

=====================================================================
PHASE 6 — STANDALONE VAL INTERFACE
=====================================================================

Dedicated UI layer.

=====================================================================
PHASE 7 — CAPSULE NETWORK
=====================================================================

Future trust-circle vault sharing.

=====================================================================
LONG TERM ARCHITECTURE
=====================================================================

1. Encrypted storage
2. Deterministic engine
3. Merge layer
4. Memory spine
5. Scheduler
6. Ops CLI
7. Orchestration surface
8. Validator + advisory layer
9. Renderer layer
10. UI
11. Client E2EE

=====================================================================
WHAT WE WILL NOT DO
=====================================================================

No model-generated legal facts.
No silent DB mutation.
No uncontrolled feature creep.

=====================================================================
CURRENT PRIORITY
=====================================================================

1. Finish Phase 1 hardening
2. Phase 0.4 orchestration surface
3. Phase 2 automation
4. Ops doctor tooling
5. Hybrid voice/text stability

Revenue stability first.
Architecture second.
Ambition third.

=====================================================================
CHANGE CONTROL
=====================================================================

Every structural modification must:

1. Be reflected here
2. Be committed clearly
3. Preserve determinism
4. Be CLI-testable