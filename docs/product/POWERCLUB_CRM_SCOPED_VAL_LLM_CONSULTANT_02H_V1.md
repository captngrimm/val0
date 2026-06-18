# POWERCLUB-CRM-BATTLE-02H — Scoped Val LLM Consultant Layer

## Why This Lane Exists

The deterministic process-mapping consultant from 02G.3 works for simple signals, but it reaches its limit when a client answer contains several business concepts at once.

Example answer:

```text
Gerencia necesita ver por sucursal cuántos leads están sin contacto por más de 24 horas, quién es el asesor responsable y cuál fue el último contacto.
```

Expected interpretation:

- This is a management/risk-rescue report need.
- Key report fields include sucursal, asesor responsable, leads sin contacto +24h, and ultimo contacto.
- Recommended CRM section is `Riesgo y rescate`.
- Next question should ask about review frequency, alert threshold, or owner.

Local keyword logic can place some nodes, but it does not sound consultative enough. The scoped Val LLM layer is designed to turn one captured answer into bounded consultant output without becoming a free-form chatbot.

## Current Implementation Status

Status: provider-ready mock only.

- Browser never sees API keys.
- No real provider call is made in this lane.
- Backend reads provider configuration only from environment variables.
- If provider or key is missing, the endpoint returns safe local fallback.
- Mock mode returns the scoped consultant response schema.
- Frontend validates the response before using it.
- Deterministic local fallback remains available.
- No persistence, database, systemd, production service, real PowerClub data, STT expansion, or voice/avatar implementation was added.

Relevant environment variables:

- `VAL_POWERCLUB_LLM_PROVIDER=mock|local|openai`
- `VAL_POWERCLUB_LLM_API_KEY=...`
- `VAL_POWERCLUB_LLM_MODEL=...`
- `VAL_POWERCLUB_LLM_MOCK_ENABLED=1`

For this lane, use mock mode for browser testing.

## Scoped LLM Role

Val may act as:

- discovery facilitator
- process-mapping consultant
- operational memory organizer
- report/metric suggester
- next-question recommender
- CRM demo section recommender

Val must not act as:

- autonomous decision-maker
- free-form chatbot
- legal or financial advisor
- production PowerClub CRM
- PowerClub system of record
- source of pricing, scope, or implementation commitments
- replacement for Frank

## Request Schema

The frontend/backend seam sends a bounded JSON payload:

```json
{
  "client_name": "PowerClub",
  "meeting_goal": "Validar dolor operativo y alcance de piloto",
  "meeting_context": {
    "client_or_person": "PowerClub",
    "role_context": "GM / gerencia comercial",
    "meeting_objective": "Validar proceso, datos, riesgos y próximo paso",
    "current_step": "conversation"
  },
  "current_question": "¿Qué dato necesitaría ver gerencia para saber si ese dolor está mejorando?",
  "captured_response": "Gerencia necesita ver por sucursal cuántos leads están sin contacto por más de 24 horas...",
  "selected_category": "metricas",
  "current_business_memory": {
    "estructura": "por validar",
    "roles": "por validar",
    "canales": "por validar",
    "dolor_principal": "por validar",
    "metrica_a_validar": "por validar",
    "vista_recomendada": "Vista gerencial",
    "proxima_pregunta": "por validar",
    "roadmap_piloto": "por validar"
  },
  "current_map_nodes": [],
  "process_domains": [
    "Estructura del negocio",
    "Personas / roles",
    "Ventas / leads",
    "Seguimiento comercial",
    "Canales / herramientas",
    "Reportes / métricas",
    "Procesos / operación",
    "Dolores / riesgos",
    "Roadmap / piloto"
  ],
  "allowed_demo_sections": [
    "Vista gerencial",
    "Riesgo y rescate",
    "Ficha del asesor",
    "Cola del asesor",
    "Templates / dictado",
    "Scope freeze / piloto"
  ],
  "roadmap_scope": "pilot/discovery only; no production promise",
  "guardrails": [
    "Spanish by default",
    "Frank approves before use",
    "No real PowerClub data",
    "No production promise",
    "No pricing/legal/commitment authority",
    "No implementation promises",
    "Route out-of-scope requests to phase two or scope freeze"
  ]
}
```

## Response Schema

The backend returns a validated structured suggestion:

