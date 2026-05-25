# TUESDAY_LIVE_DEMO_RUNBOOK_V0

Purpose:
Practical live demo/runbook for Karen Tuesday founder-beta delivery.

This is an operator runbook only. It is not runtime config, not a bot route, not a deployment checklist for system changes, and not a promise that roadmap features are ready before Tuesday.

Tone:
Spanish-first prompts, practical, calm, honest, demo-safe.

---

## 1. Purpose

The Tuesday live demo should show Karen what Val can do now, explain limits clearly, and collect week-1 feedback without destabilizing the founder-beta runtime.

The goal is:

```text
Show useful workflows, protect trust, and leave Karen with a simple way to test Val during week 1.
```

This runbook is for Frank/operator. It should be used alongside the Karen final delivery pack and week-1 test manual.

---

## 2. Demo Principles

- Do not overpromise.
- Show what works.
- Clearly mark roadmap/future features.
- Avoid risky live runtime edits.
- Capture feedback without derailing the demo.
- Run one prompt at a time.
- Wait for Val to answer before sending the next prompt.
- Do not upload new sensitive documents unless explicitly approved for the demo.
- Do not present OCR/photo reading as final.
- Do not let legal/admin organization sound like legal advice.

Simple line:

```text
Esto es founder-beta: útil para probar flujos concretos, no la app final.
```

Roadmap line:

```text
Eso está en roadmap, pero no lo voy a vender como listo hoy.
```

---

## 3. Pre-Demo Checklist

Do this before the live demo window. If any check fails, do not live-edit runtime; note the issue and use the failure handling section.

### Runtime / Repo State

- [ ] Bot active.
- [ ] Repo clean: `git status --short`.
- [ ] Latest commit known.
- [ ] No uncommitted docs/code changes.
- [ ] No runtime edits in progress.

### Calendar / Agenda

- [ ] Google Calendar read check.
- [ ] Agenda query check.
- [ ] Tomorrow query check.

Suggested precheck prompts:

```text
Val, qué tengo hoy?
Val, qué tengo mañana?
```

### Founder Intro

- [ ] Founder intro check.

Prompt:

```text
Val, qué eres?
```

Expected:

- founder-beta framing
- personal operating layer
- no magic/infinite memory
- no autonomous-action claim

### Capability Check

- [ ] Capabilities answer is short and realistic.

Prompt:

```text
Val, qué puedes hacer?
```

Expected:

- documents
- chronology
- agenda/reminders where enabled
- Daily Operator
- meeting/lawyer prep
- limits are not hidden

### Finca / Case Context

- [ ] Finca facts check.
- [ ] Case/year recall check if needed.

Prompts:

```text
Val, qué sabes de la finca 10082?
Val, qué pasó en 2024?
```

Expected:

- grounded context
- no legal conclusions
- no invented facts
- no raw technical dump

### Documents

- [ ] Document inventory check.

Prompt:

```text
Val, qué documentos tengo?
```

Expected:

- compact inventory/status
- no technical IDs by default
- OCR/review limits honest

### Daily Operator

- [ ] Daily Operator check.

Prompt:

```text
Val, qué hago hoy?
```

Expected:

- compact next-step summary
- not a long full report by default
- no unsupported drilldown promise

---

## 4. Suggested Demo Sequence

Use this order unless Karen naturally asks for something else.

### 1. What Val Is

Prompt:

```text
Val, qué eres?
```

Say:

```text
Quiero empezar por cómo Val se explica a sí mismo.
```

Look for:

- founder-beta framing
- clear limits
- practical value

### 2. What Val Can Do

Prompt:

```text
Val, qué puedes hacer?
```

Say:

```text
Esto marca qué sí probar esta semana y qué queda en roadmap.
```

### 3. Agenda Today / Tomorrow

Prompts:

```text
Val, qué hago hoy?
Val, qué tengo mañana?
```

Say:

```text
Aquí quiero ver si ayuda a decidir qué sigue y a prepararte para mañana.
```

### 4. Finca Facts

Prompt:

```text
Val, qué sabes de la finca 10082?
```

Say:

```text
Esto debe organizar contexto, no dar conclusiones legales.
```

### 5. Document Status

Prompt:

```text
Val, qué documentos tengo?
```

Say:

```text
Aquí lo importante es que se entienda qué existe y qué requiere revisión/OCR.
```

### 6. Roadmap / Future

Prompt:

```text
Val, qué sigue?
```

Say:

```text
Esto debe separar lo listo de lo planificado.
```

### 7. Founder-Beta Trial Frame

Prompt:

```text
Val, puedo probar Val una semana?
```

Say:

```text
La idea de esta semana es probar flujos concretos y mandarme feedback.
```

### 8. Reminder / Calendar Create Only If Safe

Only show creation if the current runtime has already been verified and the action is low-risk.

If safe:

```text
Val, recuérdame mañana revisar los documentos.
```

If not safe, say:

```text
Crear o cambiar cosas en vivo lo dejamos fuera de esta demo. Hoy quiero enseñarte las consultas seguras.
```

---

## 5. Exact Sample Prompts In Spanish

Primary prompts:

```text
Val, qué eres?
Val, qué puedes hacer?
Val, qué tengo mañana?
Val, qué sabes de la finca 10082?
Val, qué documentos tengo?
Val, qué sigue?
Val, puedo probar Val una semana?
```

Optional prompts:

