# VAL0 FOUNDER-BETA CHECKPOINT

## Date
2026-05-07

## Branch
val0-voice-shakedown-and-tester-pass

## Current status
Val0 is guided-demo ready and solo founder-beta rehearsal passed.

## Latest milestone
Founder-beta package, solo rehearsal results, and demo runbook are committed.

## Latest commits
- a3e01e4 docs: add Val0 founder-beta demo runbook
- 4200576 docs: add solo founder-beta rehearsal results
- 775d837 fix: answer calendar capability with beta-safe scope
- 99e033c fix: answer reminder capability deterministically
- dd1779c fix: route vague voice reminder questions through text pipeline
- bc3791e fix: tolerate short voice tomorrow transcripts
- 97d7baa fix: route natural ideas through guided idea flow
- 4e53955 fix: hard-gate report flows before memory task capture

## What passed
- Greeting
- Reminders
- /reminders
- Tomorrow dashboard
- Notes
- Idea capture
- /idea report flow
- /reports
- Document/email state
- Voice reminder
- Voice tomorrow dashboard
- Reminder capability answer
- Calendar capability answer
- /feedback and /cancelreport

## Parked
- TTS voice replies
- Gmail audio worker files
- External tester onboarding
- Local model routing
- Dashboards
- Infinite memory claims

## Known untracked files
- gmail_audio_worker.py
- gmail_auth_bootstrap.py

## Next recommended step
Prepare first real founder-beta candidate list and send one controlled demo offer.
