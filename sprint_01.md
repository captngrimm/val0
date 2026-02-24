# SPRINT_01.md
SPRINT 01 — Stability + Launchable Basic
Dates: 2026-02-23 to 2026-03-01
Assumption: 10 hours/day average

Definition of Done:
- Bot runs 24h without crash loops.
- Reminders send reliably.
- Ops report green (git dirty explainable).
- 5-user isolation confirmed.
- Basic $30 package operational.

---

## 1) Service reliability hardening
- [ ] Remove/disable undefined handlers
- [ ] Clean restart via systemctl
- [ ] Scheduler confirmed running in logs

## 2) Reminder Runner stability
- [ ] Insert 3 due reminders → 3 delivered
- [ ] No stuck "sending" rows
- [ ] due_now returns 0 post-delivery

## 3) Ops visibility
- [ ] val0ctl ops prints:
  - service active
  - DB path + key file
  - cipher_version + integrity_check
  - reminder stats
  - git status summary
  - python compile pass

## 4) Multi-user isolation sanity
- [ ] Create 2 test users
- [ ] Cross-user reminder test
- [ ] No leakage
- [ ] Logs identify user_id

## 5) Memory Spine (Minimal)
- [ ] memory_entries table verified
- [ ] Insert + recall test
- [ ] Keyword recall works
- [ ] Date-range recall works

## 6) Launch package docs
- [ ] CLIENT_POLICY.md defined
- [ ] WISHLIST.md intake rules defined

---

## Not In This Sprint
- Voice cloning
- UI overhaul
- Calendar snapshot sync
- Advanced analytics
- Jarvis automation