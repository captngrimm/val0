# POWERCLUB CRM - Val Discovery Stage V1

## Purpose

Define the Val Discovery Stage used by Frank/Isthmus Dynamics during the PowerClub discovery and boss/GM meeting.

Important distinction:

- PowerClub CRM Demo = what PowerClub might use in a pilot.
- Val Discovery Stage = Isthmus Dynamics internal meeting cockpit used to guide discovery, capture notes, decisions, risks, and next steps.

This is not a full AI agent. It is not a human avatar. It is not raw ChatGPT. It is a premium static discovery cockpit with Val presence, deterministic question flow, local capture, and optional browser-native speech.

## File

Static page:

`docs/demo/powerclub_crm/val_discovery.html`

Linked from:

`docs/demo/powerclub_crm/index.html`

Label:

`Val Discovery Mode · herramienta interna de reunión`

## Positioning

Use this wording:

```text
Herramienta interna de Isthmus Dynamics para guiar discovery, capturar decisiones y ordenar próximos pasos.
```

Say:

- "herramienta interna en desarrollo"
- "discovery guiado"
- "captura de decisiones"
- "próximos pasos"
- "Frank opera la reunión"

Do not say:

- "Val analiza automáticamente"
- "Val ya opera PowerClub"
- "Val reemplaza consultores"
- "IA autónoma"
- "producción lista"

## Visual Direction

The stage should feel like a premium internal AI Ops cockpit:

- Dark premium background.
- Isthmus Dynamics mark used subtly.
- Red pulsing core inspired by an AI operations nucleus.
- Cyan wave when Val is "speaking."
- Metallic/futuristic tone.
- No avatar.
- No human face.
- Readable meeting text.
- Professional, not gimmicky.

## Required UI Covered

Header / brand:

- Isthmus Dynamics.
- Val Discovery Mode.
- Meeting Ops / Honest AI Ops.
- Internal positioning line.

Central Val presence:

- Animated red core.
- Idle pulse state.
- Speaking pulse state.
- Cyan accent wave when speaking.
- No human avatar.

Main controls:

- Iniciar sesión.
- Hablar como Val.
- Siguiente pregunta.
- Siguiente pregunta inteligente.
- Generar resumen.
- Copiar resumen.

Val dice panel:

- Shows scripted Val message.
- Updates on button clicks.
- Works if speech is unavailable.

Browser-native TTS:

- Uses `speechSynthesis` if available.
- Optional only.
- No external API.
- No ElevenLabs.
- No audio files.
- If unsupported, text remains available.

Meeting agenda:

- Validar dolor operativo.
- Revisar vista gerencial.
- Revisar flujo asesor.
- Identificar datos/campos necesarios.
- Definir alcance de piloto.
- Acordar próximo paso.

Guided question bank:

- Dolor operativo.
- Visibilidad gerencial.
- Flujo asesor.
- Datos y fuentes.
- Alcance de piloto.
- Riesgos / exclusiones.
- Próximo paso.

Capture panels:

- Notas.
- Decisiones.
- Riesgos / parking lot.
- Próximos pasos.

Operator-assisted capture:

- Respuesta capturada.
- Capturar dolor.
- Capturar decisión.
- Marcar riesgo.
- Dato pendiente.
- Candidato para piloto.

Val observa:

- Updates after Frank classifies a captured answer.
- Suggests deterministic next action.
- Does not generate AI analysis.

Summary:

- Generates local summary from captured fields.
- Includes pains, decisions, risks, pending data, pilot candidates, notes, and next steps.
- Copies summary to clipboard when the browser allows it.
- Gives manual copy fallback.
- No persistence.

## Scripted Val Lines

Intro:

```text
Hola. Esta sesión busca validar dolor operativo, visibilidad gerencial, flujo asesor y alcance de piloto.
```

Framing:

```text
Mi objetivo es ayudar a que esta conversación termine con decisiones claras, no con ideas sueltas.
```

Manager visibility:

```text
Pregunta sugerida: ¿qué necesita ver gerencia cada mañana para saber dónde actuar?
```

Advisor workflow:

```text
Pregunta sugerida: ¿qué necesita hacer el asesor en menos clics para mantener el seguimiento actualizado?
```

Scope:

```text
Antes de cotizar, conviene separar piloto, fase dos y deseos futuros.
```

Wrap-up:

```text
Cierre sugerido: confirmar dolor, datos necesarios, responsable de decisión y próximo paso.
```

## Operator-Assisted Intelligence Behavior

This is deterministic and local. It should feel consultative without claiming real AI.

Capture logic:

- If pain is captured, Val suggests asking about impact and frequency.
- If decision is captured, Val suggests confirming owner and date.
- If risk is captured, Val suggests moving it to exclusions/scope.
- If data pending is captured, Val suggests asking for source/export/sample.
- If pilot candidate is captured, Val suggests scope freeze next.

Smart next-question behavior:

- Uses current captured state.
- Chooses from the existing structured question bank.
- Does not generate new text with AI.
- Does not call external services.

## Meeting Usage Flow

1. Frank opens meeting.
2. Frank introduces Val as internal Isthmus Dynamics discovery tool.
3. Frank clicks "Iniciar sesión."
4. Val gives short intro.
5. Frank shows CRM demo.
6. Frank returns to Val for next guided question.
7. Frank captures notes, decisions, risks, data needs, and pilot candidates.
8. Val helps generate local summary and next steps.
9. Frank copies summary or uses it after the meeting.

## Sample Dialogue

Frank:

```text
Antes de enseñarles la maqueta, les muestro una herramienta interna que estamos desarrollando en Isthmus Dynamics. Se llama Val Discovery Mode. Nos ayuda a guiar discovery, capturar decisiones y convertir la reunión en próximos pasos.
```

Val:

```text
Bienvenidos. Hoy vamos a validar tres cosas: dónde se pierden oportunidades, qué necesita ver gerencia y cómo puede trabajar el asesor con menos fricción.
```

Client:

```text
¿Eso es parte del CRM?
```

Frank:

```text
No exactamente. El CRM es lo que estamos evaluando para PowerClub. Val es nuestra capa interna de discovery y operaciones. Hoy me ayuda a correr la reunión; más adelante puede convertirse en copiloto si el cliente lo necesita y se aprueban datos, reglas y alcance.
```

Val:

```text
Primera pregunta sugerida: ¿en qué parte del seguimiento sienten que se pierden más oportunidades hoy?
```

## Summary Structure

The generated summary should include:

- Captured pains.
- Decisions.
- Risks.
- Pending data.
- Pilot candidate notes.
- General notes.
- Next step.
- Guardrail that it is local/demo output with no real connected data.

## Guardrails

- No real AI claims.
- No OpenAI/ChatGPT API.
- No ElevenLabs/API.
- No external services.
- No microphone.
- No STT.
- No recording.
- No backend.
- No client data persistence.
- No real PowerClub data.
- No WhatsApp/email/payment integration.
- No production promise.
- No claim that Val is complete.
- No broad refactor.
- No Karen live files.
- Static, local, demo-safe, deterministic.

## Recommended Next Evolution

Only after the PowerClub conversation validates the need:

- More reusable discovery templates by client.
- Exportable meeting recap.
- Approved client-safe data import.
- Optional real Copilot layer after data, permissions, formulas, and scope are approved.
- Optional voice/STT module only as separately scoped work.
