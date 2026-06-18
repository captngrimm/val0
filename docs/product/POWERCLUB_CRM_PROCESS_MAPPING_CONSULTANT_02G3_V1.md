# POWERCLUB-CRM-BATTLE-02G.3 — Progressive Process Mapping Consultant

## Product Insight From Frank

The business graph should not only look better. Val Discovery should behave like a lightweight process-mapping consultant:

- interview the owner or GM
- identify which operating domain each answer belongs to
- map the company progressively
- detect missing process information
- suggest useful reports or metrics
- connect findings to the PowerClub pilot and roadmap

The target flow is:

conversation -> process understanding -> map -> gaps -> useful next question.

This remains a deterministic local demo. It does not use a real LLM, API key, external call, backend persistence, voice implementation, or real PowerClub data.

## Process-Mapping Consultant Model

Val applies a bounded playbook to each captured answer. Frank remains the operator and can correct the response before processing.

The presentation flow stays simple:

1. Val asks a process-mapping question.
2. Frank enters what the client said.
3. Frank clicks `Procesar respuesta`.
4. Val extracts process signals locally.
5. Val places discovered information into the map.
6. Val updates the operating memory card.
7. Val asks the next best question based on missing information.

## Bounded Playbook Domains

Val now classifies answers into these local domains:

- `Estructura del negocio`: sucursales, sedes, gimnasios, regiones, ubicaciones.
- `Personas / roles`: gerencia, asesores, vendedores, operadores, responsables, supervisores.
- `Ventas / leads`: leads, prospectos, cierres, oportunidades, fuente del lead.
- `Seguimiento comercial`: WhatsApp, llamadas, contacto, ultimo contacto, proximo paso.
- `Canales / herramientas`: WhatsApp, Instagram, Facebook, llamadas, Excel, CRM, sistema actual.
- `Reportes / metricas`: dashboard, reportes, KPIs, visibilidad, ranking, tasa de contacto, tiempo de respuesta.
- `Procesos / operacion`: asignacion, atencion, escalamiento, registro, flujo actual.
- `Dolores / riesgos`: perdida de oportunidades, falta de seguimiento, datos incompletos, baja visibilidad, alcance riesgoso.
- `Roadmap / piloto`: piloto, fase 1, fase 2, alcance, implementacion, prioridad.

## Progressive Question Logic

Val asks the next question based on what is still missing:

- If structure is unknown: `Cuantas sucursales tienen y como se distribuyen?`
- If structure is known but roles are unknown: `Quien es responsable del seguimiento comercial por sucursal?`
- If roles are known but channels are unknown: `Por que canales llegan y se atienden los leads?`
- If channels are known but pain is unknown: `En que punto se pierden mas oportunidades?`
- If pain is known but metrics are unknown: `Que dato necesita ver gerencia para saber si ese dolor esta mejorando?`
- If metrics are known: `La primera vista recomendada seria Riesgo y rescate. Quieren validar ese piloto primero?`

The goal is to avoid a rigid script. If the conversation naturally jumps from follow-up to branches, roles, or channels, Val can move the map and question forward.

## Better-Practice Suggestions

Val phrases recommendations as validation prompts, not production promises.

For follow-up:

- Conviene validar ultimo contacto.
- Conviene validar proxima accion.
- Conviene validar asesor dueno.
- Conviene validar sucursal.
- Conviene validar estado del lead.
- Conviene validar antiguedad de oportunidad.
- Conviene validar razon de perdida.

For management visibility:

- Una vista util podria mostrar atrasos por sucursal.
- Una vista util podria mostrar ranking de asesores.
- Una vista util podria mostrar cola de riesgo/rescate.
- Una vista util podria mostrar fuente de leads.
- Una vista util podria mostrar conversion por sucursal.

For process mapping:

- Conviene validar rol responsable.
- Conviene validar fuente de datos.
- Conviene validar frecuencia de revision.
- Conviene validar herramienta actual.
- Conviene validar pain point.
- Conviene validar dueno de decision.

## Business Memory Card

The memory card now reads like an emerging operating model:

- `Estructura`
- `Roles`
- `Canales`
- `Dolor principal`
- `Metrica a validar`
- `Vista recomendada`
- `Proxima pregunta`
- `Roadmap / piloto`

Unknown fields show `por validar` so the card communicates missing information instead of empty UI.

## PowerVal Roadmap Hint

After enough information is captured, the demo can safely show:

`Esto puede alimentar una memoria operativa de PowerClub: procesos, decisiones, pendientes y roadmap del piloto.`

This is a roadmap hint only. It does not claim PowerVal is already implemented, connected to PowerClub data, or production-ready.

## Browser QA Script

Run the local browser harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

- `http://127.0.0.1:8767/val_discovery.html`
- public tunnel / exposed URL if Frank is testing remotely

Suggested test answer:

```text
PowerClub tiene 25 sucursales, asesores por sede, y se nos pierden leads porque no dan seguimiento por WhatsApp a tiempo.
```

Expected behavior:

- `25 sucursales` appears under structure.
- `Asesores / vendedores` appears under people.
- `WhatsApp` appears under process / channels.
- `Leads perdidos` and `Falta de seguimiento` appear under pains.
- Business memory updates.
- Next question moves toward the next missing domain, usually metrics.

Correction test:

```text
No son 25, son 24 sucursales activas.
```

Expected behavior:

- Structure count updates where possible instead of creating a confusing duplicate.

## Limitations

- This is deterministic and keyword-based.
- It does not understand Spanish semantically like a real LLM.
- It does not persist meeting memory.
- It does not ingest Excel, PDF, CRM exports, or real PowerClub data.
- It does not record audio or use custom STT.
- Frank remains responsible for confirming interpretation and client-safe wording.

## Future

- Scoped LLM using this same playbook through a secure backend.
- Browser or premium STT/voice with explicit approval.
- PDF/Excel intake for discovery prep.
- Obsidian/Markdown export of the process map.
- Corporate PowerVal memory by company, role, permission, process, decision, and roadmap.
- Val personal for GM users, scoped by permissions and approved data sources.
