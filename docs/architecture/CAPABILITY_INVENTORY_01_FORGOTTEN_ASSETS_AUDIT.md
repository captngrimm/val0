# Capability Inventory 01 Forgotten Assets Audit

## 1. Purpose

This audit inventories existing Val0 / ValPrime / OPEL-adjacent capabilities so the Personal OS, adaptive intake, memory spine, LLM/shadow classifier, operator response composer, and founder-beta product lanes assimilate what already exists instead of rebuilding it.

This is an audit-only lane. It adds no runtime behavior, no DB migrations, no client data edits, no production restart, no commits, no profile persistence, and no calendar/task/reminder behavior changes.

## 2. Existing Capability Inventory

| Category | Existing assets | Status | Current use / risk |
| --- | --- | --- | --- |
| Router / shadow / intent infrastructure | `core/intent_router_v2.py`, `core/intent_router_v2_observer.py`, `core/conversation_router.py`, `core/intent_interpreter.py`, `scripts/ops/router_shadow_mode.sh`, `scripts/diagnostics/intent_router_v2_sample_harness.py`, `scripts/diagnostics/intent_router_v2_coverage_report.py`, router reports and playbook | Shadow-only / diagnostic / docs | Do not rebuild. Expand sample coverage and observation before any runtime classifier. |
| LLM / fallback / response composition | `call_openai`, generic fallback path, `core/bounded_voice_renderer.py`, `docs/product/BOUNDED_LLM_VOICE_RENDERER_V1_DESIGN.md`, response-envelope smokes | Runtime fallback plus shadow/test-only renderer | LLM must remain last and cannot execute tools or writes. Use bounded voice/composer validation patterns. |
| Memory / library / vault / persistence | `memory_store.py`, SQLCipher DB env via `scripts/val0py`, `core/context_snapshot.py`, `core/memory_spine.py`, `docs/architecture/INFINITE_MEMORY_LIBRARY_ARCHITECTURE_V0.md`, `docs/product/MEMORY_SPINE_01A_*`, `docs/product/MEMORY_SPINE_01B_*` | Mixed runtime DB, design docs, fixture-only spike | Do not activate memory spine casually. Confirmed memory writes need consent and deterministic path. |
| Adaptive intake / onboarding / founder-beta flows | `core/adaptive_intake.py`, `core/onboarding_discovery.py`, INTAKE-01A/B/C docs, ONBOARDING-01A through 01H docs, founder intro/product docs | Runtime active for volatile flows; docs for designs | Assimilate into future classifier sample harness. Keep volatile state and no persistence. |
| Calendar / reminders / pending confirmations | Google Calendar read/create/delete handlers in `bot.py`, `core/client_gcal_*`, `core/gcal_*`, `core/pending_actions.py`, `core/reminders.py`, `core/reminders_mvp.py`, many Karen agenda/reminder/task smokes | Runtime active | High-trust lane. Pending confirmations beat new intent; deterministic handlers execute. |
| Documents / OCR / Caso Finca / legal-admin workflows | `core/document_*`, `core/case_workspace.py`, `core/case_timeline_events.py`, `core/karen_*case*`, `docs/architecture/KAREN_DOCUMENT_INGESTION_READINESS_PLAN.md`, Caso Finca docs/smokes | Runtime active plus fixture/test SQLite lanes | Strong product asset. Keep source-grounded, read-only unless explicit reviewed write lane. |
| Voice / transcription / voice renderer | `handle_voice` in `bot.py`, Whisper path, `/voice`, `core/karen_voice.py`, `core/bounded_voice_renderer.py`, voice renderer diagnostics/smokes | Runtime active for voice input/replies; renderer shadow/test-only | Voice normalization remains WATCH. Do not merge voice/text routing until text router is stable. |
| n8n / Nathan / external automation | `docs/architecture/TOOL_ASSIMILATION_MAP.md`, `docs/architecture/INFINITE_MEMORY_LIBRARY_ARCHITECTURE_V0.md`, document ingestion readiness notes mention n8n/Nate-style intake | Docs-only candidate | External automation may send non-sensitive events; it must not mutate Val0 memory/calendar/legal/client files. |
| Ops / Launchpad / Night Runner / OPEL / ValPrime continuity | `docs/ops/NIGHT_RUNNER_*`, `scripts/ops/night_runner_*`, `scripts/diagnostics/new_chat_recovery_brief.py`, `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`, `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md` | Diagnostic / ops docs | Night Runner is guarded diagnostics/reporting; ValPrime is operational continuity; OPEL is event/audit concept. |
| Product / sales / founder-beta / Ale/Karen setup kits | Founder beta docs, Ale brief docs, setup kits, Karen RC status map, offer/pricing docs | Docs/product | Use for packaging and talk track; do not treat all product docs as runtime truth. |
| Quality gates / smokes / diagnostics | `scripts/quality/*`, `scripts/diagnostics/*`, `karen_rc_full_smoke.py`, `client_isolation_audit.py`, markdown inventory diagnostics | Runtime-independent quality layer | This is the executable memory of the system. Expand it before refactoring. |
| Deprecated, stale, duplicated, risky systems | Older state docs, old branch names in source indexes, old Karen handoffs, legacy `core/karen_intent_router.py`, older case MVP variants | Historical / stale / unknown | Preserve for audit; do not let old snapshots override current branch/head/smokes. |

