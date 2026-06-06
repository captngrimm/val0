# FOUNDER-DEMO-FIX-02 Live Path Mismatch

## Problem

FOUNDER-DEMO-FIX-01 covered helper paths, but the live Telegram rehearsal still showed mismatches:

1. After opening Caso Finca, "Val, ves algo raro?" did not reliably reach the bounded possible-contradictions answer.
2. "Val, resume el documento 1" could still be intercepted by a generic document-summary path that exposed technical IDs.
3. Exact duplicate saves to the Libro folder could still be caught outside the generic folder duplicate guard.

## Fix

This lane adds narrow live-handler route protection in `bot.py`:

- Contextual Caso Finca weirdness phrases get a guarded early Q&A gate before founder/generic responses.
- Numbered Caso Finca document-summary requests get a guarded early workspace-summary gate before generic VFMS summaries.
- Generic folder commands get an earlier folder gate before older notes/case capture handlers.

The underlying renderers and duplicate guard remain deterministic and Karen-scoped.

## Safety Boundaries

- Contextless "Val, ves algo raro?" is not made globally Caso Finca.
- Normal document summaries hide `ID técnico del documento` and `vfms:` labels.
- Explicit technical details can still show technical IDs.
- Duplicate detection is exact normalized text within the same folder.
- No client data files, DB files, systemd, OAuth, or secrets are changed.

## Runtime Env Watch

Runtime logs mentioned `RuntimeError: Missing RESEND_API_KEY`. This lane does not change environment, systemd, or secrets. Operator should verify the runtime environment separately without printing secret values.
