# VAL0 NARRATIVE CAPTURE V1 CHECKPOINT

## Date
2026-05-09

## Branch
val0-voice-shakedown-and-tester-pass

## Status
PASS.

Narrative Capture v1 is working.

## What changed

Val0 can now accept longer free-form story input without requiring /journal.

Example:

Val, holy shit today was awful. Carlos called me twice because he still needs the solar quote. The supplier ghosted me again and now I look bad. Also save this idea: Val should track supplier follow-ups and warn me when a provider is becoming unreliable.

Val0 can classify and store separate structured memory items:

- reflection: user had a horrible/rough day and feels pressure
- follow_up: Carlos still needs the solar quote
- follow_up: supplier did not respond / ghosted
- idea: Val should track supplier follow-ups and warn about unreliable providers

## Proven loop

Natural story
→ classifier extracts items[]
→ storage saves separate memory records
→ /exosummary shows grouped capture
→ /whatnow recovers context and recommends next action
→ /draftfollowup drafts a usable message

## Why this matters

This is the core freedom layer.

The user does not need to speak in slash commands or perfect prompts.
They can tell Val a messy story, and Val starts sorting it into useful memory/action pieces.

## Current working commands

- /classify
- /journal
- /exosummary
- /exorecent
- /whatnow
- /draftfollowup

## Known limitations

- /whatnow still depends mostly on recent memory.
- /exosummary groups by timestamp window, not explicit capture_id.
- There is no true document vault yet.
- Raw conversation storage and structured memory are not the same thing as exact document storage.
- User-facing onboarding consultant is not built yet.
- Pattern detection is not built yet.
- Cold storage / document retrieval is not built yet.

## Memory doctrine

Val0 memory should be layered:

1. Raw message log
   - preserves what the user actually said
   - useful for audit and reconstruction

2. Structured Exocortex items
   - bucket, summary, raw_span, timestamp
   - useful for whatnow, pattern detection, and operator behavior

3. Operating profile
   - user/business/work/life context
   - useful for first-contact onboarding and personalization

4. Pattern memory
   - repeated blockers, unreliable people/providers, recurring loops
   - useful for insight and proactive suggestions

5. Cold document storage
   - exact saved document bodies
   - useful when the user asks for exact line-by-line retrieval

## Important distinction

Do not treat fuzzy memory as exact document storage.

If the user asks:
"Give me that document again."

Val should only reproduce exact text if it was stored as a document/cold-storage record or preserved as a raw message containing the full document.

Otherwise Val must say it can reconstruct a draft from memory, but not guarantee exact verbatim text.

## Next recommended milestone

Mark 1.1 options:

A. Cold document storage
- /docsave
- /docget
- /docsearch

B. Onboarding Consultant v1
- first-contact flow
- operating profile
- user/business/workflow intake

C. Pattern Detection v0
- "you keep mentioning supplier delays"
- "this is becoming a recurring blocker"

Recommended next:
Cold storage doctrine first, then choose between document vault and onboarding.
