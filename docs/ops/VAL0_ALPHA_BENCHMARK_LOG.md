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
| A-020 | Generic Folder Create v1 | 2-4 h | 2026-06-04 10:30 | 2026-06-04 10:42 | Added Karen-scoped text-only generic folders with JSON storage, create/list/open/save/list routes, and temp-file smoke coverage. | `03ef297` | PASS | Generic folders like Libro now work without moving documents or touching CLIENT_GROCERY.md. |
| A-021 | Folder UX Polish v1 | 1-2 h | 2026-06-04 10:55 | 2026-06-04 11:01 | Added folder type labels, default folder icons, and display capitalization for folder notes. | `3c6eefe` | PASS | Folder replies now render labels like 📚 📁 **Libro** and capitalize listed notes without mutating live folder data. |
| A-022 | Founder Demo Readiness v1 | 1-2 d | 2026-06-04 11:23 | 2026-06-04 11:31 | 0.2 h | `67d370f` | PASS | Added canonical founder-demo readiness doc with current demo path: agenda, tasks, calendar confirmation, Caso Finca, document summary, and generic folder Libro. Runtime untouched; live client data not staged. |
| A-023 | Demo Natural Alias Routing v1 | 1-2 h | 2026-06-04 11:58 | 2026-06-04 12:47 | 0.8 h | `3a145c3` | PASS | Fixed messy founder-demo aliases: tomorrow pending routes to agenda, finca aliases route to Caso Finca workspace/documents, first-document phrase routes to document 1 summary, and ideas in Libro route to generic folder contents instead of roadmap backlog. Runtime restarted and live Telegram retest passed. |
| A-024 | Caso Finca Conversational Q&A Design v1 | 1-2 h | 2026-06-04 13:04 | 2026-06-04 13:12 | 0.2 h | `8a2dcdf` | PASS | Added design-first bounded Caso Finca conversational Q&A layer. Defines source-grounded case Q&A goals, non-goals, retrieval packet, legal/OCR boundaries, deterministic vs LLM responsibilities, test plan, and next lane A-024B. |
| A-024B | Caso Finca Deterministic Q&A Packet + Read-Only Renderer v1 | 2-4 h | 2026-06-04 13:15 | 2026-06-04 14:02 | 0.8 h | `e778bdb` | PASS | Implemented bounded deterministic Caso Finca Q&A with read-only packet/renderer, context-aware routing for ambiguous follow-up questions, legal/OCR boundaries, and live Telegram validation. No LLM renderer yet; no writes or live data mutation. |
| A-025 | Bounded LLM Voice Renderer Design v1 | 1-2 h | 2026-06-04 14:06 | 2026-06-04 14:08 | 0.1 h | `4939f66` | PASS | Added design-first bounded LLM voice renderer plan for Caso Finca Q&A packets. Defines packet contract, LLM prompt contract, safety guardrails, validation/post-checks, fallback behavior, tone profiles, examples, and next lane A-025B. |
| A-025B | Bounded LLM Voice Renderer Skeleton + Validation Smokes | 1-2 h | 2026-06-04 14:13 | 2026-06-04 14:21 | 0.2 h | `fa4c2fa` | PASS | Added test-only bounded voice renderer skeleton with packet adapter, prompt builder, fail-closed validation, deterministic fallback, and smokes for boundary, OCR caveat, forbidden legal claims, internal leakage, action claims, and max length. No runtime behavior changed and no real API calls. |
| A-025C | Bounded Voice Renderer Shadow Candidate Generation v1 | 1-2 h | 2026-06-04 14:36 | 2026-06-04 14:49 | 0.2 h | `c63c1ea` | PASS | Added shadow-only voice candidate generation for bounded Caso Finca Q&A packets. Candidate validation records safe/unsafe results while user-facing answer remains deterministic. No runtime Telegram behavior changed, no real API calls, no writes or mutations. |
| A-027 | Night Runner v0 Dry-Run Design | 30-60 min | 2026-06-04 15:04 | 2026-06-04 15:08 | 0.1 h | `38d2e0b` | PASS | Added design-only Night Runner v0 dry-run plan. Defines branch-only/report-only behavior, lane packet format, forbidden live-data guard, git status guard, allowed/forbidden command categories, report format, stop conditions, future phases, and next lane NIGHT-RUNNER-01 dry-run validator script. |
| NIGHT-RUNNER-01 | Night Runner Dry-Run Validator Script | 1-2 h | 2026-06-04 17:05 | 2026-06-04 17:19 | 0.25 h | `6559581` | PASS | Added refusal-first Night Runner dry-run validator. Supports JSON/simple YAML lane packets, branch/git/forbidden-file checks, unsafe flag rejection, broad allowed-file rejection, unsafe prompt detection, safe report-path validation, and dry-run report writing. No tests executed by runner yet, no commits/restarts/live data mutation. |
| NIGHT-RUNNER-02 | Night Runner Morning Report/Test Runner Layer | 1-2 h | 2026-06-04 17:24 | 2026-06-04 17:30 | 0.1 h | `e175e9b` | PASS | Added --run-tests to Night Runner. It validates lane packets first, refuses unsafe work, runs only allow-listed diagnostics/tests from tests_to_run, captures output/exit codes, and writes a report. Still no commits, restarts, production actions, live data mutation, or autonomous editing. |
| NIGHT-RUNNER-03 | Night Runner Bedtime Packet + Launchpad Morning Report Workflow | 30-60 min | 2026-06-04 17:42 | 2026-06-04 17:51 | 0.15 h | `83b8dca` | PASS | Added canonical Night Runner bedtime workflow doc and packet. Operator can run one safe bedtime command using night_runner_dry_run.py with --run-tests, generating tmp/night_runner/morning_report.md. Current behavior correctly refuses when protected live Karen files are dirty. |
| NIGHT-RUNNER-04 | Night Runner Clean Readonly Report Mode | 1-2 h | 2026-06-04 18:09 | 2026-06-04 18:16 | 0.15 h | `db49a7c` | PASS | Added opt-in protected-dirty read-only mode. Night Runner can now run safe bedtime diagnostics while CLIENT_GROCERY.md and CLIENT_FOLDERS.json are dirty, provided they are forbidden, unstaged, and untouched. Real proof run passed 4/4 commands and wrote tmp/night_runner/morning_report.md. |
| A-025D | Bounded Voice Renderer Shadow Observation Logging v1 | 2-3 h | 2026-06-04 18:27 | 2026-06-04 18:56 | 0.5 h | `55d5e01` | PASS | Added safe shadow observation logging for bounded voice renderer candidates. Logs accepted/rejected status, rejection reason, safety flags, OCR caveat and legal-boundary presence, deterministic-answer hash/excerpt, and redacted candidate excerpt to tmp/voice_renderer_shadow/observations.jsonl. Deterministic answer remains user-facing; no Telegram/runtime behavior changed, no API calls, no live data mutation. |
| A-025E | Voice Renderer Shadow Review / Operator Comparison v1 | 1-2 h | 2026-06-04 19:05 | 2026-06-04 19:58 | 0.9 h | `23e84c3` | PASS | Added read-only operator review diagnostic for bounded voice renderer shadow observations. Reports accepted/rejected counts, rejection reasons, safety flags, OCR caveat/legal-boundary stats, safe excerpts, and recommendation. No Telegram/runtime behavior changed, no API calls, no user-facing LLM output, no live data mutation. |
| A-026 | Caso Finca Grounded Q&A v2 | 1-2 h | 2026-06-04 20:03 | 2026-06-04 20:18 | 0.25 h | `51ac8ac` | PASS | Human outcome: Caso Finca answers are now less generic and more useful. Karen can ask what Val knows, what is still uncertain, what needs review, what to ask Nora, which document to review first, and why the first document matters. Answers now separate Hechos en Val, Señales / indicios, Falta confirmar, Preguntas para Nora, and Próximo paso sugerido. Technical change: strengthened deterministic Caso Finca Q&A packet with facts_in_val, evidence_signals, and review_gaps. Still read-only, deterministic, legal-boundary-safe, bounded to Caso Finca data, no live OCR extraction, no LLM live response. |
| A-026B | Caso Finca Document Priority Natural Alias Fix | 30-60 min | 2026-06-04 20:29 | 2026-06-04 20:35 | 0.1 h | `6cee01e` | PASS | Human outcome: Karen can now ask naturally 'Val, cuál documento reviso primero?' or 'Val, qué documento reviso primero?' and Val routes to Caso Finca document-priority guidance instead of generic Qué hago ahora. Technical change: added narrow document-priority alias and smoke coverage while preserving generic whatnow behavior and bounded Caso Finca routing. No LLM/live response path changed. |
| A-027B | Caso Finca Timeline / Events v1 | 1-2 h | 2026-06-04 20:45 | 2026-06-04 21:06 | 0.35 h | `f9d3c9c` | PASS | Human outcome: Karen can now ask for a Caso Finca timeline and date-ordering gaps. Val returns a read-only timeline view with Eventos confirmados en Val, Eventos por confirmar, Huecos / falta fecha, Preguntas para Nora, and Próximo paso sugerido instead of dumping the full workspace. Technical change: added timeline and date-gap aliases plus deterministic read-only timeline renderers. No event registration/write path, no LLM, no OCR extraction, no document mutation. |
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
| 12 | Founder Demo Readiness v1 | 1-2 d | DONE | Demo flow: agenda, tasks, reminders, docs, Caso Finca, natural tone. |
## Current Tactical Note

A-027B is sealed. Recommended next: restart Val0 runtime, live Telegram retest timeline/gap phrases, then decide between timeline event registration design or folder/case runtime v1.
