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
| A-027C | Caso Finca Date-Gap Alias Priority Fix | 30-60 min | 2026-06-04 21:12 | 2026-06-04 21:16 | 0.1 h | `739dbef` | PASS | Human outcome: Karen can now ask 'Val, qué falta ordenar por fecha?' and Val routes to Caso Finca date-gap/timeline guidance instead of founder-beta limitations. Technical change: added narrow date/timeline gap markers to the founder-intro exclusion route so the existing Caso Finca workspace route can handle the phrase later in the chain. No write/event registration behavior added. |
| A-027D | Caso Finca Date-Gap Runtime Priority Fix | 30-60 min | 2026-06-04 21:25 | 2026-06-04 21:38 | 0.25 h | `5c35593` | PASS | Human outcome: Karen can now ask 'Val, qué falta ordenar por fecha?' and Val should route through the real runtime path to Caso Finca Huecos / falta fecha instead of founder-beta limitations. Technical change: fixed the actual handle_text route priority before founder_intro and updated runtime smoke harness to use unique fake message IDs so idempotency does not false-fail or false-pass. Controls preserved: real limitations prompts still reach founder limitations; generic whatnow remains operational summary. No write/event registration behavior added. |
| A-028 | Caso Finca Timeline Event Registration Design v1 | 30-60 min | 2026-06-04 21:43 | 2026-06-04 21:48 | 0.1 h | `c575130` | PASS | Human outcome: Karen now has a safe design path toward registering Caso Finca timeline events naturally, with confirmation, source labels, legal boundaries, date precision, and audit trail discipline. Design defines draft-before-write flow, event schema, safety model, storage options, correction/delete rules, test plan, and acceptance criteria. No runtime behavior changed and no live data mutation. |
| A-028B | Timeline Event Draft Parser + Confirmation Skeleton | 1-2 h | 2026-06-04 21:52 | 2026-06-04 22:00 | 0.15 h | `45ec02a` | PASS | Human outcome: Karen can now say timeline event registration phrases like 'Val, registra en Caso Finca que en 2021 pasó X' and Val returns a safe Spanish draft preview asking confirmation while explicitly saying it is not saved yet. Technical change: added deterministic parser, draft object, preview renderer, volatile-only handler, and narrow runtime route. No event persistence, no OCR extraction, no legal advice, and no live data mutation. |
| A-028C | Timeline Event Storage Spike / Fixture Store | 1-2 h | 2026-06-04 22:08 | 2026-06-04 22:17 | 0.15 h | `165b8bf` | PASS | Human outcome: Caso Finca timeline event drafts can now become durable records in a safe temp/fixture JSON store, be read back, sorted into timeline order, rendered safely, and soft-deleted with audit history before any live 'sí, guárdalo' path exists. Technical change: added fixture/temp JSON store, event record model, audit trail creation, sorted timeline reads, soft-delete, and protected live-path refusal. No live Telegram persistence and no live data mutation. |
| A-028D | Timeline Event Confirmation Handler Fixture-Only | 1-2 h | 2026-06-04 22:23 | 2026-06-04 22:29 | 0.1 h | `f372887` | PASS | Human outcome: After a Caso Finca timeline draft, Karen can reply 'sí, guárdalo' in test/fixture mode and Val completes the confirmation flow into a temp JSON store. In normal live mode, Val refuses clearly and does not write real timeline memory. Technical change: added narrow pending timeline-event confirmation gate, fixture-only confirmation handling, live-persistence refusal, and event-added summary rendering. No live client persistence, no SQLite migration, no OCR extraction, no legal advice, and no live data mutation. |
| A-028E | Timeline Live Persistence Decision / SQLite-vs-JSON Guardrail Design | 30-60 min | 2026-06-04 22:32 | 2026-06-04 22:37 | 0.1 h | `56a0362` | PASS | Human outcome: We chose the real persistence vault for Caso Finca timeline events before enabling live saves. Recommendation is hybrid SQLite primary plus export/report view: SQLite as source of truth for auditability, soft-delete, correction support, transaction safety, client isolation, and lower git-contamination risk; reports/exports for operator review; JSON remains fixture/temp only. No runtime behavior changed and no live data mutation. |
| A-028F | Timeline Event SQLite Store Adapter + Temp DB Smokes | 1-2 h | 2026-06-04 22:40 | 2026-06-04 22:47 | 0.15 h | `def4452` | PASS | Human outcome: We proved Caso Finca timeline events can be stored in SQLite safely before live 'sí, guárdalo' enablement. Records can be inserted, read back, sorted, audited, soft-deleted, and isolated by client/case in a temp DB. Technical change: added temp-DB-only SQLite adapter, schema init, insert/read/sort, audit rows, soft-delete, client/case filtering, and non-temp DB refusal. No production DB migration, no live Telegram persistence, and no live data mutation. |
| A-028G | Timeline Event SQLite Confirmation Wiring in Fixture Mode | 1-2 h | 2026-06-04 22:52 | 2026-06-04 22:58 | 0.1 h | `0ab0080` | PASS | Human outcome: In fixture/test mode, Karen's 'sí, guárdalo' after a Caso Finca event draft can now save to a temp SQLite DB, read back the event, and return a safe confirmation summary. Live/default mode still refuses real persistence. Technical change: added explicit SQLite fixture confirmation mode via SQLITE_STORE_PATH_KEY; JSON fixture mode and live refusal remain intact. No production DB migration, no live Telegram persistence, no real Val0 DB writes, and no live data mutation. |
| A-028H | Timeline Read From SQLite Temp Store | 1-2 h | 2026-06-04 23:05 | 2026-06-04 23:23 | 0.3 h | `2f619a4` | PASS | Human outcome: In fixture/test mode, after Caso Finca timeline events are saved into temp SQLite, Val can render a Spanish timeline from SQLite records instead of static fixture timeline data. Technical change: added SQLite temp-store timeline read/render helpers and smoke coverage for exact-date, year-only, unknown-date, deleted, and other-client/case events. Sorting, deleted-event filtering, client/case isolation, and legal-boundary-safe rendering passed. Live mode remains unchanged; no live Telegram SQLite reads, no production DB migration, and no live data mutation. |
| A-028I | Timeline SQLite Export / Operator Diagnostic | 1-2 h | 2026-06-04 23:26 | 2026-06-04 23:32 | 0.1 h | `85863a3` | PASS | Human outcome: Operator can inspect temp SQLite Caso Finca timeline records and audit actions in a safe, human-readable report before any live persistence is enabled. Technical change: added temp SQLite operator export diagnostic requiring explicit --db-path, refusing non-/tmp paths by default, filtering by client/case, hiding deleted records unless --include-deleted is passed, including audit summary/latest actions/safety notes, and avoiding raw internal IDs in normal output. No live Telegram persistence, no production DB migration, no production DB read/write path, and no live data mutation. |
| A-028J | SQLite Timeline Migration Plan + Live Guard Smoke | 1-2 h | 2026-06-04 23:34 | 2026-06-04 23:43 | 0.15 h | `a6455bf` | PASS | Human outcome: Before enabling real Caso Finca timeline saves, we added a reviewed migration/enablement plan and a fail-closed live guard smoke proving live persistence cannot accidentally activate. Technical change: added migration plan doc, fail-closed live helper in core/case_timeline_events.py, and live guard smoke. Policy files read: AGENTS.md and docs/architecture/CLIENT_ISOLATION_CONTRACT_V0.md. No production DB migration, no live Telegram persistence, no real Val0 DB writes, and no live data mutation. |
| A-028K | Timeline SQLite Migration Dry-Run Smoke | 1-2 h | 2026-06-05 00:00 | 2026-06-05 00:13 | 0.2 h | `9052b63` | PASS | Human outcome: A-028K proves the Caso Finca timeline SQLite schema can be applied repeatedly to a temp DB, verified, used for insert/read/audit, and exported safely before any production DB is touched. Technical change: added migration dry-run script and smoke. Policy files read: AGENTS.md and docs/architecture/CLIENT_ISOLATION_CONTRACT_V0.md. No production DB migration, no live Telegram persistence, no production enablement flag wiring, and no live data mutation. |
| NIGHT-RUNNER-05 | Codex Bridge Discovery + Bedtime Packet v1 | 1-2 h | 2026-06-05 00:17 | 2026-06-05 00:24 | 0.15 h | `3f8fc32` | PASS | Human outcome: Night Runner now has a safe discovery bridge that reports whether local Codex invocation appears feasible, without running Codex on a task, exposing secrets, editing code, or touching protected live data. Discovery found local Codex ready via VS Code extension binary path, ~/.codex present with auth/config, and Night Runner files available. Technical change: added Codex bridge discovery script, smoke, packet, and operator doc. No autonomous coding yet, no production restart, no live DB writes, no protected live data mutation. |
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

NIGHT-RUNNER-05 is sealed. Recommended next: ValPrime checkpoint, then NIGHT-RUNNER-06 Branch-only Codex Attempt Dry-Run. Keep it no-op/dry-run first; no autonomous coding beyond guarded branch attempt.
