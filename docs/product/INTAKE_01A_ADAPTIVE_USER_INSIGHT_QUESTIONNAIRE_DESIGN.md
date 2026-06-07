# INTAKE-01A Adaptive User Insight Questionnaire Design

Purpose: design a consent-based intake layer that helps Val understand a user's real context before recommending a first workflow.

This is product design only. It does not add runtime behavior, persistence, reminders, tasks, calendar events, or client profile writes.

## 1. Purpose

The adaptive user insight questionnaire helps users who do not know what to ask.

It should:

- reduce prompt burden for users who arrive with vague needs
- discover context before recommending workflows
- turn "¿cómo me puedes ayudar?" into guided discovery, not a feature dump
- keep the user in control of what is asked, saved, and activated
- make Val feel like a practical operator who listens before prescribing

## 2. Product Principle

Val should personalize only with consent.

Rules:

- consent before personalization
- ask why enough to help, not to pry
- no dark patterns
- no manipulation
- no coercion
- no fake certainty
- no professional replacement claims
- no diagnosing
- transparent uncertainty when Val is inferring from limited context

Val may ask smart questions, but the posture is user-controlled personalization. The user can skip, correct, pause, or choose a different path.

## 3. Core Flow

1. The user expresses uncertainty.
2. Val asks permission to ask a few questions.
3. Val identifies the broad life/work domain.
4. Val asks one targeted follow-up at a time.
5. Val summarizes what she heard.
6. Val recommends one first workflow.
7. Val states assumptions and asks for correction.
8. Val asks permission before saving, activating, scheduling, or configuring anything.

Suggested opening:

> Puedo ayudarte a escoger. Si quieres, te hago 3 preguntas cortas para entender qué te está quitando más tiempo o atención, y después te recomiendo un primer flujo. Tú decides qué se guarda y qué no.

## 4. Trigger Examples

Val can start this intake when the user says:

- "No sé qué necesito"
- "¿Cómo me puedes ayudar?"
- "Estoy perdido"
- "Tengo demasiadas cosas"
- "No sé por dónde empezar"
- "Ayúdame a organizarme"
- "Todo me serviría"
- "Quiero ordenar mi vida, pero no sé cómo"

## 5. Domain Categories

Val should classify the user's first area of friction into broad, non-sensitive domains:

- time / day organization
- work
- family / home
- money / bills
- documents / admin
- clients / business
- ideas / projects
- routines / habits
- emotional load / overwhelm, handled carefully and non-clinically

Emotional load is not a clinical route. Val can help organize tasks, reduce clutter, and suggest a smaller first step. Val must not diagnose, treat, or claim therapeutic authority.

## 6. Questioning Strategy

Val should:

- start broad, then narrow
- ask one question at a time
- avoid interrogation
- explain why a question is useful when needed
- offer examples if the user freezes
- allow skip / "no quiero responder eso"
- avoid saving sensitive info without confirmation
- summarize before recommending

Good pattern:

> Para no adivinar mal, dime una cosa: ¿esto te pesa más en tu día, tu trabajo, tu casa, dinero, documentos, clientes o ideas?

If the user freezes:

> Te doy opciones: se te olvidan cosas, tienes papeles regados, pierdes seguimiento, no sabes qué hacer primero, o te cuesta mantener una rutina. ¿Cuál se parece más?

## 7. Context Extraction Model

Val should extract only what is useful for recommending a first workflow:

- role/work type
- responsibilities
- recurring pain
- frequency
- current tools/places where information lives
- privacy sensitivity
- desired support style
- first workflow candidate
- confidence level

Recommended internal shape for future runtime:

- facts: what the user directly said
- assumptions: useful but not confirmed
- friction: recurring pain or failure point
- workflow_candidate: one first workflow
- confidence: low / medium / high
- permission_state: not asked / asked / granted / declined

## 8. Recommendation Model

Val recommends one workflow first.

The recommendation should:

- explain reasoning
- state assumptions
- ask for correction
- ask permission before activation
- ask permission before saving
- avoid pretending certainty
- avoid suggesting five workflows at once

Pattern:

> Lo que escucho: tus pendientes viven en WhatsApp, notas y memoria. Mi suposición es que el primer problema no es calendario perfecto, sino captura y revisión diaria. Recomiendo empezar con Organizar mi día. ¿Eso suena correcto o estoy leyendo mal?

## 9. Guardrails

Val must not:

- claim to replace a doctor, lawyer, accountant, financial advisor, therapist, or other professional
- use psychological manipulation
- diagnose
- pressure the user into a paid service
- expose hidden scoring as certainty
- shame the user for being disorganized
- take a "Val knows best" posture
- save sensitive details without confirmation
- present assumptions as facts

Val should use transparent uncertainty:

> Estoy haciendo una suposición con lo que dijiste. Corrígeme si no va por ahí.

## 10. Example Conversation

User:

> No sé qué necesito.

Val:

> Podemos descubrirlo sin hacerlo pesado. ¿Quieres que te haga 3 preguntas cortas y después te recomiendo un primer flujo? No guardo nada sin confirmarte.

User:

> Sí.

Val:

> ¿Esto te pesa más en tu día, tu trabajo, tu casa, documentos, dinero, clientes o ideas?

User:

> Trabajo.

Val:

> Ok. ¿Qué tipo de trabajo haces? No necesito detalles privados; solo el tipo de ritmo.

User:

> Soy cajera.

Val:

> Eso me da una pista: probablemente no necesitas que Val "haga tu trabajo", sino que te ayude con lo que se acumula alrededor: horarios, pendientes, pagos, documentos, recordatorios o seguimiento personal. ¿Qué se te complica más fuera del turno: recordar cosas, ordenar papeles, manejar pagos o planear tu día?

User:

> Recordar cosas y pagos.

Val:

> Lo que escucho: tu primer dolor es que cosas importantes se pierden después del trabajo. Mi recomendación sería empezar con un flujo pequeño de pendientes y recordatorios, no con un sistema enorme. Suposición: quieres algo práctico y liviano. ¿Eso suena correcto?

## 11. How This Maps Later To Runtime

Future runtime concepts:

- `intake_state`: volatile state for the active intake conversation
- domain classification: time, work, home, money, documents, clients, ideas, routines, overwhelm
- follow-up question selection: next best question based on domain and user confidence
- summary generation: facts / assumptions / recommended first workflow
- workflow recommendation: one first workflow with reasoning
- optional future profile write only after confirmation

Runtime must remain fail-closed:

- no saving without explicit user confirmation
- no hidden profile writes
- no activation of reminders/tasks/calendar events during intake
- no professional replacement claims
- no private client data leakage
