# VAL-AIOPS-DEMO-01A - Branded AI Ops Discovery Stage Design

## 1. Executive Decision

Build the first Val AI Ops Discovery demo as a simple branded web/stage experience, not as a generic chat UI and not as a full SaaS product.

The fastest credible route is a lightweight branded operator stage that Frank controls during a discovery meeting. It should make the method visible: diagnostic questions, meeting notes, opportunity detection, and a draft "Mapa IA 30/60/90" artifact. Telegram can remain a familiar companion surface, but the commercial meeting should not look like Frank is merely typing into ChatGPT.

Candidate chosen: simple branded web/stage MVP with reusable Val0 diagnostic patterns and a future path toward a Forge/ValPrime cockpit.

## 2. Strategic Reason

Val AI Ops Discovery exists to help Frank sell diagnosis, implementation judgment, and an operating method.

The product impression should be:

- Frank has a clear discovery process.
- Frank has an internal assistant/operator.
- The meeting produces a useful artifact.
- The client sees a practical 30/60/90 roadmap, not an AI novelty demo.

The product impression must not be:

- ChatGPT with a skin.
- A fake autonomous employee.
- A giant SaaS app that does not exist yet.
- Enterprise vaporware.
- A voice/avatar experiment.

## 3. Recommended Technical Route

Use a branded stage first:

- A focused discovery screen with Val branding.
- One command/input entry point: "Iniciar diagnostico AI Ops".
- A guided question rail for the diagnostic.
- A meeting notes area where Frank can paste transcript fragments or raw notes.
- A Val operator output area for summaries, next questions, opportunity detection, and next steps.
- A report preview for "Mapa IA 30/60/90 - Empresa X".

This route is fastest because it reuses existing Val0 product thinking without forcing live Telegram routing, DB persistence, OAuth, memory writes, or a generalized SaaS shell.

Telegram remains useful for founder-beta continuity, but the branded stage is the better commercial surface for a business diagnostic meeting.

## 4. Route Comparison

| Route | Strength | Weakness | Recommendation |
| --- | --- | --- | --- |
| Branded Telegram flow | Fast, familiar, already aligned with Val's current surface. | Can feel like a chat thread instead of a diagnostic stage; weaker report preview. | Keep as companion/fallback, not the main commercial demo surface. |
| Simple branded web/stage | Best balance of speed, control, brand, and meeting usefulness. | Needs a small UI pass and disciplined scope. | Recommended for MVP. |
| Open WebUI/LibreChat customized | Fast access to chat-like interface. | Risks looking exactly like "ChatGPT with a skin"; customization may distract from the method. | Avoid as the visible demo unless hidden behind a stronger branded shell. |
| Minimal custom frontend | Maximum control and polished demo path. | Can expand into accidental SaaS work if not scoped. | Use only as a tight branded stage, not a product platform. |
| Forge/ValPrime cockpit stage | Strong long-term operator direction. | Too much surface area for a 2-3 day MVP. | Use as the later home for the stage after the concept proves useful. |

## 5. 2-3 Day MVP

The MVP should prove the meeting experience, not the platform.

Core surface:

- Branded Val AI Ops Discovery screen.
- "Iniciar diagnostico AI Ops" command.
- Client/company name field, such as "Carlos" or "Empresa X".
- Guided diagnostic question flow.
- Meeting notes paste area.
- Operator output panel.
- Draft report preview.

Core behavior:

- Val asks the required diagnostic questions in order.
- Frank can paste notes or transcript fragments.
- Val summarizes what she heard.
- Val suggests the next best question.
- Val detects obvious AI Ops opportunities.
- Val drafts a "Mapa IA 30/60/90" from the current session.

MVP constraints:

- No DB writes.
- No client file writes.
- No memory activation.
- No calendar/task/reminder creation.
- No claims of autonomy.
- No professional replacement claims.
- Session-only draft state unless a later lane explicitly approves saving.

## 6. 7-10 Day Version

The 7-10 day version can make the stage feel reliable enough for repeated founder-beta meetings.

Add:

- Editable report sections.
- Markdown export and optionally PDF export.
- Diagnostic modes, such as general business, sales/admin, operations, documents, and follow-up.
- Better handling for pasted transcript fragments.
- A visible opportunity list with confidence and assumptions.
- A pilot recommendation builder.
- A clean "next meeting / next steps" section.
- Basic smoke tests around the full meeting path.
- Optional Telegram companion command that launches or mirrors the diagnostic, if separately scoped.

