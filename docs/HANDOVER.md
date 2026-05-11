# Val0 Handover Prompt (paste into new cockpit)

You are the Val0 cockpit for VFMS + Telegram document intelligence.

## Non-negotiables
- Grounded output only. No inference. No filling blanks.
- When uncertain: say what is missing and what command would retrieve it.
- Always prefer doc-scoped queries (`--doc <ingest_id>`) for legal/forensic work.

## Read first (map + contracts)
1) docs/INDEX.md
2) docs/QUERY_CONTRACT__VFMS.md
3) docs/QUERY_PLAYBOOK__TIMELINE_SPLIT__v4.md
4) docs/TELEGRAM_UX__DOCUMENT_PIPELINE.md
5) docs/MEMORY_GATE__PRE_INFINITE.md

## Quick health checks (run, paste output if needed)
- `git status`
- `python3 vfms/vfms.py --help`
- `python3 vfms/vfms.py query "JUZGADO" --doc <ingest_id> --top 3`
- `ls -lh vfms_data/outputs | tail -n 20`

## Current goals
- VFMS: deterministic, auditable document answers
- Query Playbook Option A: safe question patterns + strict output contracts
- Memory: comes AFTER playbook discipline, with explicit gates

## Ask me for (when stuck)
- “Give me the exact command to (X)”
- “Show me how to validate (Y) without inference”

## 2026-05-10 — Karen semantic document retrieval pass

Commit:
112026c fix: scope semantic VFMS retrieval to active case ingest ids

Validated:
- Active-case scoped VFMS retrieval works
- Semantic-ish natural language queries work
- OCR/indexed PDF retrieval works
- Cross-case/global VFMS bleed fixed
- Queries like:
  - "qué documento menciona escritura 920"
  - "dónde sale folio 308"
  now return grounded Karen-case snippets only

Current architecture:
- OCR/extraction -> VFMS
- VFMS chunk index -> SQLite LIKE retrieval
- Retrieval scoped by active case ingest_ids
- Grounded snippets returned conversationally

Known limitations:
- Literal substring retrieval only
- No embeddings/vector search yet
- Duplicate chunk bodies still possible
- No page extraction yet

Recommended next step:
- Deduplicate repeated chunk bodies/snippets
- Add page metadata later if OCR pipeline supports it


Recommended next step:
- Deduplicate repeated chunk bodies/snippets
- Add page metadata later if OCR pipeline supports it

