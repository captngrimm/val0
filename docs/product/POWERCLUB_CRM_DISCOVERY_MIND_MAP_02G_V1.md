# PowerClub CRM Battle 02G - Discovery Mind Map / Business Graph Mode

## Purpose

Add a live visual business map to Val Discovery so the meeting feels more consultative and intelligent without adding a real LLM or exposing more operator complexity.

This is an enhancement to the existing Val Discovery experience, not a separate product.

## UX Intent

The guided wizard remains the meeting driver:

1. Preguntar
2. Capturar
3. Sugerir
4. Aprobar y organizar
5. Recomendar / avanzar

The new map shows what Val has structurally understood after Frank approves or organizes a response.

Target feeling:

- consultant mapping the business live
- high-trust business graph
- “Val is organizing the conversation”
- visual output, not just text boxes

## What Was Added

The page now includes:

- central/root node for the client/company
- group nodes for business structure, people, pains, process/channels, metrics, risks
- linked insight nodes created from approved organized answers
- compact “Val ha organizado…” cue
- animated “Val ubicando…” chip when a new insight is placed
- node settle animation for the newest map item

Presentation Mode keeps the wizard primary and shows the map as a visual result layer. Operator Mode still has the deeper cockpit below.

## Deterministic Extraction Rules

No LLM is used. The map is built with local deterministic keyword rules.

### Business Structure

Examples:

- `25 sucursales`
- `sedes`
- `gimnasios`
- `ubicaciones`

These attach to `Estructura`.

### People / Roles

Examples:

- asesores
- vendedores
- gerencia
- gerente
- operadores
- usuarios

These attach to `Personas / roles`.

### Pains / Problems

Examples:

- seguimiento
- leads perdidos
- contacto tardío
- se enfría
- atrasos

These attach to `Dolores`.

### Process / Channels

Examples:

- WhatsApp
- llamadas
- Excel
- CRM

These attach to `Proceso / canales`.

### Metrics / Missing Metrics

Examples:

- visibilidad
- reportes
- dashboard
- datos/campos por confirmar

These attach to `Métricas faltantes`.

### Risks / Decisions

Examples:

- alcance
- piloto
- riesgo
- exclusión

These attach to `Riesgos / decisiones`.

## Placement Rules

- Root node = client/company name.
- Group hubs connect to root.
- Extracted insights connect to the matching group hub.
- Newest item animates into place.
- Duplicate labels in the same group are not re-added.
- The map keeps a compact recent set to avoid visual chaos.

## Example

Captured response:

`Tenemos 25 sucursales y los asesores no dan seguimiento por WhatsApp; muchos leads se enfrían.`

Map result:

- PowerClub
  - Estructura
    - 25 sucursales
  - Personas / roles
    - Asesores / vendedores
  - Proceso / canales
    - WhatsApp
  - Dolores
    - Falta de seguimiento
    - Leads perdidos
    - Contacto tardío

## Animation Behavior

When Frank approves or organizes:

1. A small `Val ubicando...` chip appears.
2. The newest map node settles into its group.
3. Links remain visible so the viewer sees the relationship.

Motion is intentionally short and subtle: visible enough to feel alive, not slow or playful.

## Browser QA Checklist

Start harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

`http://127.0.0.1:8765/val_discovery.html`

Public harness when active:

`http://167.172.239.59:8767/val_discovery.html`

Test:

1. Confirm Presentation Mode starts with the wizard and map.
2. Confirm the map root shows `PowerClub`.
3. Enter:
   `Tenemos 25 sucursales y los asesores no dan seguimiento por WhatsApp; muchos leads se enfrían.`
4. Capture response.
5. Request Val suggestion.
6. Use and organize.
7. Confirm the map adds relevant nodes:
   - 25 sucursales
   - Asesores / vendedores
   - WhatsApp
   - Falta de seguimiento
   - Leads perdidos or contacto tardío
8. Confirm the wizard still shows the next primary action.
9. Confirm CRM navigation link still works.

## Guardrails

- no real LLM provider
- no API keys
- no external calls
- no avatar
- no voice implementation
- no persistence
- no real PowerClub data
- no production promise
- no systemd
- deterministic fallback remains
- Frank remains operator and approver

## Remaining Limitations

- The extraction rules are intentionally simple.
- The map is a visual discovery aid, not a database.
- It does not infer hidden facts.
- It does not replace Frank's judgment.
- Real semantic reasoning should wait for the controlled backend/LLM lane.
