# VAL0 SOLO FOUNDER-BETA REHEARSAL

## Goal
Simulate founder-beta users when no external testers are available.

## Rule
Do not freestyle. Run one persona at a time. Capture failures through /bug, /feedback, or /idea.

## Persona 1 — Busy professional
Needs reminders, notes, and daily agenda.

Test messages:
1. Hola
2. Recuérdame mañana a las 10 revisar una compra.
3. /reminders
4. ¿Qué tengo mañana?
5. Anota que tengo que llamar al contador el lunes.
6. /feedback

Expected:
- Greeting is clean.
- Reminder confirms correct local time.
- /reminders shows pending reminder.
- Tomorrow dashboard shows reminder.
- Note capture preserves meaning.
- Feedback flow works.

## Persona 2 — Solopreneur
Needs idea capture and task organization.

Test messages:
1. Ayuda
2. Tengo una idea: vender paquetes de automatización por WhatsApp.
3. Anota idea: crear demo de Val0 para emprendedores.
4. /idea
5. /reports

Expected:
- Ayuda is founder-beta friendly.
- Idea/note capture works.
- /idea guided flow works.
- /reports shows useful block.

## Persona 3 — Document/email user
Needs simple document generation and email follow-up.

Test messages:
1. Necesito un modelo simple de contrato de trabajo. Envíamelo por correo.
2. ¿Qué fue lo último que enviaste por correo?
3. ¿A qué correo lo enviaste?
4. ¿Tenía adjunto?
5. /bug

Expected:
- Contract/doc flow does not contradict itself.
- Last email state works.
- Recipient state works.
- Attachment state works.
- Bug flow works.

## Persona 4 — Voice user
Needs voice mode and simple voice interaction.

Test messages:
1. /voice on
2. Send voice note: “Recuérdame mañana a las 9 revisar el alpha.”
3. /reminders
4. Send voice note: “Qué tengo mañana.”

Expected:
- Voice mode turns on.
- Voice transcription works.
- Reminder is created or clear failure is logged.
- Tomorrow dashboard works.

## Persona 5 — Confused beginner
Needs safe onboarding and boundaries.

Test messages:
1. ¿Qué puedes hacer?
2. ¿Puedes recordarme cosas?
3. ¿Puedes manejar mi calendario completo?
4. /feedback

Expected:
- Val0 explains capabilities without overpromising.
- Boundaries are clear.
- Feedback flow works.

## Scoring
PASS = works cleanly
POLISH = works but wording/UX rough
BLOCKER = breaks trust, wrong state, wrong time, contradiction, crash

## After each persona
Record:
- persona
- PASS/POLISH/BLOCKER
- exact message that failed
- expected behavior
- actual behavior
