# KAREN_TUESDAY_DELIVERY_SMOKE_CHECKLIST_V0

Purpose:
Tuesday founder-beta delivery smoke checklist for Karen / client-zero.

Use this before showing or delivering the current Val0 Personal founder-beta experience to Karen. This is not a production launch, not a final app checklist, and not a promise that every future workflow is ready. It is an operator checklist for Frank to confirm that the useful Tuesday flows are working, honest, and safe enough to show.

Tone:
Spanish-first, operator-ready, practical, honest, no corporate sludge.

---

## 1. Delivery Framing

Tuesday delivery is founder-beta functional delivery.

Say it plainly:

```text
Esto no es la app final. Es una entrega founder-beta: ya debe servir para flujos concretos, y lo que no esté listo queda claro en roadmap.
```

The Tuesday core is useful for:

- understanding what Val is and what it can do now
- document inventory/status
- chronology/timeline
- year-specific case questions
- Daily Operator compact
- full Daily Operator summary by explicit request
- tomorrow agenda
- lawyer/advisor meeting prep
- honest OCR/photo/document boundaries
- roadmap after delivery

The roadmap continues after Tuesday. Do not turn Tuesday into a promise of full self-serve onboarding, perfect document reading, legal analysis, autonomous action, or final product readiness.

---

## 2. Must-Pass Smoke Tests

Run in the intended Karen/client-zero test chat only.

### 1. Identity / Framing

Prompt:

```text
Val, qué eres
```

Must pass:

- explains Val as founder-beta / personal operating layer
- does not frame Val as only a Telegram bot
- does not claim final public SaaS readiness
- does not promise magic memory or autonomous actions

### 2. Capability Summary

Prompt:

```text
Val, qué puedes hacer
```

Must pass:

- names current useful capabilities in plain Spanish
- keeps the answer short enough to read
- mentions documents, reminders/agenda, chronology, Daily Operator, and meeting prep only as scoped current capabilities
- avoids promising every module is enabled everywhere

### 3. Documents

Prompt:

```text
Val, qué documentos tengo
```

Must pass:

- routes to document inventory/status
- does not route to Daily Operator
- does not route to timeline
- does not expose raw paths, server internals, private IDs, or unrelated client data
- shows readiness/status honestly

### 4. Chronology

Prompt:

```text
Val, ordéname la cronología del caso
```

Must pass:

- routes to case timeline/chronology
- shows registered chronology or a clear no-events message
- preserves source/provenance where available
- includes legal/professional boundary
- does not become generic advice

### 5. Year-Specific Case Question

Prompt:

```text
Val, qué pasó en 2024
```

Must pass:

- routes to the case timeline/year route
- does not answer as generic world history
- does not route to document inventory
- does not invent facts outside registered context

### 6. Daily Operator Compact

Prompt:

```text
Val, qué hago hoy
```

Must pass:

- routes to Daily Operator
- returns compact output by default
- stays short and numbered
- shows read-only boundary
- shows legal/professional boundary when relevant
- does not dump old timeline/history
- does not dump full document lists
- does not say `dame detalles del 1` until drilldown exists
- includes the full-summary hint:

```text
Val, dame el resumen completo de hoy
```

### 7. Daily Operator Next

Prompt:

```text
Val, qué sigue
```

Must pass:

- routes to compact Daily Operator if currently handled by that route
- remains short
- does not duplicate the same pending item as both next pending and suggested action
- keeps read-only wording

### 8. Daily Operator Full Summary

Prompt:

```text
Val, dame el resumen completo de hoy
```

Must pass:

- returns the fuller Daily Operator view
- keeps read-only boundary
- keeps legal/professional boundary
- is available only by explicit full-summary request
- does not become the default for `qué hago hoy`

### 9. Tomorrow Agenda

Prompt:

```text
Val, qué tengo mañana
```

Must pass:

- routes to agenda/calendar/reminder dashboard
- does not route to Daily Operator
- does not route to document/timeline/legal routes
- does not claim unsupported calendar access

### 10. Lawyer / Advisor Meeting Prep

Prompt:

```text
Val, prepárame para hablar con la abogada
```

Must pass:

- produces checklist-style prep
- helps organize questions, documents, and next actions
- does not give legal conclusions
- does not replace lawyer/advisor judgment
- does not invent private facts

Optional companion prompt:

```text
Val, prepárame para hablar con el advisor
```

---

## 3. Route Preservation Checks

Pass only if:

- document route is not stolen by Daily Operator
- timeline route is not stolen by Daily Operator
- agenda/calendar route is not stolen by Daily Operator
- reminder mutation routes are not stolen by Daily Operator
- Founder Intro / capability route remains safe and short
- compact Daily Operator stays compact
- full Daily Operator appears only by explicit full-summary phrase

Red flag examples:

- `Val, qué documentos tengo` returns `🧭 Hoy`
- `Val, ordéname la cronología del caso` returns a generic assistant answer
- `Val, qué tengo mañana` returns Daily Operator
- `Val, qué hago hoy` returns a long report by default
- compact output tells Karen to say `dame detalles del 1`

