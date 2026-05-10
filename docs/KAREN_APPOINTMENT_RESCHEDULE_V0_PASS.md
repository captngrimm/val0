# KAREN APPOINTMENT / RESCHEDULE V0 PASS

## Date
2026-05-10

## Branch
karen-client-zero-mvp-2026-05-25

## Status
PASS.

## Context

Karen asked whether Val could handle appointment changes naturally, such as changing a meeting with the attorney from one day/time to another.

## Validated inputs

User:

Val, tengo cita con la abogada Nora Santa el lunes 11 a las 10 AM para revisar el caso del terreno.

Val saved the appointment/agenda item inside the land case.

User:

Val, cambiaron la cita con Nora. Ya no es lunes 11, ahora queda para martes 12 a las 9 AM.

Val saved the appointment/reschedule change inside the land case.

User:

Dame un resumen de los últimos eventos compartidos

Val included both:
- Cita / agenda: Nora Santa, lunes 11, 10 AM
- Cambio de cita / agenda: changed from lunes 11 to martes 12 at 9 AM

## Result

PASS.

## What this supports

Karen can now naturally say:
- Tengo cita con la abogada...
- Cambiaron la cita...
- Ya no es lunes, ahora es martes...
- Queda para tal día/hora...

Val records those as case agenda/follow-up notes and includes them in recent activity summaries.

## Boundary

This is not yet full calendar editing.

Current behavior:
- saves appointment/case agenda information
- saves reschedule/change as a case event/note
- shows it in recent case summary

Future behavior:
- update/replace prior appointment more cleanly
- create or update real reminders
- optionally integrate with calendar after account/permission validation

## User trust impact

High.

This answers Karen's practical concern about whether Val can track changing attorney appointments.
