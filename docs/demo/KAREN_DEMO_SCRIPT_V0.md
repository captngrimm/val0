# KAREN_DEMO_SCRIPT_V0 — Val Personal / Karen

Purpose:
Define a controlled demo/test script for Karen founder-beta.

This script is not meant to prove that Val does everything.
It is meant to prove that Val can help with a few useful workflows reliably.

---

## Demo principle

Keep the demo narrow.

Do not ask Karen to test everything at once.

Current test focus:
1. What can Val do today?
2. Grocery/list add/list/delete.
3. Idea capture.
4. Roadmap/status.
5. Legal/document support only if Karen naturally asks.

Avoid for this demo:
- photo/OCR
- barcode
- nutrition facts
- full open ChatGPT-like conversation
- deep legal advice
- advanced reminders unless explicitly testing agenda

---

## Tester message already sent

Karen was asked to try:

1. “Val, ¿qué puedes hacer hoy?”

2. Grocery/list:
- “Val, anota arroz, huevos y café para el súper.”
- “Val, ¿qué tengo en la lista del súper?”
- “Val, borra café de la lista del súper.”

3. Idea capture:
- “Val, tengo una idea: que me ayudes con ______.”

Goal:
See whether Val understands, responds clearly, and avoids confusing Karen.

---

## Demo flow A — What can Val do?

User says:
Val, ¿qué puedes hacer hoy?

Expected:
Val explains current useful capabilities:
- legal/finca/caso
- agenda/recordatorios básicos
- roadmap/ideas
- grocery/list if included in current build

Pass criteria:
- answer is clear
- Spanish is natural enough
- does not overpromise
- does not say it can do full OCR/photo/barcode yet

Fail criteria:
- response too robotic/menu-heavy
- promises unsupported features
- confuses Karen with internal roadmap language

---

## Demo flow B — Grocery/list add

User says:
Val, anota arroz, huevos y café para el súper.

Expected:
Val confirms items added.

Expected items:
- arroz
- huevos
- café

Pass criteria:
- items are parsed separately
- no duplicate weirdness
- response is short and clear

Fail criteria:
- saves whole sentence as one item
- misses items
- routes to unrelated reminder/drift handler

---

## Demo flow C — Grocery/list show

User says:
Val, ¿qué tengo en la lista del súper?

Expected:
Val shows saved list.

Pass criteria:
- list includes recently added items
- formatting is readable
- no unrelated roadmap/status response

Fail criteria:
- says empty when items exist
- shows wrong client/context
- includes deleted items incorrectly

---

## Demo flow D — Grocery/list delete

User says:
Val, borra café de la lista del súper.

Expected:
Val removes café.

Pass criteria:
- deletes café only
- confirms deletion
- list remains otherwise intact

Fail criteria:
- deletes wrong item
- says it is a reminder
- fails because of phrase parsing

Optional shortcut:
quitar café

Expected:
Deletes café if item exists.

---

## Demo flow E — Idea capture

User says:
Val, tengo una idea: que me ayudes con [idea].

Expected:
Val captures idea and frames it as roadmap/backlog, not automatic promise.

Pass criteria:
- idea is extracted cleanly
- response says it is saved/captured
- does not promise immediate build

Fail criteria:
- idea not saved
- response overpromises
- routes as random chat

---

## Demo flow F — Ideas list

User says:
Val, ¿qué ideas tengo guardadas?

Expected:
Val lists saved ideas.

Pass criteria:
- shows captured idea(s)
- explains backlog/roadmap status clearly

Fail criteria:
- empty list when idea exists
- too much internal markdown
- confusing formatting

---

## Demo flow G — Roadmap/status

User says:
Val, ¿qué viene después?

Expected:
Val summarizes near-term roadmap:
- stabilize current flows
- reminders/agenda
- grocery/list expansion
- document/legal support
- later: photo/OCR/barcode

Pass criteria:
- clear and non-technical
- does not overwhelm
- no false promises

Fail criteria:
- too long
- too technical
- promises public-ready product

---

## Optional legal/admin flow

Only test if Karen naturally asks.

User examples:
- Val, ayúdame a preparar lo de Nora.
- Val, ¿qué tengo pendiente para la abogada?
- Val, tengo los papeles regados, ¿por dónde empiezo?

Expected:
Val routes to:
- Nora package
- missing-review checklist
- Carpeta Clara

Pass criteria:
- helpful organization
- clear legal boundary
- no legal advice pretending certainty

Fail criteria:
- gives legal conclusions
- gets lost in generic response
- asks Karen to repeat too much

---

## Feedback questions for Karen

After testing, ask:

1. ¿Qué te funcionó?
2. ¿Qué te confundió?
3. ¿Qué esperabas que hiciera y no hizo?
4. ¿Qué sería lo más útil para ti esta semana?
5. ¿Te gustaría usarlo por voz, texto, o ambos?
6. ¿La respuesta se sintió clara o muy robótica?

---

## Pass/fail summary template

Date:
Tester:
Tested flows:
- what_can_do:
- grocery_add:
- grocery_list:
- grocery_delete:
- idea_capture:
- ideas_list:
- roadmap_status:
- legal_docs_optional:

Overall result:
PASS / PARTIAL / FAIL

Top friction:
1.
2.
3.

Next patch recommended:
1.

---

## Current known limits

- Voice can fail download/transcription.
- OCR/photo/barcode are deferred.
- Some routing is deterministic.
- Karen-specific context still exists.
- Reminder/agenda needs more QA.

---

## Demo promise

This demo proves:
Val can help Karen remember, organize, list, and recover context in a few specific workflows.

This demo does not prove:
Val is a finished general assistant or public product.

