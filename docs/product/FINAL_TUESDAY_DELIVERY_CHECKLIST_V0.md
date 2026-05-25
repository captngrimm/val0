# FINAL_TUESDAY_DELIVERY_CHECKLIST_V0

Purpose:
Final delivery checklist for Tuesday Karen founder-beta so the operator can verify readiness without improvising or touching runtime.

This is an operator checklist only. It is not runtime config, not a bot route, not a deployment plan, and not permission to change production behavior before Tuesday.

Tone:
Practical, verify-only, founder-beta safe.

---

## 1. Purpose

This checklist keeps Tuesday delivery calm and bounded.

Use it to verify:

- repo state
- service availability
- core founder-beta prompts
- calendar/agenda reads
- document inventory
- Daily Operator
- founder intro
- feedback capture readiness

Do not use this checklist as a reason to live-edit runtime.

---

## 2. Final Delivery Principle

Verify, do not modify.

Rules:

- No runtime changes unless there is a true delivery blocker.
- No promises beyond current capability.
- No feature expansion before the demo.
- No risky fixes during the demo window.
- No touching sensitive systems unless explicitly scoped.

Operator line:

```text
Antes del martes verifico. No improviso features.
```

If a non-blocker appears:

```text
Lo marco para después del demo. No lo arreglo en vivo.
```

---

## 3. Night-Before Checklist

### Repo / Docs

- [ ] Repo clean: `git status --short`.
- [ ] Branch is correct.
- [ ] Latest commit known.
- [ ] AGENTS.md present.
- [ ] No uncommitted docs/code changes.
- [ ] Demo runbook ready: `docs/product/TUESDAY_LIVE_DEMO_RUNBOOK_V0.md`.
- [ ] Feedback capture doc ready: `docs/product/FOUNDER_BETA_WEEK1_FEEDBACK_CAPTURE_V0.md`.
- [ ] Final delivery pack ready: `clients/karen/KAREN_FINAL_DELIVERY_PACK_V0.md`.
- [ ] Week-1 test manual ready: `clients/karen/KAREN_WEEK1_TEST_MANUAL_V0.md`.

### Operator Checkpoint

- [ ] Latest checkpoint posted to ValPrime or operator notes.
- [ ] Known limitations reviewed.
- [ ] Roadmap wording ready: ready vs planned vs later.
- [ ] Feedback categories ready: bug, confusion, delight, missing feature, trust concern, willingness-to-pay signal.

### Service State

- [ ] Service active.
- [ ] No duplicate/conflicting bot process known.
- [ ] No planned runtime edits.
- [ ] No dependency or integration changes queued.

Night-before decision:

```text
If it is not a blocker, leave runtime alone.
```

---

## 4. Morning-Of Checklist

Run one check at a time. Save outputs only as operator notes if needed; do not paste private details into product docs.

### Bot Status

- [ ] Bot responds.
- [ ] Response time is acceptable.
- [ ] No obvious error loop.

### Founder Intro Smoke

Prompt:

```text
Val, qué eres?
```

Pass if:

- says founder-beta or equivalent honest framing
- describes personal operating layer
- does not promise magic memory
- does not promise autonomous actions

### Capability Smoke

Prompt:

```text
Val, qué puedes hacer?
```

Pass if:

- short, useful list
- no unsupported broad promises
- current workflows are recognizable

### Agenda Read Smoke

Prompt:

```text
Val, qué tengo mañana?
```

Pass if:

- answers agenda/tomorrow intent
- does not route to documents or chronology
- does not invent calendar access

### Google Calendar Read Smoke

Prompt:

```text
Val, qué tengo en calendario?
```

Pass if:

- read behavior works where configured
- calendar source is not confused with internal reminders
- no calendar write action happens

### Daily Operator Smoke

Prompt:

```text
Val, qué hago hoy?
```

Pass if:

- compact daily summary
- useful next step
- no long full report by default
- no unsupported drilldown promise

### Finca Facts Smoke

Prompt:

```text
Val, qué sabes de la finca 10082?
```

Pass if:

- grounded context
- no legal conclusions
- no invented facts
- no raw technical dump

### Document Inventory Smoke

Prompt:

```text
Val, qué documentos tengo?
```

Pass if:

- compact document inventory/status
- no technical IDs by default
- OCR/manual-review limits honest
- no unrelated client data

Morning-of decision:

```text
If all core smokes pass, stop checking and preserve the baseline.
```

---

## 5. Optional Safe Live Tests

Only use these if the core smokes passed and the demo needs them.

### Agenda Query

```text
Val, qué tengo mañana?
```

Use if:

- agenda smoke passed
- Karen asks about tomorrow/prep

### Roadmap Query

