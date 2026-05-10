# KAREN CASE FACTS SUMMARY V0 PASS

## Date
2026-05-10

## Branch
karen-client-zero-mvp-2026-05-25

## Status
PASS.

Karen/user-facing saved-summary behavior now shows useful land-case facts instead of generic internal Exocortex memory.

## Problem

Karen asked:

"Enséñame qué guardaste."

Bad earlier behavior:
Val showed:
- "Última captura Exocortex"
- generic note: "Usuario planea compartir información para que Val la guarde."

This was confusing and user-facing internal jargon.

## Fixes

1. Rebranded user-facing summary header:
- From: "Última captura Exocortex"
- To: "Esto guardé"

2. Added Karen context-aware summary behavior:
If the chat has Karen land-case facts, saved-summary intent now returns:
- Finca
- Tomo/Rollo
- Folio
- Propietario original
- Tipo de proceso
- Fecha de fallecimiento
- Fecha de escritura
- Notaría
- Herederos declarados
- Next consultative step

3. Patched both:
- fallback natural phrase route
- LLM router exosummary route

## Validated output

Karen asked:

"Enséñame qué guardaste."

Val returned:
- Finca: 10082
- Tomo/Rollo: 316
- Folio: 308
- Propietario original: Eufemio Montenegro
- Tipo de proceso: Sucesión intestada
- Fecha de fallecimiento: 30 de junio de 1995
- Fecha de escritura: 16 de agosto de 2002
- Notaría: Notaría Sexta del Circuito de Panamá (La Chorrera)
- five declared heirs

## Result

PASS.

This improves Karen trust because "what did you save?" now shows the useful case memory, not internal/debug memory.
