[2025-12-16] Google Places
- Location: places/places_engine.py
- Status: VERIFIED
- Test: Manual runtime query via Telegram
- Result: PASS

[2025-12-16] SQLite Memory
- Location: memory/database.py
- Status: UNKNOWN
- Test: —
- Result: —

[2025-12-16] FAISS Semantic Memory
- Location: faiss/memory_embeddings.py
- Status: UNKNOWN
- Test: —
- Result: —

[2025-12-16] SQLite Memory Spine
- Location: memory_store.py, memory/database.py, memory/memory_engine.py
- Status: TODO-VERIFY
- Test: Telegram convo → restart → recall
- Result: TBD

[2025-12-16] FAISS Semantic Memory
- Location: faiss/faiss_index.py, faiss/memory_embeddings.py
- Status: TODO-VERIFY
- Test: embeddings created + semantic recall
- Result: TBD

[2025-12-16] Emoji Engine
- Location: engagement/emoji_engine.py
- Status: TODO-VERIFY
- Test: trigger emoji behavior in Telegram
- Result: TBD

[2025-12-16] Sticker Engine
- Location: engagement/sticker_engine.py
- Status: TODO-VERIFY
- Test: Telegram sends sticker
- Result: TBD

[2025-12-16] TTS Engine
- Location: tts/tts_engine.py
- Status: TODO-VERIFY
- Test: generate audio + send
- Result: TBD

[2025-12-16] Voice Input
- Location: voice/
- Status: TODO-VERIFY
- Test: voice note → transcript
- Result: TBD

[2025-12-16] SQLite Persistent Memory
- Location: val0_memory.db, memory/database.py
- Status: VERIFIED
- Test: Direct sqlite3 open + table enumeration
- Result: PASS
[2025-12-17 04:59:01 UTC] FAISS Memory
- Location: faiss/
- Status: VERIFIED
- Test: Existing embeddings load + query without error
- Result: PASS

[2025-12-16] Memory backend
- SQLite: VERIFIED
- FAISS: PRESENT BUT INACTIVE
- Source of truth: SQLite
- Status: CONFIRMED


[2025-12-16] Telegram Core
- Bot: RUNNING
- Mode: TEXT (EMOJI+STICKERS = CODE PRESENT, RUNTIME UNVERIFIED)
- Persistence: ENABLED (SQLite)
- Status: VERIFIED

[2025-12-16] FAISS Semantic Memory
- Location: faiss/memory_embeddings.py
- Status: BROKEN
- Finding: file is 0 bytes (empty), imports fail
- Evidence: ls shows size=0, wc -l = 0
- Next: restore or implement MemoryEmbeddings + persistence + test

[2025-12-17] FAISS Semantic Memory
- Location: faiss/faiss_index.py, faiss/memory_embeddings.py, faiss/faiss_store/
- Status: VERIFIED (local test)
- Test: Added 2 memories + semantic search query
- Result: PASS

[2025-12-17] FAISS Semantic Memory
- Location: semantic/ (semantic/faiss_index.py, semantic/memory_embeddings.py, semantic/faiss_store/)
- Status: VERIFIED
- Test: Added 2 memories + semantic search query (python snippet)
- Result: PASS
- Notes: Uses openai.Embedding.create (openai==0.28.1); methods = add_memory(), search()
