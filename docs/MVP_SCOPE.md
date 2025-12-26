NOTE: This file defines MVP scope and limitations. Daily execution is tracked in VAL0_STATE.md.

# NEXT ACTIONS (ALWAYS CURRENT)

✅ MVP FROZEN — Val0 v0

## What Val0 DOES (MVP scope)
- Conversational assistant (ES/EN auto)
- Persistent facts (name, language, color, goals)
- Notes (/note, /notes, /search)
- Google Places:
  - Explicit search intent only
  - Returns lists
  - Number-based drill-down (1–5)
- Semantic memory:
  - Manual save (/sremember)
  - Automatic recall (read-only, assistive)
-Places: explicit intent gate + session cached drill-down (1–5)
-Semantic memory: manual save + auto recall injected into prompt (read-only)
-Language enforcement: preferred_language forces replies (accent-insensitive)



## Known Limitations (Accepted)
- No autonomous decision-making on lists
  (e.g. “escoge uno de esos” is NOT supported)
- No preference-based ranking
- No long-term taste modeling
- No multi-step task execution

## Next Phase (POST-MVP)
- C3: decision-on-results
- UX polish
- Preference heuristics
- System hardening

If unsure what to do:
→ Do NOT change bot.py.
→ Log ideas in SIDEBOARD.md.
