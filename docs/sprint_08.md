# Sprint 08 — Live Case Event Creation Wiring

Updated: 2026-03-07

## Goal

Wire the live message-processing path to create real `case_events`
through `memory_store.insert_case_event()`.

This sprint reconnects the bridge between:

- user text input
- active case detection
- deadline phrase detection
- persistent case event storage

The objective is simple:

When a user writes a clear case-related deadline message, Val should store it
as both:

- a note in `case_notes`
- an event in `case_events`

This allows due queries, daily briefs, and future conflict warnings to operate
on live user input.

---

# A) Problem

The live system could:

- detect active case context
- store notes in `case_notes`
- read from `case_events`

But the live path was **not verified to create new `case_events`**.

This meant:

- due queries depended on pre-existing DB rows
- daily brief could only see manually created events
- immediate scheduling logic had no reliable live event insertion path

Sprint08 restores that path.

---

# B) Scope

This sprint is limited to:

1. restoring a live `insert_case_event(...)` helper in `memory_store.py`
2. wiring `_maybe_capture_case_note(...)` in `bot.py` to call it
3. adding a minimal deterministic deadline extractor for live text capture

This sprint does **not** include:

- collision warnings yet
- event deduplication yet
- advanced parsing
- calendar sync writes
- travel feasibility logic
- advisory reasoning

---

# C) Live Path

## Current message flow

User message
→ case detection
→ active case set
→ note stored

## New message flow after Sprint08

User message
→ case detection
→ active case set
→ note stored in `case_notes`
→ deadline phrase extracted
→ event stored in `case_events`

This is the first live bridge from conversational input into deterministic
deadline storage.

---

# D) Restored Helper

## File

`memory_store.py`

## Added helper

```python
insert_case_event(...)

Purpose:

Insert a case_events row in a schema-compatible way across legacy deployments.

Expected parameters:

chat_id

case_id

event_text

term_days

start_date

deadline_date

raw_text

principal_id

Returns:

case_events.id

This helper restores the missing live insertion capability.

E) Deterministic Deadline Extraction
File

bot.py

Added helper
_extract_deadline_date(text: str) -> str

Minimal deterministic patterns supported in Sprint08:

vence hoy

vence mañana

vence manana

vence el YYYY-MM-DD

Returns:

ISO date string (YYYY-MM-DD)

or empty string if no deterministic date is found

This is intentionally narrow.

The purpose is to prove the live insertion path, not to solve all natural language.

F) _maybe_capture_case_note(...) Upgrade
File

bot.py

This function previously:

extracted case id

stored note in case_notes

After Sprint08 it now also:

extracts deadline phrase

resolves active expediente to real cases.id

inserts a real case_events row through insert_case_event(...)

Behavior:

if no active case exists → no event insertion

if no deadline phrase exists → note only

if both active case and deadline phrase exist → note + event

This preserves the original behavior while extending it safely.

G) First Supported User Pattern

Example:

CASE:524242024 vence mañana

Expected behavior:

active case becomes 524242024

note is stored in case_notes

deadline extractor returns tomorrow’s date

matching cases.id is resolved

case_events row is inserted

Expected stored event:

event_text = CASE:524242024 vence mañana

deadline_date = YYYY-MM-DD (tomorrow)

H) Validation
Verified

Live message:

CASE:524242024 vence mañana

Produced real DB rows in case_events.

Observed rows:

chat_id = 1789350565

case_id = 3

event_text = CASE:524242024 vence mañana

deadline_date = 2026-03-08

This confirms that the live path now reaches deterministic event storage.

I) Known Issue Discovered During Sprint08

Duplicate rows were inserted for the same message content.

Observed example:

same chat_id

same case_id

same event_text

same deadline_date

This indicates that the new event insertion path is not yet idempotent.

This is not a Sprint08 failure.
It is the next hardening item discovered by Sprint08.

J) Follow-On Task
Sprint08.1 / Next patch

Add idempotency guard to insert_case_event(...).

Rule:

If same:

chat_id

case_id

event_text

deadline_date

already exists, do not insert a duplicate row.

This should be implemented before immediate collision warnings.

K) Definition of Done

live user message can create a real case_events row

insert_case_event(...) exists in live memory_store.py

_maybe_capture_case_note(...) can route qualifying messages into event storage

due system and evening brief can now operate on newly created live events

service remains stable

no architecture rewrite introduced

L) Non-Goals

Sprint08 does not include:

dedupe

collision warning at creation time

reminder auto-creation from case deadlines

fuzzy date parsing

legal interpretation by model

event editing

event deletion

Those belong to follow-on hardening sprints.

END OF SPRINT 08