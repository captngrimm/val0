# INTAKE-01C Volatile Intake Recommendation

Purpose: add a volatile recommendation step after adaptive intake collects the user's first practical pain point.

This lane does not add persistence, DB writes, profile writes, production memory writes, calendar/task/reminder creation, client data writes, or memory-spine runtime activation.

## 1. Behavior

After INTAKE-01B reaches the work/cashier narrowing question:

```text
Para tu caso podríamos empezar con horarios, pendientes, recordatorios, dinero/pagos o rutina después del turno. ¿Qué parte te pesa más?
```

Val now recognizes answers like:

- horarios
- pendientes
- recordatorios
- dinero / pagos
- rutina después del turno
- cansancio
- cosas que se me olvidan
- todo / todo eso

Then Val gives:

- concise summary of what she understood
- one first workflow recommendation
- why that workflow fits
- one-week test idea
- no saving/no action boundary
- confirmation question for first pilot

## 2. Recommendations

Examples:

- horarios -> Rutina y Turnos
- pendientes -> Organizar mi día laboral
- recordatorios -> Recordatorios básicos
- dinero/pagos -> Pagos y fechas importantes, with no financial-advice boundary
- cansancio -> Cierre de turno, practical and non-clinical
- todo -> gently narrow to one workflow first

## 3. State Model

State remains volatile in `context.chat_data`.

Added state:

- adaptive_intake_recommendation

No state is persisted outside the current conversation/session.

## 4. Guardrails

- no saving claims
- no memory candidate creation
- no memory persistence
- no calendar/task/reminder creation
- no fake certainty
- no manipulation
- no coercion
- no medical/legal/financial professional replacement
- no Karen/private data
- no client-specific reusable copy

## 5. Persistence Boundary

MEMORY-SPINE-01B remains disabled and unused by runtime.

The recommendation is volatile only. It does not call `core/memory_spine.py`.

## 6. Smoke Coverage

`scripts/quality/intake_adaptive_recommendation_smoke.py` verifies:

- horarios recommendation
- pendientes recommendation
- recordatorios recommendation
- dinero/pagos recommendation with financial boundary
- cansancio recommendation with non-clinical boundary
- todo narrowing
- no saving/action/private/professional/fake-consciousness claims
- protected live data not staged