```json
{
  "val_says": "Estoy entendiendo una necesidad de reporte gerencial de riesgo: leads sin contacto por más de 24 horas, por sucursal y con asesor responsable.",
  "val_message": "Estoy entendiendo una necesidad de reporte gerencial de riesgo: leads sin contacto por más de 24 horas, por sucursal y con asesor responsable.",
  "summary": "Gerencia necesita ver por sucursal cuántos leads están sin contacto por más de 24 horas...",
  "detected_pain": "seguimiento",
  "detected_domains": [
    "Reportes / métricas",
    "Seguimiento comercial",
    "Personas / roles"
  ],
  "nodes_to_add": [
    {
      "domain": "Reportes / métricas",
      "label": "Leads sin contacto +24h",
      "detail": "Indicador de oportunidades en riesgo"
    }
  ],
  "nodes_to_update": [
    {
      "domain": "Personas / roles",
      "match": "asesor",
      "label": "Asesor responsable"
    }
  ],
  "business_memory_update": {
    "estructura": "por sucursal",
    "roles": "Asesor responsable",
    "canales": "por validar",
    "dolor_principal": "Seguimiento comercial",
    "metrica_a_validar": "Leads sin contacto +24h por sucursal",
    "vista_recomendada": "Riesgo y rescate",
    "proxima_pregunta": "¿Cada cuánto necesita gerencia revisar esta vista: diario, semanal o por alerta?",
    "roadmap_piloto": "Vista de riesgo/rescate para seguimiento comercial"
  },
  "recommended_demo_section": "Riesgo y rescate",
  "follow_up_question": "¿Cada cuánto necesita gerencia revisar esta vista: diario, semanal o por alerta?",
  "next_question": "¿Cada cuánto necesita gerencia revisar esta vista: diario, semanal o por alerta?",
  "out_of_scope": false,
  "out_of_scope_response": "",
  "risk_flags": [
    "Sugerencia mock; Frank debe confirmar antes de usar."
  ],
  "next_step": "Frank confirma la lectura y decide si mostrar la sección recomendada.",
  "confidence": "medium",
  "needs_frank_confirmation": true
}
```

Strict validation:

- `needs_frank_confirmation` must always be true.
- `recommended_demo_section` must be in the allowed list.
- `detected_domains` must be in the allowed domain list.
- `nodes_to_add`, `nodes_to_update`, `whiteboard_cards`, and `risk_flags` must be arrays.
- `business_memory_update` must be an object.
- `out_of_scope` must be boolean.

## Frontend Behavior

Presentation Mode:

- Primary action remains `Procesar respuesta`.
- The page tries the same-origin scoped Val endpoint.
- If the endpoint returns a valid suggestion, Val updates:
  - consultant sentence
  - map nodes
  - business memory
  - next question
  - recommended CRM section
- If the endpoint is unavailable, invalid, or disabled, local deterministic fallback runs.
- No API/backend/mock technical copy is shown in the main presentation flow.

Operator Mode:

- Shows compact status: local fallback, mock, provider unavailable, or suggestion received.
- Keeps Frank approval with `Usar y organizar`.
- Debug/status remains secondary.

## Out-of-Scope Behavior

If the client asks about something outside the current CRM pilot, Val redirects naturally.

Example:

Client:

```text
¿También puedes manejar inventario completo y nómina?
```

Val:

```text
Eso se puede evaluar como fase posterior, pero no está dentro del piloto actual. Para esta reunión estoy enfocada en seguimiento comercial, visibilidad gerencial y rescate de oportunidades.
```

This becomes a scope/phase-two item, not a promise.

## Browser QA Script

Start the local harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

- `http://127.0.0.1:8767/val_discovery.html` if configured for port 8767
- or the harness URL printed by the server

Test answer:

```text
Gerencia necesita ver por sucursal cuántos leads están sin contacto por más de 24 horas, quién es el asesor responsable y cuál fue el último contacto.
```

Expected behavior:

- Val says this is a risk/reporting need.
- Map gains nodes for `Leads sin contacto +24h`, `Asesor responsable`, `Último contacto`, and `Por sucursal`.
- Memory updates metric to `Leads sin contacto +24h por sucursal`.
- Recommended demo becomes `Riesgo y rescate`.
- Next question asks about review frequency or alert threshold.

## Future Phases

- Real provider through secure backend/proxy only.
- No API key in browser.
- Stronger prompt capsule using this schema.
- STT/voice only after explicit approval.
- PDF/Excel intake for discovery prep.
- Corporate PowerVal memory by company, role, permission, process, decision, and roadmap.
- Val personal for GM by role/permission.