---

## 4. Expected Output Criteria

Compact outputs:

- short enough to read on WhatsApp/Telegram
- 3-5 numbered items max
- focused on today / next useful action
- no old history unless directly relevant
- no full document dump
- no duplicate next pending / suggested action
- full summary available only by explicit request

Boundaries:

- no professional/legal advice claim
- no autonomous action claim
- OCR/photo limitations stated honestly
- DOCX/photo extraction not guaranteed
- read-only boundary visible where relevant
- legal/professional boundary visible for case/legal/admin flows

Daily Operator compact must include:

```text
Si quieres más detalle, pide: "Val, dame el resumen completo de hoy".
```

Daily Operator compact must not include:

```text
dame detalles del 1
```

until detail drilldown exists.

---

## 5. Nice-To-Have Tests

Run only after must-pass checks are green.

- Voice version of top prompts, if voice path is enabled.
- One uploaded clean text/PDF, only if safe and non-sensitive.
- One photo/screenshot boundary test, only with a harmless file.
- One reminder/agenda check that does not mutate without confirmation.
- One founder-intro question:

```text
Val, puedo probar esto una semana?
```

Expected:

- guided one-workflow pilot
- not "test everything"
- no self-serve onboarding promise

---

## 6. Known Limitations To Disclose

Say these plainly if they come up:

- OCR/photos are not final.
- DOCX/photo extraction is not guaranteed.
- Val does not have infinite memory.
- Val is not yet a full ChatGPT-like open conversation for every topic.
- Val does not provide legal advice or professional judgment.
- Val does not take autonomous actions.
- Folders/carpetas are roadmap, not Tuesday core.
- Unified agenda is roadmap, not fully merged yet.
- Detail drilldown like `dame detalles del 1` is not implemented yet.
- Tuesday is not self-serve onboarding.

Safe wording:

```text
Prefiero que Val diga "esto todavía necesita revisión" antes que fingir que ya lo entendió todo.
```

---

## 7. Tuesday Demo Order

Use this order. Do not start with the longest report.

1. `Val, qué eres`
2. `Val, qué puedes hacer`
3. `Val, qué documentos tengo`
4. `Val, ordéname la cronología del caso`
5. `Val, qué pasó en 2024`
6. `Val, qué hago hoy`
7. `Val, qué tengo mañana`
8. `Val, prepárame para hablar con la abogada`
9. Explain OCR/photo/DOCX boundaries.
10. Explain roadmap / what improves after Tuesday.

Only show full Daily Operator if Karen asks for more context, or as a controlled second step:

```text
Val, dame el resumen completo de hoy
```

---

## 8. Failure Handling

If a route is stolen:

- pause
- mark blocker
- fix before delivery
- rerun compile, audit, relevant smoke, and live prompt

If output is too long:

- mark polish blocker
- do not explain it away as "more complete"
- compact the default or move detail behind explicit request

If OCR/photo expectation appears:

- disclose limitation
- show status honesty
- put improvement on roadmap

If legal conclusion appears:

- treat as blocker
- add or tighten legal/professional boundary
- do not deliver that flow until fixed

If real private data appears in an unsafe place:

- stop demo
- do not continue live
- identify source and containment path
- do not paste private details into product docs

---

## 9. Monday Work Plan

Monday is for stabilization, not feature sprawl.

Do:

- run this checklist
- run existing smoke scripts
- fix blockers only
- avoid new feature creep
- document known limits
- prepare Karen handoff message
- prepare a short roadmap-after-Tuesday note

Do not:

- add major new workflows
- add detail drilldown unless already scoped and tested
- promise folders/carpetas as Tuesday core
- promise unified agenda as complete
- upload sensitive documents just to test
- change route ordering unless a blocker requires it

---

## 10. Tuesday Pass / Fail

### PASS

Proceed if:

- must-pass smoke tests pass
- compact Daily Operator is short
- full summary route works by explicit request
- documents/timeline/agenda routes are preserved
- OCR/photo/DOCX limits are honest
- legal boundary is visible
- no private/server data leaks

### PARTIAL

Proceed only with passing flows if:

- one nice-to-have fails
- optional upload is skipped
- a limitation is disclosed clearly

### FAIL

Do not deliver if:

- route stealing affects core prompts
- Daily Operator default is long again
- OCR/photo response overpromises
- legal advice appears
- autonomous action happens or is implied
- unrelated client/private data appears

---

## 11. Recommendation

Tuesday should be treated as founder-beta delivery, not final launch.

No new major features after smoke unless they are blockers. The win is not "Val does everything." The win is:

- Karen understands what Val is.
- Karen can see documents/status.
- Karen can ask chronology/year questions.
- Karen can ask `qué hago hoy` and get a compact useful answer.
- Karen can get full detail when she explicitly asks.
- Karen can prepare for a lawyer/advisor conversation without Val pretending to be the lawyer/advisor.
- Karen knows what is roadmap after Tuesday.
