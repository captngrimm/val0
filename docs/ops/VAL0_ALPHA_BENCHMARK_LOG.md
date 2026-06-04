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
| A-006 | Calendar Follow-up v2 — Missing Date Bridge | 2-4 h | 2026-06-03 13:41 | 2026-06-03 13:46 | ~5 min verify/push window after Codex handoff | `859b3f7` | PASS | Added missing-date follow-up bridge for calendar drafts; fixtures now 21/21 PASS; GCal write still requires explicit confirmation. |
| A-007 | Karen Legal/Document Summary Warmth v1 | 3-6 h | 2026-06-03 13:47 | 2026-06-03 14:00 | ~13 min verify/push window after Codex handoff | `322ef22` | PASS | Warmed Karen document/legal summaries with Nora-oriented consultative sections; OCR/watermark/legal guards PASS. |
| A-008 | Source-of-Truth/Roadmap Harness v1 | 1-2 h | 2026-06-03 14:02 | 2026-06-03 16:32 | elapsed includes pause/wait | `d67cd42` | PASS | Added Alpha brief command that summarizes repo state, Alpha lanes, next milestones, live-data warnings, and validation commands. |
| A-010 | Caso Finca / Carpeta Clara Design v1 | 1-2 h | 2026-06-03 | 2026-06-03 | same-day design lane | `8f99aa1` | PASS | Design-only lane for the first clear workspace/case model around Karen's Caso Finca. |
| A-011 | Caso Finca Read-Only Workspace Status v1 | 2-4 h | 2026-06-03 17:04 | 2026-06-03 17:11 | ~7 min verify/push window after Codex handoff | `f82f33d` | PASS | Added fixture/static read-only Caso Finca workspace status view with route smoke; no live data mutation. |
| A-012 | Benchmark Auto-Update Helper v1 | 1-2 h | 2026-06-03 17:14 | 2026-06-03 17:18 | ~4 min verify/push window after Codex handoff | `c4609eb` | PASS | Added helper to close Alpha benchmark lanes safely with duplicate protection, replace mode, dry-run, tactical notes, and planned-status updates. |
| A-013 | Caso Finca Source-Labeled Data Read-Only v1 | 2-4 h | 2026-06-03 17:21 | 2026-06-03 17:26 | ~5 min verify/implementation window after Codex handoff | `this commit` | PASS | Connected read-only Caso Finca workspace to safe source-labeled fixture records; no live data mutation. |
| A-014 | Existing Document Inventory / Case Attachment Audit | 1-2 h | 2026-06-03 17:30 | 2026-06-03 17:36 | ~6 min implementation/verify window after Codex handoff | `this commit` | PASS | Added metadata-only Karen document inventory audit for existing uploads, OCR status, summary status, and Caso Finca relevance; no document body dump or live mutation. |
| A-015 | Trusted Caso Finca Document Attachments v1 | 1-2 h | 2026-06-03 21:27 | 2026-06-03 21:31 | ~4 min implementation/verify window after Codex handoff | `this commit` | PASS | Linked trusted A-014 metadata-only document attachments into the read-only Caso Finca workspace; no OCR run, body dump, or live mutation. |
| A-019 | Caso Finca Document OCR Bridge v1 | 1-2 h | 2026-06-03 22:25 | 2026-06-03 22:39 | Added read-only OCR-backed summaries for Caso Finca numbered attachments when saved OCR exists. | `5a4395f` | PASS | Document 1 now summarizes saved OCR safely; documents without OCR keep graceful metadata fallback. |
## Human Outcome Summaries

### A-002 / A-006 — Calendar follow-up

Plain-English goal:
- Let Karen create Google Calendar events naturally, even when she gives part of the event in one message and completes it in the next.

Now Val can:
- Start a calendar draft when the title/date/time are not all present.
- Ask for the missing date or time.
- Continue the same draft when Karen replies.
- Show a confirmation preview before any Google Calendar write.

Example interaction:
- Karen: "Val, agenda cita con la bróker y mi mamá a la 1:30 PM"
- Val: asks what date.
- Karen: "mañana"
- Val: shows the Google Calendar confirmation preview.

Remaining gap / watch item:
- Multi-turn calendar is v1/v2 bridge behavior, not a broad router refactor. Keep watching voice follow-ups and ambiguous dates.

### A-003 — Task delete interpreter support

Plain-English goal:
- Stop treating direct numbered task delete phrases as vague chat.

Now Val can:
- Interpret "elimina la tarea 1", "borra la tarea 2", and "quita tarea uno" as task_delete in diagnostics/fixtures.
- Keep deterministic runtime responsible for the actual task action.

Example interaction:
- Karen: "Val elimina la tarea 1"
- Val/routing: understands this as a task delete/list-removal command, not a case or Google Calendar request.

Remaining gap / watch item:
- Interpreter classification is not the executor. Runtime safety and task history rules still decide what happens.

### A-004 / A-005 — Karen conversationality/personality

Plain-English goal:
- Make Val feel less like a canned Telegram bot in safe read/list responses.

Now Val can:
- Add Karen-scoped Tany openings to agenda, reminders, and tasks.
- Keep the tone warmer and lightly sassy without weakening write/delete safety.
- Avoid stale contamination phrases and fake legal authority.

