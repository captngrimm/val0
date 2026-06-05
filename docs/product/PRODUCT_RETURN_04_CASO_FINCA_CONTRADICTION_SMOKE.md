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

PRODUCT-RETURN-05 adds narrow context-aware support for these variants:

- `Val, ves algo raro?`
- `Val, algo no cuadra?`

They should route to `possible_contradictions` only with active Caso Finca context. Without active/explicit case context, they should not hijack generic conversation.

## Remaining Guardrail

- do not route generic weirdness questions globally,
- keep legal boundary,
- keep Nora review framing,
- no internal IDs,
- no raw OCR dumps,
- no live data mutation.

## Runtime Statement

No runtime behavior changed in PRODUCT-RETURN-04. PRODUCT-RETURN-05 is the narrow runtime alias lane for the vague variants.
