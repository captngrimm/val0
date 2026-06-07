# MEMORY-SPINE-01A Intake Memory / Library Layer Design

Purpose: design how confirmed onboarding and intake answers can become durable, inspectable user memory later without adding runtime behavior now.

This is product/design only. It does not add persistence, profile writes, reminders, tasks, calendar events, routing changes, database migrations, or production configuration.

## 1. Purpose

MEMORY-SPINE-01A turns confirmed intake/onboarding answers into a future durable memory path.

The goal is to:

- preserve useful operational preferences after guided intake
- prevent memory chaos by separating candidates, confirmed records, indexes, and archives
- preserve consent and trust before any profile-like storage
- support future Personal OS behavior where Val can remember workflow setup safely
- keep reusable memory logic client-isolated and free of client-specific names

This lane designs the spine only. Runtime will later decide where records live, how they are indexed, and how delete/update memory commands work.

## 2. Memory Layers

Frank's memory model maps intake context into four layers:

### Desk / Hot Session Memory

Desk / hot memory is the active conversation state currently on the table.

Examples:

- current intake answer
- pending yes/no confirmation
- current workflow recommendation
- "Val, do not save that" instruction in the same thread
- active assumptions that still need correction

Desk memory is volatile. It helps Val finish the current conversation, but it is not durable memory by itself.

### Side Table / Warm Active Workflow Memory

Side Table / warm memory is recent confirmed workflow setup and active preferences that are likely useful across nearby turns.

Examples:

- selected first workflow for the pilot
- daily review contents the user confirmed
- source places such as WhatsApp, notes, calendar, paper, or email
- active privacy boundaries for the current workflow
- recent correction patterns that should affect this setup

Warm memory should still be inspectable and scoped. It is not a place for secret profiling.

### Library Index / Librarian / Catalog

Library Index / librarian is the catalog that knows what memories and workflows exist and where to retrieve them.

The librarian should answer:

- which confirmed memory exists for this user/client
- what workflow it belongs to
- how sensitive it is
- whether it is active, stale, archived, or deleted
- which source or confirmation created it
- which retrieval tags can safely load it

The index does not need every detail. It points Val to the right shelf without dumping the whole library onto the desk.

### Vault / Cold Storage

Vault / cold storage is the deeper archive for records, docs, logs, summaries, and full history.

Vault records are not loaded by default. Val retrieves them only through the Library Index and only when the user task, client scope, consent status, sensitivity, and freshness make retrieval appropriate.

## 3. What Gets Stored Vs Not Stored

Future runtime may store only confirmed operational preferences and workflow facts.

Examples of storeable confirmed memory:

- preferred name and preferred language
- selected first workflow
- workflow sources such as WhatsApp, notes, calendar, paper, email, or documents
- desired daily review contents
- user communication style preference
- "what Val should never do"
- privacy boundaries
- actions Val may draft but not send
- actions Val must never take without confirmation
- professional boundaries for legal, medical, accounting, tax, or financial matters

Do not silently store:

- sensitive personal disclosures
- medical, legal, financial, tax, or accounting conclusions
- unconfirmed guesses
- raw emotional disclosures
- private third-party data
- anything the user declined to save
- hidden scores, personality judgments, or manipulation labels
- facts copied from one client/user scope into another

If a useful fact is sensitive, Val can summarize it as a memory candidate and ask whether the user wants to save a safer operational version.

## 4. Consent Model

Val asks before saving.

Before creating confirmed memory, Val should:

- summarize what she heard
- explain exactly what will be saved
- say why it would help the workflow
- let the user say yes, no, or edit
- accept "do not save this" without friction

User rights:

- the user can ask what Val remembers
- the user can delete/change memories
- the user can ask Val to stop using a memory
- the user can decline saving without losing help in the current conversation

Trust rules:

- consent before saving
- consent before personalization
- no hidden profiling
- no hidden profile writes
- no manipulation
- no dark patterns
- no pressure to save more than needed

## 5. Intake-To-Memory Flow

The future intake-to-memory flow:

1. Val asks permission to ask a few intake questions.
2. Val asks one question at a time.
3. Val extracts current facts, assumptions, friction, sources, privacy sensitivity, and confidence.
4. Val summarizes what she heard.
5. Val recommends one first workflow.
6. Val states assumptions and asks for correction.
7. Val proposes a memory record.
8. The user confirms, declines, or edits.
9. Record is saved later by runtime only after confirmation.
10. Library Index is updated later by runtime only after the save succeeds.

Proposed wording:

```text
Lo que guardaria, si me confirmas, es esto: prefieres empezar con Organizar mi dia; tus pendientes viven en WhatsApp y notas; quieres una revision diaria con agenda, tareas y pendientes sin fecha; y Val nunca debe crear eventos ni enviar mensajes sin preguntarte. Lo puedo guardar asi, editarlo o no guardarlo.
```

During this lane, the flow remains design-only.

## 6. Retrieval Model

Val should use memory only when it clearly helps the current task.

Use memory when:

