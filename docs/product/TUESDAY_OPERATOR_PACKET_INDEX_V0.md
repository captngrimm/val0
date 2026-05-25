# TUESDAY_OPERATOR_PACKET_INDEX_V0

Purpose:
One operator index for Frank: which docs to use before, during, and after the Karen Tuesday founder-beta demo.

This is a docs-only index. It is not runtime config, not a bot route, not a deployment instruction, and not permission to change runtime before Tuesday.

---

## 1. Purpose

This packet index tells the operator exactly which docs to open at each stage of the Tuesday founder-beta delivery.

Use it to avoid improvising:

- which checklist to run
- which prompts to demo
- how to capture feedback
- which recap to send
- which roadmap/design docs to reference after the demo
- which branch to open next

---

## 2. Current Branch / Head

- Branch: `karen-client-zero-mvp-2026-05-25`
- Latest sealed milestone: M40 Branch Close / Delivery Handoff Report
- Current HEAD before this index: `6fc2c98` `Add branch close delivery handoff report`
- Runtime posture: frozen unless blocker

Rule:

```text
Verify and demo. Do not keep patching runtime on this branch unless delivery is blocked.
```

---

## 3. Before Demo

Open these first.

### Final Delivery Checklist

Doc:
`docs/product/FINAL_TUESDAY_DELIVERY_CHECKLIST_V0.md`

Use for:

- night-before checklist
- morning-of checklist
- do-not-touch list
- blocker vs cosmetic decision
- post-demo checklist

### Demo Smoke Test Script

Doc:
`docs/product/DEMO_SMOKE_TEST_SCRIPT_V0.md`

Use for:

- pre-demo smoke
- exact smoke prompts
- pass/fail table
- failure handling
- go/no-go decision

Before-demo rule:

```text
If the core smoke passes, stop checking and preserve the baseline.
```

---

## 4. During Demo

### Live Demo Runbook

Doc:
`docs/product/TUESDAY_LIVE_DEMO_RUNBOOK_V0.md`

Use for:

- demo principles
- prompt order
- what not to demo
- failure handling
- feedback capture during demo

### Exact Demo Prompt Order

Recommended order:

1. `Val, qué eres?`
2. `Val, qué puedes hacer?`
3. `Val, qué hago hoy?`
4. `Val, qué tengo mañana?`
5. `Val, qué sabes de la finca 10082?`
6. `Val, qué documentos tengo?`
7. `Val, qué sigue?`
8. `Val, puedo probar Val una semana?`

Optional if useful:

- `Val, qué pasó en 2024?`
- `Val, ordéname la cronología del caso`
- `Val, prepárame para hablar con la abogada`
- `Val, dame el resumen completo de hoy`

Run one prompt at a time.

### What Not To Demo

Do not demo:

- untested OCR/photo reading
- full free chat as grounded memory
- legal conclusions
- unsupported file types as understood
- runtime changes
- bulk document upload/migration
- multi-client onboarding
- full carpetas runtime
- unified agenda as complete runtime unless separately verified
- autonomous actions

Safe phrase:

```text
Eso está en roadmap, pero no lo vendo como listo hoy.
```

---

## 5. During Feedback

### Feedback Capture Design

Doc:
`docs/product/FOUNDER_BETA_WEEK1_FEEDBACK_CAPTURE_V0.md`

Use for:

- feedback categories
- capture sources
- daily review loop
- what not to do
- success metrics

### Feedback Log Template

Doc:
`docs/product/FOUNDER_BETA_FEEDBACK_LOG_TEMPLATE_V0.md`

Use for:

- structured feedback record fields
- severity scale
- reuse potential scale
- example Karen entries
- daily review process

Feedback categories:

- bug
- confusion/friction
- delight/value moment
- missing feature
- roadmap idea
- trust/safety concern
- willingness-to-pay signal
- reusable pattern
- client-only case detail

Feedback rule:

```text
Capture the product signal. Do not paste sensitive case facts into product docs.
```

---

## 6. After Demo

### Karen Post-Demo Recap

Doc:
`docs/product/KAREN_POST_DEMO_RECAP_MESSAGE_V0.md`

Use for:

- normal recap
- shorter recap
- if something failed
- if Karen is excited
- if Karen seems confused/overwhelmed
- follow-up questions

### Post-Tuesday Decision Matrix

Doc:
`docs/product/FOUNDER_BETA_POST_TUESDAY_DECISION_MATRIX_V0.md`

Use for:

- what to build immediately
- what needs Karen feedback first
- what stays doc-only
- what stays parked
- what requires paid/business prospect

After-demo rule:

```text
Do not turn the demo into a build session. Capture, recap, checkpoint, then choose the next branch.
```

