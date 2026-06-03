# VAL0 Alpha Benchmark Log

Purpose:
Track projected vs actual execution time for Val0 cockpit lanes after the Alpha marker.

Alpha marker:
- Date: 2026-06-03
- Meaning: Point after Calendar Create Follow-up Runtime v1 was sealed/pushed and interpreter/conversationality roadmap was confirmed active.
- Workflow rule: keep working in the current cockpit; report to Orchestrator only when a lane closes, chat gets slow, a blocker appears, roadmap changes, or a new branch is needed.

## Benchmark Rules

- Estimate before or at lane start when possible.
- Start time comes from the first Launchpad output for the lane.
- End time comes from the Launchpad output after final validation/push.
- Actual = End - Start.
- Drift = Actual - Estimate.
- Use PASS / PARTIAL / BLOCKED / WATCH for status.
- Do not include private client data.
- Do not commit live user data such as `clients/karen/CLIENT_GROCERY.md`.

## Lanes Since Alpha

| ID | Lane | Estimate | Start | End | Actual | Commit(s) | Status | Notes |
|---|---|---:|---|---|---:|---|---|---|
| A-001 | Calendar fixture follow-up coverage v1 | n/a | pre-Alpha | 2026-06-03 12:57 | n/a | `79422f5` | PASS | Added calendar fixture coverage and pending_state fixture runner support. |
| A-002 | Calendar create follow-up bridge v1 | n/a | pre-Alpha | 2026-06-03 13:11 | n/a | `69361c0` | PASS | Missing-time follow-up bridge. Interpreter parses follow-up time; deterministic confirmation still executes write. |
| A-003 | Interpreter task_delete support v1 | 30-60 min | post-Alpha | 2026-06-03 13:18 | pending calibration | `b9ea395` | PASS | Closed task_delete fixture XFAIL; client fixtures now 18/18 PASS. |
| A-004 | Karen Conversationality v1 | 2-4 h | 2026-06-03 13:24 | 2026-06-03 13:34 | ~10 min implementation/verify window after Codex handoff | `e84db63` | PASS | Added Karen-scoped deterministic conversational openings for agenda/reminders/tasks; smokes PASS; no write logic changed. |
| A-005 | Karen Personality Polish v1 | 2-3 h | 2026-06-03 13:37 | 2026-06-03 13:40 | ~3 min verify/push window after Codex handoff | `cdae51b` | PASS | Warmed/sassed Karen read/list openings; reinforced Tany consistency, contamination guards, and no fake legal authority. |

## Planned Next Milestones

| # | Milestone | Estimate | Status | Notes |
|---:|---|---:|---|---|
| 1 | Karen Conversationality v1 | 2-4 h | DONE | Reduce canned Telegram-bot feel while keeping deterministic rails safe. Completed as A-004 v1. |
| 2 | Karen Personality Polish v1 | 2-3 h | DONE | Tany consistency, warmer/sarcastic style, less corporate/legal dryness. Completed as A-005 v1. |
| 3 | Calendar Follow-up v2 | 2-4 h | NEXT | Missing-date follow-up bridge. |
| 4 | Fixture Migration v2 | 3-5 h | Planned | Move more one-off Karen smokes into client fixtures. |
| 5 | M45 Router Coverage Closeout | 2-4 h | Planned | Recalculate/close router observation items. |
| 6 | Conversation State / Pending-State Map | 4-6 h | Planned | Map multi-turn continuation across calendar/tasks/reminders/docs. |
| 7 | Folders/Cases Design v1 | 4-8 h | Planned | Caso Finca / carpetas / topics model. |
| 8 | Caso Finca MVP v1 | 1-2 d | Planned | First usable workspace for notes, docs, events, and timeline questions. |
| 9 | Val0 Client-Generalization Pass | 1-2 d | Planned | Separate Karen-specific logic from reusable client platform logic. |
| 10 | Founder Demo Readiness v1 | 1-2 d | Planned | Demo flow: agenda, tasks, reminders, docs, Caso Finca, natural tone. |
