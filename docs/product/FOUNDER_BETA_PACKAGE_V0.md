# FOUNDER_BETA_PACKAGE_V0 — Val0

Purpose:
Define the first sellable/testable Val0 founder-beta package based on the current Karen MVP.

This is a founder-operated beta package, not a self-serve SaaS offer. The promise is practical help, careful setup, and trust-first operation around a few real workflows.

---

## Positioning

Val0 is a personal/operator assistant that runs through Telegram and is configured around a specific person, family, case, or workflow.

It is not a generic chatbot. It is not public SaaS yet. It is a founder-operated system where setup, workflow selection, privacy boundaries, and safety checks matter.

The value:

- remember and organize the things that are currently scattered
- turn documents, notes, reminders, and next steps into a usable operating flow
- keep client-specific data behind explicit profile and workflow boundaries
- avoid pretending unfinished features are ready

Short version:

Val0 helps a client stop losing track of important things, starting with 1-3 focused workflows.

---

## What Val0 Can Do Now

Current founder-beta capabilities:

- Telegram assistant for daily interaction.
- Notes, reminders, tasks, and idea capture.
- Karen-style legal/admin case organization.
- Document inventory and document status flows.
- Document/photo upload status that says whether a file is stored, extracted, indexed, unsupported, or needs OCR/manual review.
- Case timeline from scoped case notes and document metadata.
- Daily Operator mode for read-only “what should I look at next?” summaries.
- Google Calendar agenda/create/delete flows with explicit confirmations.
- Client isolation and unknown-client workflow guards.
- Technical paste guard for commands, logs, and code blocks.
- Deterministic response safety layer for limited warmth without changing facts.

These capabilities are strongest when used as a guided workflow with known boundaries, not as an open-ended “ask anything” product.

---

## Readiness Matrix

### Ready

- Telegram text interaction.
- Notes/tasks/reminders basics.
- Technical paste guard.
- Client profile and protected workflow denial for unknown chats.
- Karen/client-zero legal/admin route cluster for controlled use.
- Pending confirmations for sensitive calendar create/delete actions.
- Client isolation audit and smoke-test discipline.

### Beta-Safe

- Document upload status.
- Document inventory/listing when scoped to the active case/client.
- Grounded document summaries when text has been extracted and source IDs are available.
- Case timeline from case notes/document metadata.
- Daily Operator read-only summaries.
- Google Calendar create/delete with explicit confirmation.
- Deterministic response warmth for safe response types.

### Internal-Only

- Raw ops commands and server health details.
- VFMS internals, local paths, and extraction implementation details.
- Launchpad recovery/server verification workflow.
- Conversation router shadow logs.
- Broad operator/debug modes unless intentionally demoed.

### Not Ready

- Fully automated OCR/photo legal reading.
- Reliable DOCX extraction.
- Public dashboard or client portal.
- Autonomous actions without confirmation.
- Real external SaaS integrations carrying client data.
- Multi-client onboarding beyond the current profile/guard skeleton.
- “Infinite memory” as a client-facing product claim.

---

## Karen-Style Demo Script

Use a controlled 8-10 minute demo. Do not ask Val0 to prove everything in one session.

1. `Val, qué puedes hacer hoy`
2. `Val, qué documentos tengo`
3. Upload or reference a safe demo document, then show the upload/status response.
4. `Val, ordéname la cronología del caso`
5. `Val, qué pasó en 2024`
6. `Val, qué hago hoy`
7. `Val, prepárame el paquete para Nora`
8. `Val, qué falta revisar antes de hablar con la abogada`

Demo goal:

- show that Val0 can organize a messy real-life/admin workflow
- show that document status is honest
- show that timeline and operator modes are read-only and bounded
- show that sensitive actions stay behind confirmation

This demo does not prove:

- perfect OCR
- full legal advice
- public SaaS readiness
- autonomous work
- complete multi-client onboarding

---

## $150 Assessment Package

Best for:
business owners, professionals, families, or operators who suspect Val0 could help but do not yet know what to build.

Format:

- 45-60 minute workflow assessment
- focused conversation around current operational pain
- no promise that every requested feature already exists

Assessment covers:

