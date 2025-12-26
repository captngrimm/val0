# Val0 Docs Index (anti-drift)

This file is the canonical map of Val0's docs.
If you're unsure what a file is for, start here.

## Core contracts (authoritative)
- docs/QUERY_CONTRACT__VFMS.md  
  Defines evidence rules: grounded output only, no inference, cite chunks, failure modes.

- docs/QUERY_PLAYBOOK__TIMELINE_SPLIT__v4.md  
  Deterministic timeline extraction rules (facts/dates only, no inference).

- docs/MEMORY_GATE__PRE_INFINITE.md  
  Rules for what can be remembered vs what must stay document-scoped.

## Telegram UX (experience layer)
- docs/TELEGRAM_UX__DOCUMENT_PIPELINE.md  
  Defines how Telegram uploads/queries map to VFMS behaviors and safe responses.

## System state / logging
- docs/VAL0_STATE.md  
  Running status, recent milestones, and current operational focus.

## Generated outputs (not always committed)
- vfms_data/outputs/  
  Grounded summaries, binders, audits, merges. Treat as artifacts; prefer re-generating when possible.

## If you're lost (quick start)
1) Read docs/QUERY_CONTRACT__VFMS.md
2) Read docs/QUERY_PLAYBOOK__TIMELINE_SPLIT__v4.md
3) Run: `python3 vfms/vfms.py --help` and `python3 vfms/vfms.py summarize --help`
4) Use doc-scoped queries: `python3 vfms/vfms.py query "..." --doc <ingest_id> --top 5`
