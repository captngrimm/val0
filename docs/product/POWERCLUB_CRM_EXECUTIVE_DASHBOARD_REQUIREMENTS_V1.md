# POWERCLUB-CRM-BATTLE-01A - Executive Dashboard Requirements V1

## 1. Purpose

Define the executive management dashboard for the PowerClub CRM Battle Stage.

The dashboard must sell operational visibility, not generic CRM storage. It should help management see where money is leaking because of weak follow-up, low advisor accountability, poor branch visibility, source/channel noise, and stuck opportunities.

This is a fake-data pilot spec. It is not a backend, production CRM, payment integration, WhatsApp automation lane, or real PowerClub data import.

## 2. Executive Dashboard Story

Dashboard narrative:

```text
Pain: Managers cannot intervene early because follow-up, advisor effort, branch performance, and lead quality are invisible or scattered.

Visibility: The dashboard shows advisor rankings, follow-up risk, branch comparisons, source quality, status distribution, and stuck opportunities in one executive view.

Action: The dashboard tells the manager what to do today: rescue hot leads, coach specific advisors, inspect weak branches, rebalance workload, and review poor-quality sources.

Recovered money: The dashboard estimates avoided lost sales using fake at-risk lead value and fake recovery probability assumptions.
```

## 3. Layout Requirements

### Required Header Controls

- Date range: today, this week, this month, custom demo range.
- Branch filter.
- Advisor filter.
- Source/channel filter.
- Status filter.
- Lead temperature filter.
- Visible label: `Demo con datos ficticios`.
- Visible label: `Piloto de visibilidad, no CRM final de produccion`.

### Executive KPI Strip

| KPI | What it shows | Why manager needs it | Decision supported | Cash / avoided loss translation | Required fields | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| Open opportunities | Active leads not converted or lost | Shows size of current pipeline | Decide where management attention is needed | Open pipeline is potential membership value not yet closed | `lead_id`, `status`, `estimated_membership_value`, `branch_id`, `owner_advisor_id` | MVP |
| Follow-ups due today | Follow-ups due before day-end | Gives same-day control | Push advisor action today | Timely follow-up protects warm intent | `follow_up_id`, `lead_id`, `due_at`, `owner_advisor_id`, `follow_up_status` | MVP |
| Overdue follow-ups | Follow-ups past due | Shows preventable leakage | Escalate or reassign | Late follow-up increases probability of lost sale | `due_at`, `completed_at`, `overdue_hours`, `lead_temperature`, `estimated_membership_value` | MVP |
| Hot leads at risk | Hot leads overdue, stuck, or without next step | Focuses manager on highest urgency | Rescue, reassign, or call now | Hot-risk leads carry the highest recoverable value | `lead_temperature`, `risk_reason`, `next_follow_up_at`, `last_activity_at`, `estimated_membership_value` | MVP |
| Estimated recovered opportunity | Fake value potentially protected by intervention | Translates visibility into money | Prioritize actions by estimated value | At-risk value multiplied by fake recovery probability | `estimated_membership_value`, `recovery_probability_fake`, `risk_reason`, `branch_id`, `owner_advisor_id` | MVP |

## 4. MVP Widget Requirements

### Advisor Activity Ranking

What it shows:
Calls, messages, notes, visit actions, and completed follow-ups by advisor.

Why manager needs it:
Managers need to know whether advisors are actively working opportunities or only reporting outcomes after the fact.

Decision supported:
Coach low activity, recognize consistent execution, and rebalance coverage.

Cash / avoided loss:
Low activity creates silent opportunity decay. Fixing activity cadence protects leads before they go cold.

Required fields:
`advisor_id`, `advisor_name_fake`, `branch_id`, `activity_id`, `activity_type`, `activity_at`, `activity_outcome`, `meaningful_activity_flag`, `lead_id`.

Widget:
Leaderboard with total meaningful activities plus activity mix.

Phase:
MVP.

### Advisor Result Ranking

What it shows:
Conversions, new socios, lost leads, conversion rate, overdue rate, and estimated value by advisor.

Why manager needs it:
Activity alone can hide poor closing. Result ranking shows which advisors turn opportunity into business.

Decision supported:
Coach weak conversion, study top performers, and avoid rewarding empty activity.

Cash / avoided loss:
Improving conversion monetizes existing lead flow without buying more leads.

Required fields:
`advisor_id`, `lead_id`, `status`, `converted_at`, `lost_at`, `lost_reason`, `estimated_membership_value`, `owner_advisor_id`.

