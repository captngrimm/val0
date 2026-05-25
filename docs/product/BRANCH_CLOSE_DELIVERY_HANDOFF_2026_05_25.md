# BRANCH_CLOSE_DELIVERY_HANDOFF_2026_05_25

Purpose:
Closeout / delivery handoff report for the `karen-client-zero-mvp-2026-05-25` branch.

This is a docs-only handoff. It is not runtime config, not a deployment instruction, not a legal record, and not permission to keep adding risky runtime work to this branch before Tuesday delivery.

---

## 1. Purpose

Summarize what this branch became, what is ready for Tuesday Karen founder-beta delivery, what should stay protected, and what should happen next.

Use this report to:

- orient the operator before Tuesday
- preserve the sealed milestone state
- avoid improvising runtime changes
- guide post-demo branch selection
- keep roadmap items separate from ready runtime

Rule:

```text
This branch should close as a delivery branch, not become an endless staging ground.
```

---

## 2. Branch Info

- Branch name: `karen-client-zero-mvp-2026-05-25`
- Repo: `/opt/val0`
- Service: Val0 Telegram bot / Karen client-zero founder-beta surface
- Current latest HEAD after M39C: `798dc8e` `Polish founder trial response personality`
- Worktree at handoff creation: clean before this docs commit

---

## 3. What This Branch Became

### Karen Founder-Beta Delivery

This branch now contains the delivery packet, manual, smoke docs, runbook, final checklist, recap template, and targeted founder-trial copy polish needed to put Karen in a practical Tuesday founder-beta pilot.

### Founder / Val1 Offer Foundation

The branch also clarified founder-beta framing:

- not final app
- no magic memory
- no legal advice
- no autonomous actions
- roadmap continues after Tuesday
- feedback drives the next build

It also preserves a separate path for Val1 Business so business execution does not silently invade Karen's personal founder-beta.

### Memory / Conversationality Foundation

The branch produced the product design foundation for:

- Carpetas / Topic Containers
- document labels and naming
- unified agenda
- Memory Library v1
- conversational memory retrieval
- implementation phases after Tuesday

These are design foundations, not all runtime-ready features.

### Tuesday Demo Preparation

The branch now has:

- live demo runbook
- final delivery checklist
- smoke test script
- feedback capture system design
- feedback log template
- Karen post-demo recap message

---

## 4. Sealed Milestone Summary

| Milestone | Summary | Commit |
|---|---|---|
| M26 | Carpetas / Topic Containers design | `869ef47` |
| M27 | Document Labels / Naming Convention design | `a593dfb` |
| M28 | Unified Agenda / Single Day View design | `c441094` |
| M29 | Memory Library v1 design | `b1322b7` |
| M30 | Conversational Memory Retrieval design | `d2fb243` |
| M31 | Memory Foundation Implementation Map | `4d586f6` |
| M32 | Founder-Beta Post-Tuesday Decision Matrix | `8304539` |
| M33 | Founder-Beta Week-1 Feedback Capture design | `42c3c6f` |
| M34 | Tuesday Live Demo Runbook | `da698ce` |
| M35 | Final Tuesday Delivery Checklist | `21243ca` |
| M36 | Founder-Beta Feedback Log Template | `d229fc4` |
| M37 | Demo Smoke Test Script | `9f9e912` |
| M38 | Karen Post-Demo Recap Message Template | `89781a5` |
| M39 | Final Runtime Smoke + Founder Trial Copy Polish | `aa582a9`, `e806c6b`, `eb0de0c`, `798dc8e` |

M39 final state:
The response to `Val, puedo probar Val una semana?` is now warmer and closer to the Friends & Family founder-beta tone, while preserving route behavior and safety boundaries.

---

## 5. Current Runtime Readiness

Latest verified command checks from M39C:

- Compile passed: `./scripts/val0py -m py_compile bot.py`
- Client isolation audit passed: `python3 scripts/quality/client_isolation_audit.py || true`
- Founder intro smoke passed: `python3 scripts/quality/founder_intro_smoke.py`
- Founder trial copy polished: yes, in `core/founder_intro.py`

Operator/runtime smoke state from recent Tuesday prep:

- Bot service active: operator should verify again with final smoke before demo.
- Recent errors clean: operator should verify through the safe smoke path before demo if needed.
- Calendar/agenda read smoke works: recent smoke target is documented; verify again before demo with read-only prompts.

Important:
This handoff did not inspect or modify systemd, OAuth, tokens, `/etc/val0`, real client data, Google Calendar internals, memory schema, OCR, or external services.

---

## 6. Safe To Demo Tuesday

Safe demo candidates, assuming final smoke passes:

- `Val, qué eres?`
- `Val, qué puedes hacer?`
- `Val, qué tengo mañana?`
- `Val, qué hago hoy`
- `Val, qué sabes de la finca 10082?`
- `Val, qué documentos tengo?`
- `Val, qué sigue?`
- `Val, puedo probar Val una semana?`
- `Val, qué pasó en 2024?`
- `Val, ordéname la cronología del caso`
- `Val, prepárame para hablar con la abogada`

Demo stance:

```text
Show useful founder-beta workflows. Do not pretend the roadmap is ready.
```

---

## 7. Do Not Demo Or Promise

Do not demo or promise:

- perfect OCR/photo reading
- unsupported file types as understood
- full free-chat memory retrieval
- full carpetas/folders runtime
- unified agenda as complete runtime unless separately verified
- autonomous actions
- legal conclusions
- self-serve onboarding
- bulk document upload/migration
- multi-client onboarding
- Val1 Business workflows without paid/prospect scope

Safe wording:

```text
Eso está en roadmap, pero no lo vendo como listo hoy.
```

---

## 8. Do Not Touch Before Tuesday Unless Blocker

Do not touch:

- `bot.py`
- OAuth/tokens
- systemd
- Google Calendar internals
- memory schema/runtime
- OCR runtime
- conversational router runtime
- `/etc/val0`
- real client data
- production documents
- external service configuration

Only exception:

```text
Delivery is impossible, the blocker is clearly identified, and the fix is explicitly scoped.
```

---

## 9. Tuesday Operator Plan

1. Run final smoke.
   - Use `docs/product/DEMO_SMOKE_TEST_SCRIPT_V0.md`.
   - Stop once the core checks pass.

2. Use demo runbook.
   - Use `docs/product/TUESDAY_LIVE_DEMO_RUNBOOK_V0.md`.
   - Run one prompt at a time.
   - Keep roadmap language honest.

3. Capture feedback.
   - Use categories from `FOUNDER_BETA_WEEK1_FEEDBACK_CAPTURE_V0`.
   - Use the log shape from `FOUNDER_BETA_FEEDBACK_LOG_TEMPLATE_V0`.
   - Do not copy private case facts into reusable product docs.

4. Send recap.
   - Use `docs/product/KAREN_POST_DEMO_RECAP_MESSAGE_V0.md`.
   - Choose normal, failed-demo, excited, or overwhelmed variant.

5. Checkpoint after demo.
   - What worked.
   - What failed.
   - What confused Karen.
   - What created value.
   - What is next.
   - What stays roadmap/parked.

---

## 10. Post-Tuesday Recommended First Build Lanes

Recommended first lanes after Tuesday:

1. Feedback Log v0
   - Create a privacy-safe actual feedback record for Karen week 1.
   - Keep private legal facts out of product docs.

2. Memory Inventory read-only
   - Read-only source-aware inventory and review-needed views.
   - Client-scoped lookup required.

3. Document Labels runtime
   - Better human labels, source labels, status labels.
   - Preserve OCR/manual-review honesty.

4. Unified Agenda runtime v0
   - Read-only single-day view across calendar/reminders/tasks/document review.
   - Must preserve source labels and avoid mutation.

5. Carpetas basic commands
   - Only after read-only memory and labels are stable.
   - Start broad: Finca, Proyectos, Pendientes.

6. Conversational Memory Retrieval v0 later
   - Build only after safe read paths exist.
   - Do not start with full free-chat.

---

## 11. Open Risks

- Bot/service could fail on demo morning.
- Agenda/calendar read could be stale or unavailable.
- Timeline/provenance may still feel technical.
- Karen may ask for OCR/photo upload before it is ready.
- Karen may ask for legal conclusions.
- Operator may be tempted to live-edit runtime.
- Roadmap items may sound more exciting than current ready workflows.
- Feedback may include sensitive case detail that must not enter product docs.
- Current branch may accumulate too much unrelated runtime work if not closed.

Risk posture:

```text
Protect trust first. A clear limitation is better than a rushed promise.
```

---

## 12. Recommended Next Branch Options

### `karen-week1-feedback-2026-05-26`

Use for:

- actual post-demo feedback log
- checkpoint summaries
- week-1 polish decisions
- privacy-safe Karen founder-beta learning

### `val0-memory-foundation-runtime-v0`

Use for:

- read-only memory inventory
- document labels runtime
- source/status rendering
- client-isolated memory tests

### `val1-business-assessment-first-client`

Use for:

- paid/prospect-scoped Val1 Business assessment
- business workflow evaluation
- separate support/privacy assumptions

### `outreach-execution-founder-beta`

Use for:

- founder-beta outreach
- personal founder user discovery
- positioning validation
- lightweight non-runtime offer tests

---

## 13. Final Recommendation

Close this branch after Tuesday delivery or after final smoke, unless a true delivery blocker requires a tightly scoped fix.

Do not keep piling runtime onto this branch forever.

Recommended posture:

```text
Ship the Tuesday founder-beta baseline, capture feedback, then branch deliberately for the next lane.
```