## 3. Runtime-Active vs Shadow vs Diagnostic vs Stale

### Runtime-active

- `bot.py` deterministic routing and fallback path.
- Google Calendar read/create/delete with confirmation where configured.
- Val reminders, tasks, pending action flows, agenda/Daily Operator paths.
- Document inventory, summaries, OCR runtime, Caso Finca workspace/Q&A/timeline read paths.
- Voice transcription and `/voice` mode.
- Volatile adaptive intake and onboarding discovery.
- SQLCipher-backed existing memory/log/task/reminder/case infrastructure through established runtime paths.

### Shadow-only

- Intent Router v2 predictions and observer comparisons.
- Conversation router shadow logging.
- Bounded voice renderer candidate generation / observation.
- Intent interpreter shadow logging where enabled.

### Diagnostic

- Router sample harness and coverage report.
- Markdown docs inventory.
- New chat recovery brief.
- Night Runner dry-run, readiness, patch review, and guarded report scripts.
- OCR spike diagnostics and document inventory audit.
- Benchmark/radar diagnostics.

### Docs-only

- LLM router assimilation and Personal OS conversationality path.
- Memory spine durable intake design and object model.
- External automation/tool assimilation strategy.
- Obsidian/vault role clarification.
- Product packaging, founder beta, Ale, roadmap, and setup-kit docs.

### Stale / historical / unknown

- Old state/checkpoint docs that refer to prior branches or older milestone names.
- Older Karen handoffs and dated pass reports.
- Older case MVP variants and legacy intent helpers that still contain useful patterns but may not be current source-of-truth.
- Product/demo docs that describe aspiration rather than active runtime.

## 4. Borg-Assimilation Candidates

1. Adaptive intake sample expansion: add INTAKE-01B/01C phrases to the existing Intent Router v2 sample harness instead of creating a new classifier harness.
2. Operator response composer: reuse `core/bounded_voice_renderer.py` validation patterns for side-effect-free response composition.
3. Memory proposal flow: reuse MEMORY-SPINE-01A object model and MEMORY-SPINE-01B fixture-only consent guards before any runtime persistence.
4. Personal OS daily workflow: reuse Daily Operator collectors/renderers, agenda/reminder/task smokes, and onboarding discovery rather than writing a new daily planner.
5. External automation: use `TOOL_ASSIMILATION_MAP` and n8n/Nate-style dummy payload tests before connecting any real integration.
6. Continuity: use ValPrime / New Chat Recovery / source-of-truth index / markdown inventory instead of relying on chat memory.
7. Document intelligence: reuse Caso Finca deterministic Q&A packets and OCR boundary docs before adding LLM answer generation.

## 5. Deprecated / Ignore List

- Do not use old demo/state docs as current truth without checking head, branch, and latest smokes.
- Do not revive legacy route helpers unless a focused lane proves they are still canonical.
- Do not treat Obsidian or `valeria_vault` as runtime truth.
- Do not treat Night Runner as an autonomous coding/deployment actor.
- Do not treat external automation as source-of-truth storage.
- Do not use product sales docs to infer implemented behavior.
- Do not trust old branch names in static docs over `git status --short --branch`.

## 6. Do-Not-Rebuild Warnings

