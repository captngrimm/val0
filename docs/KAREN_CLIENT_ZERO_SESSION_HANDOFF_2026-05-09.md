# KAREN CLIENT-ZERO SESSION HANDOFF — 2026-05-09

Branch:
karen-client-zero-mvp-2026-05-25

Latest validated commit:
c2eb645 docs: checkpoint Karen lawyer package v0 pass

## Sprint target

Deliver a rough but functional Karen LandOps MVP by 2026-05-25.

Primary use case:
Karen needs a legal/admin copilot for a family land process involving five heirs, with events from 1986 to present.

Val does not replace a lawyer.
Val organizes facts, documents, timeline, tasks, appointments, and questions for lawyers/family.

## Current MVP status

Approx progress:
82%

Validated modules:
- Karen Interrogator v0
- Karen Plan State v0
- Karen Lawyer Questions v0
- Save lawyer questions into case
- Telegram inline button for next action
- Document Inventory v0
- Document holder/custody capture
- Registry pending capture
- Karen Case Status Query v0
- Karen Lawyer Package v0

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
Generates initial package for lawyer.

## Working natural phrases

¿Cuál es el plan?
Shows active plan.

¿Qué tengo del caso del terreno?
Shows case status.

prepara paquete para abogado
Generates lawyer package.

armemos preguntas para el abogado
Shows lawyer questions.

guardar preguntas en el caso
Saves lawyer questions into case and offers document inventory.

## Validated flow

1. User starts /interrogate.
2. Val asks:
   - case name
   - people/heirs
   - oldest timeline event
   - documents available
   - urgency / lawyer appointment
3. Val closes with plan.
4. User asks /karenplan.
5. User asks /lawyerquestions.
6. User says guardar preguntas en el caso.
7. Val saves questions and shows inline button.
8. User taps ✅ Sí, empezar inventario.
9. Val starts document inventory.
10. User gives document inventory.
11. Val detects categories.
12. Val asks who has documents.
13. User gives document custody.
14. Val asks registry identifiers.
15. Val completes document inventory.
16. User asks /karencase.
17. User asks /lawyerpackage.

## Known issues

1. Active flow state is RAM-based.
If bot restarts mid-flow, it forgets where it was.

Future fix:
Persistent Flow State v0.

2. Pasted transcripts can be consumed as active-flow answers.
If user pastes long Telegram transcripts while Val is waiting for an answer, Val may save the whole transcript as the current answer.

Future fix:
Pasted Transcript Guard v0.

3. Mixed inventory/custody answers are handled literally.
If user answers "Karen has documents..." when Val asks "what documents exist?", Val stores it as inventory first, then asks custody again.

Future fix:
Mixed inventory/custody detection.

4. Lawyer Package v0 repeats some next-action language.
It embeds full /karencase output.

Future fix:
Compact Lawyer Package v1.

5. Telegram inline button works, but app abstraction is future work.
Logic should remain portable beyond Telegram.

Future fix:
Action abstraction layer for app/frontend.

## Next recommended build options

Priority 1:
Compact Lawyer Package v1
- avoid repeated next-action language
- produce cleaner attorney-facing summary
- keep it copy/paste friendly

Priority 2:
Persistent Flow State v0
- preserve active flow across bot restart
- needed before real users depend on longer guided flows

Priority 3:
Pasted Transcript Guard v0
- detect long pasted logs/transcripts
- ask whether to use as answer, save as note, or ignore current flow

Priority 4:
Phrase Feedback / Alias Trainer v0
- user can correct phrases
- e.g. "when I say guardar preguntas en el caso, route to lawyer question save"
- style corrections too, e.g. "say arroz con mango, not arroz con moño"

## Suggested next test with Karen

Have Karen try:
1. /karencase
2. /lawyerpackage
3. Ask: ¿Cuál es el plan?
4. Ask: ¿Qué falta?
5. Use one real document/photo summary if available.

Goal:
See whether she understands the value without Frank explaining every command.

## Current value statement

Karen can already use Val to:
- start the land case
- register core facts
- organize documents
- track who has documents
- prepare lawyer questions
- generate an initial lawyer package
- ask what is currently known about the case
- ask where the plan stands

This is enough for a rough client-zero MVP conversation.
