# VAL-AIOPS-DEMO-01C - Visual Verification and Demo Runbook

## Purpose

This doc verifies the static Val AI Ops Discovery stage from 01B and gives Frank a short runbook for opening it in a business diagnostic meeting.

The stage remains static/offline. There is no runtime Telegram wiring, DB write, real LLM call, persistence, memory activation, production deployment, or real client data feature in this lane.

## Candidate Chosen

Candidate chosen: keep the existing static stage and add a runbook plus a smoke check for demo copy, controls, and boundaries.

Stage:

```text
docs/demo/aiops_discovery/index.html
```

## How To Open

Open the file directly in a browser:

```text
docs/demo/aiops_discovery/index.html
```

No local server is required.

## Meeting Opening Line

Frank can say:

```text
Este es un stage interno de Val AI Ops Discovery. Lo uso para estructurar diagnósticos, detectar oportunidades y producir un Mapa IA 30/60/90.
```

English fallback if needed:

```text
This is an internal Val AI Ops Discovery stage. I use it to structure diagnostics, detect opportunities, and produce a 30/60/90 AI map.
```

## Demo Command

Use:

```text
Iniciar diagnóstico AI Ops con Carlos
```

In the static stage, type `Carlos` or `Empresa Carlos` in the company field, then click:

```text
Iniciar diagnostico AI Ops
```

## Suggested Flow

1. Open the static stage in the browser.
2. Set the company field to `Carlos` or `Empresa Carlos`.
3. Click `Start Diagnostic` / `Iniciar diagnostico AI Ops`.
4. Click `Load sample notes`, or paste the sample notes below.
5. Click `Summarize Notes`.
6. Click `Suggest Next Question`.
7. Click `Detect Opportunities`.
8. Click `Generate Draft Map`.
9. Walk through the report preview from executive summary to next steps.

## Sample Notes For Demo

Paste these into the meeting notes area:

```text
Carlos runs a service business.
Leads arrive through WhatsApp and referrals.
Follow-up is manual.
Quotes are tracked in Excel or notebooks.
Some prospects are lost because nobody follows up.
Carlos wants better visibility and fewer missed opportunities.
```

## What Frank Says After The Report

Frank can say:

```text
Esto no promete automatizar todo. Primero identifica el proceso más rentable para un piloto pequeño y medible.
```

Then:

```text
Si esto te hace sentido, el siguiente paso es un diagnóstico AI Ops 30/60/90 más estructurado o un primer piloto pequeño con límites claros.
```

## Boundaries To Say Out Loud If Needed

- No fake autonomy.
- No professional replacement claims.
- No ChatGPT/OpenAI visible branding.
- No real client data in demo unless manually approved.
- No implementation without human confirmation.
- No hidden persistence or memory saving.
- No promise that Val will run the business.

## Next Commercial Step

Offer one of two clean next steps:

- Paid/structured AI Ops 30/60/90 diagnostic.
- First small AI Ops pilot around the most valuable process found in the diagnostic.

The commercial language should stay practical:

```text
No vendemos una app gigante de entrada. Primero encontramos el flujo donde IA puede quitar más carga y lo probamos con una métrica clara.
```

## Visual Verification Result

Manual/source inspection was completed for:

- Branded header visible in source: `Val AI Ops Discovery`.
- Report framing visible in source: `Mapa IA 30/60/90`.
- Founder-beta diagnostic stage label present.
- Command area present.
- Guided diagnostic questions present.
- Meeting notes area present.
- Operator panels ordered as summary, next question, opportunities, risks, and recommended pilot.
- Report preview includes all required sections.
- Static controls are present.
- No visible ChatGPT/OpenAI branding in the stage files.
- No obvious broken copy or missing closing tags found during source review.
- CSS includes responsive breakpoints for narrower screens.

Screenshot limitation: no local screenshot-capable browser binary was available in this environment (`chromium`, `google-chrome`, `firefox`, and `wkhtmltoimage` were not found), so visual verification is manual/source-based rather than screenshot-based.

## Guardrails

- No runtime behavior changed.
- No production restart.
- No DB/OAuth/systemd/config changes.
- No Telegram route changes.
- No memory activation.
- No real LLM calls.
- No `clients/**` edits.
- Protected live data must remain unstaged.

## Demo Readiness Checklist

- Open the stage before the call.
- Set the company field.
- Use the sample notes if the audience needs a clean walkthrough.
- Click the buttons in the suggested order.
- Keep the pitch focused on diagnosis, pilot design, and the 30/60/90 map.
- Avoid claiming that Val can automate everything today.
