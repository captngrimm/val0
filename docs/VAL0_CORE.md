# VAL0 CORE MANUAL

This is the authoritative reference for how Val0 works.
It exists to preserve **intent, guarantees, and recovery paths**.
**Chat history is not a source of truth.**

---

## 0) Authority Order (no drift)
If anything conflicts, the authority order is:

1) `VAL0_CORE.md` (THIS FILE) — intent + guarantees  
2) `docs/VAL0_STATE.md` — current runtime state + known limits  
3) `docs/*HANDOVER*.md` — deployment/recovery steps  
4) Code — implementation detail (must conform to this file)

If code behavior violates this file, the code is wrong.

---

## 1) System Model (Deterministic First)

Val0 is a **deterministic-first system**.

Execution model:

1. Input is processed through a **deterministic pipeline**
2. Structured actions are handled by:
   - detection logic (terms, reminders, notes)
   - confirmation flows
   - handler registry
3. Only if no deterministic path handles the input:
   → LLM is used as a **final-stage mouthpiece**

### LLM Role (Strictly Limited)
The LLM:
- does NOT write to memory
- does NOT decide system actions
- does NOT modify state
- is used only to generate natural language responses

If a structured action was expected but not handled:
→ system must **fail explicitly**, not fall back silently to LLM

---

## 2) Non-Negotiable Guarantees (Promise-Safe)

Val0 MUST:

- Prefer **truth over helpfulness** when uncertain.
- Say **“I don’t know / not available / not implemented”** rather than invent.
- Keep behavior **consistent across restarts** (via explicit docs + data).
- Keep the system **auditable**: explain *what source* a claim came from:
  - (a) user message in this chat
  - (b) stored memory (facts/notes/dailies)
  - (c) user-provided document(s)
  - (d) external API result (explicitly labeled)

Val0 MUST NOT:
- Pretend it did something it didn’t do.
- Claim a feature exists unless it is implemented and verified.

---

## 3) Core Data Model (Source of Truth vs Derived)

### Source-of-truth tables
These define reality:

- `cases`
- `case_events`
- `case_notes`

These must NEVER be replaced or bypassed.

### Derived layer (Phase 2)
Val0 includes a **cache layer**:

- `case_summaries`

Properties:

- keyed by `(chat_id, case_id)`
- fully rebuildable from source tables
- NOT canonical
- NOT authoritative
- used for:
  - fast cockpit rendering
  - future LLM context packaging

### Update rules

`case_summaries` is refreshed ONLY after:

- successful `insert_case_event`
- successful `insert_case_note`
- successful undo/delete operations affecting those

It must NEVER be written during:
- detection phase
- suggestion phase
- disambiguation phase

---

## 4) Multi-Tenant Model (chat_id vs case_id)

Val0 is multi-tenant by design:

- `chat_id` = tenant / user
- `case_id` = unit of work (case, deal, project, etc.)

Rules:

- All reads and writes MUST be scoped by `chat_id`
- No cross-tenant leakage is allowed
- Same client name across tenants must remain isolated

This enables Val0 to operate across professions:
- legal
- logistics
- operations
- personal tracking

---

## 5) In-Memory State Contract

The system uses in-memory coordination state:

- `_PENDING_CASE_DISAMBIG`
- `_PENDING_TERM_CONFIRM`
- `_PENDING_REMINDER_CONFIRM`
- `_LAST_ACTION`

### `_LAST_ACTION` contract

All write operations MUST register:

```python
{"type": "...", "id": ..., "case_id": ...}

Supported types:

note_insert
note_delete
term_insert
reminder_insert

Rules:

single-step undo only
state is ephemeral (does not survive restart)
undo must trigger summary refresh
6) Privacy Model (Trust First)

Each user’s Val0 instance (their S.O.U.L.) is private by default.

No admin/operator access by default
No silent exposure via logs or dashboards
Debugging must use redacted data unless user opts in

Any access must be:

explicit
scoped
revocable
7) Memory Rules (Structured Only)

Memory is explicit and typed:

Recent context (short window)
Facts (structured key/value)
Notes (user-saved)
Dailies (summaries)
Critical rule

Val0 does NOT:

auto-store everything
infer long-term memory silently

Memory writes require:

explicit command
explicit instruction
documented system rule
8) Time & Awareness
Timezone must be known or explicitly assumed
Relative dates must resolve deterministically
Reminders must confirm interpretation when ambiguous
9) Pipeline Protection Rules (DO NOT TOUCH)

The following must NOT be altered:

_process_text_pipeline routing order
deterministic detection before LLM fallback
confirmation flows (term/reminder/note)
disambiguation behavior
insert semantics for:
case_events
case_notes

LLM must remain:

last-stage only
non-mutating
non-authoritative
10) Recovery & Source of Truth

System must be reconstructible from:

this file
VAL0_STATE.md
database contents
minimal run instructions

Chat history is disposable.

11) UX Tone Requirements

Val0 is:

tactical
direct
minimal
Spanish-first unless overridden

Avoids:

filler
generic AI tone
unnecessary questions
12) Change Control (Anti-Drift)

Any change affecting:

memory model
privacy
routing
data structures
cross-user behavior

must be defined here FIRST.

If it’s not written here, it is not real.