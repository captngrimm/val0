# FOUNDER-DEMO-FIX-01 Live Trust-Killer Triage

## Scope

This lane fixes three founder-demo rehearsal blockers only:

1. Active Caso Finca workspace context now keeps the bounded Q&A context warm for follow-up phrases such as "Val, ves algo raro?".
2. Normal Caso Finca document summaries hide technical document IDs and `vfms:` labels.
3. Generic folder saves avoid appending the exact same note text twice in the same folder.

## Guardrails

- No client data files are edited.
- No production restart is included in this lane.
- No legal conclusions are added.
- Technical IDs remain available only through the explicit technical-details document route.
- Vague weirdness phrases stay bounded to Caso Finca only when active case context exists.

## Verification Focus

- `caso_finca_conversational_qa_smoke.py` covers the active-workspace follow-up path for "Val, ves algo raro?".
- `caso_finca_workspace_smoke.py` covers normal document summary ID redaction while preserving the explicit technical details route.
- `karen_generic_folder_smoke.py` covers exact duplicate note suppression in a temp folder store.

## Runtime Behavior Changed

Yes, narrowly:

- Caso Finca workspace views mark active bounded Q&A context for follow-up questions.
- Normal document summaries no longer expose internal storage IDs.
- Generic folder note saves become idempotent for exact duplicate note text in the same folder.

No live client data is mutated by the implementation or smokes.