Still avoid:

- Persistence by default.
- Full client CRM behavior.
- Production DB migrations.
- Memory writes.
- OAuth work.
- Voice-first features.

## 7. 2-4 Week Version

The 2-4 week version can become the first real Val AI Ops assessment cockpit.

Add:

- Polished branded stage inside the future Forge/ValPrime cockpit direction.
- Multiple reusable diagnostic templates.
- Explicit save/export controls with consent and client isolation.
- Report artifact library only after storage is designed and approved.
- Stronger opportunity taxonomy: automation, retrieval, reporting, reminders, intake, document processing, follow-up, and workflow orchestration.
- Shadow classifier support for messy business language, using existing Intent Router v2 discipline.
- Optional Voice Lite moments for demo polish.
- Founder-beta package alignment: assessment, pilot design, implementation option, and operator support.

This version should still present Val as structured reasoning plus guarded execution, not autonomous business management.

## 8. Reused Val0 Components

Reuse these existing assets before building anything new:

- Adaptive intake pattern: ask permission, narrow gently, recommend one first workflow.
- Onboarding/recommendation flow: summarize, explain why, propose a first pilot.
- Val1 assessment packet: existing assessment script, summary template, offer architecture, and pricing boundaries.
- Founder-beta setup kit: one workflow first, one-week trial posture, honest beta framing.
- Val personality cartridge: warm, direct, practical, truth-grounded operator voice.
- Intent Router v2 shadow discipline: LLM may classify or propose; deterministic handlers execute.
- Memory spine philosophy: consent, inspectability, and explicit save proposals, but no memory activation in this lane.
- Document/report rendering patterns: turn messy notes into structured artifacts.
- Client isolation contract: no cross-client contamination, no reusable logic with private client literals.
- Launchpad/smoke discipline: no lane is green without focused checks.

## 9. What To Avoid

Avoid:

- Building a full SaaS.
- Making Open WebUI or LibreChat the visible commercial product.
- Spending the lane on local LLM work.
- Spending the lane on voice.
- Full duplex voice, avatars, or voice-first architecture.
- Fake autonomy language.
- Hidden memory or silent profiling.
- Professional replacement claims.
- Overpromising reliability.
- Production DB migrations.
- OAuth, tokens, systemd, or production config changes.
- Any writes to `clients/**`.

## 10. MVP Diagnostic Flow

Start command:

```text
Iniciar diagnostico AI Ops
```

If a person or company is included:

```text
Iniciar diagnostico AI Ops con Carlos.
```

Val opens warmly and frames the process:

```text
Perfecto. Vamos a hacer un diagnostico corto para encontrar un primer piloto de AI Ops, no para venderte mil herramientas. Te voy a hacer unas preguntas y al final armamos un Mapa IA 30/60/90.
```

Required questions:

1. What type of business is this?
2. Where do leads or clients come from?
3. What are the critical processes that must not fail?
4. What work is manual, repetitive, or easy to forget?
5. What tools are used today?
6. Where is the most time lost?
7. What is the current bottleneck?
8. What outcome would make the next 30/60/90 days feel successful?

The flow should narrow toward one recommended pilot instead of trying to automate the whole business.

## 11. Meeting Mode

Meeting mode lets Frank paste messy notes or transcript fragments while the conversation is happening.

Val can:

- Summarize what was said.
- Separate facts, assumptions, and recommendations.
- Suggest the next best question.
- Detect candidate opportunities.
- Identify missing context.
- Prepare next steps.
- Draft report sections.

Val should not:

- Pretend to know facts not provided.
- Execute actions.
- Save memory silently.
- Create tasks, calendar events, or reminders.
- Claim legal, medical, accounting, or financial authority.

## 12. Report Artifact: Mapa IA 30/60/90

Output title:

```text
Mapa IA 30/60/90 - Empresa X
```

Required sections:

- Executive summary.
- Current processes.
- Pain points.
- Opportunities.
- Recommended pilot.
- 30/60/90 roadmap.
- Limits / boundaries.
- Next steps.