```text
Val, qué sigue?
```

Use if:

- roadmap answer mode is expected to separate ready/planned/later
- operator is ready to clarify if Val overstates readiness

### Capabilities Query

```text
Val, qué puedes hacer?
```

Use early in demo.

### Finca Memory Query

```text
Val, qué sabes de la finca?
```

Use if:

- finca facts smoke passed
- operator is ready to remind: organization, not legal advice

Rule:
Optional tests are read-only unless a create action is explicitly verified as safe and needed.

---

## 6. Do-Not-Touch List

Do not touch before or during Tuesday delivery:

- `bot.py`
- OAuth/token files
- systemd
- calendar write internals
- memory schema/runtime
- OCR runtime
- conversational router runtime
- real client data
- production documents
- external service configuration
- `/etc/val0`

Do not "quick fix":

- route ordering
- calendar writes
- document ingestion
- OCR/photo handling
- memory schema
- cross-client behavior

Unless:

```text
Delivery is impossible, the blocker is clearly identified, and the fix is explicitly scoped.
```

---

## 7. If Something Fails

### Classify Blocker Vs Cosmetic

Blocker examples:

- bot does not respond
- founder intro makes unsafe claims
- document inventory exposes unrelated client data
- legal conclusion is presented as fact
- agenda route is completely broken for required demo path

Cosmetic examples:

- answer is slightly long
- provenance is mildly technical
- copy feels a little stiff
- roadmap wording needs operator clarification

### Fallback Phrase To Karen

For a bug:

```text
Esto es founder-beta y lo marco como fallo. No lo voy a arreglar en vivo para no romper otra cosa.
```

For roadmap/future:

```text
Eso tiene sentido, pero no está listo hoy. Lo marco como roadmap.
```

For OCR/photo:

```text
Fotos/OCR todavía no son final. Lo correcto es que Val diga si requiere revisión.
```

For legal boundary:

```text
Val organiza información y preguntas, pero no reemplaza criterio legal.
```

### Capture Feedback

Record:

- prompt/workflow
- what happened
- category
- severity
- user reaction
- next action

### Postpone Risky Fix

Postpone unless delivery is impossible.

Decision line:

```text
If the demo can continue honestly, continue. Do not repair runtime live.
```

---

## 8. Demo Success Criteria

The demo succeeds if:

- Karen understands what Val is.
- Karen sees real value in at least 2 workflows.
- Karen knows what is ready vs roadmap.
- No trust-breaking behavior happens.
- No legal advice is implied.
- No unsupported OCR/photo claim is made.
- No autonomous action claim is made.
- Document status is honest enough to test.
- Agenda/tomorrow flow is understandable enough to test, if configured.
- Feedback is captured.
- Karen knows what to try during week 1.

Minimum success:

```text
Karen leaves knowing what Val can help with this week and how to send feedback.
```

---

## 9. Post-Demo Checklist

### Checkpoint

- [ ] Create post-demo checkpoint.
- [ ] Record what passed.
- [ ] Record what failed.
- [ ] Record what was confusing.
- [ ] Record what created value.
- [ ] Record what stayed roadmap/parked.

### Feedback Log Update

- [ ] Add bugs.
- [ ] Add confusion/friction.
- [ ] Add delight/value moments.
- [ ] Add missing features.
- [ ] Add trust/safety concerns.
- [ ] Add willingness-to-pay signals if explicit.
- [ ] Keep Karen-only sensitive details out of reusable product docs.

### Next Build Decision

- [ ] Decide whether any blocker requires hotfix.
- [ ] Decide whether next build is feedback capture, read-only memory inventory, document labels, or Daily Operator polish.
- [ ] Do not start high-risk runtime work without a scoped milestone.

### Karen Recap Message

Send a short recap:

```text
Gracias por probar Val hoy. Lo que puedes probar esta semana: documentos, cronología, qué hago hoy/mañana y preparación para reunión. Lo que marqué como feedback: [2-3 puntos]. Lo que queda en roadmap: [1-2 puntos]. Si algo sale raro, largo o confuso, mándame screenshot o copia de la respuesta.
```

---

## 10. Open Risks

- Bot/service unavailable on demo morning.
- Calendar read fails or is stale.
- Agenda route answers the wrong intent.
- Document inventory exposes technical noise.
- Finca answer drifts toward legal conclusion.
- Daily Operator gets too long.
- Roadmap answer overstates readiness.
- Karen asks to upload photos/documents live.
- Operator is tempted to live-edit runtime.
- Feedback includes private legal details that should not enter product docs.
- A cosmetic issue feels urgent and distracts from delivery.

Risk posture:

```text
Protect trust first. A small honest limitation is better than a live risky fix.
```
