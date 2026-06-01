# NEWCHAT-01 Recovery Protocol

## Purpose

This protocol defines how any new chat or cockpit recovers Val0 state.

It prevents reliance on memory, stale chat context, or huge pasted context. The recovery recipe combines ValPrime continuity with repo source-of-truth verification.

## Existing Continuity System

ValPrime already has a continuity model:

- `/continuity`
- natural "new chat bundle"
- Desk
- Side Table
- Library Index
- Vault

NEWCHAT-01 does not replace this system. It adds repo verification around it.

## Recovery Model

- Desk = active context loaded into every new chat.
- Side Table = recent/relevant context.
- Library Index = catalog of sources.
- Vault = archived/deep detail retrieved only when needed.

## Required Startup Flow

When the user says "status Val0", "next", "where are we", or opens a new Val0 cockpit:

1. Ask for or use ValPrime `/continuity` output first if available.
2. Run or inspect:

```bash
python3 scripts/diagnostics/val0_source_of_truth_check.py
```

3. If working on runtime, run:

```bash
python3 scripts/diagnostics/val0_source_of_truth_check.py --full
```

4. Review current docs:

- `docs/product/VAL0_MASTER_MILESTONE_MAP.md`
- `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`
- `docs/ops/VAL0_SESSION_STARTUP_CHECKLIST.md`
- `docs/product/VAL0_DOCS_VALUE_MAP.md`
- `docs/architecture/INTENT_ROUTER_V2_MARCHING_ORDER.md`
- latest `docs/architecture/ROUTER_*` reports
- `docs/product/ROADMAP_02_VALPRIME_SIGNAL_PROTOCOL.md`
- `docs/product/ROADMAP_03_SIGNAL_REGISTRY_STORAGE_DESIGN.md`
- `docs/architecture/OBSIDIAN_01_VAULT_ROLE_CLARIFICATION.md`

## New Chat Starter Prompt

Copy/paste this into a new ChatGPT chat:

```text
Val, new chat recovery. Do not rely on memory. Ask me for ValPrime /continuity and Launchpad output if needed. Current repo is /opt/val0. Use val0_source_of_truth_check.py to verify technical state before continuing.
```

## Minimal Recovery Output Format

Every recovered chat should answer with:

- Current branch/head
- Current macro milestone
- Active lane
- Health status
- Top source-of-truth docs
- ValPrime continuity summary if provided
- Next safe action
- Stop conditions

## Stop Conditions

Stop and report if:

- ValPrime continuity conflicts with repo source-of-truth.
- `git status -sb` shows unexpected dirty runtime or client files.
- Karen RC full smoke fails before runtime work.
- Shadow mode is ON unexpectedly.
- The user asks for broad router refactor before source-of-truth says it is next.

## Guardrails

- Do not continue from memory only.
- Do not start broad router refactor unless source-of-truth says it is next.
- Do not enable shadow unless running short observation.
- Do not touch client/private files without audit.
- Do not commit dirty client state.
- If ValPrime continuity conflicts with repo source-of-truth, stop and report the conflict.

## Runtime Note

This protocol changes no runtime behavior. It does not integrate external services or change ValPrime continuity.
