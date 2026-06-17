# PowerClub CRM Battle 02F.2 - Val Mentor UX Simplification

## Purpose

Simplify Operator Mode so Frank can run Val Mentor as a guided meeting flow instead of hunting through technical panels.

The mock/backend seam from 02F stays intact. This lane does not add real LLM calls, browser secrets, persistence, real PowerClub data, or production behavior.

## UX Problem Found

Frank's browser test confirmed the mock flow worked, but the interface still felt like several competing panels:

- `Sugerir con Val` lived inside a technical drawer
- category detection could remain unknown even when the response sounded like follow-up
- `Usar sugerencia` updated text but did not clearly organize the response
- the next action after accepting was not obvious
- Frank could not easily tell whether Val had only spoken or had placed the idea into the whiteboard

## Changes Made

Operator Mode now has a clearer primary drawer:

`VAL MENTOR / flujo guiado`

It shows:

- `Respuesta capturada`
- `Categoría detectada`
- `Sugerencia de Val`
- `Demo recomendado`
- `Próxima pregunta`
- `Qué hago ahora`

Primary buttons:

- `Sugerir con Val`
- `Usar y organizar`
- `Ignorar`

The language is intentionally operator-friendly instead of backend/technical.

## Category Inference

Before sending the mock/backend request, Val Mentor now deterministically refreshes the detected category from the captured response unless Frank explicitly selected a category.

Follow-up defaults to `seguimiento` when the response includes signals such as:

- seguimiento
- WhatsApp
- contacto
- oportunidades perdidas
- no llaman
- no responden
- tarde
- pendiente
- se enfria / se enfría

Advisor defaults to `asesor` when the response includes:

- asesor
- vendedor
- usuario
- operador

Manager visibility defaults to `visibilidad` when the response includes:

- gerente
- gerencia
- sucursal
- dashboard
- visibilidad
- reporte

This is local deterministic logic, not AI inference.

## Accept And Organize Behavior

`Usar sugerencia` was renamed to:

`Usar y organizar`

After Frank approves:

- Val updates the message
- the recommended demo section updates
- the next question updates
- a card is placed into the whiteboard using the approved suggestion
- `Val observa` shows a clear completion line:

`Listo. Val organizó la respuesta como [categoría]. Demo recomendado: [sección]. Siguiente pregunta: [pregunta].`

Frank still has approval control. Nothing is executed without Frank pressing the button.

## Panel Visibility

Presentation Mode remains clean and does not show technical LLM details.

Operator Mode keeps the advanced tools available, but the primary flow is now Val Mentor. These remain collapsed or secondary:

- Guardrails
- Q&A seguro
- Categorías
- Captura avanzada
- ArcX / teclado debug
- Voice/STT controls

## Fallback

If the mock/backend endpoint fails:

- the UI stays usable
- Val shows local deterministic suggestion behavior
- status remains clear: `Modo local activo`
- Frank can continue with manual capture and whiteboard organization

## Guardrails Preserved

- no real LLM implementation
- no API keys in browser
- no external services
- no persistence
- no recording
- no real PowerClub data
- no production promise
- no human/AGI framing
- Frank remains operator
- deterministic fallback remains available

## Manual Browser Test

1. Start the harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

2. Open:

`http://127.0.0.1:8765/val_discovery.html`

3. Switch to Operator Mode.
4. Type a response such as:

`El seguimiento llega tarde y las oportunidades se enfrían.`

5. Confirm that `Categoría detectada` becomes `Seguimiento`.
6. Click `Sugerir con Val`.
7. Click `Usar y organizar`.
8. Confirm:
   - whiteboard receives a card
   - Val observa shows the completion line
   - Demo recomendado and Próxima pregunta are visible
   - Frank can still ignore a later suggestion

## Known Limitations

- The mock response is still deterministic scaffolding.
- The browser page does not call a real LLM.
- Manual Frank confirmation remains required.
- Full production LLM behavior still requires the secure backend lane described in 02E/02F.
