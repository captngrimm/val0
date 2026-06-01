# Val0 Master Milestone Map

## Purpose

This is the human-readable map for current Val0, Karen RC, Router, OCR, and continuity work.

It exists to prevent drift across chats, Codex sessions, ValPrime, and repo docs. When names like M41, ROUTER-16, OCR-RUNTIME, and OBSIDIAN start to blur together, start here.

## Current Macro Milestone Mapping

| Milestone | Lane | Status |
| --- | --- | --- |
| M42 | Karen RC Health / Full Smoke Runner | DONE |
| M43 | OCR Registro Publico / Watermark PDFs | DONE v1 |
| M44 | Intent Router v2 Shadow Foundation | DONE |
| M45 | Router Coverage / Observation | ACTIVE |
| M46 | Intent Router v2 Refactor Planning | NOT STARTED |
| M47 | Carpetas / Topic Containers Runtime v1 | FUTURE |
| M48 | Multi-client Cleanup / Client Isolation Hardening | FUTURE |
| M49 | Obsidian / Visual Second Brain Sync Layer | FUTURE |
| M50 | Personal OS / OPEL Productization Layer | FUTURE |

## Current Active Lane

The active lane is M45: Router Coverage / Observation.

Next recommended step: ROUTER-17, focused on remaining router observation using test data only.

Remaining router observation gaps:

- `pending_action_reply`
- `reminder_update`
- `task_complete`
- `task_create`
- `task_delete`

Do not begin broad Intent Router v2 refactor work until the observation lane is complete enough to support a migration proposal.

## Current System Health

Karen RC full smoke command:

```bash
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
```

Expected current result: 24/24 PASS.

Shadow mode should be OFF unless intentionally running a short observation window with the Router shadow playbook.

## Do Not Forget

- Check source-of-truth files before continuing.
- Do not start broad router refactor yet.
- Continue shadow measurement before migration.
- Use only test data for destructive observations.
- Do not commit dirty client data accidentally.
- Treat repo docs and smokes as technical source-of-truth.
- Treat ValPrime/checkpoints as operational recovery source-of-truth.
- Treat OPEL as event/audit log source-of-truth.
