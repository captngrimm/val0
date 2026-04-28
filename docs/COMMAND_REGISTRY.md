# Val0 Command Registry

Purpose:
Track available Val0 commands, natural intents, handlers, data touched, risk level, and test status.

## Telegram Slash Commands

| Command | What it does | Handler / Area | Data touched | Status |
|---|---|---|---|---|
| /start | Starts user flow / onboarding entry | start | users/messages/facts likely | Needs test |
| /ops | Ops/system command surface | ops_cmd | system/status | Needs test |
| /health | Health check | health_cmd | system/env/db | Needs test |
| /reminders | Show reminders | reminders_cmd | reminders | Needs test |
| /rmd | Reminder command | rmd_cmd | reminders | Needs test |
| /memory | Show memory/facts | memory_cmd | user_facts/messages | Needs test |
| /status | User/system status | status_cmd | messages/user_facts/focus | Needs test |
| /note | Add note | note_cmd | notes | Needs test |
| /notes | List notes | notes_cmd | notes | Needs test |
| /daily | Daily log/report | daily_cmd | daily_logs | Needs test |
| /context | Context summary | context_cmd | messages/memory/focus | Needs test |
| /focus | Set PM focus | focus_cmd | pm_current_focus | Needs test |
| /showfocus | Show current focus | showfocus_cmd | pm_current_focus | Needs test |
| /cancelreport | Cancel report flow | cancelreport_cmd | reports/session state | Unknown |
| /handoff | Generate handoff | handoff_cmd | context/messages/focus | Needs test |
| /semana | Weekly view | semana_cmd | reminders/tasks/cases likely | Needs test |
| /dailies | Daily summaries/search | dailies_cmd | daily_logs | Needs test |
| /dsearch | Search daily logs | dsearch_cmd | daily_logs | Needs test |
| /search | Search notes/memory | search_cmd | notes/memory | Needs test |
| /place | Places lookup | place_cmd | places session/API | Needs test |
| /followuptest | Follow-up test | handle_followup_test | operator followup | Dev/test |
| /statepacket | State packet | handle_statepacket | state/context | Needs test |
| /voice | Voice mode toggle/status | voice_cmd | chat_prefs | Needs test |
| /bug | Report bug | bug_cmd | bug report flow | Needs test |
| /feedback | Capture feedback | feedback_cmd | feedback/notes likely | Needs test |
| /idea | Capture idea | idea_cmd | notes/memory/parking style | Needs test |
| /reports | Reports | reports_cmd | reports/daily/cases likely | Needs test |
| /mem | Memory helper | handle_mem | memory_items/facts | Needs test |
| /remember | Store memory | handle_remember | user_facts/memory_items | Needs test |
| /sremember | Store semantic memory | sremember_cmd | semantic FAISS | Needs test |
| /ssearch | Search semantic memory | ssearch_cmd | semantic FAISS | Needs test |

## Natural Input Handlers

| Intent | What it does | Handler / Area | Data touched | Status |
|---|---|---|---|---|
| Text message | Main natural conversation path | handle_text | messages/memory/facts | Working, needs fresh-user test |
| Voice note | Transcribes voice and routes text | handle_voice | messages/memory_items/tasks/commitments/cases | Working, needs trust test |
| Case note mention | Saves natural note to known case | _maybe_capture_case_note | cases/case_notes/case_summaries | Needs test |
| Due today / due range | Legal deadline/reminder queries | try_due_today / try_due_range | case_events/reminders/cases | Needs test |
| Where were we / recovery | Resume context from Forge/graph | try_where_were_we / try_recovery_protocol | Forge context/tasks | Fragile/important |
| Focus recovery | Maintains current PM focus | PM/focus block | pm_current_focus/pm_decisions | Important |
| Places request | Searches places | places_engine | external API/session | Needs test |
| Email/document request | Draft/send email/doc logic | email overrides/doc mode | user_facts/email state | High risk, needs test |
| Reminder/task capture | Detects tasks/reminders | reminder/task gates | reminders/tasks/commitments | High value, needs test |