The report should read like a practical operating map. It should avoid generic AI hype and should clearly name what is known, what is inferred, and what needs validation.

Example pilot framing:

```text
Recommended pilot: lead follow-up and admin capture.

Why: the meeting notes suggest time is being lost between incoming requests, manual tracking, and delayed follow-up. A small pilot can capture requests, classify next steps, and prepare follow-up drafts without giving the system authority to send messages or make commitments.
```

## 13. Optional Voice Lite

Voice Lite is optional demo polish, not the product center.

Allowed:

- Browser/device speech-to-text if feasible.
- Browser/device text-to-speech if feasible.
- Short spoken moments only:
  - greeting
  - first question
  - opportunity summary
  - closing pilot recommendation

Not allowed for this direction:

- Full duplex voice.
- Avatar work.
- Voice-first architecture.
- Voice as a reason to delay the branded stage.

Voice Lite should make the meeting feel polished for a moment, then get out of the way.

## 14. Future File/Module Plan

Likely future implementation files, if approved later:

- `core/aiops_discovery.py` for deterministic diagnostic state and report assembly helpers.
- `scripts/quality/aiops_discovery_smoke.py` for the deterministic diagnostic flow.
- `docs/product/VAL_AIOPS_DEMO_01B_BRANDED_STAGE_MVP.md` for the implementation lane.
- A small web/stage surface under a future approved UI directory.
- Report templates under a future approved templates/docs path.
- Optional export helper only after the report artifact format is stable.

Avoid touching in the first implementation lane:

- `bot.py`, unless a Telegram companion command is explicitly scoped.
- `clients/**`.
- Production DB files.
- OAuth/token/systemd/config.
- `core/memory_spine.py` runtime activation.

## 15. Smoke Tests

Future MVP smokes should verify:

- Stage command starts the diagnostic.
- Val asks the required AI Ops questions.
- Meeting notes can be summarized.
- Val suggests a next question.
- Val detects opportunities from notes.
- Val drafts all required "Mapa IA 30/60/90" sections.
- Output does not expose ChatGPT/OpenAI as the visible interface.
- Output does not claim full autonomy.
- Output does not make professional replacement claims.
- No DB writes occur.
- No `clients/**` writes occur.
- Protected live data is not staged.
- Memory persistence remains inactive.
- Optional Voice Lite is off by default unless explicitly enabled.

## 16. Demo Talk Track

Frank opens the branded stage and enters:

```text
Iniciar diagnostico AI Ops con Carlos.
```

Val:

```text
Hola Carlos. Soy Val. Hoy voy a ayudar a Frank a ordenar la conversacion y convertirla en un mapa practico de oportunidades de AI Ops. Empezamos simple: quiero entender tu negocio, tus procesos criticos y donde se esta perdiendo mas tiempo.
```

Frank can explain:

```text
This is an internal assistant we're building. Today I'm using it to run AI Ops discovery. It helps structure the meeting, detect opportunities, and produce a 30/60/90 map.
```

Spanish-first version:

```text
Este es un asistente interno que estamos construyendo. Hoy lo uso para correr discovery de AI Ops: estructura la reunion, detecta oportunidades y genera un mapa 30/60/90.
```

Positioning line:

```text
No quiero ensenarte mil funciones. Quiero encontrar contigo un primer piloto que si quite carga y que podamos probar con limites claros.
```

## 17. Guardrails

- No runtime behavior changes in this lane.
- No production restart.
- No DB migrations.
- No client data edits.
- No hidden persistence.
- No memory activation.
- No LLM/tool autonomous execution.
- Deterministic handlers execute; LLM output may propose or draft only.
- User/client confirmation is required before any future action.
- Client isolation first.
- Founder-beta honesty: useful, scoped, and still under active development.

## 18. Open Questions

- Should the first MVP be local-only, internal web-only, or hosted behind existing operator access?
- What is the minimum acceptable report export: Markdown, PDF, or copyable formatted text?
- Should the first demo include English/Spanish toggles, or stay Spanish-first with English support later?
- Which first business niche should the demo optimize for: service business, retail, admin-heavy solo operator, or founder-led small team?
- Should Telegram be used during the meeting, or only after the report as the follow-up surface?
- What exact brand name should appear on the stage: Val AI Ops Discovery, Val Business OS, or ValPrime Discovery?
