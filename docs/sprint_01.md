SPRINT 01 — Stability + Launchable Basic
Dates: 2026-02-23 to 2026-02-27
Actual Duration: 4 days

Definition of Done:
- Bot runs 24h without crash loops.
- Reminders send reliably.
- Ops report green.
- 5-user isolation confirmed.
- Basic $30 package operational.

---

## 1) Service reliability hardening
- [x] Undefined handlers removed
- [x] Clean restart via systemctl verified
- [x] Scheduler confirmed running in logs
- [x] No crash loop after reminder exceptions

STATUS: COMPLETE

---

## 2) Reminder Runner stability
- [x] Insert 3 due reminders → 3 delivered
- [x] Blocked-user path marks failed
- [x] No stuck "sending" rows
- [x] due_now returns 0 post-delivery
- [x] Schema verified (due_at_utc authoritative)

STATUS: COMPLETE

---

## 3) Ops visibility
- [x] val0ctl ops shows service active
- [x] DB path + SQLCipher active
- [x] reminder stats visible
- [x] scheduler health visible
- [x] python compile passes
- [x] git dirty detection active

STATUS: COMPLETE

---

## 4) Multi-user isolation sanity
- [ ] 2-user cross isolation test
- [ ] No leakage confirmed in logs

STATUS: PENDING

---

## 5) Memory Spine (Minimal)
- [ ] memory_entries table verified
- [ ] Insert + recall test
- [ ] Keyword recall works
- [ ] Date-range recall works

STATUS: PENDING

---

## 6) Launch package docs
- [ ] CLIENT_POLICY.md defined
- [ ] WISHLIST.md intake rules defined

STATUS: PENDING

---

SPRINT 01 = 60–70% COMPLETE

Remaining scope small and well defined.
No architectural debt added.
Core deterministic layer stable.