- Do not rebuild a router; use `intent_router_v2`, observer labels, sample harness, and coverage report.
- Do not rebuild response safety from scratch; use bounded voice renderer validation ideas.
- Do not rebuild memory object shape; use MEMORY-SPINE-01A and the fixture-only MEMORY-SPINE-01B guard model.
- Do not rebuild onboarding from menus; use `core/onboarding_discovery.py` and `core/adaptive_intake.py`.
- Do not rebuild Daily Operator; use existing collectors/renderers and smokes.
- Do not rebuild OCR/document Q&A blindly; inspect document registry, OCR runtime, Caso Finca Q&A, and Forge/ValPrime OCR notes first.
- Do not build external automation before reading `TOOL_ASSIMILATION_MAP`.
- Do not add a new continuity protocol before checking New Chat Recovery and ValPrime source-of-truth docs.

## 7. Recommended Next 5 Lanes After LLM-ROUTER-01A

1. LLM-ROUTER-01B: expand existing shadow sample harness with adaptive intake/onboarding/founder-beta phrases.
2. ROUTER-ACTUAL-LABELS-01: add actual handler labels for adaptive intake and onboarding paths where missing, still shadow/diagnostic only.
3. LLM-CLASSIFIER-01: controlled JSON classifier spike, shadow only, using current router priority doctrine.
4. OPERATOR-RESPONSE-01: side-effect-free response composer using bounded voice renderer validation patterns.
5. MEMORY-SPINE-01C: confirmed memory save proposal flow design/smoke, disabled until explicit runtime approval.

## 8. Source-of-Truth Desk Files

Use `docs/architecture/CAPABILITY_INVENTORY_01_DESK_SOURCE_OF_TRUTH.md` as the short Desk map for this workstream.

Primary current files:

- `AGENTS.md`
- `docs/product/VAL0_MASTER_MILESTONE_MAP.md`
- `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`
- `docs/product/VAL0_DOCS_VALUE_MAP.md`
- `docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md`
- `docs/product/KAREN_RC_STATUS_MAP.md`
- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`
- latest `docs/architecture/ROUTER_*`
- `docs/architecture/CONVERSATIONAL_ROUTER_V1_DESIGN.md`
- `docs/architecture/LLM_ROUTER_01A_EXISTING_SHADOW_ROUTER_ASSIMILATION_PLAN.md`
- `docs/architecture/TOOL_ASSIMILATION_MAP.md`
- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`

## 9. Guardrails At Risk Of Being Forgotten

- Protected live data may be dirty; do not stage, reset, discard, edit, or commit it.
- Client isolation first.
- Shadow mode default OFF.
- Pending confirmations beat new intent.
- Deterministic high-trust routes beat LLM.
- LLM fallback last.
- LLM cannot execute tools, write memory, create/delete calendar events, create reminders, or mutate client files.
- No hidden memory/persistence; consent before saving.
- OCR/LLM summaries are not legal truth.
- External automation cannot become source-of-truth or mutate sensitive systems.
- Night Runner cannot commit, restart, deploy, or touch live client data unless a future explicit approval changes its scope.

## 10. Immediate Risks Found

1. Source-of-truth drift: some docs point to older branches or older milestone assumptions. Always verify current branch/head/status.
2. Route overlap: adaptive intake, onboarding, case/finca, documents, reminders, tasks, GCal, and generic fallback all rely on careful ordering.
3. Duplicate router concepts: `intent_router_v2`, `conversation_router`, `intent_interpreter`, and older Karen router helpers can confuse future work unless lanes state which one owns what.
4. Hidden already-built capability: bounded voice renderer and Night Runner are more complete than active memory may recall.
5. Stale context bleed: already observed in onboarding; future LLM classifier work must preserve active-state consumption.
6. Docs sprawl: useful product/architecture/ops material exists but can be mistaken for current runtime behavior.
7. External automation temptation: n8n/Nathan/Nate-style tools are useful only with dummy payloads until privacy/source-of-truth rules are explicit.

## 11. Recurring Audit Command

Use this before deep Personal OS/router/operator-response work:

```bash
git status --short --branch
git log --oneline -5
python3 scripts/diagnostics/val0_source_of_truth_check.py
python3 scripts/diagnostics/markdown_docs_inventory.py
python3 scripts/diagnostics/intent_router_v2_coverage_report.py
python3 scripts/quality/karen_rc_full_smoke.py --keep-going
python3 scripts/quality/client_isolation_audit.py
git diff --check
git diff --cached --name-only -- clients/karen/CLIENT_FOLDERS.json clients/karen/CLIENT_GROCERY.md
```

For a lightweight docs-only inventory lane, use:

```bash
python3 scripts/quality/capability_inventory_audit_smoke.py
python3 scripts/quality/client_isolation_audit.py
git diff --check
git status --short --branch
```
