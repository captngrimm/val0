# KAREN CLIENT-ZERO SESSION HANDOFF — 2026-05-10

Branch:
karen-client-zero-mvp-2026-05-25

Latest validated commit:
d8f0e13 docs: checkpoint Karen pasted transcript guard v0 pass

Approx MVP progress:
93%

## Sprint target

Deliver a rough but functional Karen LandOps MVP by 2026-05-25.

Primary use case:
Karen needs a legal/admin copilot for a family land process involving five heirs, with events from 1986 to present.

Val does not replace a lawyer.
Val organizes facts, documents, timeline, tasks, appointments, and questions for lawyers/family.

## Validated modules

- Karen Interrogator v0
- Karen Plan State v0
- Karen Lawyer Questions v0
- Save lawyer questions into case
- Telegram inline button for next action
- Document Inventory v0
- Document holder/custody capture
- Registry pending capture
- Karen Case Status Query v0
- Karen Lawyer Package v1 compact
- SQLCipher-safe Karen Flow State module
- Persistent Karen Interrogator flow state
- Persistent Karen Document Inventory flow state
- Pasted Transcript Guard v0

## Working commands

/interrogate
Starts guided case intake.

/karenplan
Shows active Karen LandOps plan.

/lawyerquestions
Shows lawyer questions.

/karencase
Shows current case status.

/lawyerpackage
Generates compact initial package for lawyer.

## Working natural phrases

¿Cuál es el plan?
Shows active plan.

¿Qué tengo del caso del terreno?
Shows case status.

prepara paquete para abogado
Generates compact lawyer package.

armemos preguntas para el abogado
Shows lawyer questions.

guardar preguntas en el caso
Saves lawyer questions into case and offers document inventory.

## Reliability improvements validated

Persistent Interrogator:
- active step is saved to DB
- survives bot restart
- clears state after completion

Persistent Document Inventory:
- active inventory state is saved to DB
- survives bot restart
- resumes correct step after restart
- preserves last inventory and detected categories

Pasted Transcript Guard:
- detects long transcript/log blocks during active Karen flows
- asks whether to use as answer, save as note, or ignore
- option 3 ignore validated
- prevents accidental memory contamination during testing/support

## Known issues

1. Mixed inventory/custody answers are handled literally.
Example:
If Val asks "what documents exist?" and user says "Karen has documents...", Val may treat it as document inventory first, then ask custody again.

Future fix:
Mixed Inventory/Custody Detection v0.

2. Pasted Transcript Guard is mostly operator/debug protection.
Useful, but not likely a core Karen behavior.

3. Lawyer Package v1 is static/templated.
Useful and clean, but future v2 should pull more dynamically from case notes.

4. Telegram is current interface, not final product layer.
Logic should remain portable to app/front-end later.

5. Gmail files remain untracked and unrelated:
- gmail_audio_worker.py
- gmail_auth_bootstrap.py

Do not touch these during Karen sprint unless explicitly reprioritized.

## Current value statement

Karen can already use Val to:
- start the land case
- register core facts
- organize documents
- track who has documents
- note pending registry identifiers
- prepare lawyer questions
- generate an initial lawyer package
- ask what is currently known about the case
- ask where the plan stands
- continue key flows even after bot restart

## Suggested Karen live test

Give Karen minimal guidance only.

Ask her to try:
1. ¿Qué tengo del caso del terreno?
2. ¿Cuál es el plan?
3. prepara paquete para abogado
4. guardar preguntas en el caso
5. tap the document inventory button
6. answer one document inventory question in natural Spanish

Pass criteria:
- Karen understands what Val is doing without Frank translating every command.
- Karen sees practical value for the land/legal-admin case.
- Karen can identify at least one thing she would actually use next week.

## Remaining path to 100%

P0:
- Karen Live Test Pass

P1:
- Mixed Inventory/Custody Detection v0
- Small UX polish: friendlier confirmations, maybe sticker/file_id collector
- Update docs after live test

P2:
- Attachment/photo logging into case
- Dynamic lawyer package v2
- Phrase Feedback / Alias Trainer v0
