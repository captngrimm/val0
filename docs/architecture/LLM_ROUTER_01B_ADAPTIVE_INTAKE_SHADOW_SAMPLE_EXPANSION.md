# LLM Router 01B Adaptive Intake Shadow Sample Expansion

## Purpose

Expand the existing Intent Router v2 shadow/sample diagnostics with adaptive intake phrases from INTAKE-01B and INTAKE-01C. This prepares measurement for future LLM-assisted classification without creating a new router and without changing live routing behavior.

This lane does not edit `bot.py`, does not route messages through Intent Router v2, does not enable shadow mode, does not write DB rows, does not write memory, does not touch client files, and does not create calendar events, reminders, or tasks.

## What Changed

The existing sample harness now includes adaptive intake examples for:

- initial uncertainty / help-start phrases
- broad domain phrases
- work-role follow-up phrases
- recommendation-area replies
- short orphan phrases that must remain fallback without adaptive state
- pending adaptive-state phrases that can receive diagnostic adaptive labels

## Diagnostic Labels

Added diagnostic-only labels in `core/intent_router_v2.py`:

- `adaptive_intake_start`
- `adaptive_intake_domain`
- `adaptive_intake_followup`
- `adaptive_intake_recommendation`

These labels are for shadow/sample measurement only. Deterministic runtime handlers still execute adaptive intake.

## Sample Coverage

Representative phrases include:

- `Val, no se que necesito`
- `Val, ayudame a empezar`
- `Val, estoy perdida`
- `Val, tengo demasiadas cosas`
- `Val, no se por donde empezar`
- `todo me sirve`
- `trabajo`
- `soy cajera`
- `soy cajera en una tienda de departamento`
- `atiendo caja en una tienda`
- `trabajo en retail`
- `horarios`
- `pendientes`
- `recordatorios`
- `dinero y pagos`
- `cansancio despues del turno`
- `tengo clientes que perseguir`
- `tengo papeles regados`
- `ideas para un libro`
- `quiero organizar mi dia`

## Safety Boundary

Short orphan replies such as `trabajo`, `horarios`, `pendientes`, and `recordatorios` remain `llm_fallback` unless a matching adaptive intake pending state is supplied to the shadow classifier.

This preserves the doctrine from LLM-ROUTER-01A:

- pending confirmations beat new intent
- deterministic high-trust routes beat LLM
- LLM fallback last
- deterministic handlers execute
- LLM/router cannot execute tools, write memory, create/delete calendar events, create reminders, mutate client files, or write DB rows

## Gap Discovered

Intent Router v2 did not previously distinguish adaptive pending states from action-confirmation pending states. Before this lane, any `pending_state` became `pending_action_reply`.

This lane adds diagnostic adaptive pending-state mapping inside the shadow classifier only. It does not change runtime state handling.

## Next Step

Use these samples in a future observation/actual-label lane:

- add or verify actual handler labels for `maybe_handle_adaptive_intake`
- compare predicted adaptive labels to actual deterministic handlers
- keep feature flag default OFF
- keep shadow/sample diagnostics separate from runtime routing
