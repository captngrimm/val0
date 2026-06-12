# PowerClub CRM Battle 02C.5 - Animated Consultant Whiteboard

## Purpose

This lane makes Val Discovery Mode feel more interactive and consultative while staying deterministic, local, and operator-assisted.

Val does not autonomously understand the meeting. Frank captures or confirms the response, and Val applies local rules to organize the conversation into the whiteboard.

## Animated Whiteboard Behavior

When Frank confirms and organizes a response:

- Val briefly enters `organizando` state.
- The message area shows "Val organizando..." before the full response appears.
- A whiteboard card is created locally.
- The target lane receives a subtle glow.
- The new card slides/fades into place.
- The card includes:
  - category badge
  - recommended CRM demo section badge
  - captured response text

Whiteboard lanes remain:

- Dolor detectado
- Señales / patrones
- Datos pendientes
- Decisiones
- Riesgos / exclusiones
- Próximo paso recomendado

## Consultant-Like Local Reasoning

The cockpit now maps captured text and selected category to a local interpretation:

| Signal | Whiteboard lane | Val interpretation | Recommended demo |
| --- | --- | --- | --- |
| Seguimiento | Dolor detectado | "Ok, esto lo voy a tratar como dolor principal de seguimiento." | Riesgo y rescate + Cola del asesor |
| Leads | Señales / patrones | "Esto suena a problema de entrada o calidad de leads." | Vista gerencial |
| Visibilidad gerencial | Dolor detectado | "Esto apunta a visibilidad gerencial." | Vista gerencial |
| Flujo asesor | Señales / patrones | "Esto conecta con la operación diaria del asesor." | Cola del asesor |
| Datos/fuentes | Datos pendientes | "No lo vendería todavía como feature." | Scope freeze / piloto |
| Alcance/piloto | Próximo paso recomendado | "Esto apunta a definición de piloto." | Scope freeze / piloto |
| Riesgo/exclusión | Riesgos / exclusiones | "Esto puede crecer el alcance." | Scope freeze / piloto |
| Decisión | Decisiones | "Esto suena a decisión de reunión." | Scope freeze / piloto |

## Natural Val Language

Val now uses controlled consultative phrases such as:

- "Ok, esto lo voy a tratar como..."
- "Esto suena a..."
- "Lo separo para no mezclarlo..."
- "Antes de mostrar el demo, conviene validar..."
- "Esto conecta con..."
- "No lo vendería todavía como feature..."

Avoided language:

- "La IA detectó..."
- "Val sabe..."
- "Val escucha todo..."
- "Estoy analizando autónomamente..."
- "He entendido perfectamente..."

## Demo Bridge

Each organized card updates:

- `Val recomienda mostrar`
- `Siguiente pregunta sugerida`

Examples:

- Seguimiento -> Riesgo y rescate + Cola del asesor
- Visibilidad -> Vista gerencial
- Asesor -> Cola del asesor
- Datos/riesgo/alcance -> Scope freeze / piloto

## Presentation Mode Impact

Presentation Mode keeps the whiteboard highlights prominent:

- operator controls stay hidden
- new cards remain visually noticeable
- only the first three whiteboard lanes are shown by default to avoid clutter
- Val's current line and next question remain easy to read

## Operator Mode Preservation

Operator Mode still supports:

- manual response capture
- category chips
- advanced capture buttons
- notes/decisions/risks/next steps
- summary generation
- browser voice fallback
- browser STT fallback

## Future LLM Upgrade Path

This lane does not add LLM behavior. A future controlled upgrade could augment or replace local rules only through:

- secure backend/proxy
- no API key in browser
- prompt capsule scoped to PowerClub discovery
- allowed topics list
- refusal behavior for unsupported claims or production promises
- fallback to deterministic local mode
- privacy/logging boundaries
- explicit meeting safety guardrails

Recommended principle:

Use LLM only after the deterministic cockpit is meeting-safe. The LLM should help phrase, summarize, and suggest within approved scope; it should not claim autonomy, record meetings silently, or make production promises.

## Guardrails

- No OpenAI, ChatGPT, or external LLM API call.
- No backend.
- No persistence.
- No recording.
- No audio storage.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- Frank remains the operator.
- Val Discovery Stage remains separate from the PowerClub CRM Demo.

## Remaining Limitations

- The reasoning is simple keyword/category logic.
- Visual animation still requires Frank-machine browser QA.
- Presentation Mode currently highlights the first three lanes to avoid clutter; Operator Mode shows the full whiteboard.
- Future LLM work must be separately scoped.
