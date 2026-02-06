# Val0 Docs Index (anti-drift)

This file is the canonical map of Val0's docs.
If you're unsure what a file is for, start here.

## Core Contracts & State (Authoritative)

These documents define current system behavior.
Anything not listed here is non-authoritative.

- docs/VAL0_STATE.md  
  _Living snapshot of Val0’s current capabilities, limits, and recent changes._

- docs/QUERY_CONTRACT__VFMS.md  
  _Rules governing what document-based questions are allowed and how they must be answered._

- docs/QUERY_PLAYBOOK__TIMELINE_SPLIT__v4.md  
  _Deterministic timeline extraction rules. No inference._

- docs/MEMORY_GATE__PRE_INFINITE.md  
  _Constraints and safeguards before enabling persistent memory._

- docs/TELEGRAM_UX__DOCUMENT_PIPELINE.md  
  _How documents enter Val0 via Telegram and how users interact with them._

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
