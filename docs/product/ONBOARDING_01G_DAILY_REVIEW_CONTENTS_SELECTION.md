# ONBOARDING-01G Daily Review Contents Selection

Purpose: document the volatile onboarding step where the user chooses what the Daily Operator review should include.

## Runtime Behavior Added

After the user confirms "Organizar mi día" as the first pilot flow, Val asks what the daily review should include. ONBOARDING-01G handles the next answer when the user chooses:

- agenda
- tareas
- recordatorios
- prioridades
- pendientes sin fecha
- todo / todos / todo eso
- más simple / simple

## Response Shape

Val summarizes the selected contents and explains what the first daily review would look like:

- show what is on the user's plate each morning
- surface what cannot be forgotten
- help decide what goes first

For "más simple", Val recommends a smaller pilot:

- agenda
- tareas importantes
- pendientes sin fecha

## Guardrails

- no client data writes
- no persistent profile or setup writes
- no tasks, reminders, or calendar events are created
- no claim that setup is complete
- no broad router refactor
- no unrelated agenda/task/calendar/Caso Finca behavior changes
- no Karen private data, client file names, implementation details, AGI claims, or magic-AI claims

## Scope

This lane still only defines the flow. It does not schedule a review time, save preferences, or activate a Daily Operator pilot.
