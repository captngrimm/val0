# PowerClub CRM Battle 02E - Val Mentor Discovery Brain

## Purpose

Define the safe future architecture for a mentor-like Val Discovery Brain.

This lane does not implement a real LLM, backend, microphone capture, persistent storage, or production AI. It defines how Val could later become a controlled discovery facilitator while Frank remains the operator.

## Target Mentor Discovery Flow

1. Frank introduces Val as an internal Isthmus Dynamics discovery tool.
2. Val gives a short intro and asks the first pain question.
3. The client answers.
4. Frank captures, confirms, or corrects the answer.
5. Val summarizes: `Si entiendo bien...`
6. Val asks one intelligent follow-up question.
7. Val updates the whiteboard with the confirmed signal.
8. Val recommends the CRM demo section to show next.
9. Frank shows the CRM demo section.
10. Val helps close with decisions, pending data, risks, and next steps.

The desired experience is a live discovery consultant, not a generic chatbot and not a button panel.

## Safe LLM Role

Val may act as:

- discovery facilitator
- meeting organizer
- operational consultant
- whiteboard assistant
- next-step recommender
- scope-risk spotter

Val must not act as:

- autonomous decision-maker
- legal or financial advisor
- human persona
- production AI
- PowerClub system of record
- replacement for Frank
- source of real PowerClub facts
- pricing or commitment authority

## Mentor Behavior Boundaries

Val should:

- speak Spanish by default
- be warm, concise, and consultative
- avoid hype
- ask one question at a time
- summarize before asking a follow-up
- flag uncertainty clearly
- recommend CRM sections without forcing them
- park out-of-scope questions
- ask Frank for confirmation before use

Val should not:

- invent PowerClub facts
- claim access to real data
- claim it heard or understood everything autonomously
- make production promises
- commit to price, timeline, legal terms, or integrations
- imply WhatsApp/payment/email/auth integrations exist

## LLM Backend Architecture

Future controlled LLM support should use this flow:

1. Browser collects bounded meeting context already visible in Val Discovery.
2. Browser sends sanitized context to an Isthmus backend endpoint.
3. Backend stores the API key securely outside the browser.
4. Backend applies the Val prompt capsule and request validation.
5. Backend calls the selected model/provider.
6. Backend validates the model response against the schema.
7. Backend returns a bounded response to the browser.
8. Frontend displays the response as a suggestion.
9. Frank approves, edits, or discards it.
10. Deterministic local mode remains available if anything fails.

## No Browser API Keys

Hard rule:

- no OpenAI/LLM key in HTML
- no client-side secret
- no direct browser LLM calls
- no model endpoint called from static demo files
- no hidden API key in JavaScript

The browser may only call an approved Isthmus backend/proxy after that backend exists and is explicitly scoped.

## Response Shape

The future backend should return a JSON-style response:

```json
{
  "val_message": "Si entiendo bien, el problema principal es seguimiento atrasado.",
  "summary": "El cliente siente que oportunidades se enfrían por falta de contacto a tiempo.",
  "detected_pain": "seguimiento",
  "follow_up_question": "¿Cuántas oportunidades sienten que se enfrían por semana por falta de contacto?",
  "whiteboard_cards": [
    {
      "lane": "Dolor detectado",
      "title": "Seguimiento atrasado",
      "body": "Oportunidades se enfrían antes de que gerencia lo vea."
    }
  ],
  "recommended_demo_section": "Riesgo y rescate",
  "risk_flags": ["Validar reglas reales de seguimiento antes de prometer alertas automáticas."],
  "next_step": "Pedir muestra aprobada de datos y confirmar reglas de follow-up.",
  "confidence": "medium",
  "needs_frank_confirmation": true
}
```

## Safety And Fallback

If the LLM fails:

- use local deterministic Val mode
- show the scripted question bank
- keep manual capture and whiteboard organization
- generate the local summary

If the response is too broad:

- ask Frank to narrow the client answer
- ask one clarifying question
- avoid creating too many whiteboard cards

If the client asks off-topic:

- park the question in risks / parking lot
- return to discovery or scope

If pricing/legal/commitment questions arise:

- direct to discovery, scope freeze, and proposal follow-up
- do not quote or commit

## GM Meeting Positioning

Frank can say:

```text
This is an internal discovery tool. Some parts are scripted or assisted today. If we connect a language model later, it would go through a secure backend and approved scope.
```

Spanish version:

```text
Esta es una herramienta interna de discovery. Algunas partes hoy son guiadas o asistidas. Si más adelante conectamos un modelo de lenguaje, sería mediante un backend seguro, con datos aprobados, alcance definido y Frank validando las respuestas.
```

Frank should not say:

- "Val ya usa un LLM en vivo."
- "Val entiende automáticamente la reunión."
- "Val escucha todo."
- "Val puede decidir el alcance."
- "Val ya opera PowerClub."

## Implementation Levels

| Level | Description | Safe for GM meeting | Recommendation |
| --- | --- | --- | --- |
| Level 2 | Current deterministic/operator-assisted mode | Yes | Use as meeting baseline |
| Level 3 | LLM-ready backend design | Yes, as roadmap only | Discuss if asked |
| Level 3.5 | Controlled LLM pilot through backend | Not by default | Build only if separately approved |
| Level 4 | Voice/STT/live listening + LLM | No | Future/high-risk |

## ETA Tracker

Planning assumption for this architecture package:

- Docs-only 02E lane: 2-3 effective hours
- Future controlled LLM pilot: 18-30 effective hours
- Future voice/STT/live listening layer: 25-50+ effective hours

| Lane / Workstream | Planned hours | Actual hours | Variance | Status | Updated total ETA | Notes |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 02E architecture docs | 2-3 | TBD | TBD | on track | 28-35 base remains | This lane is plan-only. |
| Backend skeleton | 4-6 | TBD | TBD | not started | 18-30 for LLM pilot | Can cut persistence/logging UI. |
| Prompt capsule implementation | 3-5 | TBD | TBD | not started | 18-30 for LLM pilot | Must not cut guardrails/schema. |
| Frontend integration | 4-6 | TBD | TBD | not started | 18-30 for LLM pilot | Can cut polish; keep approval flow. |
| Safety/fallback | 4-6 | TBD | TBD | not started | 18-30 for LLM pilot | Must not cut deterministic fallback. |
| QA/rehearsal | 3-5 | TBD | TBD | not started | 18-30 for LLM pilot | Must not cut GM failure script. |
| Premium voice/avatar intro | 4-8 | TBD | TBD | optional | stretch only | Cut first if time slips. |

## Guardrails

- No real LLM implementation in this lane.
- No API keys.
- No backend code in this lane.
- No real PowerClub data.
- No sensitive meeting persistence.
- No microphone/STT expansion.
- No production promise.
- No human/AGI framing.
- Frank remains operator.
- PowerClub CRM Demo and Val Discovery Stage remain separate but connected in story.
