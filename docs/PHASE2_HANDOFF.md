# VAL0 Phase 2 Handoff — Deterministic Summary Cache

## Purpose

This file exists to reduce drift during handoff between chats while implementing Phase 2.

Phase 2 goal is narrow and locked:

- add a persistent deterministic case summary cache layer
- keep `cases`, `case_events`, and `case_notes` as canonical
- do not change routing order
- do not move logic into LLM
- do not redesign architecture

---

## System identity

System root:

- `/opt/val0/`

Core runtime:

- Telegram-based legal assistant
- deterministic-first shell
- Spanish-first UX
- LLM is fallback only
- future LLM role = presentation / mouthpiece, NOT decision engine

---

## Canonical vs derived data

### Canonical (source of truth)

- `cases`
- `case_events`
- `case_notes`

### Derived (non-authoritative)

- `case_summaries` (Phase 2)

### Hard rules

- `case_summaries` must NEVER be treated as source of truth
- `case_summaries` must always be rebuildable from canonical tables
- if cache conflicts with canonical data, canonical data wins
- summary layer is cache/view only

---

## Protected pipeline contract

Protected function:

- `async def _process_text_pipeline(update, context, text)`

Routing order is intentional and must remain unchanged.

### Current protected order

1. slash bypass
2. undo gate
3. case disambiguation handler
4. pending reminder confirmation
5. pending term confirmation
6. deterministic reminder create/cancel gate
7. deterministic registration/note commands
8. natural reminder detection
9. natural term detection
10. natural note capture
11. deterministic case/report handlers
12. only then LLM fallback

### Do NOT

- reorder handlers
- merge reminder / term / note flows
- shortcut confirmation logic
- collapse disambiguation into one step
- move structured detection into the LLM

### Allowed

- post-write hooks only
- helper calls after successful writes only

---

## Detection vs write separation

### Detection phases (no write, no refresh)

- natural term detection
- natural reminder detection
- case disambiguation

These are suggestion-only stages.

### Write phases (write allowed, refresh allowed)

- confirmed term insert
- confirmed reminder insert
- confirmed note insert
- delete operations
- undo operations

Only successful canonical mutations may trigger summary refresh.

---

## Multi-case disambiguation model

In-memory pending state:

- `_PENDING_CASE_DISAMBIG`
- `_PENDING_TERM_CONFIRM`
- `_PENDING_REMINDER_CONFIRM`

### Rules

- system must not guess case
- user must confirm selection
- disambiguation must remain explicit
- no auto-resolution shortcuts

---

## In-memory state contract

### `_PENDING_CASE_DISAMBIG`

