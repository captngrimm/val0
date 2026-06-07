# ONBOARDING-01H Demo Polish + Stale Context Bleed Fix

Purpose: document the narrow demo polish and onboarding context-bleed guard after ONBOARDING-01G rehearsal.

This is a runtime polish note only. It does not add persistence, profile writes, reminders, tasks, calendar events, database migrations, production config, or client data edits.

## Problem

The fake-Ale rehearsal exposed three trust killers:

- opening copy made Telegram sound like the whole product surface
- recommendation copy sounded stiff with "eso me dice algo importante"
- after "todo eso", onboarding must not fall through into unrelated Caso Finca, Nora, legal, or document context

## Behavior

Opening copy now frames Telegram as the current surface:

```text
Por ahora puedo ayudarte como operadora personal desde Telegram...
```

Daily Operator recommendation copy now uses a more natural scattered-source phrase:

```text
Perfecto, entonces tus pendientes estan regados entre WhatsApp, notas y tu cabeza.
```

The onboarding daily review selection remains a hard consume when active. A full sequence ending in "todo eso" should produce the daily review proposal only, with no unrelated legal/document response.

## Guardrails

- no client data writes
- no persistent profile writes
- no tasks, reminders, or calendar events created
- no broad router refactor
- no unrelated Caso Finca behavior changes
- no client-specific names in reusable onboarding copy
- protected live data stays unstaged

## Smoke Coverage

`scripts/quality/onboarding_context_bleed_smoke.py` covers:

- "Val, como me puedes ayudar?"
- "Organizar mi dia"
- "WhatsApp, notas y cabeza"
- "Si"
- "todo eso"

It asserts one reply per turn, daily review proposal on the final turn, and no Nora/Caso Finca/legal/document wording in the onboarding sequence.
