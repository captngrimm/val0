# KAREN CLIENT-ZERO MVP BACKLOG

## Sprint target

2026-05-25

## North Star

Karen can use Val to organize the family land/legal-admin process.

Val should help her:
- register what happened
- remember dates/years
- track pending tasks
- save questions
- log documents/photos/audio
- ask what is next
- give feedback for future improvements

Val is not a lawyer and does not replace legal advice.

## P0 — Must have before May 25

### 1. Human profile summary

Replace technical /onboardstatus-style output with human language.

Example:
"Esto es lo que tengo de ti hasta ahora..."

### 2. Rich-story-first routing

If user tells a messy story with emotion/context, capture it first before jumping to /whatnow.

Example:
"Tengo muchas cosas mezcladas..." should store the story, not immediately produce generic advice.

### 3. Case timeline capture

Allow user to register land/family case events.

Examples:
"Registra que en 2018 pasó X con el terreno."
"Guarda esto como evento del caso familiar."

### 4. Case timeline query

Allow user to ask:
"¿Qué pasó en 2018?"
"¿Qué tengo registrado del terreno?"
"¿Qué fue lo último del caso?"

### 5. Simple case tasks

Allow user to register pending tasks:
"Pendiente: pedirle a mi prima la foto del documento."
"Recuérdame revisar el documento mañana."

### 6. Basic attachment logging

When Karen sends photo/document/audio, Val should log it with metadata and ask for description.

No OCR requirement for MVP.

### 7. Tester feedback loop

Karen can say:
"Me gustaría que Val hiciera X."
Val stores it as idea/flow_request/bug.

### 8. Privacy/boundary message

Clear beta boundary:
- not lawyer
- not doctor
- not perfect memory
- beta storage
- avoid highly sensitive content until privacy pass improves

## P1 — Should have if time allows

### 9. Monthly hard reminder

Injection reminder / important recurring reminders.

### 10. Health/life profile template

Simple habit-support profile:
- water
- sleep
- food
- movement
- motivation style
- no diagnosis

### 11. Grocery memory v0

Register purchases and help prepare future shopping list.

### 12. Context-sensitive help

User asks:
"¿Qué sabes de mí?"
"¿Qué significa esto?"
"No entiendo qué estoy haciendo."
Val explains in human language.

## P2 — Later

- Word ingestion
- OCR
- legal document analysis
- web monitoring
- dashboard
- export/delete memory UX
- autonomous sending

## Daily sprint rule

Every change must answer:

Does this help Karen with:
1. land/family case memory,
2. timeline,
3. tasks/reminders,
4. documents/photos,
5. or feedback?

If not, parking lot.