```text
Val, qué hago hoy?
Val, qué pasó en 2024?
Val, ordéname la cronología del caso
Val, prepárame para hablar con la abogada
Val, dame el resumen completo de hoy
```

Operator rule:
Send one prompt at a time and wait for the answer.

---

## 6. What Not To Demo

Do not demo:

- untested OCR
- full free chat as if grounded memory retrieval is finished
- legal conclusions
- unsupported file types as if understood
- runtime changes
- bulk document upload/migration
- system/admin commands
- multi-client onboarding
- carpetas/folders as ready runtime if still roadmap
- unified agenda as ready if it has not been verified
- autonomous actions

Safe wording:

```text
Eso todavía no lo probamos como feature lista. Lo marco como feedback/roadmap.
```

---

## 7. Failure Handling

### If Agenda Fails

Say:

```text
Esto lo marcamos como fallo de agenda. No voy a arreglarlo en vivo; lo reviso después para no romper la demo.
```

Then:

- capture as bug
- continue to documents or intro flow
- do not edit runtime

### If Calendar Fails

Say:

```text
Si Google Calendar no responde bien, lo marco como integración/lectura de calendario. Val no debe inventar eventos.
```

Then:

- capture source of failure
- avoid create/delete calendar demo
- continue with document or Daily Operator flow

### If Val Gives Weird Answer

Say:

```text
Esto es justo el tipo de cosa que quiero capturar en founder-beta: respuesta rara, confusa o demasiado larga.
```

Then classify:

- bug
- confusion/friction
- trust/safety concern

Do not argue with the answer in front of the user. Move on.

### If Karen Asks For Future Feature

Say:

```text
Eso tiene sentido, pero no lo vendo como listo hoy. Lo marco como roadmap y vemos si aparece como prioridad esta semana.
```

Then:

- capture as missing feature or roadmap idea
- ask if it is high priority only if useful
- do not promise timeline

### If Upload / Photo Does Not Parse

Say:

```text
Fotos/OCR todavía no son final. Si Val dice que requiere revisión, eso es esperado. Lo importante es que no finja entenderlo.
```

Then:

- capture as OCR/manual review feedback
- do not retry repeatedly with sensitive documents
- do not present unsupported extraction as ready

---

## 8. Feedback Capture During Demo

Capture short notes without derailing the flow.

Categories:

- bug
- confusion
- delight
- missing feature
- trust concern
- willingness-to-pay signal

Simple capture template:

```text
Feedback:
- Prompt/workflow:
- What happened:
- Category:
- Severity:
- User reaction:
- Next action:
```

Examples:

```text
Bug: agenda routed to documents.
Confusion: document status was too technical.
Delight: prep checklist helped before lawyer conversation.
Missing feature: wants easier photo/document upload.
Trust concern: did not know whether item was saved.
WTP signal: says she would use/pay if reminders before meetings are reliable.
```

Rule:
Capture product signal, not private legal details.

---

## 9. Post-Demo Actions

### 1. Checkpoint

Create a short post-demo checkpoint:

- what worked
- what failed
- what confused Karen
- what created value
- what is next
- what stays roadmap/parked

### 2. Update Feedback Log

Classify feedback:

- bug
- confusion/friction
- delight/value moment
- missing feature
- roadmap idea
- trust/safety concern
- willingness-to-pay signal
- reusable pattern
- Karen-only case detail

### 3. Decide Next Fix / Build

Use the post-Tuesday decision matrix:

- fix blocker
- polish confusing existing flow
- add to roadmap
- park
- scope as paid/client-driven if applicable

### 4. Send Karen Recap

Suggested recap:

```text
Gracias por probarlo hoy. Lo que quedó listo para probar esta semana: documentos, cronología, qué hago hoy/mañana y preparación para reunión. Lo que marqué como feedback: [2-3 puntos]. Lo que queda roadmap: [1-2 puntos]. Si algo sale raro, mándame screenshot o copia de la respuesta.
```

Do not include private case details in reusable product docs.

---

## 10. Success Criteria

Demo is successful if:

- Karen understands Val is founder-beta, not final app.
- Karen sees at least 2 useful workflows.
- Val does not imply legal advice.
- Val does not imply autonomous actions.
- Val does not claim OCR/photos are final.
- Document inventory/status is understandable enough to test.
- Agenda/tomorrow flow is understandable enough to test, if configured.
- Feedback is captured without derailing the demo.
- Roadmap/future features are framed honestly.
- No live runtime edits are made.

Minimum good outcome:

```text
Karen knows what to try this week and how to send feedback.
```

---

## 11. Open Risks

- Agenda or calendar read may fail live.
- Val may answer too long or too technically.
- Timeline may still show provenance noise.
- Karen may ask for OCR/photo upload before it is ready.
- Karen may ask for legal conclusions.
- A future feature may sound more exciting than the current working baseline.
- Operator may be tempted to fix live.
- Feedback may include sensitive details that should not enter product docs.
- Calendar/reminder create may be unsafe to demo unless verified immediately before.

Risk rule:

```text
If something fails, capture it and keep the demo moving. Do not repair runtime live.
```

---

## 12. Operator Close

Close with:

```text
Esta semana no quiero que pruebes todo. Quiero que uses estos flujos cuando te sirvan: documentos, cronología, qué hago hoy/mañana y preparación para reunión. Si algo ayuda, confunde, sale largo o falta, me lo mandas y lo uso para decidir la próxima mejora.
```
