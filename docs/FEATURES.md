# VAL0 — FEATURE LEDGER (INTERNAL)

## ✅ SHIPPED (Working now)
- Telegram bot (polling) with text + voice handlers
- Error handling + logging
- Persistent chat logging (DB)
- Persistent facts per chat:
  - preferred name, color, goal, preferred language (stored)
- Notes:
  - /note, /notes, /search
  - natural-language note capture
- Google Places:
  - /place + 1–5 results
  - stores last results + number drill-down
  - intent-gated natural-language Places requests
- Voice input (Whisper transcription)
- Semantic memory (FAISS):
  - /sremember, /ssearch
  - auto semantic recall injected into prompts

## 🟡 RELEASE REQUIRED (Promise-safe Val0)
- Preferred language enforcement (not just stored)
- Semantic recall clarity (header + explainability)
- Semantic recall relevance tuning (reduce noise)
- Places intent detection robustness

## ⏸️ PLANNED (POST-RELEASE)
- Decision-on-results (pick/rank from Places results)
- Preference heuristics
- Document categorization + retrieval
- Barcode scanning (Open Food Facts)
- Receipt analysis / spend awareness
- Voice output (TTS)
- Proactive messaging (opt-in timers/schedules)

## ❌ NOT VAL0
- Implicit behavioral learning / profiling
- Autonomous monitoring
- Multi-step agentic workflows (planning/execution loop)
- “Infinite memory” marketing claims