```python
{
  chat_id: {
    "type": "note" | "term" | "reminder",
    "candidates": [(case_id, client_name), ...],
    "payload": {...}
  }
}
_PENDING_TERM_CONFIRM
{
  chat_id: {
    "case_id": int,
    "client_name": str,
    "event_text": str,
    "deadline_date": "YYYY-MM-DD"
  }
}
_PENDING_REMINDER_CONFIRM
{
  chat_id: {
    "case_id": int,
    "client_name": str,
    "reminder_text": str,
    "due_date": "YYYY-MM-DD"
  }
}
_LAST_ACTION

Current reality:

single-step only
in-memory only
not persistent across restart

Phase 2 target shapes:

{"type": "note_insert", "id": note_id, "case_id": case_id}

{"type": "note_delete", "id": note_id, "note_text": str, "chat_id": int, "case_id": case_id, "source": "text"}

{"type": "term_insert", "id": event_id, "case_id": case_id}

{"type": "reminder_insert", "id": event_id, "case_id": case_id}
Undo contract
summary refresh must occur after successful undo
undo must not silently skip summary refresh
summary must reflect post-undo state immediately
Exact file anchors
/opt/val0/bot.py
async def _process_text_pipeline(update, context, text)
async def _maybe_capture_case_note(update, chat_id: int, text: str, source: str)

Known inline sections inside _process_text_pipeline(...):

# Case disambiguation handler
# Pending reminder confirmation
# Pending term confirmation
# NATURAL REMINDER DETECTION (suggestion only, no write)
# NATURAL TERM DETECTION (suggestion only, no write)

LLM fallback lives at bottom via:

call_val_openai(...)
/opt/val0/memory_store.py
def init_db()
def _get_conn()
def insert_case_note(...)
def insert_case_event(...)
def get_recent_messages(...)
def upsert_case(...)
def get_fact(...)
def get_all_facts(...)
def upsert_fact(...)
/opt/val0/core/case_mvp.py
def generate_case_cockpit(chat_id: int, case_id: str) -> str
async def try_delete_last_note(update, chat_id, text) -> bool
async def try_undo_last_action(update, chat_id, text) -> bool
async def try_case_status(update, chat_id, text) -> bool
Known schema / typing reality

This system is operationally mixed and must NOT be “cleaned up” during Phase 2.

### Observed identifier split

Notes / cockpit note access are expediente-oriented:
- `fetch_case_notes(chat_id, case_id)` uses:
  - `parent_ref = CASE:<case_id>`
  - fallback `case_notes.case_id = <case_id>`

Events access is often numeric-oriented:
- many `case_events` queries cast `case_id` with `int(case_id)`

Implication:
- Phase 2 summary refresh/build must tolerate both identity styles
- do not attempt full identifier normalization in Phase 2

Important reality

case_id usage is mixed across current flows:

insert_case_note(..., case_id: str, ...)
insert_case_event(..., case_id: int, ...)

There are also direct casts in live code:

some note queries use str(case_id)
some event queries use int(case_id)
Rule for Phase 2

Do NOT force a new universal type for case_id.

Instead:

preserve existing source-of-truth behavior
keep summary layer compatible with current practical usage
do not perform normalization cleanup in Phase 2
Existing runtime behavior observed from code
_maybe_capture_case_note(...)

Natural note capture:

blocks explicit commands / structured flows
requires non-trivial text
matches cases by client_name
uses explicit disambiguation when multiple matches exist
inserts into case_notes
currently writes _LAST_ACTION as {"type": "note_insert", "id": note_id}
Phase 2 must enrich that shape with case_id
Phase 2 must refresh summary after successful insert
_process_text_pipeline(...)

Confirmed write points relevant to Phase 2:

disambiguation branch for "type": "note"
pending reminder confirmation "yes"
pending term confirmation "yes"
deterministic case note command:
nota del caso <id>: <texto>

Phase 2 must add summary refresh after those successful writes.

The deterministic case note command currently inserts note but does not set _LAST_ACTION.
That is an existing consistency gap and should be fixed in Phase 2.

generate_case_cockpit(...)

Current cockpit already derives case summary-like information from canonical sources:

client name from cases by expediente
notes via fetch_case_notes(chat_id, case_id, limit=20)
reminder/task view from linked timeline using parent_ref = CASE:<case_id>
active dated events from case_events
health derived from note recency

Important:

cockpit currently works without case_summaries
summary cache must be additive only
cockpit must never depend on cache existence

Also note:

cockpit queries case_events using int(case_id)
cockpit queries cases using expediente = str(case_id)

This mixed behavior is real and must be respected during Phase 2.

try_undo_last_action(...)

Current undo supports:

note insert → delete inserted note
note delete → restore deleted note
term insert → delete inserted event
reminder insert → delete inserted event

Phase 2 must:

refresh summary after successful undo mutation
use enriched _LAST_ACTION["case_id"] to refresh without extra lookup
keep undo single-step and in-memory only
Event model constraints

case_events currently stores both:

terms
reminders

There is no strict normalized event type system yet.

Phase 2 rule

Summary builder must reuse existing semantics only.

Do NOT:

introduce a new classification system
refactor event schema
invent new reminder lifecycle states

Use only:

existing insert patterns
existing duplicate detection logic
existing reminder semantics already supported by the live system

open_reminders_count must be based only on currently supported deterministic semantics.

Phase 2 implementation target
New derived table
case_summaries

Effective key must be:

(chat_id, case_id)
Summary layer requirements

refresh_case_summary(chat_id, case_id) must be:

deterministic
idempotent
safe to call multiple times
side-effect free beyond cache write

It must NOT:

call LLM
mutate canonical tables
depend on external services
Preferred file split
/opt/val0/memory_store.py

Responsibilities:

schema addition for case_summaries
summary read/write helpers
canonical read helpers used by summary build
/opt/val0/core/case_summary.py

Responsibilities:

deterministic summary composition
refresh helper
optional lazy-get helper
Cockpit integration rule

generate_case_cockpit(...) must not depend on summary existence.

Allowed behavior:

read cached summary and append it
lazy-generate on miss
show fallback text if unavailable

System must never break due to missing summary row.

Do-not-touch list

The following must remain unchanged during Phase 2:

message routing order
insert_case_event semantics
insert_case_note semantics
duplicate detection rules
confirmation wording flows
disambiguation structure
deterministic-first architecture

Phase 2 is extension, not redesign.

Phase 2 success definition (locked)

Phase 2 is complete when:

note insert updates summary
term insert updates summary
reminder insert updates summary
undo updates summary
delete updates summary
cockpit can display summary
no pipeline changes were made
no LLM involvement was added

Anything beyond this is out of scope.

Current authoritative docs

Core authority:

/opt/val0/VAL0_CORE.md
/opt/val0/docs/ROADMAP.md
/opt/val0/docs/MEMORY_CONTRACT.md

Supporting state:

/opt/val0/docs/VAL0_STATE.md
Rules
these documents override assumptions
if implementation conflicts with them, implementation is wrong
do not reinterpret them casually
extend only if necessary and explicitly
Acceptance test checklist
Summary creation / refresh
create note → summary updates
create term → summary updates
create reminder → summary updates
delete last note → summary updates
undo note insert → summary updates
undo note delete → summary updates
undo term insert → summary updates
undo reminder insert → summary updates
Cockpit
cockpit works when summary row is missing
cockpit can display summary after refresh
cockpit does not treat summary as truth
Safety
no routing order changes
no LLM used for summary generation
no writes during suggestion-only detection
no source-of-truth mutation by summary layer
Next patch anchors still needed

Before exact replacement blocks are written, inspect or capture:

async def try_delete_last_note(...)
case read helpers in memory_store.py
any existing fetch helpers used by cockpit:
fetch_case_notes(...)
fetch_timeline_for_parent(...)

These affect exact Phase 2 patch placement.

