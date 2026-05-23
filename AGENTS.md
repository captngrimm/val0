# Val0 Engineering Guardrails

These rules are mandatory for future Codex/assistant work in this repo.

## Client Isolation First

- Before coding reusable features, classify what is client-specific versus reusable.
- Scan for hardcoded names, nicknames, emails, chat IDs, paths, and client IDs before and after edits.
- Prefer config, client profiles, and the client identity resolver over hardcoded copy or client literals.
- Check cross-client contamination risk any time code touches routing, memory, calendar, documents, reminders, groceries, ideas, or user-facing copy.

## Workflow Discipline

- Decide Codex-vs-hotfix before edits.
- Multi-file changes and refactors must use Codex.
- Launchpad verifies server state, logs, tests, and systemd when deployment/runtime behavior is in scope.
- No feature is PASS without compile, audit, and a smoke test appropriate to the change.

## Scope Boundaries

- Do not touch OAuth, tokens, systemd, `/etc/val0`, or real client data unless explicitly scoped.
- Keep edits scoped to the requested files and behavior.
- Do not refactor unrelated Karen/client-zero legal, finca, calendar, or data flows unless explicitly scoped.
