# INTAKE-01B Volatile Runtime Adaptive Intake

Purpose: add a narrow, consent-based adaptive intake runtime for users who do not know where to start.

This lane adds volatile conversation state only. It does not add persistence, production memory writes, profile writes, database migrations, client data writes, calendar/task/reminder creation, or memory-spine runtime activation.

## 1. Trigger

Adaptive intake starts when the user says something like:

- "Val, no sé qué necesito"
- "Val, ayúdame a empezar"
- "Val, estoy perdida"
- "Val, estoy perdido"
- "Val, tengo demasiadas cosas"
- "Val, no sé por dónde empezar"

The existing "Val, ¿cómo me puedes ayudar?" guided onboarding route remains separate and still shows the current menu-style discovery flow.

## 2. Consent First

Val asks permission before intake questions:

```text
Te puedo hacer 2 o 3 preguntas rápidas para ubicarte mejor. No guardo nada sin que tú me confirmes. ¿Empezamos?
```

Refusal is respected:

```text
Perfecto, no pasa nada. Podemos seguir con ejemplos generales o escoger un flujo manualmente.
```

## 3. Volatile State Model

State lives only in `context.chat_data`.

States:

- adaptive_intake_permission
- adaptive_intake_domain
- adaptive_intake_followup

No state is persisted outside the current conversation/session.

## 4. Broad Domain Question

After confirmation, Val asks:

```text
¿Dónde sientes más desorden ahora: tiempo/día, trabajo, casa/familia, dinero/pagos, documentos, clientes/negocio, ideas/proyectos o rutinas?
```

## 5. Targeted Follow-Up

Val asks one targeted follow-up based on the domain.

Examples:

- trabajo: "¿Qué tipo de trabajo haces y qué se te complica más: horarios, pendientes, seguimiento, cansancio, pagos o cosas que se olvidan?"
- tiempo/día: "¿Dónde viven tus pendientes ahora: calendario, WhatsApp, notas, papel o en tu cabeza?"
- documentos: "¿Qué quieres ordenar primero: documentos personales, un caso, contratos, recibos o algo administrativo?"

If the user answers "soy cajera", Val avoids irrelevant client-flow assumptions and suggests horarios, pendientes, recordatorios, dinero/pagos, or routine after the shift.

## 6. Too-Broad Answers

If the user says "todo" or "todo me sirve", Val narrows gently:

```text
Total, pero si empezamos con todo nos ahogamos elegante. Escogemos uno primero...
```

## 7. Guardrails

- Spanish-first
- warm, concise, operator-like
- no manipulation
- no coercion
- no fake certainty
- no professional replacement claims
- no medical/legal/financial conclusions
- no saving claims
- no hidden profile writes
- no memory-spine activation
- no calendar/task/reminder creation
- no Karen/private data
- no client-specific copy in reusable logic

## 8. Runtime Placement

`bot.handle_text` checks adaptive intake after the name/language guard and before the existing onboarding discovery route.

This lets uncertainty phrases enter adaptive questioning while preserving the existing menu path for "¿cómo me puedes ayudar?".

## 9. Smoke Coverage

`scripts/quality/intake_adaptive_runtime_smoke.py` verifies:

- trigger phrase asks permission
- confirmation asks the broad domain question
- work domain asks targeted work follow-up
- "soy cajera" gets bounded support areas
- "todo me sirve" narrows to one workflow
- refusal is respected
- existing onboarding route still works
- contextless "trabajo" does not hijack routing
- no saving/action/professional/private-data claims

## 10. Persistence Boundary

MEMORY-SPINE-01B remains disabled and unused by runtime.

No confirmed memory candidate is created. No fixture or production memory is written. This lane is volatile intake only.
