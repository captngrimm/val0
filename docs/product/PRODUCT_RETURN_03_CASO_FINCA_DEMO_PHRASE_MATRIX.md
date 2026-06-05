# PRODUCT-RETURN-03 Caso Finca Founder Demo Q&A Phrase Matrix

## Purpose

Map founder-demo Caso Finca phrases to expected routes, existing smoke protection, remaining gaps, and safety boundaries.

This is the first NR27 actual one-shot worker target. It is docs-only and product-safe: no runtime behavior, no fixture edits, no smoke edits, and no client data changes.

## Phrase Coverage Matrix

| demo step / scenario | canonical phrase | natural Karen phrase variants | expected route/surface | currently protected by | gap / next protection needed | legal/safety boundary | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Open Caso Finca | `Val, abre mi Caso Finca` | `Val, abre lo de la finca`; `Val, qué sabemos del Caso Finca?` | Compact Caso Finca dashboard / first screen | `scripts/quality/caso_finca_workspace_smoke.py`; `docs/product/FOUNDER_DEMO_READINESS_V1.md` | Add demo phrase matrix smoke only if future route aliases expand | Read-only workspace; Nora/la abogada confirms legal effect | PASS |
| Show Caso Finca documents | `Val, muéstrame documentos del Caso Finca` | `Val, enséñame los papeles de la finca`; `Val, qué papeles tengo de la finca?` | Compact document list, no technical IDs by default | `scripts/quality/caso_finca_workspace_smoke.py`; `scripts/quality/caso_finca_conversational_qa_smoke.py` indirectly protects no internal IDs | Add focused demo sequence smoke linking dashboard -> docs list -> summary | Do not dump raw OCR/body; internal IDs only in technical details route | PASS |
| Summarize document 1 | `Val, resume el documento 1` | `Val, dime qué dice el primer documento`; `Val, explícame el documento 1` | Numbered document summary; OCR-backed if saved text is available | `scripts/quality/caso_finca_workspace_smoke.py`; `scripts/quality/caso_finca_conversational_qa_smoke.py` for “primer documento” importance | Add demo copy note that this is reading aid, not legal conclusion | OCR caveat when OCR-backed; Nora/la abogada confirms legal effect; no raw OCR body dump | PASS |
| Ask what is missing / needs review | `Val, qué falta revisar del Caso Finca?` | `Val, qué falta revisar?` after active Caso Finca context; `Val, qué falta confirmar?` | Bounded Caso Finca Q&A needs-review answer | `scripts/quality/caso_finca_conversational_qa_smoke.py` protects context-aware route and founder-limitation separation | Add founder-demo script note: use explicit “del Caso Finca” unless active context is established | Must not globally hijack generic “qué falta”; legal boundary required | POLISH |
| Ask what is known vs uncertain | `Val, qué sabemos seguro y qué falta confirmar del Caso Finca?` | `Val, qué sabemos seguro y qué falta confirmar?` with active case context | Known-vs-uncertain Q&A answer with grounded sections | `scripts/quality/caso_finca_conversational_qa_smoke.py` | Add demo expectation for “Hechos en Val / Falta confirmar” language | Separate facts, signals, and uncertainty; no legal certainty | PASS |
| Ask what to ask Nora | `Val, qué le pregunto a Nora?` | `Val, qué debería llevarle a Nora?`; `Val, qué preguntas preparo para la abogada?` | Nora questions Q&A answer | `scripts/quality/caso_finca_conversational_qa_smoke.py`; workspace full view has Nora question section | Add natural variants for “llevarle a Nora” and “preguntas para la abogada” if not already protected | Val prepares questions only; Nora/la abogada confirms legal effect | POLISH |
| Ask what document to review first | `Val, cuál documento debería revisar primero?` | `Val, cuál documento reviso primero?`; `Val, qué documento reviso primero?` | Document-priority Q&A answer recommending document 1 and safe next command | `scripts/quality/caso_finca_conversational_qa_smoke.py` protects current aliases | Add “qué documento reviso primero?” explicitly if not already in smoke route coverage | Recommendation is operational priority, not legal weight | PASS |
| Ask plain-language explanation | `Val, explícame el Caso Finca en palabras simples.` | `Val, explícame lo de la finca en palabras simples`; `Val, dime qué es este caso en fácil` | Plain-language bounded Q&A answer | `scripts/quality/caso_finca_conversational_qa_smoke.py`; design doc examples | Add “en fácil” / “como si estuviera ordenándolo para Nora” as future natural aliases | No invented facts; no legal conclusions | POLISH |
| Ask about contradiction / weirdness | `Val, hay algo raro o contradictorio en el Caso Finca?` | `Val, ves algo raro?`; `Val, algo no cuadra?` with active case context | Contradiction/weirdness Q&A answer, framed as items to review | `scripts/quality/caso_finca_conversational_qa_smoke.py` now protects the explicit phrase | Vague variants still need runtime support or a future context-aware alias before demoing them live | Frame as “cosas que revisaría con Nora”; no conclusions | POLISH for explicit phrase; BLOCKER risk for vague variants |
| Ask next action before talking to lawyer | `Val, qué hago antes de hablar con la abogada?` | `Val, qué hago antes de hablar con Nora?`; `Val, cómo me preparo para Nora?` | Next-action Q&A answer with practical prep | `scripts/quality/caso_finca_conversational_qa_smoke.py` protects lawyer phrase | Add “preparo para Nora” variant if demo wants it | Operational prep only; lawyer confirms legal effect | POLISH |

