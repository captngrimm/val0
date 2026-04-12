# Val0 — Changelog

Format:
- Date: YYYY-MM-DD
- Version label: vX (internal)
- Notes: short, factual, testable

---

## 2025-12-21 — v1 (Baseline MVP)
- Telegram text pipeline operational
- DB-backed chat logging + recent context block
- Persistent facts stored via trigger phrases (name/language/color/goal)
- Notes: /note, /notes, /search
- Places: /place returns list
- Known issues:
  - Natural-language Places could over-trigger on normal chat
  - preferred_language stored but replies could drift

## 2025-12-21 — v2 (C1: Places intent guardrails + drill-down)
- Added explicit intent gate for natural-language Google Places
- Cached last Places results in-session
- Added 1–5 number drill-down to fetch place details
- Reduced false triggers from short chatter

## 2025-12-21 — v3 (C2: Semantic recall integration, read-only)
- Integrated FAISS semantic recall block into OpenAI prompt
- Manual save: /sremember
- Automatic recall: semantic search on user text → inject top hits
- Filtering by chat_id

## 2025-12-21 — v4 (Hard language enforcement + normalization)
- Enforced reply language when preferred_language is set
- Added one-time confirmation prompt for sustained mixing
- Added accent/uppercase-insensitive normalization (e.g., “espanol” == “español”)
- Side-effect: normalization improves intent detection reliability

---

## 2026-04-12 — vPM1 (PM loop + session continuity MVP)

- Audited live runtime source of truth:
  - service: `val0-bot.service`
  - entrypoint: `/opt/val0/.venv/bin/python /opt/val0/bot.py`
  - DB: `/opt/val0/val0_memory.enc.db`
  - DB key file: `/etc/val0/db_key`

- Confirmed these files are empty stubs and not runtime source of truth:
  - `/opt/val0/system/val0.service`
  - `/opt/val0/system/service_start.sh`

- Confirmed live but previously under-documented behavior:
  - voice input pipeline
  - Whisper transcription
  - voice reply mode
  - TTS reply path
  - background Forge voice ingest
  - centralized prompt assembly in `_process_text_pipeline()`
  - centralized model gateway in `call_val_openai(...)`
  - existing message logging / recent-memory / semantic-memory hooks
  - `_ACTIVE_NODE` / `retoma` flow
  - legal/case/reminder routing
  - reminder runner / polling loop

- Added PM loop MVP:
  - `pm_current_focus`
  - `pm_decisions`
  - `/focus`
  - `/showfocus`
  - PM evaluation on every user input
  - PM drift surfacing
  - PM prompt injection

- Added session continuity MVP:
  - persist inbound user turns into `messages`
  - persist outbound assistant turns into `messages`
  - trim recent per-chat messages to last 12

- Added deterministic focus-query override for:
  - “What are we working on?”
  - “What is the current focus?”

- Fixed SQLCipher compatibility issue:
  - replaced `ON CONFLICT ... DO UPDATE`
  - with `INSERT OR IGNORE` + `UPDATE`

- Verified working:
  - `/focus` updates PM focus
  - PM focus persists in DB
  - drift example correctly returns `DEFER`
  - focus queries resolve from PM state
  - session messages continue storing successfully

- Known caveat:
  - generic conversation can still pick up noise from older reminder/task/case layers unless intercepted deterministically or improved in a later continuity polish pass