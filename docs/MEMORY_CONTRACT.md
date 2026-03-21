# MEMORY CONTRACT — VAL0

## Purpose

Val0 memory exists to preserve **structured user work and state across time**.

It is:
- explicit
- auditable
- deterministic

It is NOT:
- an autonomous reasoning system
- a hidden learning layer
- a place for implicit inference

---

## 1) Memory Model (Two Layers)

Val0 memory is split into:

### A. Source of Truth (Canonical)

These define reality:

- `cases`
- `case_events`
- `case_notes`
- `facts` (key/value user data)

Properties:

- authoritative
- directly written by system actions
- must never be overwritten by derived logic
- must remain simple and auditable

---

### B. Derived Memory (Cache Layer — Phase 2)

- `case_summaries`

Properties:

- derived from canonical tables
- rebuildable at any time
- not authoritative
- used for:
  - fast display (cockpit)
  - future LLM context packaging

---

## 2) Memory Write Rules

Memory writes ONLY occur through:

- explicit user commands
- deterministic system actions:
  - note insert
  - term insert
  - reminder insert
  - undo / delete operations

Val0 MUST NOT:

- silently store arbitrary user messages
- infer long-term memory without instruction
- write memory through LLM output

---

## 3) Memory Read Rules

All memory reads must be:

- scoped by `chat_id` (tenant isolation)
- tied to a known entity (`case_id`, fact key, etc.)

Val0 must be able to answer:

> “Where did this come from?”

Valid answers:

- case_event
- case_note
- fact
- user input

Never:

- “I assumed”
- “It seemed like”

---

## 4) Case Summary Layer (Phase 2)

### Purpose

Provide a **fast, deterministic snapshot** of a case.

### Structure

Table:

- `case_summaries(chat_id, case_id)`

Contains:

- summary_text
- next_deadline
- open_reminders_count
- last_event_at
- last_note_at
- last_summary_refresh

### Rules

- MUST NOT replace source tables
- MUST NOT be edited manually
- MUST be regenerated from canonical data

### Refresh triggers

Summary is refreshed ONLY after:

- successful event insert
- successful note insert
- successful undo/delete affecting those

Summary MUST NOT be updated during:

- detection phase
- suggestion phase
- disambiguation

---

## 5) No Inference Rule

Val0 does NOT:

- infer facts from conversation
- “learn patterns”
- store implied preferences

All memory must be:

- explicit
- traceable
- reversible

---

## 6) Deletion & Reversibility

Val0 must support:

- deleting notes
- deleting events (via undo or command)
- updating facts

Derived memory (`case_summaries`) must:

- update automatically after deletion
- never become stale source-of-truth

---

## 7) Multi-Tenant Isolation

All memory is scoped by:

- `chat_id`

Rules:

- no cross-user reads
- no shared memory unless explicitly designed later
- same names across users must not collide

---

## 8) What Memory is NOT

Memory is NOT:

- a vector database (in Phase 2)
- an LLM context store
- a reasoning engine
- a background learning system

LLM usage is separate and must consume memory, not define it.

---

## 9) Simplicity Rule

If memory behavior cannot be:

- explained clearly
- traced to a table
- reversed safely

→ it does not belong in the system