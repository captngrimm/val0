# VAL0 SESSION CHECKPOINT — 2026-05-09

## Branch

val0-voice-shakedown-and-tester-pass

## Current status

Val0 now has a coherent founder-beta product loop.

This session moved Val0 from a rough Telegram bot with notes/reminders into a crude but real profile-aware exocortex / operator demo.

## What now works

### 1. Smart Journal / Natural Capture

User can send messy natural input without /journal.

Example:
Val, holy shit today was awful. Carlos called me twice because he still needs the solar quote. The supplier ghosted me again and now I look bad. Also save this idea: Val should track supplier follow-ups and warn me when a provider is becoming unreliable.

Val classifies and stores:
- reflection
- follow_up
- follow_up
- idea

### 2. Narrative Capture v1

Longer messy stories are split into item-specific memory records.

Example memory split:
- reflection: rough day / emotional pressure
- follow_up: Carlos needs solar quote
- follow_up: supplier ghosted
- idea: track supplier reliability

### 3. Exocortex summary

/exosummary shows latest grouped capture cleanly.

### 4. What Now recovery

/whatnow uses:
- recent structured memory
- operating profile facts
- main goal
- friction points
- current tools
- starter workflow

It recommends a next action.

### 5. Draft follow-up

/draftfollowup drafts a practical message using recent follow_up memory.

Fixed trust issue:
- Carlos is treated as client/requester, not as supplier.
- Unknown supplier gets generic greeting.

### 6. Onboarding Consultant v1

/onboard asks 7 profile questions and stores durable facts.

Saved facts include:
- preferred_name
- primary_role
- use_case
- main_goal
- friction_points
- current_tools
- tracking_buckets
- starter_workflow
- onboarding_status

/onboardstatus displays profile.

### 7. Workflow Designer / flow_request

/flowrequest captures workflow or feature ideas safely.

Purpose:
- do not overpromise
- store roadmap request
- separate target_context from active_user_profile
- allow manual workaround now

Example:
Carpenter wants to monitor new carpentry tools/newsletters.

Stored as:
- bucket: parking_lot
- target_context: carpentry
- active_user_profile: current saved user profile

## Current demo flow

1. /onboard
2. /onboardstatus
3. natural messy story
4. /exosummary
5. /whatnow
6. /draftfollowup
7. /flowrequest

## Product sentence

Val0 starts as a smart private journal that becomes your operator over time.

## What this proves

First contact
→ operating profile
→ free-form story
→ structured memory
→ recovery
→ action draft
→ roadmap-safe improvement capture

## Honest current readiness

- Crude demo: ready
- Controlled friend/family showcase: close / usable with explanation
- Paid founder-beta: not yet fully ready
- Public product: not ready

## Remaining blockers before first external tester

1. Privacy/boundary explanation must be used.
2. Demo should be rehearsed once cleanly.
3. Some commands are still visible and clunky.
4. No autonomous sending.
5. No web monitoring.
6. No cold document vault.
7. No memory delete/export UX yet.
8. No polished localization layer yet.

## Next recommended work

Recommended next:
Prepare one controlled founder-beta demo/rehearsal package.

Do not add many new features before one demo rehearsal.

Suggested next steps:
1. Create short demo checklist.
2. Create tester invite message.
3. Run one clean rehearsal as if talking to a real tester.
4. Decide first candidate.
5. Keep scope tight.

## Current latest commits of interest

- docs: add Val0 founder beta boundaries v2
- docs: add Val0 founder beta demo v2
- docs: checkpoint workflow flow request capture
- feat: add workflow flow request capture
- docs: define workflow designer and flow request doctrine
- fix: prevent follow-up drafts from confusing client and provider
- feat: make whatnow use operating profile facts
- feat: add onboarding consultant v1
- docs: define Val0 memory doctrine
- docs: checkpoint Val0 narrative capture v1

## Recovery note

If context is lost, ask for:

git log --oneline -20
cat docs/VAL0_SESSION_CHECKPOINT_2026_05_09.md
cat docs/VAL0_FOUNDER_BETA_DEMO_V2.md
cat docs/VAL0_FOUNDER_BETA_BOUNDARIES_V2.md
