# KAREN VOICE EVENT CAPTURE V0 PASS

## Date
2026-05-10

## Branch
karen-client-zero-mvp-2026-05-25

## Status
PASS.

## Context

Karen/Frank tested voice-note input for Karen LandOps after earlier voice attempts fell into wrong routes.

Previous bad behavior:
- "No encuentro ese caso en tu base de datos."
- "No me encargo de recordatorios ni avisos automáticos."

## Fix

Added direct Karen voice routing before legacy/generic voice handling.

Voice transcription now routes explicit Karen commands such as:
- registra este evento
- resumen de últimos eventos
- inventario de documentos

before generic legal/case handlers.

## Validated voice input

Voice transcription captured:

Val, registra este evento del caso del terreno. El lunes 11 tengo que llevar la documentación impresa al despacho de la abogada Nora Santa. Ya le mandé los pdf pero dijo que necesita todo impreso para estudiar y analizar el caso. Después de revisar ella nos dirá cómo proceder.

## Validated result

Val responded:
- Guardé este evento del caso.

Then text query:
- Dame un resumen de los últimos eventos compartidos

Val returned the new voice-captured event in the recent case summary.

## Result

PASS.

Voice/STT is now usable for basic Karen event capture.

## Remaining polish

- Clean voice command prefixes from stored event text.
- Later support update/reschedule language for appointments.
- Continue treating important legal reminders as beta until due-time notification behavior is validated.
