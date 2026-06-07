# ONBOARDING-01H.1 Post-Onboarding Stale Response Fix

Purpose: document the narrow fix for a live Telegram stale response after the ONBOARDING-01H demo flow.

This is a runtime routing/idempotency fix. It does not add persistence, profile writes, reminders, tasks, calendar events, database migrations, production config, or client data edits.

## Problem

The live fake-Ale Telegram test produced the correct onboarding copy, then an unrelated stale response mentioning client-zero agenda/case/document context.

The clean onboarding smoke did not reproduce it because it sent each message once with fresh context.

## Root Cause

`bot.handle_text` had the text idempotency guard below early deterministic routes, including onboarding discovery.

That meant an onboarding turn could:

1. produce the correct onboarding reply
2. clear onboarding state
3. return before the Telegram message id was marked processed

If Telegram redelivered the same update, the duplicate no longer had active onboarding state. It could then continue into later stale pending/calendar/case/document routes.

## Fix

`bot.handle_text` now marks text updates as processed before early routing.

The later idempotency guard remains as fallback for cases where the early guard fails, but it no longer rejects the original call after the early mark succeeds.

## Guardrail

`scripts/quality/onboarding_no_double_reply_live_path_smoke.py` feeds the exact fake-Ale sequence and then redelivers the final `todo eso` with the same Telegram message id.

Expected behavior:

- original five turns each produce one onboarding reply
- duplicate final delivery produces no reply
- final real reply is the daily review proposal
- no Tany, Nora, finca, abogada, timeline, broker, or Google Calendar stale text appears

## Scope

- no broad router refactor
- no Caso Finca route behavior changed
- no calendar confirmation behavior changed
- no client live data touched
