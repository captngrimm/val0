# Client Isolation Contract v0

## Purpose

Val0 must not leak one client's identity, nickname, data paths, or workflow into another client's experience.

This became mandatory after Karen MVP hardcoded values such as `Insanity` and `client_id="karen"` appeared inside reusable calendar/grocery/context flows.

## Rules

1. Reusable flows must not hardcode a client id such as `karen`.
2. Reusable copy must not hardcode a client nickname such as `Insanity`.
3. Client-specific personality must come from a client profile/config layer.
4. Calendar, grocery, agenda, reminder, and audit flows must resolve client context from chat/user/session, not from literal strings.
5. Karen-only legal/finca modules may remain Karen-specific, but they must be clearly isolated.
6. New product features must pass client-isolation audit before commit/merge.
7. Test/demo copy may be playful, but production-critical actions must remain precise and safe.

## Accepted temporary debt

Karen MVP still contains Karen-specific code. This is allowed temporarily only because Karen is client-zero and the current sprint is scoped to her delivery.

## Required next migration

- Add `resolve_client_id(chat_id)`.
- Add `client_display_name(client_id)` / `client_vocative(client_id)`.
- Replace Calendar/Grocery/Agenda hardcoded `karen` with resolved client id.
- Keep Karen legal/finca modules as explicit Karen-only modules until generalized.

## Guardrail

Any future reusable module should fail audit if it contains:
- `Insanity`
- `client_id="karen"`
- direct `/clients/karen` paths
- `"karen"` passed into reusable calendar/grocery/agenda functions
