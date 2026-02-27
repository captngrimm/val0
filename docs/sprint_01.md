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
- [x] 2-user cross isolation test (DM + group)
- [x] No leakage confirmed in logs
  - DM chat_id=1789350565 stored only DM secret
  - Group chat_id=-5109037524 stored only group secret
  - journalctl shows correct chat_id per message

STATUS: COMPLETE

---

## 5) Memory Spine (Minimal)
- [x] memory_entries table verified/created
- [x] Insert + recall test
- [x] Keyword recall works (alpha returns only DM row)
- [x] Date-range recall works (last 1 day returns both rows)

STATUS: COMPLETE

---

## 6) Launch package docs
- [ ] CLIENT_POLICY.md defined
- [ ] WISHLIST.md intake rules defined

STATUS: PENDING

---

SPRINT 01 = 5/6 SECTIONS COMPLETE

Remaining scope:
- Create launch docs (CLIENT_POLICY.md + WISHLIST.md)
No architectural debt added.
Core deterministic layer stable.
