# PowerClub CRM - Val Discovery Architecture Roadmap V1

## Purpose

Define how Val Discovery Stage can evolve from a static internal cockpit into more capable meeting intelligence without pretending current demo behavior is real AI.

Core distinction:

- Current Val Discovery Stage is static, deterministic, and operator-assisted.
- Future Val levels require explicit architecture, security, privacy, consent, and scope approval.

## Architecture Principles

- Keep PowerClub CRM Demo and Val Discovery Stage separate.
- Never put API keys in frontend code.
- Never call LLMs directly from browser demos.
- Keep deterministic fallback available at every level.
- Avoid human/AGI framing.
- Avoid fake LLM claims.
- Avoid production claims.
- Require explicit approval before microphone, STT, recording, persistence, or real client data.

## Level 1 - Static Guided Cockpit

Capability:

- Static Val Discovery page.
- Scripted Val lines.
- Structured agenda.
- Question bank.
- Manual notes/decisions/risks/next steps.
- Optional browser-native TTS.
- Local summary generation.
- No persistence.
- No API calls.

Effort estimate:
Already implemented for demo baseline; 1-2 hours for minor polish after visual QA.

Risk:
Low.

Dependencies:

- Static files.
- Browser support for basic HTML/CSS/JS.
- No server.

Safe for GM meeting:
Yes, if framed as an internal Isthmus meeting cockpit in development.

Recommendation:
Use this as the default GM meeting mode unless there is enough time to validate Level 2.

## Level 2 - Operator-Assisted Deterministic Intelligence

Capability:

- Client/context inputs.
- Response capture tied to current question.
- Category buttons:
  - leads
  - follow-up
  - close
  - manager visibility
  - advisor workflow
  - data sources
  - pilot scope
  - risks/exclusions
- Deterministic `Val observa`.
- Recommended next question.
- Recommended CRM section to show.
- Improved local summary.
- No real AI.
- No backend.
- No persistence.

Effort estimate:
5-8 hours depending visual polish and summary structure.

Risk:
Low-medium. The main risk is making deterministic logic feel more intelligent than it is.

Dependencies:

- Existing Level 1 cockpit.
- Confirmed demo narrative order.
- Frank's preferred meeting flow.

Safe for GM meeting:
Yes, if the UI says it is guided/operator-assisted and Frank explains he is operating it.

Recommendation:
Target this for the GM meeting if Day 1 visual QA passes quickly. It creates the best "consultative cockpit" value without real AI risk.

## Level 3 - LLM-Ready Prompt / Backend Plan

Capability:

- Architecture document for future secure backend/proxy.
- Prompt capsule/shard defining Val Discovery role.
- Allowed topics.
- Refusal/guardrail behavior.
- Privacy/logging boundaries.
- Deterministic fallback mode.
- Criteria for when not to use LLM live.
- No implementation required.

Effort estimate:
4-6 hours for architecture, prompts, and risk model.

Risk:
Medium. Even planning a live LLM path can create expectation risk if over-described in the meeting.

Dependencies:

- Hosting decision.
- Model/provider decision later.
- Data policy.
- Logging policy.
- Scope approval.

Safe for GM meeting:
Safe as a future architecture conversation only. Do not show it as live capability unless separately implemented and tested.

Recommendation:
Prepare the architecture story, but keep the live meeting on Level 1 or Level 2 unless asked.

## Level 3.5 - Controlled LLM Through Secure Backend

Capability:

- Backend/proxy handles model calls.
- No API key in browser.
- Server-side prompt capsule.
- Request validation.
- Allowed-topic enforcement.
- Refusal behavior.
- Optional logging with explicit policy.
- Redaction or no-real-data mode.
- Deterministic fallback if backend fails.

Effort estimate:
12-20 hours for a minimal safe prototype, not including production hardening.

Risk:
High. Risks include latency, bad outputs, privacy, logging ambiguity, prompt leakage, overconfidence, cost, and live-demo failure.

Dependencies:

- Secure hosting.
- Secret management.
- Approved model/provider.
- Prompt/rule review.
- Privacy/logging decision.
- Test data only.
- Failure-mode rehearsals.

Safe for GM meeting:
Not recommended unless built, tested, and explicitly framed as founder-beta/internal. Do not present as PowerClub production AI.

Recommendation:
Do not pursue for the immediate GM meeting unless there is a specific strategic reason and enough test time. Keep as post-meeting evolution.

## Level 4 - Voice + Live Listening + STT + LLM

Capability:

- Microphone capture.
- Live listening.
- STT transcription.
- LLM interpretation.
- Real-time meeting prompts.
- Potential recap generation from transcript.
- Possible voice response.

Effort estimate:
25-50+ hours for a responsible prototype, plus policy/security review and rehearsal.

Risk:
Very high. Risks include consent, privacy, recording concerns, transcription errors, meeting trust, data retention, hallucinated interpretation, and live-demo fragility.

Dependencies:

- Explicit consent model.
- Recording/transcription policy.
- Secure backend.
- STT provider or local model decision.
- LLM provider decision.
- Data retention policy.
- Client/legal expectations.
- Fallback script.

Safe for GM meeting:
No. Not safe for the immediate GM meeting.

Recommendation:
Do not implement or imply this now. Mention only as a future, separately approved, high-risk capability if asked.

## Recommended Near-Term Path

For the upcoming GM meeting:

1. Use Level 1 as stable baseline.
2. Build Level 2 if Day 1 visual QA is clean.
3. Prepare Level 3 as internal architecture language.
4. Do not implement Level 3.5 before GM unless there is a separate approved lane.
5. Do not implement Level 4 before GM.

## What Frank Can Safely Say

```text
Hoy Val Discovery Mode es una herramienta interna en desarrollo. En esta versión guía preguntas, captura decisiones y estructura próximos pasos de forma local. Si más adelante quieren una capa de IA real, se diseña con backend seguro, datos aprobados, reglas claras y fallback determinístico.
```

## What Frank Should Not Say

- "Val ya entiende la reunión automáticamente."
- "Val escucha todo."
- "Val graba y resume solo."
- "Esto ya usa un LLM conectado."
- "Podemos poner la API key en el navegador."
- "Esto está listo para producción."
- "Val reemplaza al consultor."
- "Val ya puede operar PowerClub."

## Level Comparison Table

| Level | Capability | Effort | Risk | Safe for GM? | Recommendation |
| --- | --- | ---: | --- | --- | --- |
| Level 1 | Static guided cockpit | Done / 1-2h polish | Low | Yes | Use as baseline |
| Level 2 | Operator-assisted deterministic intelligence | 5-8h | Low-medium | Yes | Best immediate upgrade |
| Level 3 | LLM-ready architecture plan | 4-6h | Medium | Yes as roadmap only | Prepare, do not demo as live |
| Level 3.5 | Controlled LLM via secure backend | 12-20h | High | Not by default | Defer unless separately approved |
| Level 4 | Voice + listening + STT + LLM | 25-50h+ | Very high | No | Future only |

## Guardrails

- Deterministic/operator-assisted unless explicitly scoped otherwise.
- No fake LLM claims.
- No human/AGI framing.
- No real PowerClub data.
- No backend/persistence in current static demo.
- No mic/STT/recording without explicit future approval.
- No API keys in frontend.
- No OpenAI/LLM browser direct calls.
- No WhatsApp/email/payment/auth promises.
- No production promise.
- Keep CRM Demo and Val Discovery Stage clearly separated.
- Frame Val as internal tool in development.
