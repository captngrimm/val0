# Val0 Guided Demo Script

## Purpose

This is a short guided demo to show what Val0 can do today without overpromising.

Val0 is a Telegram-based personal assistant with memory, notes, reminders, tasks, pending dashboards, and basic continuity.

This is not a stress test. It is a controlled demo.

## Demo Promise

Val0 helps users:

- save notes
- create reminders
- track tasks
- recover what is pending
- remember basic personal context
- report bugs, feedback, and ideas

Do not present Val0 as:

- AGI
- perfect memory
- full business OS
- full calendar/email automation
- legal/professional guarantee
- autonomous life manager

## Demo Setup

Use a clean or controlled account when possible.

Known accounts:

- Karen = known-good proof account. Do not reset unless intentionally testing fresh onboarding.
- Frank = cleaned dirty/dev regression account.

Before demo, send: `/status`

Expected:

- system active
- memory ok
- no unexpected open tasks

## Demo Flow

1. Send: `/start`
   Expected: Valeria introduces herself clearly.

2. Send: `Ayuda`
   Expected: founder-beta friendly help menu.

3. Send: `Me llamo [Nombre]`
   Then send: `¿Qué recuerdas de mí?`
   Expected: memory dashboard includes the saved name.

4. Send: `Guarda esta nota: llamar a mamá sobre la cena del viernes`
   Then send: `/notes`
   Expected: note appears at the top, preserving accents and casing.

5. Send: `Recuérdame llamar a mamá mañana a las 9`
   Then send: `/reminders`
   Expected: reminder appears with date and time.

6. Send the same reminder again:
   `Recuérdame llamar a mamá mañana a las 9`
   Expected: Valeria warns that a similar reminder already exists and does not create a duplicate.

7. Send: `Tengo que revisar el contrato mañana`
   Then send: `/tasks`
   Expected: task appears.

8. Send: `Ya hice revisar el contrato`
   Then send: `/tasks`
   Expected: task is closed or no longer shown as open.

9. Send: `¿Qué tengo pendiente?`
   Expected: live open tasks and pending reminders.

10. Send: `¿Qué tengo mañana?`
    Expected: tomorrow’s reminders and tasks.

11. Send: `/idea Debería tener un modo familia`
    Expected: idea/report flow starts or records the idea.

## Demo Close

Val0 is early. The point is not magic.

The point is that it remembers, tracks, reminds, and helps recover what is pending through Telegram.

Founder-beta promise:

A Telegram assistant with memory, notes, reminders, tasks, and continuity.

## Scoring

After the demo, score only:

- PASS
- POLISH
- BLOCKER

Track only the top 3 issues.

## Observer Questions

Ask:

1. Did this feel useful?
2. What part would you actually use?
3. What felt confusing?
4. Would this be worth paying for if it stayed reliable?
5. What would it need to do for you personally?

## Known Limitations

- Not infinite memory yet.
- Not full calendar/email/doc automation yet.
- Not a business OS yet.
- Voice mode exists but still needs polish.
- Founder beta, not public product.

## Next Product Step

After one clean guided demo:

- patch only trust-killers
- avoid feature sprawl
- prepare $30 founder-beta offer
- start Memory v2 planning
