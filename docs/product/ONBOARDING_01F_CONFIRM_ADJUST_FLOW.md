# ONBOARDING-01F Confirm / Adjust Flow

Purpose: document the narrow confirmation and adjustment step after Val recommends the first Daily Operator pilot flow.

## Runtime Behavior Added

After Val recommends "Organizar mi día" and asks:

> ¿Te parece que probemos Organizar mi día como primer flujo piloto?

Val keeps a volatile confirmation state. The next user reply can:

- confirm the pilot
- pivot to another flow
- cancel or pause

## Confirmation

Recognized confirmations include: sí, si, dale, correcto, me parece, vamos, ok.

Val responds by confirming "Organizar mi día" as the first pilot flow and asking what the daily review should include:

- agenda
- tareas
- recordatorios
- prioridades
- pendientes sin fecha

Val still says nothing has been saved or configured and no tasks, reminders, or calendar events were created.

## Adjustment / Pivot

Recognized pivots include phrases such as:

- mejor documentos
- mejor clientes
- mejor ideas
- mejor pendientes
- prefiero documentos
- prefiero clientes
- quiero documentos

Val does not fight the user. It acknowledges the pivot and asks the next setup question for that category.

## Cancel / Pause

If the user says no or cancels, Val acknowledges and offers to pick another flow or stop. No data is written.

## Guardrails

- no client data writes
- no persistent profile writes
- no reminders, tasks, calendar events, folders, or documents are created
- no claim that setup is complete
- no broad router refactor
- no unrelated agenda/task/calendar/Caso Finca behavior changes
- no Karen private data, client file names, implementation details, AGI claims, or magic-AI claims

## Scope

This lane adds one volatile confirmation/adjustment step only. It does not implement actual setup persistence or workflow activation.