Example interaction:
- Karen: "Val, qué tareas activas tengo?"
- Val: answers with a warmer Tany-facing task list instead of dry bot copy.

Remaining gap / watch item:
- This is deterministic copy polish only. Broader personality memory and sarcasm consistency are still future work.

### A-007 — Legal/document summary warmth

Plain-English goal:
- Turn document summaries into useful Nora-oriented review packets without pretending Val is a lawyer.

Now Val can:
- Present grounded document facts with "Lo importante", "Qué puede significar", "Qué falta confirmar", "Preguntas para Nora", and "Próximo paso sugerido".
- Keep OCR/watermark boundaries intact.
- Explain that the summary is a reading aid, not a legal decision.

Example interaction:
- Karen: "Val, resume con OCR el último documento"
- Val: returns a first-pass OCR summary with facts, questions for Nora, and legal review boundaries.

Remaining gap / watch item:
- Val still does not provide legal conclusions. OCR can be noisy, and Nora/the abogada must confirm legal effect.

### A-008 — Source-of-truth/Roadmap Harness

Plain-English goal:
- Give any cockpit/Codex a one-command briefing for where Val0 is, what changed, what comes next, and what live data must not be touched.

Now Val can:
- Print the current branch, git status, recent commits, Alpha lanes, planned milestones, tactical note, live-data warning, and validation commands.

Example interaction:
- Operator runs: `python3 scripts/diagnostics/val0_alpha_brief.py`
- Val0 prints the Alpha brief and flags `clients/karen/CLIENT_GROCERY.md` as live user data.

Remaining gap / watch item:
- The brief depends on this benchmark log staying current after each lane closes.

### A-010 — Caso Finca / Carpeta Clara Design

Plain-English goal:
- Design the first clear workspace/case model so Karen can open Caso Finca as a living folder instead of remembering scattered commands.

Now Val can:
- Not implemented yet; this lane defines the workspace model, phases, safety boundaries, test strategy, and next implementation milestone.

Example interaction:
- Future: "Val, abre mi Caso Finca"
- Future Val: shows what is known, what is uncertain, documents, timeline/events, questions for Nora, pending items, and next actions.

Remaining gap / watch item:
- Runtime implementation is still future. First safe next step is read-only case/workspace status with fixture data and no live data mutation.

### A-011 — Caso Finca Read-Only Workspace Status

Plain-English goal:
- Let Karen open Caso Finca and see a clear read-only workspace overview instead of scattered case/document commands.

Now Val can:
- Recognize explicit workspace phrases like "Val, abre mi Caso Finca".
- Render a Tany-facing read-only overview with what is known, what needs confirmation, related documents, Nora questions, pending items, and next steps.
- Keep legal boundaries visible and avoid writes.

Example interaction:
- Karen: "Val, abre mi Caso Finca"
- Val: opens the workspace dashboard and says it is only organizing information, not moving or changing anything.

Remaining gap / watch item:
- This v1 uses fixture/static workspace data. Next step is connecting the read-only renderer to stored notes/documents/timeline with careful source labels.

## Planned Next Milestones

| # | Milestone | Estimate | Status | Notes |
|---:|---|---:|---|---|
| 1 | Karen Conversationality v1 | 2-4 h | DONE | Reduce canned Telegram-bot feel while keeping deterministic rails safe. Completed as A-004 v1. |
| 2 | Karen Personality Polish v1 | 2-3 h | DONE | Tany consistency, warmer/sarcastic style, less corporate/legal dryness. Completed as A-005 v1. |
| 3 | Calendar Follow-up v2 | 2-4 h | DONE | Missing-date follow-up bridge. Completed as A-006. |
| 4 | Caso Finca / Carpeta Clara Design v1 | 1-2 h | DONE | Design-only workspace model before implementation. |
| 5 | Caso Finca Read-Only Workspace Status v1 | 2-4 h | DONE | First fixture/static read-only workspace dashboard. Completed as A-011. |
| 6 | Fixture Migration v2 | 3-5 h | Planned | Move more one-off Karen smokes into client fixtures. |
| 7 | M45 Router Coverage Closeout | 2-4 h | Planned | Recalculate/close router observation items. |
| 8 | Conversation State / Pending-State Map | 4-6 h | Planned | Map multi-turn continuation across calendar/tasks/reminders/docs. |
| 9 | Folders/Cases Runtime v1 | 4-8 h | WATCH | Connect Caso Finca / carpetas / topics model to stored source-labeled data. |
| 10 | Caso Finca MVP v1 | 1-2 d | Planned | First usable workspace for notes, docs, events, and timeline questions. |
| 11 | Val0 Client-Generalization Pass | 1-2 d | Planned | Separate Karen-specific logic from reusable client platform logic. |
| 12 | Founder Demo Readiness v1 | 1-2 d | Planned | Demo flow: agenda, tasks, reminders, docs, Caso Finca, natural tone. |
## Current Tactical Note

A-015 is sealed. Recommended next: live-review Caso Finca attachment copy with Karen, then consider a read-only attachment selector or source-linked notes lane.