- the user asks "what do you remember?"
- the user asks about a configured workflow
- the current request depends on a confirmed preference
- a safety boundary affects the response
- recent confirmed setup changes the next best question

Avoid overusing memory when:

- the memory is stale
- the task is unrelated
- the user is sharing something new and does not ask for setup
- retrieval would feel like surveillance
- the memory has low confidence or unclear source

Natural mention pattern:

```text
Segun lo que me confirmaste para tu flujo diario, quieres revisar agenda, tareas importantes y pendientes sin fecha. Si eso cambio, lo ajusto.
```

If unsure, Val asks:

```text
Tengo una memoria de preferencia sobre este flujo, pero puede estar vieja. Quieres que la use o prefieres actualizarla?
```

Retrieval should prefer confirmed memory over guesses, recent active memory over stale memory, and source-grounded records over generated summaries.

## 7. Privacy And Trust Guardrails

Val must not:

- manipulate the user into saving memory
- coerce consent
- create secret scoring
- diagnose
- act as a professional replacement
- make medical, legal, financial, tax, or accounting conclusions
- save without permission
- store raw secrets as reusable preferences
- turn emotional disclosures into durable labels
- leak one client/user's memory into another client/user scope
- place client-specific names in reusable memory logic

Client isolation first:

- no cross-client contamination
- every future memory object must be scoped by client_id/user_id before retrieval
- reusable logic must not hardcode client IDs, nicknames, emails, chat IDs, paths, or client-specific copy
- index lookup must filter by client/user scope before semantic or keyword retrieval
- unknown users must not inherit another user's workflow profile

## 8. Memory Lifecycle

Memory moves through explicit states:

- candidate: extracted from intake, not yet proposed or confirmed
- proposed: shown to the user as something Val could save
- confirmed: user approved the record
- active: record is available for retrieval in relevant workflows
- stale: record may be outdated and needs review before strong use
- archived: retained as history but not active retrieval context
- deleted: removed from active use and no longer retrievable except for narrow audit requirements if policy allows

No runtime should treat candidate or proposed memory as confirmed memory.

## 9. Conflict And Correction Handling

User correction overrides memory.

When corrected, Val should:

- accept the correction plainly
- state what changed
- update the current Desk / hot memory immediately
- propose whether the durable memory should be updated
- archive or update the old memory after confirmation
- optionally create a correction log candidate later

Example:

```text
Got it. I had your daily review set to agenda and tasks. You are changing it to agenda, tasks, and reminders. I can update that memory, or just use it for this chat.
```

Conflicts should not be smoothed away. If two confirmed records disagree, Val should surface the conflict and ask which one is current.

## 10. Examples

### Daily Operator Onboarding Memory

User confirms:

```text
Quiero empezar con Organizar mi dia. Mis pendientes viven en WhatsApp y notas. La revision diaria debe incluir agenda, tareas importantes y pendientes sin fecha.
```

Proposed memory:

```text
Val may save a Daily Operator workflow profile with selected workflow, source locations, daily review contents, and the boundary that no reminders or calendar events are created without confirmation.
```

### Documents / Admin Memory

User confirms:

```text
Quiero que me ayudes a ordenar documentos. Puedes recordar que primero quiero listar, resumir y preparar preguntas, pero no sacar conclusiones legales.
```

Proposed memory:

```text
Val may save a documents/admin workflow preference: inventory first, summaries second, questions for professional review, no legal conclusions.
```

### Client Follow-Up Memory

User confirms:

```text
Mi problema es dar seguimiento a clientes. Lo que se pierde es proximo paso, fecha y contexto. Val no debe enviar mensajes sin que yo confirme.
```

Proposed memory:

```text
Val may save a client follow-up workflow profile with sources, next-action focus, and send-with-confirmation boundary.
```

### "Do Not Save This" Example

User:

```text
Te cuento esto para desahogarme, pero no lo guardes.
```

Val:

```text
Entendido. Lo uso solo para responderte ahora y no lo propongo como memoria.
```

### User Asks What Val Remembers

User:

```text
Que recuerdas sobre mi workflow?
```

Val:

```text
Tengo confirmado que tu primer flujo es Organizar mi dia, que tus pendientes suelen vivir en WhatsApp y notas, y que tu revision diaria debe incluir agenda, tareas importantes y pendientes sin fecha. Tambien tengo una frontera: no crear eventos, recordatorios ni enviar mensajes sin confirmarte. Quieres cambiar algo?
```

## 11. Future Runtime Mapping

No implementation yet.

Likely future components:

- memory_candidate
- confirmed_profile_memory
- workflow_profile
- memory_index
- retrieval helper
- delete/update memory command
- audit log

Runtime principles:

- create memory_candidate from Desk / hot memory
- promote only confirmed memory into active records
- write workflow_profile only after explicit consent
- update memory_index only after the underlying record exists
- keep Vault / cold storage separate from default prompt context
- make memories inspectable, editable, deletable, and scoped
- keep protected client data and reusable memory logic separate
