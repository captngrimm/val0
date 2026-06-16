# PowerClub CRM Battle 02F - Controlled Val LLM Backend Prototype

## Purpose

Add the first backend-ready Val Mentor seam without putting secrets in the browser and without making real LLM calls.

This lane creates a safe scaffold:

- backend/proxy stub under `tools/`
- frontend Operator Mode suggestion drawer
- bounded request shape
- schema validation
- Frank approval before use
- deterministic local fallback if anything fails

No production service, systemd unit, database, persistence, real PowerClub data, OpenAI browser call, or live provider call was added.

## Backend / Proxy Scaffold

File:

`tools/powerclub_val_llm_proxy_stub.py`

Behavior:

- exposes a small stdlib HTTP stub if run manually
- endpoint: `/powerclub/val/mentor-suggest`
- health: `/health`
- no external framework required
- no persistence
- no database
- no production service
- no systemd

Environment variables:

- `VAL_POWERCLUB_LLM_MOCK_ENABLED=1` enables mock structured responses
- `VAL_POWERCLUB_LLM_API_KEY` is the placeholder for a future provider key

If neither mock mode nor provider key exists, the stub returns safe unavailable/local fallback JSON.

The current scaffold deliberately does not call a real provider. That is the correct behavior until a secure backend/provider lane is approved.

## No Browser API Keys

Hard rules preserved:

- no API key in `val_discovery.html`
- no provider secret in static assets
- no direct browser-to-OpenAI/LLM call
- no checked-in key
- no key name exposed in the frontend

The browser only knows a local integration seam:

`VAL_LLM_ENDPOINT = "/powerclub/val/mentor-suggest"`

## Bounded Request Shape

Frontend function:

`buildValLlmRequest()`

Sends:

- `meeting_context`
- `current_question`
- `captured_response`
- `selected_category`
- `whiteboard_state`
- `allowed_demo_sections`
- `guardrails`

The request intentionally excludes secrets, real PowerClub data, audio, transcript persistence, payment/auth/WhatsApp data, and unrelated Val0 client data.

## Response Schema

The frontend and stub expect:

- `val_message`
- `summary`
- `detected_pain`
- `follow_up_question`
- `whiteboard_cards`
- `recommended_demo_section`
- `risk_flags`
- `next_step`
- `confidence`
- `needs_frank_confirmation`

Frontend function:

`validateValMentorSuggestion()`

It rejects missing keys, disallowed demo sections, non-list card/risk fields, and any suggestion that does not require Frank confirmation.

## Frank Approval Behavior

Operator Mode now includes:

- `Sugerir con Val`
- `Usar sugerencia`
- `Ignorar`
- status line
- `Sugerencia de Val` panel

The frontend does not blindly execute backend output.

When Frank accepts:

- Val message is shown
- recommendation card updates
- next suggested question updates
- Val observation notes that Frank approved it

The frontend does not auto-write to a backend, auto-persist notes, or silently organize whiteboard cards.

## Fallback Behavior

If backend is missing, unavailable, returns non-OK, returns invalid JSON, or returns invalid schema:

- frontend builds a deterministic local suggestion
- status says `Modo local activo`
- meeting does not break
- Frank can continue with local Val workflow

Fallback keeps the local question bank, local capture, local whiteboard, and local summary.

## Prompt Capsule Usage

Source-of-truth:

`docs/product/POWERCLUB_CRM_VAL_LLM_PROMPT_CAPSULE_02E_V1.md`

The stub exposes `PROMPT_CAPSULE_DOC` pointing to that file. A real future backend should inject the prompt capsule server-side, not from the browser.

Val rules remain:

- Spanish by default
- concise
- ask one question at a time
- summarize before follow-up
- avoid hype
- never invent PowerClub facts
- never promise production
- never commit price/scope
- route legal/pricing/commitment questions to Frank/scope freeze
- keep Frank as operator

## What Was Deferred

Deferred intentionally:

- real provider call
- model selection
- API key provisioning
- auth/rate limiting
- deployment/service manager
- logging policy
- persistence
- real PowerClub data
- production hardening

## Next Implementation Step

If approved, the next lane should:

1. Decide provider/model.
2. Decide hosting location.
3. Add backend auth/rate limits.
4. Store provider key server-side only.
5. Inject prompt capsule server-side.
6. Validate response schema server-side.
7. Add adversarial tests.
8. Rehearse Frank-machine fallback.

## Guardrails

- No fake LLM claims.
- No API keys in frontend.
- No real PowerClub data.
- No persistence.
- No recording.
- No STT expansion.
- No production promise.
- No human/AGI framing.
- Deterministic fallback remains.
- CRM demo and Val Discovery Stage remain separate.
