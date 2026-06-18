# PowerClub CRM Battle 02G.1 - Conversation-First Business Map

## Why 02G Was Technically Correct But UX Still Wrong

02G proved the map could work:

- nodes were added
- seguimiento was detected
- WhatsApp, asesores, leads perdidos, and falta de seguimiento appeared
- the browser harness worked

But the experience still felt like:

- wizard
- button
- button
- button

It did not yet feel like a consultant building a business graph from the conversation.

## Conversation-First Principle

The desired flow is:

`conversation -> understanding -> business map -> next intelligent question`

Not:

`wizard -> rigid step -> rigid button -> rigid next step`

Presentation Mode now emphasizes:

- the live business map
- one response input
- one primary action: `Procesar respuesta`
- Val's next question after the map updates

## Obsidian-Style Business Graph Direction

The map is the protagonist:

- central client node
- business clusters around it
- new insights added near the relevant cluster
- links remain visible
- newest node pulses/highlights
- map cue explains what Val understood

The map is still static HTML/CSS/JS, with no external graph library.

## Dynamic Question Rules

Local deterministic rules update the next question based on the captured response.

If the answer mentions sucursales, sedes, ubicaciones, or gimnasios:

`¿Cómo se distribuyen esas sucursales y quién les da seguimiento?`

If the answer mentions asesores, vendedores, or operadores:

`¿Qué responsabilidad tiene cada asesor en el seguimiento?`

If the answer mentions WhatsApp, contacto, leads, or seguimiento:

`¿Cuántas oportunidades se enfrían por falta de contacto a tiempo?`

If the answer mentions dashboard, reportes, or visibilidad:

`¿Qué necesita ver gerencia cada mañana para decidir dónde actuar?`

If the answer mentions piloto, alcance, or fase:

`¿Qué debe entrar en piloto y qué debe quedar para fase dos?`

## Business Memory Card

The map now includes a compact evolving memory:

- Estructura
- Personas
- Dolor principal
- Canal crítico
- Métrica pendiente
- Demo recomendado

This lets a non-technical viewer understand what the conversation has revealed without reading raw notes.

## Presentation Mode

Presentation Mode should feel like:

- Val asks or frames the current question
- Frank types the answer
- Frank clicks `Procesar respuesta`
- the map updates
- Val proposes the next question

It should not feel like an operator cockpit.

## Operator Mode

Operator Mode still keeps:

- old wizard/state controls
- mock/local Val Mentor drawer
- whiteboard
- notes
- Q&A
- voice/STT fallback controls
- ArcX/debug tools

These remain secondary and are not required for the GM-facing demo.

## Browser QA Script

Start harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

`http://127.0.0.1:8765/val_discovery.html`

Public harness when active:

`http://167.172.239.59:8767/val_discovery.html`

Test:

1. Confirm the map is visually dominant.
2. Confirm the visible primary button says `Procesar respuesta`.
3. Type:

`PowerClub tiene 25 sucursales y los asesores no dan seguimiento por WhatsApp. Muchos leads se enfrían.`

4. Click `Procesar respuesta`.
5. Confirm map adds:
   - 25 sucursales
   - Asesores / vendedores
   - WhatsApp
   - Falta de seguimiento
   - Leads perdidos or contacto tardío
6. Confirm memory card updates.
7. Confirm next question shifts to structure, roles, or impact depending on the answer.
8. Confirm `Volver al CRM demo` still works.

## Limitations

- No real LLM.
- No API keys.
- No external calls.
- No STT/voice/avatar implementation.
- No persistence.
- No real PowerClub data.
- No production promise.
- Extraction is deterministic and keyword-based.

## Future

- controlled backend LLM
- STT / voice capture
- Obsidian or Markdown export
- corporate Val memory layer
- richer graph layout and clustering
