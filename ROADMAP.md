# VAL0 — Legal Ops Core
Operational Roadmap
Last Updated: 2026-02-22

---

# CURRENT STATE (Verified Live)

## MVP 1.1 — Deterministic Legal Gates
- Case summary gate (DB-backed, deterministic)
- Due today gate (DB deadlines only)
- Due range gate (DB deadlines only)
- SQLCipher encrypted database
- Short-circuit pipeline confirmed
- No LLM involvement in legal gates

## MVP 1.2 — Google Calendar Merge (Events Only)
- Feature flag: VAL0_GCAL_ENABLED
- Timezone control: VAL0_TZ
- Deterministic merge layer (DB + Google Calendar)
- Events-only (no Tasks yet)
- No secrets stored in repo
- OAuth refresh token stored under /etc/val0/gcal
- Merge performed at query-time (no DB mutation)
- Short-circuit preserved
- No LLM involvement

---

# DESIGN PRINCIPLES

1. Determinism first.
2. Database is source of truth.
3. Calendar is a supplemental signal, not authority.
4. No silent data mutation.
5. Every automation must be auditable.
6. Feature flags control risk.
7. No architectural drift.

---

# PHASE 1 — Hardening the Deterministic Core

Goal: Make deadline system bulletproof.

- [ ] Enforce strict case binding pattern (CASE:<id> or VAL0_CASE_ID=<id>)
- [ ] Disable unbound GCAL events by default
- [ ] Add conflict detection (DB vs GCAL duplicate)
- [ ] Improve dedupe logic logging
- [ ] Add internal audit log for merged results
- [ ] Add structured log tags for legal audit mode
- [ ] Improve deadline formatting consistency

---

# PHASE 2 — Discipline Layer

Goal: Move from reactive to proactive.

- [ ] Reminder runner (daily scheduler)
- [ ] 08:00 daily summary auto-push
- [ ] Overdue detection
- [ ] Escalation tagging (⚠️ overdue > X days)
- [ ] Optional Telegram push notifications toggle
- [ ] Per-user timezone handling

---

# PHASE 3 — Controlled Sync (Optional)

Goal: Snapshot GCAL into DB with audit trail.

- [ ] Optional background sync job
- [ ] Snapshot Google events into case_events table
- [ ] Preserve source metadata (gcal_event_id)
- [ ] Immutable audit record of sync time
- [ ] Conflict detection on modified events
- [ ] Deletion detection handling
- [ ] Sync enable flag

Note:
This phase must NOT overwrite DB entries silently.

---

# PHASE 4 — Miguel UX Simplification

Goal: Make it usable for non-technical legal operators.

- [ ] Standardized event title template
- [ ] Simple case-binding instruction sheet
- [ ] One-line quick entry format
- [ ] Minimal friction workflow
- [ ] Optional emoji coding for priority
- [ ] Reduce need for structured syntax

---

# PHASE 5 — Operational Expansion

Goal: Expand capability without breaking core.

- [ ] Google Tasks integration (if justified)
- [ ] Multi-calendar support
- [ ] Role-based deadline filtering
- [ ] Case status classification
- [ ] Structured deadline categories
- [ ] Export to PDF summary
- [ ] Web dashboard (read-only first)

---

# PHASE 6 — Standalone VAL Interface

Goal: Move beyond Telegram.

- [ ] Dedicated web UI
- [ ] Timeline visualization
- [ ] Case dashboard view
- [ ] Deadline heatmap
- [ ] Conflict alerts
- [ ] Activity log viewer
- [ ] Auth layer (multi-user support)

---

# LONG-TERM ARCHITECTURE

Core Layers:

1. Storage (SQLCipher DB)
2. Deterministic logic gates
3. Merge layer (optional external signals)
4. Scheduler / discipline layer
5. UI layer
6. Optional LLM narrative layer (never authoritative)

---

# WHAT WE WILL NOT DO

- No auto-deleting deadlines from DB.
- No model-generated legal data.
- No hidden sync.
- No silent schema mutation.
- No uncontrolled feature creep.

---

# CURRENT PRIORITY

Focus: Phase 1 hardening.

Do NOT expand surface area until:
- Logging is stable.
- Merge logic is fully predictable.
- Audit integrity is validated.

---

# CHANGE CONTROL

Every structural modification must:
1. Be reflected in this file.
2. Be committed with a clear message.
3. Preserve determinism.
4. Be testable via CLI.

---

END OF ROADMAP

