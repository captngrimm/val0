# VAL0 Code Anchors — Protected Entry Points

Purpose:
Quick reference for critical functions and where Phase 2 hooks are allowed.

This is NOT a design doc.
This is a “don’t break the system” map.

---

## /opt/val0/bot.py

### _process_text_pipeline(update, context, text)
Role:
Main execution pipeline (protected order).

Critical:
- DO NOT reorder handlers
- DO NOT move logic into LLM
- DO NOT merge flows

Allowed:
- post-write hooks ONLY (after confirmed DB mutations)

Key write points for Phase 2:
- pending reminder confirm (YES path)
- pending term confirm (YES path)
- disambiguation → note insert
- deterministic note command
- natural note insert (_maybe_capture_case_note)

---

### _maybe_capture_case_note(update, chat_id, text, source)
Role:
Natural note capture

Writes:
- insert_case_note(...)

Phase 2:
- enrich _LAST_ACTION with case_id
- call refresh_case_summary(chat_id, case_id) AFTER successful insert

---

## /opt/val0/memory_store.py

### init_db()
Role:
Base schema creation

Phase 2:
- add case_summaries table
- DO NOT modify canonical tables

---

### insert_case_note(...)
Role:
Canonical note write

Rules:
- idempotent logic must remain unchanged

Phase 2:
- DO NOT modify logic
- refresh happens OUTSIDE (caller)

---

### insert_case_event(...)
Role:
Canonical event write (terms + reminders)

Rules:
- schema-flexible
- duplicate detection already handled

Phase 2:
- DO NOT modify logic
- refresh happens OUTSIDE (caller)

---

### _get_conn()
Role:
DB connection (SQLCipher / SQLite)

Critical:
- DO NOT break encryption flow

---

## /opt/val0/core/case_mvp.py

### generate_case_cockpit(chat_id, case_id)
Role:
Primary case view renderer

Rules:
- must work WITHOUT summary cache

Phase 2:
- summary is ADDITIVE only
- may lazy-load summary
- must NOT depend on summary existence

---

### try_delete_last_note(update, chat_id, text)
Role:
Delete most recent note

Phase 2:
- AFTER successful delete → refresh_case_summary(chat_id, case_id)

---

### try_undo_last_action(update, chat_id, text)
Role:
Undo last mutation (single-step)

Handles:
- note insert → delete
- note delete → restore
- term insert → delete
- reminder insert → delete

Phase 2:
- enrich _LAST_ACTION with case_id
- AFTER successful undo → refresh_case_summary(chat_id, case_id)

---

## New file (Phase 2)

### /opt/val0/core/case_summary.py

### build_case_summary(chat_id, case_id)
Role:
Deterministic summary builder

Reads:
- cases
- case_events
- case_notes

Rules:
- no LLM
- no writes to canonical tables

---

### refresh_case_summary(chat_id, case_id)
Role:
Cache writer

Behavior:
- calls builder
- upserts into case_summaries

Rules:
- idempotent
- safe to call repeatedly

---

## Phase 2 Hook Pattern (IMPORTANT)

All hooks must follow this exact pattern:

1. Perform canonical write (note/event/delete/undo)
2. Confirm success
3. Update _LAST_ACTION (with case_id)
4. Call:
   refresh_case_summary(chat_id, case_id)

Never:
- before write
- during detection
- during disambiguation suggestion
- during LLM fallback

---

## DO NOT TOUCH (Global)

- routing order in _process_text_pipeline
- confirmation flows
- duplicate detection logic
- event schema
- case resolution logic
- disambiguation behavior

---

## Red Flags

If you see yourself doing any of these, stop:

- “let’s normalize case_id type”
- “let’s simplify event schema”
- “let’s unify reminder and term logic”
- “let’s let the LLM decide this”
- “let’s move logic earlier in pipeline”

That is NOT Phase 2.