- what the client is currently forgetting or losing track of
- what lives in Telegram, WhatsApp, notes, Excel, screenshots, folders, or memory
- what process wastes time or creates stress
- what should not be stored or automated
- first 1-3 workflows worth testing
- privacy and data boundaries

Deliverable:

- pain-point summary
- first workflow recommendation
- month 1 roadmap
- what Val0 can do now
- what needs custom work
- what should be deferred
- setup estimate for a founder-beta implementation

Suggested client-facing phrase:

“The assessment decides whether Val0 can help your actual workflow before we pretend to build everything.”

---

## $300/Month Operator Package

Best for:
a serious founder-beta client with one clear operating workflow.

Includes:

- guided client setup
- Telegram assistant access
- 1-3 active workflows
- basic memory/profile setup
- workflow-specific guidance
- weekly or biweekly check-in
- light refinement and maintenance
- roadmap/idea capture
- compile/audit/smoke discipline before changes

Examples of active workflows:

- document/case organization
- meeting prep package
- reminders and follow-up tracking
- list/inventory workflow
- Daily Operator summary for a narrow case/project

Limits:

- not unlimited custom development
- not a full CRM/ERP replacement
- not guaranteed OCR/photo reading
- not legal, medical, financial, or accounting advice
- third-party integrations may cost extra or be deferred
- external SaaS use requires privacy review
- sensitive actions require explicit confirmation

Suggested client-facing phrase:

“We start with the few workflows that matter most, run them in Telegram, and improve based on real usage.”

---

## Onboarding Checklist

Before enabling a client:

- client profile created
- display name and language confirmed
- chat ID registered
- enabled workflows selected
- privacy comfort level documented
- “do not store/touch” boundaries documented
- first 1-3 workflows chosen
- active case/project ID set if applicable
- calendar status confirmed: none, read-only, create/delete with confirmation
- document handling consent confirmed
- unknown-client denial smoke checked
- client-specific smoke script prepared
- support/escalation lane agreed
- beta boundaries sent to client

No client should enter legal/case/document/operator flows by accident.

---

## Privacy And Safety Language

Use this with early clients:

“Val0 is founder-beta. It stores information you send through Telegram so it can help organize reminders, notes, documents, and next steps. It does not replace a lawyer, accountant, doctor, or professional reviewer. Sensitive documents should only be uploaded if you are comfortable with beta storage. Actions like creating or deleting calendar events stay behind explicit confirmation.”

Operational rules:

- client data must stay scoped to the client profile/workflow
- unknown chats must not inherit another client’s routes, data, or personality
- generated summaries are not ground truth
- document/legal answers should preserve source/provenance when possible
- external tools may help with prototypes or non-sensitive intake, not source-of-truth mutation

---

## Disclaimers

Val0 is not:

- legal advice
- medical advice
- accounting or tax advice
- a substitute for professional review
- a fully private consumer product
- a fully autonomous employee
- a public self-serve SaaS product

Known limitations:

- OCR/photo reading is not fully reliable yet
- DOCX extraction is not ready
- multi-client onboarding is guarded but not fully automated
- dashboards/client portals are not built
- Daily Operator v0 is read-only and conservative
- calendar create/delete requires confirmation

---

## Demo Do / Don’t

Do demo:

- one narrow workflow
- document inventory/status
- read-only timeline
- read-only Daily Operator
- confirmation behavior
- unknown-client safety message if useful
- honest “ready vs later” language

Do not demo:

- random real sensitive documents without consent
- OCR/photo reading as if it is guaranteed
- autonomous calendar/legal/document actions
- raw VFMS paths or server internals
- broad “ask anything” stress tests
- dashboards as if they exist
- multi-client setup as if self-serve

---

## Next Build Priorities

1. Founder-beta package docs and offer cleanup.
2. Live smoke/demo script for the Karen-style workflow.
3. Lightweight status/readiness report for founder-operated demos.
4. Client onboarding v0 using `ClientProfile` and workflow guards.
5. Document registry and extraction status refinement.
6. Safer document/source citation in summaries.
7. Dashboard prototype with fake data before any real client connection.
8. CI quality gate for compile, audit, and smoke scripts.

---

## Operating Principle

Sell value without lying.

Founder-beta clients should feel the system is useful because it is focused, honest, and careful, not because it pretends to be finished.
