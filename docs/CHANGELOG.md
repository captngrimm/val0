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
