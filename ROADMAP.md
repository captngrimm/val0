# VAL0 — Legal Ops Core
Operational Roadmap
Last Updated: 2026-02-22

---

# CURRENT STATE (Verified Live)

## VERIFIED EVIDENCE (How to re-check fast)
- Service env:
  sudo systemctl show val0-bot.service -p Environment --no-pager | tr ' ' '\n' | egrep 'VAL0_(GCAL|TZ|DB_)'
- Bot logs (gates firing):
  sudo journalctl -u val0-bot.service -n 80 --no-pager | egrep "\[GATE\]|HIT|CASE MVP"
- GCAL connectivity (direct):
  python3 /opt/val0/gcal_smoke.py
  python3 /opt/val0/gcal_events_smoke.py

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
3. Calendar is supplemental, never authoritative.
4. No silent data mutation.
5. Every automation must be auditable.
6. Feature flags control risk.
7. Memory must never override legal determinism.
8. Privacy is product.
9. No architectural drift.

---

# PHASE 0 — Trust Model Definition (NEW)

Goal: Define privacy architecture before expansion.

Telegram Phase:
- Encrypted storage (SQLCipher at rest)
- No human review of user conversations
- No analytics resale
- No model training reuse
- Server processes plaintext during execution

Standalone Phase (Future):
- End-to-end encryption (client-side encryption)
- Zero-knowledge vault design
- Server cannot decrypt vault contents
- User-controlled key model
- Optional recovery mechanism

This phase defines long-term trust contract.

---

# PHASE 0.5 — User Memory Spine (Foundation Layer)

Goal: Structured long-term recall without breaking determinism.

- memory_entries table
- memory_domains table
- idea_inbox table
- automatic interaction logging
- manual domain tagging first (LLM inference later)
- keyword recall command
- time-range recall command
- per-user vault isolation
- encryption preserved (SQLCipher)

Important:
Memory layer is advisory.
It never modifies legal deadlines automatically.

---

# PHASE 1 — Hardening the Deterministic Core

Goal: Make deadline system bulletproof.

- [ ] Enforce strict case binding pattern (CASE:<id>)
- [ ] Disable unbound GCAL events by default
- [ ] Add conflict detection (DB vs GCAL duplicate)
- [ ] Improve dedupe logic logging
- [ ] Add internal audit log for merged results
- [ ] Structured log tags for legal audit mode
- [ ] Deadline formatting normalization

No expansion until stable.

---

# PHASE 2 — Discipline Layer

Goal: Move from reactive to proactive.

- [ ] Reminder runner (daily scheduler)
- [ ] 08:00 daily summary auto-push
- [ ] Overdue detection
- [ ] Escalation tagging (⚠ overdue > X days)
- [ ] Optional push notification toggle
- [ ] Per-user timezone handling

---

# PHASE 3 — Controlled Sync (Optional)

Goal: Snapshot GCAL into DB with audit trail.

- [ ] Background sync job
- [ ] Snapshot Google events into case_events
- [ ] Preserve source metadata (gcal_event_id)
- [ ] Immutable audit record
- [ ] Conflict detection on modified events
- [ ] Deletion detection
- [ ] Sync enable flag

Never overwrite DB silently.

---

# PHASE 4 — Miguel UX Simplification

Goal: Make it usable for non-technical operators.

- [ ] Standardized event title template
- [ ] Simple case-binding instruction sheet
- [ ] One-line quick entry format
- [ ] Emoji priority tagging (optional)
- [ ] Syntax friction reduction

---

# PHASE 5 — Operational Expansion

Goal: Expand capability without breaking core.

- [ ] Google Tasks evaluation (only if justified)
- [ ] Multi-calendar support
- [ ] Role-based filtering
- [ ] Case status classification
- [ ] Structured deadline categories
- [ ] PDF export
- [ ] Read-only web dashboard

---

# PHASE 6 — Standalone VAL Interface

Goal: Move beyond Telegram.

- Dedicated web UI
- Timeline visualization
- Vault viewer
- Activity log viewer
- Auth layer
- Multi-user support
- Preparation for end-to-end encryption rollout

---

# PHASE 7 — Capsule Network (Future)

Goal: Controlled cross-user collaboration.

- Opt-in trust circles
- Explicit permission-based vault sharing
- No automatic cross-access
- Share-by-capsule model only
- Zero implicit data exposure

---

# LONG-TERM ARCHITECTURE

Core Layers:

1. Storage (Encrypted DB)
2. Deterministic legal engine
3. Merge layer
4. Memory spine
5. Scheduler / discipline layer
6. UI layer
7. Optional LLM narrative layer (never authoritative)
8. Future E2EE client layer

---

# WHAT WE WILL NOT DO

- No auto-deleting deadlines.
- No model-generated legal facts.
- No hidden sync.
- No silent schema mutation.
- No admin backdoor into vault (post-E2EE).
- No uncontrolled feature creep.

---

# CURRENT PRIORITY

1. Finish Phase 1 hardening.
2. Implement Phase 0.5 memory spine (minimal version).
3. Do not expand surface area further.

Revenue stability first.
Architecture second.
Ambition third.

---

# CHANGE CONTROL

Every structural modification must:
1. Be reflected here.
2. Be committed clearly.
3. Preserve determinism.
4. Be testable via CLI.

---

END OF ROADMAP