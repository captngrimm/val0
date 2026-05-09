# VAL0 FIRST TESTER REHEARSAL RESULT — 2026-05-09

## Status
PASS.

The full founder-beta rehearsal flow survived as a human-facing demo.

## Rehearsed flow

1. /onboardstatus
2. natural messy story
3. /exosummary
4. /whatnow
5. /draftfollowup
6. /flowrequest

## What worked

- Operating profile displayed correctly.
- Natural story capture worked without /journal.
- Exocortex memory split was visible and understandable.
- /whatnow used profile + recent context to recommend next action.
- /draftfollowup produced a usable supplier message.
- /flowrequest safely captured a roadmap idea without overpromising.

## Product proof

Val0 can now show:

first contact profile
→ messy story
→ structured memory
→ recovery
→ action support
→ roadmap-safe improvement capture

## Demo readiness

- Internal crude demo: ready
- Controlled friend/family showcase: ready with explanation
- Paid founder beta: close, but should use privacy/boundary explanation first
- Public launch: not ready

## Remaining polish

- Replies still sound slightly Mark 1 / system-ish.
- Some commands are still visible.
- Privacy/boundary explanation must be given before tester use.
- No memory delete/export UX yet.
- No autonomous sending.
- No web monitoring.
- No cold document vault.

## Recommendation

Stop adding features for this session.

Next work should be:
1. pick one controlled tester candidate
2. use the boundary script
3. run the demo
4. capture feedback as bug/confusion/feature/trust/pricing/workflow

## Karen-demo polish update

Natural operator routes were added and tested.

The user no longer needs slash commands for the core demo phrases:

- ¿Qué hago ahora?
- Muéstrame qué guardaste.
- Hazme el mensaje.

Fixes completed:
- /whatnow visible header localized to "Qué hago ahora"
- normal summary hides roadmap/parking_lot noise
- exosummary points user to natural "¿Qué hago ahora?"
- draft follow-up header localized to "Mensaje de seguimiento"
- draft follow-up preserves concrete details like cotización solar and Carlos

Latest tested natural flow:
- ¿Qué hago ahora?
- Muéstrame qué guardaste.
- Hazme el mensaje.

Status:
PASS for Karen demo polish.

Next improvement:
Replace rigid phrase matching with LLM Operator Router v1.

Principle:
LLM decides intent.
Deterministic code executes safe action.
Val replies human.
