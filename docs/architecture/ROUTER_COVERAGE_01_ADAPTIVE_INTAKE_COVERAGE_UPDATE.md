# Router Coverage 01 Adaptive Intake Coverage Update

## Purpose

Teach the Intent Router v2 coverage report about the adaptive intake diagnostic labels added in LLM-ROUTER-01B.

This lane is diagnostic/tooling only. It changes no runtime behavior, does not edit `bot.py`, does not route live messages through Intent Router v2, does not write DB rows, does not activate memory, does not touch client files, and does not restart production.

## Labels Recognized

The coverage report now recognizes:

- `adaptive_intake_start`
- `adaptive_intake_domain`
- `adaptive_intake_followup`
- `adaptive_intake_recommendation`

These labels are shadow/sample diagnostics. They are not live runtime routes.

## Honest Status

Adaptive intake currently has:

- runtime handlers via `core/adaptive_intake.py`
- shadow diagnostic labels via `core/intent_router_v2.py`
- sample coverage via `scripts/diagnostics/intent_router_v2_sample_harness.py`
- no live routing through Intent Router v2

The coverage report should therefore show:

- sample count: present
- classifier: yes
- actual label: no unless a future actual-label lane wires it
- observed: no unless a future observation lane records it
- status: `SHADOW_ONLY`

This avoids the earlier misleading `classifier=no` result while still refusing to claim runtime coverage.

## Future Lane

A future actual-label/observation lane may add deterministic handler labels for adaptive intake and compare predicted labels against actual handlers. Until then, adaptive intake remains runtime-deterministic and router diagnostics remain shadow-only.