## Existing Protection Summary

- `scripts/quality/caso_finca_workspace_smoke.py` protects workspace open, compact first screen, document list, technical details, numbered document summaries, timeline, timeline gaps, route aliases, and no live file mutation.
- `scripts/quality/caso_finca_conversational_qa_smoke.py` protects bounded Q&A classification, renderer safety, context-aware routing, founder-limitation separation, document-priority aliases, generic what-now separation, legal boundary, and no internal ID/raw OCR leakage.
- `scripts/quality/client_fixture_smoke.py --client karen` protects the broader Karen fixture route set.
- `scripts/quality/karen_rc_full_smoke.py --keep-going` protects the wider Karen RC surface.

## Recommended Next Product Lane

`PRODUCT-RETURN-04 — Caso Finca Demo Sequence Smoke`

Goal:

Add one focused non-runtime smoke that exercises the founder-demo sequence:

1. Open Caso Finca.
2. Show documents.
3. Summarize document 1.
4. Ask one grounded Q&A question.
5. Verify legal boundary, no raw OCR, no internal IDs in normal views, and no live data mutation/staging.

## Allowed Files For Next Lane

- `scripts/quality/caso_finca_demo_sequence_smoke.py`
- `docs/product/FOUNDER_DEMO_READINESS_V1.md` if adding a pointer to the smoke
- `docs/product/PRODUCT_RETURN_03_CASO_FINCA_DEMO_PHRASE_MATRIX.md` if updating this matrix

## Forbidden Files For Next Lane

- `bot.py`
- `core/**`
- `clients/**`
- `tests/fixtures/**` unless explicitly approved later
- DBs
- OAuth/token/systemd files
- production restart actions
- runtime behavior changes

## Suggested Tests

- `python3 scripts/quality/caso_finca_conversational_qa_smoke.py`
- `python3 scripts/quality/caso_finca_workspace_smoke.py`
- `python3 scripts/quality/client_fixture_smoke.py --client karen`
- `python3 scripts/quality/karen_rc_full_smoke.py --keep-going`
- `python3 scripts/quality/client_isolation_audit.py`
- `git diff --check`
- `git status --short --branch`

## NR27 One-Shot Worker Scope Result

This one-shot target stayed within allowed scope:

- docs-only product artifact
- no runtime code
- no fixture edits
- no smoke edits
- no client data edits
- no commit

It is safe to use as a future NR27 one-shot template for small product coverage artifacts when the task has exact allowed files, forbidden runtime/client paths, and a concrete smoke/audit list.

## Explicit Runtime Statement

No runtime behavior changed in PRODUCT-RETURN-03 / NR27.
