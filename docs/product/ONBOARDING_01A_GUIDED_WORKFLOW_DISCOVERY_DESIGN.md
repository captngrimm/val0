# ONBOARDING-01A Guided Workflow Discovery Design

Purpose: define how Val should answer new-user discovery prompts like "Val, ¿cómo me puedes ayudar?" as a practical operator, not a salesperson.

This is product behavior design only. It does not change runtime behavior.

## 1. Purpose

Guided workflow discovery helps a new user choose the first useful Val workflow.

Val should:

- make the possibilities concrete
- avoid feature dumping
- ask enough to choose a starting point
- keep founder beta boundaries clear
- recommend one first workflow

## 2. Problem Statement

New users often do not know what to ask.

They say:

- "Val, ¿cómo me puedes ayudar?"
- "Val, ¿qué puedes hacer?"
- "Val, ayúdame a escoger por dónde empezar."
- "No sé qué necesito, ¿qué me recomiendas?"

The wrong answer is a giant feature menu. Users need examples tied to pain, not a catalog.

Val must avoid feature dumping and instead guide the user toward a first workflow that can be tested safely.

Rule:

> No feature dumping. Give concrete examples, then ask which workflow hurts most.

## 3. Design Principle

Core principles:

- one workflow first
- pain before features
- examples before theory
- ask enough questions to choose, not interrogate forever
- founder beta honesty
- user controls what gets saved

Default pattern:

> "I can help in several ways, but the useful path is choosing one workflow first. Which one hurts most this week?"

## 4. Trigger Phrases

Spanish trigger phrases:

- "cómo me puedes ayudar"
- "qué puedes hacer"
- "ayúdame a empezar"
- "ayúdame a escoger por dónde empezar"
- "no sé qué necesito"
- "qué me recomiendas"
- "por dónde empiezo"

English equivalents:

- "how can you help me"
- "what can you do"
- "help me choose where to start"
- "I do not know what I need"

## 5. Discovery Workflow Categories

### Agenda / Tasks / Reminders

For users losing track of time, commitments, or follow-ups.

Examples:

- daily agenda
- active task list
- reminders
- calendar drafts with confirmation

### Documents / Case / Admin

For users with scattered documents, case/admin clutter, or review prep.

Examples:

- document list
- conservative summaries
- questions for lawyer/advisor
- missing-info checklist

### Clients / Business Follow-Up

For users losing leads, client promises, meetings, or next actions.

Examples:

- follow-up list
- client status notes
- meeting prep
- next-action reminders

### Ideas / Folders

For users collecting ideas, projects, book notes, or personal reference material.

Examples:

- idea capture
- lightweight folders
- "what did I save?"
- duplicate-safe note capture

### Routines / Habits

For recurring personal/admin rhythms.

Examples:

- weekly review
- end-of-day reset
- monthly admin checklist
- household/family routine

### Other / Custom

For workflows that do not fit the first categories.

Val should still ask for one concrete repeated pain before proposing custom work.

## 6. Response Pattern

Response shape:

1. Short explanation.
2. Concrete examples.
3. One-workflow-first warning.
4. Ask: "Which one hurts most this week?"

Example:

> Puedo ayudarte con agenda/tareas, documentos/admin, seguimiento de clientes, ideas/carpetas o rutinas. Pero no quiero tirarte un menú gigante: lo útil es escoger un workflow primero. ¿Cuál te duele más esta semana?

## 7. Risk And Boundary Language

Val should say:

- founder beta, not finished public SaaS
- no legal/medical/accounting replacement
- no full autonomy
- human-in-the-loop for sensitive actions
- user controls what gets saved
- sensitive writes/actions require confirmation

Short version:

> Val organiza y prepara; no reemplaza profesionales ni decide por ti. Empezamos con un flujo y límites claros.

## 8. How To Pick The First Workflow

Score quickly:

- pain: does it actually bother the user?
- frequency: does it repeat?
- available data: are there messages, docs, tasks, or examples?
- privacy risk: can it be tested safely?
- ease of setup: can current Val support a first version?
- willingness to keep using it: will the user try it for a week?

Best first workflow:

> high pain, repeated often, enough data, manageable privacy risk, easy first setup, and a user willing to test.

## 9. Output After Discovery

After discovery, Val should produce:

### Recommended First Workflow

Name one workflow, not three.

Example:

> Recomendación: empecemos con agenda/tareas/reminders porque lo mencionaste como algo diario y fácil de probar.

### What Val Would Do In Week 1

Examples:

- capture reminders
- show active tasks
- summarize documents
- list client follow-ups
- save ideas in folders
- run a weekly routine

### What Frank / Operator Needs To Configure

Examples:

- preferred name
- language/tone
- first workflow category
- allowed data
- forbidden data
- reminders/folders/routines
- success criterion

### Next User Action

Ask one concrete next action:

> Mándame 3 ejemplos reales de lo que quieres que Val te ayude a organizar.

or:

> Escoge una: agenda/tareas, documentos, clientes/seguimiento, ideas/carpetas, rutinas.

## 10. How This Later Maps To Runtime

Future runtime mapping:

- intent detector catches discovery trigger phrases
- response renderer gives concise category examples
- repair layer handles vague "todo me serviría"
- risk layer applies boundary language
- onboarding state stores only explicit user-approved setup facts
- operator review confirms first workflow before durable client configuration

Runtime must not:

- hard-sell
- feature dump
- enable every workflow by default
- store sensitive data without user consent
- imply professional replacement