Widget:
Result leaderboard with conversion value and overdue rate.

Phase:
MVP.

### Pending Follow-Ups

What it shows:
Follow-ups due today and upcoming by advisor, branch, type, and lead temperature.

Why manager needs it:
Managers need a daily control queue, not a passive list of leads.

Decision supported:
Tell advisors exactly which prospects require action today.

Cash / avoided loss:
Same-day action protects warm prospects while intent is fresh.

Required fields:
`follow_up_id`, `lead_id`, `owner_advisor_id`, `branch_id`, `due_at`, `follow_up_type`, `follow_up_status`, `lead_temperature`.

Widget:
Prioritized due-today queue.

Phase:
MVP.

### Overdue Follow-Ups

What it shows:
Late follow-ups by advisor, branch, temperature, age, and estimated value.

Why manager needs it:
Overdue follow-ups are a concrete accountability signal and a rescue list.

Decision supported:
Escalate, reassign, or require immediate action.

Cash / avoided loss:
Every hot/warm overdue lead is an avoidable lost-sale risk.

Required fields:
`follow_up_id`, `lead_id`, `owner_advisor_id`, `branch_id`, `due_at`, `completed_at`, `overdue_hours`, `lead_temperature`, `estimated_membership_value`.

Widget:
Overdue queue plus advisor overdue ranking.

Phase:
MVP.

### Follow-Up Aging

What it shows:
Overdue follow-ups grouped by age bucket: due today, 1 day late, 2-3 days late, 4-7 days late, 8+ days late.

Why manager needs it:
Volume alone is not enough. Aging shows severity and urgency.

Decision supported:
Prioritize old hot leads, detect advisor backlog, and rebalance assignments.

Cash / avoided loss:
Recovery probability drops as follow-up age increases.

Required fields:
`due_at`, `completed_at`, `overdue_hours`, `aging_bucket`, `lead_temperature`, `estimated_membership_value`, `owner_advisor_id`.

Widget:
Aging histogram and advisor/branch heatmap.

Phase:
MVP.

### Status Distribution

What it shows:
Lead counts and estimated value by funnel status.

Why manager needs it:
It reveals where leads are accumulating and which stage needs intervention.

Decision supported:
Improve first contact, visit scheduling, closing, or lost-lead review.

Cash / avoided loss:
Middle-stage accumulation means money is in motion but not closed.

Required fields:
`lead_id`, `status`, `status_changed_at`, `created_at`, `estimated_membership_value`, `branch_id`, `owner_advisor_id`.

Widget:
Funnel/status distribution chart.

Phase:
MVP.

### Branch Comparison

What it shows:
Lead volume, conversion, overdue follow-ups, stuck opportunities, and estimated value by branch.

Why manager needs it:
Management needs to know whether branch performance is a demand issue, a follow-up issue, or a conversion issue.

Decision supported:
Target branch coaching, staffing, manager review, or lead allocation.

Cash / avoided loss:
Branch comparison reveals where execution is leaking money.

Required fields:
`branch_id`, `branch_name_fake`, `advisor_id`, `lead_id`, `status`, `converted_at`, `lost_at`, `due_at`, `estimated_membership_value`.

Widget:
Branch scorecard with sortable columns.

Phase:
MVP.

### Source/Channel Performance

What it shows:
Lead volume, conversion rate, overdue rate, and estimated value by source/channel.

Why manager needs it:
Managers need to separate useful sources from noisy sources.

Decision supported:
Adjust campaign attention, branch handling, or source investment.

Cash / avoided loss:
Better source focus reduces wasted advisor time and improves close probability.

Required fields:
`source_id`, `source_name`, `channel_type`, `campaign_name_fake`, `lead_id`, `created_at`, `status`, `converted_at`, `lost_reason`, `estimated_membership_value`.

Widget:
Source performance bar chart and table.

Phase:
MVP.

### Daily/Weekly Activity

What it shows:
Activity trend by day/week, branch, advisor, and activity type.

Why manager needs it:
Managers need to detect sales cadence drops while there is still time to correct them.

Decision supported:
Intervene during the week, not only after poor month-end results.

Cash / avoided loss:
Restoring activity cadence can protect current-month opportunities.

Required fields:
`activity_id`, `activity_at`, `activity_type`, `advisor_id`, `branch_id`, `source_id`, `meaningful_activity_flag`.

Widget:
Daily/weekly trend chart with filters.

Phase:
MVP.

### Stuck Opportunities

What it shows:
Leads with no activity, no status movement, no next follow-up, or no outcome after a visit.

