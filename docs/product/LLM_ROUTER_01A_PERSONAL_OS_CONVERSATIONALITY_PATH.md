# LLM Router 01A Personal OS Conversationality Path

## 1. Why This Matters

Val needs to become less canned and less hardcoded without becoming unsafe. A Personal OS should not require the user to know the perfect prompt, the exact command, or the internal workflow name.

The target behavior is simple:

1. Val listens to messy human input.
2. Val asks or classifies carefully.
3. Val recommends one practical workflow.
4. Val asks for confirmation before actions or memory.
5. Deterministic handlers execute anything that changes state.

This is structured reasoning plus LLM interpretation plus guardrails. This is not AGI. This is not autonomous execution.

## 2. What Changes For Users In Stages

### Now: deterministic intake

INTAKE-01B/01C already give users a warmer starting path when they say things like `Val, no se que necesito` or `tengo demasiadas cosas`. Val asks permission, asks one broad question, narrows gently, and recommends one first workflow.

### Next: shadow classifier

The existing `intent_router_v2` shadow mode can learn from more examples without changing the user experience. The sample harness should include adaptive intake phrases and compare proposed labels against actual deterministic handlers.

### Later: response composer

A response composer can make Val sound less rigid while staying side-effect free. It may draft a warmer answer, but deterministic handlers execute. The composer cannot save memory, create reminders, change calendars, or write client data.

### Later: confirmed memory

Once the memory spine is approved for runtime, Val can propose what to remember and ask for explicit confirmation. Memory writes stay deterministic, inspectable, editable, and deletable.

## 3. Example Inputs And Workflow Mapping

| User says | Likely domain | Possible workflow | Why it should not depend on exact phrasing |
| --- | --- | --- | --- |
| `soy cajera en una tienda` | work / shifts | Rutina y Turnos | The role hints at schedules, after-shift routine, and reminders even if the user never says `turno`. |
| `atiendo caja` | work / retail | Organizar mi dia laboral | The system should infer practical work context, then ask what weighs most. |
| `trabajo en retail` | work / operations | Pendientes de trabajo | Retail language should map to work support without needing a hardcoded phrase. |
| `tengo clientes que perseguir` | clients / business | Seguimiento de clientes | The pain is follow-up, not generic chat. Val should recommend a client follow-up workflow and confirm. |
| `tengo papeles regados` | documents / admin | Ordenar documentos/admin | Val should map messy paper language to document/admin support without claiming legal/accounting expertise. |

The point is not to make a giant phrase dictionary. The point is to use shadow classification and response composition to connect natural language with safe deterministic workflows.

## 4. Conversationality Boundary

Better conversationality means:

- fewer brittle menus
- fewer exact trigger phrases
- more useful clarifying questions
- warmer summaries
- clearer workflow recommendations
- explicit confirmation before action

It does not mean:

- autonomous execution
- hidden memory
- fake consciousness
- professional replacement
- silent DB writes
- client data writes
- calendar/task/reminder creation by an LLM

## 5. Product Direction

For Personal OS, the sequence is:

1. Start with one workflow first.
2. Prove that it removes mental load.
3. Expand modularly into adjacent workflows.
4. Let memory help only after consent.
5. Keep user trust ahead of cleverness.

This keeps Val useful for users who do not know what to ask, while preserving the core rule: the LLM can help interpret and compose, but deterministic handlers execute and confirmations control anything consequential.
