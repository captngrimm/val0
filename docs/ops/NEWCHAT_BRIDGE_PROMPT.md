# New Chat Bridge Prompt

Copy/paste this into a new assistant chat when recovering Val0 work:

```text
We are operating Val0.

Do not rely on chat memory. Existing ValPrime continuity may be available via /continuity or a natural "new chat bundle".

Ask me for ValPrime /continuity and Launchpad output if needed.

Repo: /opt/val0

Use source-of-truth docs before acting:
- docs/product/VAL0_MASTER_MILESTONE_MAP.md
- docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md
- docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md
- docs/product/VAL0_DOCS_VALUE_MAP.md
- docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md
- docs/ops/NEWCHAT_01_RECOVERY_PROTOCOL.md

Use technical verification:
- python3 scripts/diagnostics/new_chat_recovery_brief.py
- python3 scripts/diagnostics/val0_source_of_truth_check.py
- python3 scripts/diagnostics/val0_source_of_truth_check.py --full
- python3 scripts/quality/karen_rc_full_smoke.py --keep-going

Continuity model:
- Desk = active context
- Side Table = recent/relevant context
- Library Index = source catalog
- Vault = archived/deep detail

Keep answers action-first.
Use Clippy/Launchpad workflow: verify repo state, identify active lane, run the right smoke, and stop on conflicts.
Do not enable shadow mode or touch runtime/client files unless explicitly scoped.
```
