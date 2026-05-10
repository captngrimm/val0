# KAREN CASE FACTS RECALL V0 PASS

## Date
2026-05-10

## Branch
karen-client-zero-mvp-2026-05-25

## Status
PASS.

Karen/Frank live validation confirmed that Val can now save and recall basic land-case facts.

## What was validated

Karen re-ingested clean case facts:

- Finca: 10082
- Tomo/Rollo: 316
- Folio: 308
- Propietario original: Eufemio Montenegro
- Tipo de proceso: Sucesión intestada
- Fecha de fallecimiento: 30 de junio de 1995
- Escritura Pública: No. 920
- Fecha de escritura: 16 de agosto de 2002
- Notaría: Notaría Sexta del Circuito de Panamá (La Chorrera)

Herederos declarados:
- Carmen Montenegro de Sandino
- Javier Morán Montenegro Ortega
- Odilia Montenegro de Estribí
- Teonila Antonia Montenegro de Cruz
- Martina Montenegro de Martínez

## Validated user questions

Karen asked:

¿Cuál es el número de finca?

Val answered:
- Finca: 10082
- Tomo/Rollo: 316
- Folio: 308

Karen asked:

¿Quiénes son los herederos?

Val answered with the five heirs correctly.

Karen asked:

¿Qué datos básicos tienes del caso?

Val returned the saved case facts and heirs.

## Reminder / task validation

Karen/Frank also created a real case follow-up:

"Val, recuérdame llamar al Juzgado Primero de La Chorrera el miércoles para confirmar si salió el oficio"

Val confirmed:
"Listo. Guardé la tarea..."

## Bugs found and fixed during this validation

### 1. Time hijack

Bad behavior:
Karen asked:
"Ahora Val con la información compartida ya me puedes decir el número de finca relacionada al caso?"

Val replied:
"Son las 12:16 PM."

Cause:
The time override matched "hora" inside "ahora".

Fix:
Time override now only fires on explicit time questions like:
- qué hora es
- dime la hora
- hora actual

### 2. Case facts paste treated as query

Bad behavior:
Karen pasted facts containing "Finca: 10082", but Val treated the message as a query and replied that no facts were stored.

Fix:
maybe_handle_karen_case_facts now checks whether incoming text contains strong case facts and saves them before attempting to answer queries.

### 3. Basic facts query routing

Added/expanded routing for:
- número de finca
- datos de la finca
- datos básicos del caso
- herederos
- tomo
- folio

## User-facing trust result

This pass increased Karen's trust because Val demonstrated:
- it can store core case facts
- it can recall finca/tomo/folio
- it can list heirs
- it can save a real follow-up task

## Remaining issues

- Escritura Pública No. 920 did not show in one output despite being in the pasted facts. Investigate later; not blocking the trust pass.
- Reminder display/notification behavior still needs future validation when due.
- Need test tomorrow/day-after to confirm persistence across time.
- "Última captura Exocortex" must remain hidden/rebranded from user-facing flows.

## Next recommended work

1. Commit this checkpoint.
2. Update session handoff.
3. Do not continue testing Karen tonight.
4. Next build target:
   - hide/rebrand Exocortex user-facing wording
   - then Mixed Inventory/Custody Detection v0
   - then persistence re-test tomorrow/day-after
