# VAL0 — Legal Ops Core  
Operational Roadmap  
Last Updated: 2026-02-23

---

# CURRENT STATE (Verified Live)

## VERIFIED EVIDENCE (Deterministic CLI)

Primary control surface:
```
val0ctl ops
```

Confirms:
- Service state
- SQLCipher open
- DB integrity_check
- Reminder counts
- Scheduler running
- Git clean/dirty status
- Syntax compilation check

Systemd status:
```
sudo systemctl status val0-bot.service
```

GCAL smoke:
```
python3 /opt/val0/gcal_smoke.py
python3 /opt/val0/gcal_events_smoke.py
```

---

## MVP 1.1 — Deterministic Legal Gates (LIVE)

- Case summary gate (DB-backed, deterministic)
- Due today gate (DB deadlines only)
- Due range gate (DB deadlines only)
- SQLCipher encrypted database
- Short-circuit pipeline confirmed
- No LLM involvement in legal gates
- DB integrity_check enforced via ops runner

---

## MVP 1.2 — Google Calendar Merge (Events Only) (LIVE)

- Feature flag: VAL0_GCAL_ENABLED
- Timezone control: VAL0_TZ
- Deterministic merge layer (DB + GCAL)
- Events-only
- OAuth token isolated under /etc/val0/gcal
- Merge performed at query-time
- No DB mutation
- No LLM involvement

---

## MVP 1.3 — Operational Discipline Layer (PARTIAL LIVE)

- Reminder runner (APScheduler) running
- Deterministic tick logging
- Encrypted reminder storage
- CLI-based reminder injection testable
- Scheduler health visible in ops runner
- No auto-modifying legal records

Pending:
- Daily 08:00 summary push
- Overdue escalation tagging
- Per-user timezone enforcement

---

# DESIGN PRINCIPLES (Locked)

1. Determinism first.
2. Database is source of truth.
3. Calendar is supplemental.
4. No silent mutation.
5. Every automation auditable.
6. Feature flags gate risk.
7. Memory advisory only.
8. Privacy is product.
9. No architectural drift.
10. Operational state must be CLI-verifiable.

---

# PHASE 0 — Trust Model Definition

Telegram Phase:
- SQLCipher at rest
- No analytics resale
- No model training reuse
- Server processes plaintext during execution only

Standalone Phase:
- Client-side encryption
- Zero-knowledge vault
- User key authority
- No server decryption capability

---

# PHASE 0.5 — Memory Spine (IN PROGRESS)

Baseline schema accepted.

Constraints:
- Advisory only.
- Never auto-modifies deadlines.

Components:
- memory_entries
- memory_domains
- idea_inbox
- Interaction logging
- Domain tagging (manual first)
- Recall by keyword
- Recall by time-range
- Per-user vault isolation
- SQLCipher preserved

Next step:
- Minimal deterministic recall CLI test
- Audit visibility in ops runner

---

# PHASE 1 — Deterministic Core Hardening (ACTIVE)

Remaining tasks:

- [ ] Strict CASE:<id> enforcement
- [ ] Disable unbound GCAL events by default
- [ ] Conflict detection (DB vs GCAL duplicate)
- [ ] Merge dedupe log improvement
- [ ] Internal audit log table
- [ ] Structured legal audit log tags
- [ ] Deadline normalization rules

Hard rule:
No new expansion until audit logging exists.

---

# PHASE 2 — Discipline Automation (ACTIVE)

Status:
Reminder engine running.

Remaining:

- [ ] Daily summary auto-push
- [ ] Overdue detection engine
- [ ] Escalation tagging rules
- [ ] Push toggle per user
- [ ] Per-user timezone enforcement
- [ ] Reminder state audit log

---

# PHASE 2.5 — Operational Control Layer (NEW)

Goal: Reduce manual ops drift.

Implemented:
- val0ctl ops
- DB integrity check
- Git dirty detection
- Service health verification
- Scheduler verification

Planned:
- val0ctl fix reminders
- val0ctl fix gcal
- val0ctl doctor full
- Controlled auto-fix with dry-run mode

This is foundation for future controlled automation.

---

# PHASE 3 — Controlled Sync (Optional)

- Background sync job
- Snapshot Google events into case_events
- Preserve source metadata (gcal_event_id)
- Immutable audit record
- Conflict detection on modified events
- Deletion detection
- Sync enable flag

Never overwrite DB silently.

---

# PHASE 4 — Miguel UX Simplification

- Standardized event title template
- Simple case-binding instruction sheet
- One-line quick entry format
- Emoji priority tagging (optional)
- Syntax friction reduction

---

# PHASE 5 — Operational Expansion

Frozen until Phase 1 + Phase 2 stable.

- Google Tasks evaluation
- Multi-calendar support
- Role-based filtering
- Case status classification
- Structured deadline categories
- PDF export
- Read-only web dashboard

---

# PHASE 6 — Standalone VAL Interface

Precondition:
Operational control layer must be deterministic and scriptable.

- Dedicated web UI
- Timeline visualization
- Vault viewer
- Activity log viewer
- Auth layer
- Multi-user support
- Preparation for end-to-end encryption rollout

---

# PHASE 7 — Capsule Network (Future)

- Opt-in trust circles
- Explicit permission-based vault sharing
- Share-by-capsule model only
- Zero implicit data exposure

---

# LONG-TERM ARCHITECTURE

Core Layers:

1. Encrypted storage
2. Deterministic legal engine
3. Merge layer
4. Memory spine (advisory)
5. Scheduler layer
6. Ops control layer (CLI)
7. UI layer
8. Optional narrative layer (never authoritative)
9. Future E2EE client layer

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
2. Add audit log table.
3. Complete Phase 2 automation (overdue + summary).
4. Expand ops runner into structured doctor.
5. Do not expand UI.
6. Do not add features unrelated to determinism.

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