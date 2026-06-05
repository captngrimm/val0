# PRODUCT-RETURN-04 Caso Finca Contradiction Smoke

## Scope

Non-runtime smoke coverage for Caso Finca contradiction/weirdness Q&A.

## Added Coverage

`scripts/quality/caso_finca_conversational_qa_smoke.py` now protects:

- `Val, hay algo raro o contradictorio en el Caso Finca?`

Expected behavior:

- routes to bounded Caso Finca Q&A as `possible_contradictions`,
- frames output as review focuses / possible odd points for Nora,
- includes the legal boundary,
- avoids legal certainty,
- avoids won/lost claims,
- hides internal IDs/VFMS,
- avoids raw OCR body dumps.

## Remaining Gap

These variants are not currently supported by the existing implementation, even with active case context:

- `Val, ves algo raro?`
- `Val, algo no cuadra?`

Runtime changes are forbidden in this lane, so no failing smoke was added for those variants. They remain future alias work.

## Recommended Next Lane

`PRODUCT-RETURN-05 — Caso Finca Contextual Weirdness Alias`

Add a narrow context-aware runtime alias only if approved:

- active Caso Finca context + `ves algo raro?`
- active Caso Finca context + `algo no cuadra?`

Guardrails:

- do not route generic weirdness questions globally,
- keep legal boundary,
- keep Nora review framing,
- no internal IDs,
- no raw OCR dumps,
- no live data mutation.

## Runtime Statement

No runtime behavior changed in PRODUCT-RETURN-04.
