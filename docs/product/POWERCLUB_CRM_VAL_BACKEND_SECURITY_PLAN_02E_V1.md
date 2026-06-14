# PowerClub CRM Battle 02E - Val Backend Security Plan

## Purpose

Define secure backend/proxy requirements for any future Val Mentor Discovery Brain implementation.

This lane does not build backend code. It documents what must exist before a real LLM is connected.

## Core Security Principles

- No API keys in browser files.
- No direct browser-to-LLM calls.
- No real PowerClub data without explicit approval.
- No sensitive meeting persistence by default.
- No microphone, recording, or STT expansion in this plan.
- Frank remains operator and approves outputs.
- Deterministic local fallback remains available.

## Proposed Request Flow

```text
Val Discovery frontend
  -> sanitized request packet
  -> Isthmus backend/proxy
  -> prompt capsule + validation
  -> LLM provider
  -> backend response validation
  -> bounded JSON response
  -> frontend suggestion
  -> Frank approves/edits/uses
```

## Backend Responsibilities

The backend must:

- hold API keys in server-side secrets
- authenticate/authorize requests if exposed beyond local testing
- apply rate limits
- apply request size limits
- strip or reject unexpected fields
- inject the approved prompt capsule server-side
- call the selected model/provider
- validate response schema
- block unsafe output
- return fallback output on failure
- avoid storing sensitive meeting content unless explicitly approved

## Frontend Responsibilities

The frontend must:

- never include API keys
- send only bounded meeting context
- label LLM output as a suggestion
- require Frank confirmation before organizing or presenting it
- keep deterministic mode available
- show clear error/fallback copy if backend fails

## Sanitized Request Packet

The browser should send only:

- current meeting step
- current question
- captured answer text
- selected category, if any
- existing whiteboard headings/cards
- allowed CRM demo sections
- guardrail flags

Avoid sending:

- hidden client data
- raw uploaded files
- private contact lists
- payment data
- credentials
- browser secrets
- unrelated Val0 client data

## Secrets Management

Required:

- API key stored in backend environment/secret manager
- key never rendered into HTML/JS
- separate dev/test/prod keys if this becomes real
- rotation plan
- provider usage monitoring

Forbidden:

- hardcoded API key in `val_discovery.html`
- key in static assets
- key in checked-in config
- direct model calls from browser

## Privacy And Logging

Default policy for a meeting prototype:

- no persistence of sensitive meeting content
- no transcript storage
- no audio storage
- no automatic recording
- logs contain request IDs, timing, and error codes only

If logging content is later required:

- obtain explicit approval
- define retention period
- redact personal/sensitive data
- document who can access logs
- provide deletion process

## Output Safety Checks

Backend should reject or fallback if output:

- fails JSON schema
- invents PowerClub facts
- says Val has real data
- promises production readiness
- commits to pricing, legal, SLA, integrations, WhatsApp, payments, auth, or AI autonomy
- gives more than one follow-up question
- lacks `needs_frank_confirmation: true`
- includes disallowed sections or categories

## Failure Modes

If model call fails:

- return deterministic fallback recommendation
- tell Frank to use local mode
- preserve manual capture

If latency is high:

- show local deterministic suggestion
- do not block the meeting

If response is unsafe:

- discard model output
- return a safe parking-lot response

If backend is unavailable:

- continue with current static Val Discovery Mode

## GM Meeting Safety

Safe GM wording:

```text
Hoy esta pantalla funciona como discovery guiado. Si conectamos un modelo de lenguaje más adelante, no iría directo desde el navegador: tendría backend seguro, reglas, validación, fallback y aprobación de Frank.
```

Unsafe wording:

- "Ya está conectado a IA real."
- "La IA toma decisiones."
- "Val graba y entiende toda la reunión."
- "Val puede prometer alcance o precio."
- "Esto ya está listo para producción."

## Implementation Levels

| Level | Backend needed | LLM used | Safe for GM | Notes |
| --- | --- | --- | --- | --- |
| Level 2 deterministic | No | No | Yes | Current operator-assisted mode |
| Level 3 architecture | Planned only | No | Yes as roadmap | This 02E lane |
| Level 3.5 controlled LLM | Yes | Yes | Only if tested | Requires secrets, validation, fallback |
| Level 4 live voice/listening | Yes | Yes | No | Requires consent, STT, privacy policy |

## Rough Build ETA

| Workstream | Estimated hours | Notes |
| --- | ---: | --- |
| Backend skeleton/proxy | 4-6 | Minimal endpoint, env secrets, request limits |
| Prompt capsule integration | 3-5 | Server-side prompt, bounded packet |
| Response schema validation | 3-5 | JSON validation, allowed enums, fallback |
| Frontend integration | 4-6 | Suggestion panel, approval flow, error states |
| Safety/fallback QA | 4-6 | Unsafe output tests, latency failure tests |
| Rehearsal | 2-4 | Frank dry run, GM questions, fallback script |
| Optional premium audio/avatar intro | 4-8 | Separate stretch/wow lane |

## Approval Gates

Before real implementation:

1. Confirm model/provider.
2. Confirm hosting/secrets approach.
3. Confirm no real PowerClub data or approve bounded sample data.
4. Confirm logging policy.
5. Confirm fallback script.
6. Run adversarial prompt tests.
7. Run Frank-machine demo rehearsal.

## Guardrails

- No backend code in this lane.
- No API keys.
- No persistence of sensitive meeting content.
- No real PowerClub data.
- No mic/STT expansion.
- No production promise.
- No human/AGI framing.
- No autonomous commitments.
- Frank remains operator.
