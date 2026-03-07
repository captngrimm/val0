# Sprint12 — Linked Timeline Entities via parent_ref

Updated: 2026-03-07

## Goal

Use `parent_ref` to link reminders and future tasks to a higher-level entity
such as:

- CASE:524242024
- PROJECT:PX01
- CLIENT:MIGUEL

This allows Val to answer contextual questions like:

- qué tengo del caso 524242024
- muéstrame todo lo de Miguel
- qué sigue para PX01

without creating new tables yet.

---

## Current State

Val can already:

- read reminders from the unified timeline base
- read legal events from `case_events`
- answer:
  - qué tengo hoy
  - qué tengo mañana
  - qué vence hoy
  - qué vence esta semana

But reminders/tasks are still mostly isolated rows.

---

## Objective

Add a deterministic query path for `parent_ref`-linked timeline items.

This sprint does NOT add:

- new tables
- task runner
- full task CRUD
- generic entity registry

It only adds linked reads.

---

## Scope

1. keep `reminders` as temporary unified timeline base
2. use `parent_ref` as lightweight entity linkage
3. add deterministic query:

   - qué tengo del caso 524242024

4. return linked reminders/tasks for that parent_ref

---

## Query Model

Examples of supported parent references:

- CASE:524242024
- PROJECT:PX01
- CLIENT:MIGUEL

Initial implementation focuses on:

- CASE:<id>

---

## Definition of Done

Val can answer:

- qué tengo del caso 524242024

by reading linked rows from `reminders` where:

- `parent_ref = CASE:524242024`

No LLM required.

---

## Follow-On

Later this can expand to:

- project-linked tasks
- client-linked reminders
- mixed timeline + notes views
- cross-entity summaries

END OF SPRINT 12

