# Val0 Capability Map

Purpose:
Show what Val0 can currently do as a broader encrypted operating layer, not only Legal MVP.

## Core Capability Areas

1. Conversation
- Natural text handling
- Session memory
- Recent messages
- Persistent facts

2. Voice
- Telegram voice handler
- Voice transcription
- Voice memory capture
- Task/commitment extraction from voice

3. Memory
- user_facts
- memory_items
- memory_entries
- semantic FAISS memory via /sremember and /ssearch

4. Notes
- /note
- /notes
- /search
- Natural case-note capture

5. Reminders / Tasks / Commitments
- reminders
- tasks
- commitments
- due-date flows
- reminder confirmation flow

6. Legal / Case Workflows
- cases
- case_notes
- case_events
- case_summaries
- due today/range
- idle cases
- case cockpit/summary

7. PM / Focus / Continuity
- /focus
- /showfocus
- pm_current_focus
- pm_decisions
- recovery/where-were-we flows

8. Calendar
- Google Calendar read/write sandbox pieces
- agenda/tomorrow flows
- needs separate readiness test

9. Email / Documents
- Resend email sending
- last email status
- resend/redirect/copy last email
- document drafting/email mode
- high trust-risk area

10. Places
- /place
- Google Places lookup
- session result memory

11. Reports / Daily Logs
- /daily
- /dailies
- /reports
- /semana
- daily_logs

12. Ops / Health / Debug
- /ops
- /health
- /status
- /statepacket
- /bug
- /feedback

## Live Encrypted DB Tables by Domain

### Memory / Conversation
- messages
- user_facts
- memory_items
- memory_entries

### Work Management
- tasks
- reminders
- commitments
- daily_logs
- milestones

### Legal / Cases
- cases
- case_notes
- case_events
- case_summaries
- legal_audit_log

### PM / Operator
- pm_current_focus
- pm_decisions
- user_settings
- chat_prefs

### Audit / Trace
- audit_log
- action_logs
- processed_events
- watchdog_alerts

