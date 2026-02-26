# WBS.md
Work Breakdown Structure (WBS)
Last Updated: 2026-02-23

Purpose:
- Convert ROADMAP into executable tasks.
- Prevent drift and “random feature creep”.
- Make torchpassing stable (tasks + definitions stay on VPS, not in chat).

Rules:
- Roadmap = vision.
- WBS = full task universe.
- Sprint = only what we do now.
- No new features added mid-sprint unless it’s a bugfix or a security issue.

---

## A) CORE STABILITY (ALL USERS)
### A1. Service reliability
- [ ] Bot starts clean with zero NameError risks
- [ ] systemd restart loop protections verified
- [ ] journalctl shows Scheduler started + no crash loop

### A2. SQLCipher DB integrity
- [ ] DB opens with key file
- [ ] integrity_check = ok
- [ ] no accidental DB commits (gitignore enforced)

### A3. Reminder Runner
- [ ] fetch_due_reminders stable
- [ ] claim/mark/revert logic stable
- [ ] at least 3 test reminders delivered reliably

### A4. Ops CLI (val0ctl ops)
- [ ] Reports: service, db path, cipher_version, integrity, reminders stats
- [ ] Reports: dirty repo status + top offenders
- [ ] Includes python syntax check gate

---

## B) MEMORY PERSISTENTE (PME / Motor de Memoria Persistente)
Goal: “Remember what matters” without breaking determinism.

### B1. Memory spine minimal
- [ ] memory_entries table
- [ ] memory_domains table
- [ ] idea_inbox table
- [ ] trigger policy enforced (HIT rules)

### B2. Commands
- [ ] /sremember (store)
- [ ] /ssearch (recall by keyword)
- [ ] time-range recall command (optional)

---

## C) MIGUEL MVP (LOW-FRICTION INTAKE)
Goal: “I got this case — log it and go.”

- [ ] Case binding format (CASE:<id>) enforcement
- [ ] One-line entry format (define)
- [ ] Deadline normalization
- [ ] Deterministic logging tags for audit

---

## D) LAUNCH PACK (5 FRIENDS + MIGUEL)
- [ ] Client policy: Month 1 = bugs + stability only
- [ ] Simple onboarding message template
- [ ] Basic package definition (what $30 includes)
- [ ] Wishlist intake template

---

# END