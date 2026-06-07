# ONBOARDING-01C Discovery Follow-up State

Purpose: document the narrow follow-up state for guided discovery after Val asks the user which first flow to choose.

## Runtime Behavior Added

After Val answers a discovery prompt with:

> Para empezar bien, escogemos un solo flujo primero. ¿Por dónde empezamos: organizar tu día, pendientes, documentos, clientes, ideas o algo diferente?

Val stores a volatile chat-state marker for the next answer only. If the user chooses a category, Val continues with one practical setup question:

- organizar mi día / agenda: asks where the user's pending items live now.
- pendientes / recordatorios: asks what kinds of things get lost most.
- documentos / casos / papeles: asks what document area to order first.
- clientes / seguimiento: asks who or what needs follow-up.
- ideas / carpetas: asks what the user wants to save without losing.
- otro / diferente: asks for one sentence describing what to organize.

## Guardrails

- no client data writes
- no reminders, tasks, calendar events, folders, or documents are created
- no claim that setup is complete
- no broad router refactor
- short category words such as "agenda" are only treated as onboarding choices while discovery context is active
- obvious direct setup phrases such as "quiero ordenar documentos" may be handled safely without active context
- no Karen private data, client file names, smoke details, or implementation details in user-facing replies

## Copy Pattern

Each follow-up reply stays Spanish-first, warm, and operational:

- starts with "Perfecto"
- names the selected first flow
- asks one next setup question
- reminds the user that founder beta setup is one flow first
- states that nothing is saved and no actions are created yet

## Scope

This lane adds volatile follow-up state only. It does not persist onboarding choices, create a client profile, mutate live data, or expand unrelated agenda/task/calendar/Caso Finca behavior.