---

## 7. Product / Memory Foundation References

Use these after the demo or when planning week-1/post-Tuesday builds.

### Carpetas / Topic Containers

Doc:
`docs/product/CARPETAS_TOPIC_CONTAINERS_V0.md`

Use for:

- Finca / Proyectos / Pendientes design
- avoiding folder explosion
- candidate subtopics like Libro

### Document Labels / Naming

Doc:
`docs/product/DOCUMENT_LABELS_NAMING_CONVENTION_V0.md`

Use for:

- source labels
- status labels
- action labels
- OCR/manual-review honesty

### Unified Agenda

Doc:
`docs/product/UNIFIED_AGENDA_SINGLE_DAY_VIEW_V0.md`

Use for:

- future single-day agenda read view
- Google Calendar vs Val reminder distinction
- source-labeled output

### Memory Library v1

Doc:
`docs/product/MEMORY_LIBRARY_V1_DESIGN.md`

Use for:

- memory types
- raw vs structured memory
- client isolation
- source-aware retrieval

### Conversational Memory Retrieval

Doc:
`docs/product/CONVERSATIONAL_MEMORY_RETRIEVAL_V0.md`

Use for:

- grounded natural answers
- confirmed vs inferred suggestions
- no hidden actions

### Memory Foundation Implementation Map

Doc:
`docs/product/MEMORY_FOUNDATION_IMPLEMENTATION_MAP_V0.md`

Use for:

- post-Tuesday implementation phases
- read-only first build order
- risk and smoke tests per phase

---

## 8. Emergency Rules

If something fails:

1. Classify it:
   - blocker
   - cosmetic
   - roadmap

2. Use fallback language:

```text
Esto es founder-beta y lo marco como feedback. No lo voy a arreglar en vivo para no romper otra cosa.
```

3. Do not patch runtime live unless blocker.

4. Do not touch:
   - `bot.py`
   - OAuth/tokens
   - systemd
   - `/etc/val0`
   - Google Calendar internals
   - memory schema/runtime
   - OCR runtime
   - conversational router runtime
   - real client data

5. Checkpoint after demo.

Emergency rule:

```text
If the demo can continue honestly, continue. Do not repair runtime live.
```

---

## 9. One-Page Tuesday Flow

### 1. Precheck

Use:
`FINAL_TUESDAY_DELIVERY_CHECKLIST_V0.md`

Check:

- repo clean
- latest head known
- docs ready
- service active by safe path
- no planned runtime edits

### 2. Smoke

Use:
`DEMO_SMOKE_TEST_SCRIPT_V0.md`

Run:

- `Val, qué eres?`
- `Val, qué puedes hacer?`
- `Val, qué tengo mañana?`
- `Val, qué sabes de la finca 10082?`
- `Val, qué documentos tengo?`
- `Val, qué sigue?`
- `Val, puedo probar Val una semana?`

### 3. Demo

Use:
`TUESDAY_LIVE_DEMO_RUNBOOK_V0.md`

Show:

- what Val is
- what Val can do
- agenda/tomorrow
- finca context
- documents
- roadmap/future
- founder-beta trial framing

### 4. Capture Feedback

Use:

- `FOUNDER_BETA_WEEK1_FEEDBACK_CAPTURE_V0.md`
- `FOUNDER_BETA_FEEDBACK_LOG_TEMPLATE_V0.md`

Capture:

- bug
- confusion
- delight
- missing feature
- trust concern
- willingness-to-pay signal

### 5. Send Recap

Use:
`KAREN_POST_DEMO_RECAP_MESSAGE_V0.md`

Pick:

- normal
- short
- failed-demo
- excited
- overwhelmed

### 6. Checkpoint

Record:

- what worked
- what failed
- what confused Karen
- what created value
- what is roadmap
- what to build next

### 7. Decide Next Branch

Use:
`BRANCH_CLOSE_DELIVERY_HANDOFF_2026_05_25.md`

Recommended options:

- `karen-week1-feedback-2026-05-26`
- `val0-memory-foundation-runtime-v0`
- `val1-business-assessment-first-client`
- `outreach-execution-founder-beta`

---

## 10. Open Questions

- Did final smoke pass on Tuesday morning?
- Did any demo issue qualify as blocker, or only cosmetic/roadmap?
- Which feedback item becomes the first week-1 ticket?
- Should the next branch be Karen feedback capture or memory runtime foundation?
- Did Karen understand ready vs roadmap?
- Did any answer create trust/safety concern?
- Did Karen show willingness-to-pay or continue-use signal?
- Which recap variant should be sent after the demo?
- Should branch close happen immediately after demo or after final smoke/checkpoint?

