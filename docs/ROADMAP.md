=====================================================================
VAL0 — COGNITIVE OPERATIONS CORE
=====================================================================

Operational Roadmap  
Last Updated: 2026-03-02

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
- Schema verified: due_at_utc authoritative (stored UTC, displayed raw).

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

Pending:
- Daily 08:00 summary push
- Overdue escalation tagging
- Reminder state audit log (state-change timeline)
- Per-user timezone enforcement
- Local-time display normalization for reminder list

=====================================================================
PHASE 0.5 — MEMORY SPINE (ACTIVE)
=====================================================================

Baseline schema operational.

Live:
- case_notes (encrypted)
- chat_prefs (active_case_id, voice_enabled)
- memory_entries (deterministic advisory store)
- per-user vault isolation (chat_id partitioning)

Constraints:
- Advisory only
- Never auto-modifies deadlines
- Never overrides deterministic gates

Pending:
- Memory audit visibility in ops runner
- Memory health verification command (val0ctl doctor phase)

=====================================================================
PHASE 1 — HARDENING (ACTIVE)
=====================================================================

Live:
- audit_log table exists and is populated (IN/OUT/MODEL_CALL + reminder actions)
- legal_audit_log table present (legal tagging path)

Remaining:
- Structured legal audit tagging expansion (user-facing optional)
- Deadline normalization refinement
- Merge audit table (calendar)
- Explicit GCAL conflict surfacing (optional user-facing)
- Reminder state audit timeline (sent/cancelled/failed per reminder)

Hard rule:
No scope expansion that risks deterministic stability.

=====================================================================
PHASE 2 — DISCIPLINE AUTOMATION (ACTIVE)
=====================================================================

Status:
Reminder engine running stable.

Remaining:
- Daily summary auto-push
- Overdue detection engine
- Escalation tagging rules
- Push toggle per user
- Per-user timezone enforcement
- Reminder state audit log (state transitions)

Constraint:
No mutation outside deterministic rules.

=====================================================================
PHASE 2.5 — OPERATIONAL CONTROL LAYER (LIVE + EXPANDING)
=====================================================================

Implemented:
- val0ctl ops
- DB integrity check
- Git dirty detection
- Service health verification
- Scheduler verification

Planned:
- val0ctl doctor (full)
- val0ctl fix reminders
- val0ctl fix gcal
- Controlled auto-fix with dry-run mode
- Memory health diagnostics

Purpose:
Reduce manual ops drift.
Everything scriptable.
Everything verifiable.

=====================================================================
PHASE 2.6 — MAINTENANCE HARNESS (PLANNED)
=====================================================================

Objective:
Observability layer for reliability tracking.

Scope:
- Tool success rate metrics
- Token spend logging
- Workflow latency tracking
- User correction event capture
- Weekly snapshot review mode
- Metrics + repo snapshot (manual review only)

Constraints:
- No auto-deploy
- No self-modifying behavior
- Deterministic core untouched

=====================================================================
PHASE 3 — CONTROLLED SYNC (OPTIONAL)
=====================================================================

- Background sync job
- Snapshot Google events into case_events
- Preserve source metadata (gcal_event_id)
- Immutable audit record
- Conflict detection on modified events
- Deletion detection
- Sync enable flag

Never overwrite DB silently.

=====================================================================
PHASE 4 — MIGUEL UX SIMPLIFICATION
=====================================================================

Goal:
Zero-friction courtroom workflow.

- Standardized event title template
- Simple case-binding instruction sheet
- One-line quick entry format
- Voice-first case capture
- Auto-digit parsing for expediente numbers
- Hybrid response mode (text-first + voice)
- Voice transcription recall command

Deterministic core never altered.

=====================================================================
PHASE 5 — VOICE / PERSONALITY ARCHITECTURE
=====================================================================

Objective:
Two-pass system.

1) Deterministic factual answer.
2) Controlled Voice Renderer layer.

Layers:

1. Mode Router
2. Core Answer Engine (DB-first, tool-grounded)
3. Validator / Anti-Drift Gate
   - Blocks hallucination
   - Blocks therapy tone in legal mode
   - Blocks moralizing
   - Enforces answer-first

4. Strategic Challenge Layer (Founder Mode Only)

Purpose:
Pre-execution advisory review for major strategic proposals.

Triggers:
- Scope expansion
- Product pivots
- Architecture deviation
- Runway misalignment

Returns:
- GREEN (aligned)
- YELLOW (risk detected)
- RED (priority/runway violation)

Constraints:
- Advisory only
- No execution blocking
- No DB mutation
- No impact on legal workflow
- Founder Mode only

5. Voice Renderer (output only, no reasoning)
6. User Voice Profile Store
7. Safety Caps

Rule:
Personality is an output renderer, not a reasoning bias.

=====================================================================
PHASE 6 — STANDALONE VAL INTERFACE
=====================================================================

Precondition:
Operational layer deterministic + scriptable.

- Dedicated web UI
- Timeline visualization
- Vault viewer
- Activity log viewer
- Auth layer
- Multi-user support
- Preparation for client-side encryption

=====================================================================
PHASE 7 — CAPSULE NETWORK (FUTURE)
=====================================================================

- Opt-in trust circles
- Permission-based vault sharing
- Share-by-capsule only
- Zero implicit exposure

=====================================================================
LONG-TERM ARCHITECTURE
=====================================================================

Core stack:

1. Encrypted storage (SQLCipher)
2. Deterministic legal engine
3. Merge layer
4. Memory spine (advisory)
5. Scheduler layer
6. Ops control layer (CLI)
7. Validator + Strategic advisory layer
8. Personality renderer layer
9. UI layer
10. Future E2EE client layer

=====================================================================
WHAT WE WILL NOT DO
=====================================================================

- No auto-deleting deadlines.
- No model-generated legal facts.
- No hidden sync.
- No silent schema mutation.
- No admin backdoor into vault.
- No uncontrolled feature creep.
- No personality influencing legal determinism.
- No execution blocking without Founder authorization.

=====================================================================
CURRENT PRIORITY
=====================================================================

1. Finish Phase 1 hardening.
2. Expand audit visibility (state transitions, merge audit).
3. Complete Phase 2 automation (daily + overdue).
4. Expand ops runner into structured doctor.
5. Stabilize hybrid voice/text UX.
6. Begin controlled Personality Renderer implementation.
7. Do not expand UI prematurely.

Revenue stability first.
Architecture second.
Ambition third.

=====================================================================
CHANGE CONTROL
=====================================================================

Every structural modification must:

1. Be reflected here.
2. Be committed clearly.
3. Preserve determinism.
4. Be testable via CLI.

END OF ROADMAP