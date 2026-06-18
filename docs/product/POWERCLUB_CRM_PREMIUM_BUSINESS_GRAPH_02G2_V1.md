# PowerClub CRM Battle 02G.2 - Premium Business Graph Layout

## Frank QA Finding

After 02G.1, the conversation-first map worked technically:

- PowerClub root appeared
- 25 sucursales appeared
- asesores / vendedores appeared
- WhatsApp appeared
- leads perdidos and falta de seguimiento appeared
- business memory updated

But the visual experience still did not feel premium enough. The map looked too much like static boxes and not enough like Val organizing a business graph in real time.

## Visual Problem

The previous map had:

- heavy diagonal lines
- weak animation
- box-like nodes
- limited hierarchy
- not enough sense that Val was placing ideas into structure

## Premium Graph Layout Principles

The 02G.2 layout moves toward a radial/orbit-style business graph:

- PowerClub root is central and visually stronger
- category clusters are positioned around the root
- links are thinner and curved
- insight nodes are smaller and closer to the relevant cluster
- new nodes get a stronger pulse
- the map keeps Presentation Mode clean

## Node Hierarchy

Root node:

- central
- gold accent
- stronger glow
- represents company/client

Category nodes:

- cyan outline
- compact
- simple text icon codes
- represent business branches:
  - Estructura
  - Métricas faltantes
  - Personas / roles
  - Proceso / canales
  - Riesgos / decisiones
  - Dolores

Insight nodes:

- smaller
- darker filled background
- placed around category clusters
- newest insight pulses/glows

## Val Organizing Presence

When Frank processes a response:

- the map shows `Val organizando...`
- a new insight node pulses into place
- Val displays a short deterministic interpretation

Example:

`Estoy viendo una fuga de seguimiento asociada a WhatsApp y asesores por sede.`

No real LLM is used. The interpretation is still deterministic and local.

## Business Memory

Business memory now reads as executive interpretation:

- Estructura: `25 sucursales`
- Personas: `Asesores / vendedores`
- Dolor principal: `seguimiento`
- Canal crítico: `WhatsApp`
- Métrica pendiente: `oportunidades enfriadas por semana`
- Demo recomendado: `Riesgo y rescate`

Unknown fields show:

`por validar`

## Browser QA Script

Start harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

`http://127.0.0.1:8765/val_discovery.html`

Public harness when active:

`http://167.172.239.59:8767/val_discovery.html`

Test response:

`PowerClub tiene 25 sucursales, asesores por sede, y se nos pierden leads porque no dan seguimiento por WhatsApp a tiempo.`

Expected:

- central PowerClub node remains dominant
- 25 sucursales appears under Estructura
- asesores / vendedores appears under Personas / roles
- WhatsApp appears under Proceso / canales
- leads perdidos / seguimiento appear under Dolores
- business memory reads like executive summary
- Val interpretation appears after processing
- primary action remains `Procesar respuesta`

## Known Limitations

- Still keyword-based and deterministic.
- No real LLM.
- No STT/voice/avatar implementation.
- No persistence.
- No real PowerClub data.
- Map layout may still need browser-specific tuning after Frank visual QA.

## Future

- real controlled LLM
- STT/voice
- Obsidian or Markdown export
- corporate PowerVal memory
- richer graph physics or canvas/SVG layout if needed
