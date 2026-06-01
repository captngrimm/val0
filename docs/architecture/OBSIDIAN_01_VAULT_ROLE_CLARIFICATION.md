# OBSIDIAN-01 Vault Role Clarification

## Purpose

This note clarifies the role of Obsidian and `valeria_vault` so the vault is not forgotten, but also not confused with the active operational source of truth.

Obsidian exists as a possible visual second brain and graph view. It is not currently the Val0 runtime, the ValPrime cockpit, or the primary recovery source.

## Current Discovered Facts

- `/home/forge/valeria_vault` exists.
- `/home/forge/valeria_vault/.obsidian` exists.
- Forge docs reference a continuity model with Desk, Side Table, Library Index, and Vault.
- Older Val0 backup references mention Bridge Val0 -> Forge graph memory, `valeria_graph`, and "Borrador listo para Obsidian" draft blocks.

These facts suggest there is a real Obsidian-style continuity layer, but not that it should become the active runtime source.

## Current Source-of-Truth Model

- ValPrime and checkpoints are the operational cockpit and recovery spine.
- Forge docs are durable ops and product documentation.
- OPEL is the event and audit log.
- Repo docs and smokes are the technical truth for code behavior, readiness, and regressions.
- Obsidian is a visual second brain, graph, and library view. It is not the primary source of truth.

## Recommended Role

Obsidian should be a read and visualization layer over already trusted sources.

Recommended use:

- graph view
- library navigation
- human review
- curated continuity summaries
- optional future visual index over ValPrime, OPEL, Forge docs, and repo docs

Avoid using Obsidian as a manually maintained duplicate truth. If it becomes useful, prefer exporting or syncing curated summaries from trusted sources into Obsidian rather than editing parallel state by hand.

Possible future direction:

- export selected ValPrime checkpoints into notes
- export OPEL timeline summaries into notes
- export repo architecture docs into indexed notes
- generate an Obsidian index note from trusted sources

Do not use Obsidian for runtime decisions until a separate design explicitly defines trust, sync, privacy, and ownership.

## Risks

- Split-brain: Obsidian could diverge from ValPrime, OPEL, Forge docs, or repo docs if it becomes a separate manual truth.
- Drift: copied docs can go stale when source docs change.
- Sensitive data exposure: private client docs, legal PDFs, transcripts, and operational notes should not be mirrored casually.
- Runtime confusion: using vault notes directly for runtime decisions could bypass tested repo behavior and client isolation guardrails.

## Future Path

- OBSIDIAN-02: inventory vault contents.
- OBSIDIAN-03: decide sync/export model.
- OBSIDIAN-04: generate an index note from ValPrime, OPEL, and repo docs.

Do not implement these until Karen RC and router work are stable.

## Runtime Note

This document changes no runtime behavior. It does not wire Obsidian into Val0, move files, alter routing, or change source-of-truth ownership.