Why manager needs it:
Stuck leads are not necessarily lost, but they are drifting.

Decision supported:
Assign rescue action, require next step, or reassign owner.

Cash / avoided loss:
Stuck hot leads are the most obvious recoverable-money pool.

Required fields:
`lead_id`, `status`, `lead_temperature`, `last_activity_at`, `status_changed_at`, `next_follow_up_at`, `visit_completed_at`, `estimated_membership_value`, `risk_reason`.

Widget:
Stuck opportunity list sorted by temperature and estimated value.

Phase:
MVP.

### Conversion/Outcome Indicators

What it shows:
Lead-to-contact, contact-to-visit, visit-to-close, lost rate, and no-show rate.

Why manager needs it:
Managers need to know which stage is failing.

Decision supported:
Fix response speed, visit booking, visit attendance, closing, or lost-lead handling.

Cash / avoided loss:
Stage improvements increase revenue from existing lead volume.

Required fields:
`created_at`, `first_contact_at`, `visit_scheduled_at`, `visit_completed_at`, `converted_at`, `lost_at`, `lost_reason`, `status_events`.

Widget:
Conversion cards and funnel chart.

Phase:
MVP, with deeper leakage analysis in Phase 2.

### Recovered Opportunity / Avoided Lost Sales Estimate

What it shows:
Estimated fake value of overdue or stuck leads that may still be saved.

Why manager needs it:
It converts dashboard discipline into commercial urgency.

Decision supported:
Prioritize the highest-value intervention list for today.

Cash / avoided loss:
At-risk value multiplied by fake recovery probability produces an estimated recoverable-opportunity number.

Required fields:
`lead_id`, `lead_temperature`, `risk_reason`, `estimated_membership_value`, `recovery_probability_fake`, `branch_id`, `owner_advisor_id`.

Widget:
Recovery KPI, top recoverable leads, assumptions panel.

Phase:
MVP as simple estimate; Phase 2 as configurable assumptions.

### Manager Action Prompts

What it shows:
Top recommended actions generated from fake dashboard signals.

Why manager needs it:
Dashboards should convert visibility into action.

Decision supported:
Coach advisor, rescue lead, reassign owner, inspect branch, review source, or escalate aged follow-up.

Cash / avoided loss:
Action prompts shorten time between risk detection and intervention.

Required fields:
Aggregated advisor, lead, branch, source, follow-up, aging, and recovery fields.

Widget:
Top 5 action prompt cards.

Phase:
MVP.

## 5. Phase 2 Widgets

- First response time by advisor/source.
- Lost reason distribution.
- Contact quality mix.
- Funnel leakage by stage and branch.
- Advisor coaching signal cards.
- Recovery assumptions editor.
- Overdue heatmap by advisor and day.
- Branch/source drilldowns.

## 6. Later Widgets

- Campaign ROI proxy with fake campaign costs.
- Advisor workload/capacity balancing.
- New socio onboarding handoff.
- Retention/referral signal.
- Exportable executive report.
- Production integration readiness checklist, only after separate approval.

## 7. MVP Acceptance Criteria

The executive dashboard passes when a manager can answer these questions from fake data in under one minute:

- Which advisor is most active this week?
- Which advisor converts best?
- Which follow-ups are due today?
- Which follow-ups are overdue and aging badly?
- Which hot leads are at risk?
- Which branch is leaking follow-up or conversion?
- Which source/channel produces the best conversion?
- Where are leads stuck in the funnel?
- What estimated opportunity could be recovered if the team acts today?
- What are the top manager actions for today?

## 8. Boundaries and Required Labels

Required visible labels:

- `Demo con datos ficticios`.
- `Estimacion basada en supuestos de demo`.
- `Piloto de visibilidad, no CRM final de produccion`.
- `No conectado a WhatsApp, pagos, ni datos reales`.

Do not promise:

- Real PowerClub revenue.
- Real member conversion.
- Real advisor performance.
- Automated WhatsApp follow-up in Phase 1.
- Payment reconciliation.
- Backend sync.
- Production CRM completeness.
- Production auth, permissions, or audit trails.

## 9. Recommended Next Lane

```text
POWERCLUB-CRM-BATTLE-01B - Static Executive Dashboard Prototype With Fake Fixtures
```

Scope:

- Static browser dashboard under `docs/demo/powerclub_crm/`.
- Local fake fixture data only.
- MVP widgets from this spec.
- Clear pilot/fake-data labels.
- No backend, no auth, no WhatsApp, no payments, no real client data.
