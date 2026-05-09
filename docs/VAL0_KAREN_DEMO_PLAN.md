# VAL0 KAREN DEMO PLAN

## Tester

Karen

## Goal

Run the first controlled friend/family showcase with a real person.

The goal is not to impress with fake polish.
The goal is to see whether Karen understands the concept and can imagine using Val in her real life.

## Demo principle

Do not force slash commands if avoidable.

User-facing natural phrases should be used:

- ¿Qué hago ahora?
- Enséñame el resumen de lo que guardaste.
- Hazme el mensaje.

Slash commands remain backup/operator controls.

## Before demo

Tell Karen:

Esto es una beta cruda. No es una app terminada ni magia.

La idea es simple:
tú le cuentas a Val cosas de tu vida, trabajo o pendientes en lenguaje normal, y ella empieza a ordenarlo en memoria, seguimientos, ideas y próximos pasos.

No metas nada demasiado privado todavía.

## First question

Ask Karen:

¿Quieres probarlo más para vida personal, trabajo/negocio, o una mezcla?

## Demo path

### 1. Onboarding

Use:

/onboard

Let Karen answer naturally.

Goal:
Create her operating profile.

### 2. Show profile

Use:

/onboardstatus

Explain:
Val is building a basic operating profile so she does not treat every user like the same generic person.

### 3. Natural messy input

Ask Karen to say something real but not too private.

Example prompts:

- Cuéntale a Val algo que tienes pendiente.
- Cuéntale algo que se te está enredando.
- Cuéntale algo de esta semana que necesitas ordenar.
- Cuéntale un seguimiento, cita, idea o pendiente.

### 4. Show what Val saved

Ask naturally:

Enséñame el resumen de lo que guardaste.

Expected:
Val shows structured memory.

### 5. Ask what next

Ask naturally:

¿Qué hago ahora?

Expected:
Val uses recent memory + operating profile to suggest one next step.

### 6. Draft if relevant

If there is a message/follow-up:

Hazme el mensaje.

Expected:
Val drafts a practical message.

### 7. Capture feature request if needed

If Karen says “ojalá pudiera hacer X”:

Use:

/flowrequest <idea>

Explain:
Val should not fake features. If something is not built, we capture it as roadmap/workflow request.

## Feedback questions

Ask Karen:

1. ¿Entendiste qué es?
2. ¿Qué parte sí usarías?
3. ¿Qué parte se sintió rara o falsa?
4. ¿Qué le dirías mañana en una situación real?
5. ¿Esto te ayudaría más para vida, trabajo, negocio o mezcla?
6. ¿Qué tendría que hacer para valer $30 al mes?
7. ¿Qué te haría dejar de usarlo?

## Pass criteria

PASS if Karen says:
- entiendo la idea
- esto podría ayudarme
- usaría esto para X
- está crudo pero se ve útil

FAIL if Karen says:
- no sé qué hacer con esto
- se siente como ChatGPT con pasos extra
- no entiendo la memoria
- no confiaría en meterle cosas

## Important boundaries

Do not claim:
- memory perfect
- full privacy
- web browsing active
- autonomous sending
- finished app
- full personal operating system

Say:
- beta cruda
- memoria útil pero no perfecta
- no metas nada demasiado sensible todavía
- Val puede ordenar, recordar estructura, recomendar próximos pasos y redactar mensajes
