VAL0 — LEGAL OPS CORE
Operational Roadmap
Last Updated: 2026-02-27

=====================================================================
CURRENT STATE (VERIFIED LIVE)
=====================================================================

Deterministic legal engine operational.
Encrypted storage active (SQLCipher).
Google Calendar merge hardened and gated.
Reminder engine stable and verified.
Voice ingestion + case note capture live.
Semantic recall operational (advisory only).
Ops CLI control surface active.

Reminder Runner:
- 3/3 due reminders delivered live (chat_id verified).
- Blocked-user path marks reminder failed without crash.
- No stuck "sending" rows.
- due_now returns 0 after delivery.
- APScheduler stable across restart.
- Schema verified: due_at_utc authoritative.

Isolation:
- DM + group chat isolation verified (distinct chat_id storage, no leakage in logs).

Memory Spine (Minimal):
- memory_entries table present.
- Insert verified.
- Keyword recall verified.
- Date-range recall verified.

No LLM involvement in legal gates.
No silent DB mutation.
All merge logic is query-time only.
All automation auditable via logs.

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

- Reminder runner (APScheduler stable)
- Deterministic tick logging
- Encrypted reminder storage
- CLI injection testable
- Scheduler health visible via ops
- Blocked-user handling hardened (marks failed, no crash)
- No stuck pending states post-send
- case_notes table live
- Active case binding per user
- Voice-to-note ingestion (text + voice)

Pending:
- Daily 08:00 summary push
- Overdue escalation tagging
- Reminder audit table
- Per-user timezone enforcement

=====================================================================
PHASE 0.5 — MEMORY SPINE (ACTIVE)
=====================================================================

Baseline schema operational.

Live:
- case_notes (encrypted)
- chat_prefs (active_case_id, voice_enabled)
- memory_entries (minimal deterministic store)
- per-user vault isolation (chat_id partitioning)

Verified:
- Deterministic insert works.
- Keyword recall works.
- Date-range recall works.

Constraints:
- Advisory only
- Never auto-modifies deadlines
- Never overrides deterministic gates

Pending:
- Memory audit visibility in ops runner
- Memory health verification command (val0ctl doctor phase)

=====================================================================
PHASE 1 — HARDENING (NEAR COMPLETE)
=====================================================================

Remaining:
- Internal audit_log table
- Structured legal audit tagging
- Deadline normalization refinement
- Merge audit table
- Explicit GCAL conflict surfacing (user-facing optional)

Hard rule:
No new expansion until audit logging exists.

=====================================================================
PHASE 2 — DISCIPLINE AUTOMATION (ACTIVE)
=====================================================================

Status:
Reminder engine running.

Remaining:
- Daily summary auto-push
- Overdue detection engine
- Escalation tagging rules
- Push toggle per user
- Per-user timezone enforcement
- Reminder state audit log

=====================================================================
PHASE 2.5 — OPERATIONAL CONTROL LAYER
=====================================================================

Implemented:
- val0ctl ops
- DB integrity check
- Git dirty detection
- Service health verification
- Scheduler verification

Planned:
- val0ctl doctor full
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
- No recursive automation
- Deterministic core untouched

Rule:ssh val0
Observability only. Never mutation.

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

- Standardized event title template
- Simple case-binding instruction sheet
- One-line quick entry format
- Voice-first case capture
- Auto-digit parsing for expediente numbers
- Hybrid response mode (text-first + voice)
- Voice transcription recall command

Goal:
Zero-friction courtroom workflow.

=====================================================================
PHASE 5 — VOICE / PERSONALITY ARCHITECTURE (NEW)
=====================================================================

Objective:
Two-pass system.
1) Deterministic factual answer.
2) Controlled Voice Renderer layer.

Layers:

1. Mode Router
   - Context classifier (legal/admin/personal)
   - Risk detection
   - Tone envelope selection

2. Core Answer Engine
   - Tool-grounded
   - DB-first
   - Deterministic
   - No personality influence

3. Validator / Anti-Drift Gate
   - Blocks hallucination
   - Blocks therapy tone in legal mode
   - Blocks lecturing
   - Blocks moralizing
   - Enforces answer-first

4. Voice Renderer
   - Adds cadence
   - Adds sass (bounded)
   - Adds formatting
   - No new facts allowed

5. User Voice Profile Store
   - Per-user sharpness level
   - Brevity level
   - Emoji tolerance
   - Therapy-mode allowance
   - Legal strictness override

6. Safety Caps
   - Hard sass density limit
   - Auto-suppress personality in high-risk contexts
   - Kill-switch per user

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
7. Personality renderer layer
8. UI layer
9. Future E2EE client layer

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

=====================================================================
CURRENT PRIORITY
=====================================================================

1. Finish Phase 1 hardening.
2. Add audit_log table.
3. Complete Phase 2 automation.
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
