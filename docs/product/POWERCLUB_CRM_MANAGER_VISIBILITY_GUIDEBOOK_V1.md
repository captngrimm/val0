# POWERCLUB-CRM-BATTLE-01A - Manager Visibility Guidebook V1

## 1. Executive Frame

PowerClub CRM Battle Stage should not be presented as "a CRM demo."

The commercial promise is operational visibility:

- Follow-up control.
- Advisor accountability.
- Branch performance comparison.
- Faster intervention on stalled opportunities.
- Reduced lost sales caused by forgotten leads, weak follow-up, or invisible advisor behavior.

This lane is fake-data only. It must not use real PowerClub data, real socios, real advisors, real WhatsApp messages, real payments, backend integrations, or production client files.

Pilot positioning:

- This is a Battle Stage pilot, not a final production CRM.
- The demo proves management visibility before production integration.
- Phase 1 does not automate WhatsApp, payments, billing, access control, or real member operations.

## 2. Battle Stage Narrative

Executive narrative:

```text
Pain: Sales opportunities are being lost because managers cannot see follow-up discipline, advisor accountability, branch execution, or stuck prospects early enough.

Visibility: The Battle Stage converts fake lead, advisor, branch, source, activity, and follow-up records into a management cockpit.

Action: Managers can immediately see who needs coaching, which leads need rescue today, which branch is leaking, and which source deserves attention.

Recovered money: The dashboard estimates avoided lost sales by assigning fake demo value to overdue, stuck, and hot opportunities that management can still intervene on.
```

The commercial claim is not "we store contacts." The claim is "we expose where money is leaking while there is still time to act."

## 3. Manager Pain Points

| Pain point | What the manager cannot see today | Business risk | Dashboard answer |
| --- | --- | --- | --- |
| Follow-ups live in scattered channels | Which leads need attention today, which are late, and who owns them | Warm prospects cool off and buy elsewhere | Pending and overdue follow-up queues by advisor and branch |
| Advisors report activity manually | Who is actually calling, messaging, scheduling visits, and closing | Activity is confused with results; low effort hides until month-end | Advisor activity ranking and daily activity trend |
| Results are visible too late | Which advisors convert and which lose leads after first contact | Coaching arrives after revenue is already lost | Advisor result ranking with conversion/outcome indicators |
| Branches are compared anecdotally | Whether branch A is underperforming because of lead volume, follow-up discipline, or conversion | Management guesses instead of targeting the bottleneck | Branch comparison widgets with source, status, follow-up, and conversion cuts |
| Lead source quality is unclear | Which campaigns, referrals, walk-ins, or social channels produce real socios | Budget goes to channels that create noise instead of sales | Lead source performance dashboard |
| Stuck opportunities disappear | Leads sit in "interested" or "visited" status without a next step | High-intent prospects leak from the funnel | Stuck opportunity and no-next-action alerts |
| No value story for management | CRM usage feels administrative instead of revenue-protective | Adoption drops because the tool looks like extra work | Recovered opportunity and avoided lost sales estimates |

## 4. Manager Visibility Matrix

| Metric | What it shows | Why manager needs it | Decision supported | Cash / avoided loss translation | Required fake data fields | Widget | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Advisor activity ranking | Calls, messages, notes, visits, and completed follow-ups by advisor | Reveals who is actually working the pipeline | Coach low activity; recognize consistent effort; rebalance coverage | Low activity raises the chance that warm leads go cold before conversion | `advisor_id`, `advisor_name_fake`, `branch_id`, `activity_type`, `activity_at`, `activity_outcome`, `lead_id` | Leaderboard with activity mix | MVP |
| Advisor result ranking | Conversions, new socios, lost leads, and conversion rate by advisor | Separates effort from revenue outcome | Identify top closers; coach high-activity/low-result advisors | Better conversion turns existing lead volume into more membership value | `advisor_id`, `lead_id`, `status`, `converted_at`, `lost_at`, `estimated_membership_value` | Result leaderboard | MVP |
| Pending follow-ups | Follow-ups due today and upcoming by advisor/branch | Gives same-day control of commitments | Decide who must act today and which lead gets priority | Timely follow-up protects interested leads before they choose another option | `follow_up_id`, `lead_id`, `owner_advisor_id`, `due_at`, `follow_up_type`, `lead_temperature` | Due-today queue | MVP |
| Overdue follow-ups | Follow-ups past due, overdue age, owner, and lead temperature | Exposes preventable sales leakage | Escalate overdue hot leads; coach repeat offenders | Every overdue hot/warm lead is an at-risk revenue opportunity | `follow_up_id`, `lead_id`, `owner_advisor_id`, `due_at`, `completed_at`, `overdue_hours`, `lead_temperature`, `estimated_membership_value` | Overdue table and KPI | MVP |
| Follow-up aging | Follow-ups grouped by age bucket: due today, 1 day late, 2-3 days late, 4+ days late | Shows severity, not just volume | Prioritize old hot leads and detect advisor backlog | Older follow-ups have lower recovery odds; aging makes lost value visible | `due_at`, `completed_at`, `overdue_hours`, `aging_bucket`, `lead_temperature`, `estimated_membership_value` | Aging histogram/heatmap | MVP |
| Status distribution | Lead count by stage: new, contacted, interested, visit scheduled, visited, converted, lost | Shows funnel health and bottlenecks | Decide whether the issue is contact, visit booking, closing, or lost reasons | Middle-stage pileups represent unclosed membership value | `lead_id`, `status`, `status_changed_at`, `estimated_membership_value` | Funnel/status chart | MVP |
| Branch comparison | Leads, conversions, overdue follow-ups, at-risk value, and conversion rate by branch | Makes branch performance visible beyond anecdotes | Target branch coaching, staffing, source mix, or follow-up discipline | Reveals whether money is leaking from execution, not demand | `branch_id`, `branch_name_fake`, `advisor_id`, `lead_id`, `status`, `converted_at`, `due_at`, `estimated_membership_value` | Branch scorecard table | MVP |
| Source/channel performance | Lead volume, conversion, overdue rate, and estimated value by source | Shows which channels generate quality opportunities | Shift attention and budget toward channels that convert | Stops spend/time going to noisy sources that do not become socios | `source_id`, `source_name`, `channel_type`, `campaign_name_fake`, `lead_id`, `status`, `converted_at`, `lost_reason` | Source performance chart | MVP |
| Daily/weekly activity | Activity trend by day, week, advisor, branch, and channel | Shows sales rhythm before month-end | Intervene when cadence drops; compare campaign response | Correcting activity dips mid-week can protect current-month sales | `activity_id`, `activity_at`, `activity_type`, `advisor_id`, `branch_id`, `source_id` | Activity trend line/bar | MVP |
| Stuck opportunities | Leads with no movement, no next step, or no recent activity | Finds prospects that are not lost yet but drifting | Assign rescue action; require next follow-up; escalate high-value leads | Stuck hot leads are the clearest recoverable-money pool | `lead_id`, `status`, `lead_temperature`, `last_activity_at`, `status_changed_at`, `next_follow_up_at`, `visit_completed_at`, `estimated_membership_value` | Stuck list with reason | MVP |
| Conversion/outcome indicators | Stage conversion, lost rate, no-show rate, visit-to-close rate | Shows where the sales process leaks | Decide whether to improve response, booking, visit handling, or closing | Stage improvements monetize existing lead flow without adding ad spend | `created_at`, `first_contact_at`, `visit_scheduled_at`, `visit_completed_at`, `converted_at`, `lost_at`, `lost_reason` | Funnel conversion cards | MVP |
| Recovered opportunity / avoided lost sales estimate | Estimated value of overdue or stuck leads that may still be rescued | Translates visibility into money | Decide where manager intervention has highest value today | Fake recovery probability converts at-risk pipeline into recoverable value | `lead_id`, `lead_temperature`, `risk_reason`, `estimated_membership_value`, `recovery_probability_fake`, `branch_id`, `owner_advisor_id` | Recovery KPI and assumptions panel | MVP |
| Manager action prompts | Recommended next actions based on visible risk | Turns dashboards into decisions | Call advisor, reassign lead, inspect branch, rescue source, review lost reasons | Faster intervention reduces preventable losses | All aggregated risk, follow-up, advisor, branch, source, and status fields | Prompt cards | MVP |
| First response time | Time from lead creation to first contact | Speed matters for digital and campaign leads | Coach slow responders; adjust assignment process | Faster response can increase visit booking and conversion probability | `created_at`, `first_contact_at`, `advisor_id`, `source_id` | Response time KPI/ranking | Phase 2 |
| Lost reason distribution | Why leads were marked lost | Shows repeated blockers | Address pricing objections, schedule fit, facility concerns, or advisor handling | Common lost reasons point to fixable revenue leakage | `lost_reason`, `lost_at`, `advisor_id`, `branch_id`, `source_id` | Lost reason bar chart | Phase 2 |
| Contact quality mix | Whether activity is meaningful or just logged | Prevents inflated activity rankings | Reward calls/visits/outcomes more than empty notes | Better-quality contact improves recovery odds | `activity_type`, `activity_outcome`, `meaningful_activity_flag`, `scheduled_visit_flag` | Quality mix chart | Phase 2 |
| Advisor coaching signals | Summary of each advisor's weak point | Makes rankings constructive | Coach on activity, speed, follow-up discipline, or conversion | Focused coaching improves sales without more leads | Aggregated advisor activity, result, overdue, response, and conversion fields | Coaching cards | Phase 2 |
| Campaign ROI proxy | Estimated value vs fake campaign cost | Connects channel performance to spend decisions | Decide which campaign deserves more budget | Moves spend toward sources producing converted value | `campaign_cost_fake`, `source_id`, `converted_at`, `estimated_membership_value` | Campaign ROI table | Later |
| Advisor workload/capacity | Open leads, due follow-ups, and hot-risk load per advisor | Shows assignment imbalance | Reassign leads before follow-ups are missed | Balanced load prevents avoidable late follow-up | `assigned_at`, `owner_advisor_id`, `open_lead_count`, `due_follow_up_count`, `hot_lead_count` | Workload heatmap | Later |
| New socio handoff | Whether converted leads receive onboarding handoff | Protects retention after close | Ensure new socio activation is complete | Better onboarding protects retention and referrals | `converted_at`, `membership_start_at`, `handoff_completed_at`, `advisor_id` | Handoff checklist | Later |

## 5. Cash Impact Logic

The demo should use directional estimates, not claims from real PowerClub operations.

Recommended fake-data formulas:

| Cash logic | Formula | Demo purpose |
| --- | --- | --- |
| Pipeline value | `open_leads * average_membership_value_fake` | Shows the size of unmanaged opportunity |
| At-risk value | `overdue_hot_leads * average_membership_value_fake` | Shows what late follow-up could cost |
| Recoverable value | `at_risk_value * recovery_probability_fake` | Frames management intervention as money recovered |
| Advisor lost opportunity | `lost_leads_after_overdue * average_membership_value_fake` | Shows cost of poor follow-up discipline |
| Source value | `converted_leads_by_source * average_membership_value_fake` | Helps managers compare channels |
| Branch value | `converted_leads_by_branch * average_membership_value_fake` | Connects branch execution to estimated revenue |

Use labels like "estimated," "demo," and "fake sample" wherever money is shown. Avoid presenting any number as actual PowerClub revenue.

## 6. Manager Action Prompts

The dashboard should not only report metrics. It should produce operational prompts a manager can act on.

MVP prompt examples:

| Trigger | Prompt | Decision supported | Cash logic |
| --- | --- | --- | --- |
| Hot lead overdue more than 24 hours | "Rescue now: hot lead overdue. Ask advisor to call today or reassign." | Escalate or reassign | Protects high-intent opportunity before it cools |
| Advisor high activity but low conversion | "Coach conversion: activity is high, closes are low." | Review call quality, offers, visit handling | Converts existing work into revenue |
| Branch has high leads but low conversion | "Inspect branch process: demand exists, conversion is weak." | Branch coaching or process review | Fixes execution leak without more lead spend |
| Source has high volume and low conversion | "Review source quality: channel creates noise." | Adjust campaign/source priority | Avoids wasting budget and advisor time |
| Visited lead has no outcome after 2 days | "Close the loop: visit completed without decision." | Require next step | Recovers leads already near purchase |
| Advisor has many aged follow-ups | "Backlog risk: rebalance workload." | Reassign or reduce new lead assignment | Prevents backlog from turning into lost sales |

## 7. Recommended Dashboard Widgets

### MVP Widgets

1. Executive KPI strip
   - Open opportunities.
   - Follow-ups due today.
   - Overdue follow-ups.
   - Hot leads at risk.
   - Estimated recoverable opportunity.

2. Advisor activity ranking
   - Calls, messages, visits scheduled, visits completed, notes logged.
   - Show daily and weekly totals.

3. Advisor result ranking
   - Converted leads/new socios.
   - Conversion rate.
   - Lost leads.
   - Overdue rate.

4. Pending follow-ups
   - Due today and upcoming.
   - Group by advisor, branch, lead temperature.

5. Overdue follow-ups
   - Sort by oldest overdue and highest estimated value.
   - Include owner advisor and last activity.

6. Status distribution
   - New, contacted, interested, visit scheduled, visited, converted, lost.
   - Show where leads are accumulating.

7. Branch comparison
   - Open leads, conversions, overdue follow-ups, conversion rate, estimated value.

8. Lead source performance
   - Leads created, converted, conversion rate, overdue rate, estimated value.

9. Daily/weekly activity
   - Activity trend by day.
   - Filter by branch and advisor.

10. Stuck opportunities
   - Leads with no activity or no status movement beyond threshold.

11. Follow-up aging
   - Buckets overdue follow-ups by age and temperature.

12. Manager action prompts
   - Shows top 5 actions management should take today.

### Phase 2 Widgets

- First response time by advisor/source.
- Lost reason distribution.
- Funnel leakage by stage.
- Coaching signal cards.
- Recovered opportunity estimate with configurable assumptions.
- Heatmap of overdue follow-ups by advisor and day.

### Later Widgets

- Campaign ROI proxy with fake campaign costs.
- Advisor capacity/workload balancing.
- New socio onboarding handoff.
- Retention/referral signal.
- Exportable manager report.

## 8. Fake Data Requirements Summary

The Battle Stage needs a seed dataset large enough to make ranking, comparison, and trend widgets believable.

Minimum fake dataset:

- 5 to 8 fake branches.
- 50+ fake advisors.
- 1,500 to 2,000 fake monthly records.
- 300 to 500 fake converted socios/outcomes.
- 4,000 to 8,000 fake activities.
- 1,500 to 2,500 fake follow-up records.
- 8 to 12 fake lead sources/campaigns.
- At least 250 overdue follow-ups.
- At least 150 stuck opportunities.
- At least 8 lost reasons.

Fake identities must be obviously synthetic. Use sample names and IDs that cannot be mistaken for real PowerClub people or members.

Recommended core entities:

| Entity | Purpose |
| --- | --- |
| `branches` | Branch comparison and filters |
| `advisors` | Rankings, assignment, accountability |
| `leads` | Funnel, status, source, value, owner |
| `activities` | Calls, messages, notes, visits, follow-up behavior |
| `follow_ups` | Pending, overdue, and recovery widgets |
| `status_events` | Stage movement and stuck opportunity detection |
| `sources` | Source/campaign performance |
| `outcomes` | Converted/lost/cooling off indicators |

Detailed fake-data requirements live in `docs/product/POWERCLUB_CRM_FAKE_DATA_REQUIREMENTS_V1.md`.

## 9. MVP / Phase Classification

### MVP

MVP should make management visibility obvious in one screen.

Include:

- Fake-data-only executive dashboard.
- Advisor activity and result rankings.
- Pending and overdue follow-ups.
- Lead/socio status distribution.
- Branch comparison.
- Lead source performance.
- Daily/weekly activity chart.
- Stuck opportunities.
- Basic conversion/outcome indicators.
- Estimated recovered opportunity using clear fake assumptions.
- Follow-up aging.
- Manager action prompts.

Do not include:

- Real backend.
- Real PowerClub records.
- Payment integration.
- WhatsApp automation.
- Real campaign spend.
- Production auth.
- Client data imports.

### Phase 2

Add:

- Response time.
- Lost reason analytics.
- Coaching signal cards.
- Funnel leakage analytics.
- More configurable recovery estimates.
- Better fake activity quality modeling.
- Manager filters by date, branch, advisor, status, and source.

### Later

Add only after the demo proves useful:

- Real integration planning.
- Data import design.
- Manager exports.
- Advisor workload balancing.
- Retention/onboarding signals.
- Automated reminders or WhatsApp only if explicitly scoped in a separate lane.

## 10. Manager Talk Track

Suggested framing:

```text
This is not valuable because it stores names in a CRM. It is valuable because management can finally see where sales are leaking: who followed up, who did not, which branch is stuck, which sources convert, and how much opportunity might be protected by acting today.
```

The demo should keep returning to one question:

```text
What does the manager know today that they could not see yesterday, and what action can they take before the opportunity is lost?
```

## 11. Risks and Boundaries

- Fake recovery estimates can look like financial claims if not labeled clearly.
- Advisor rankings can feel punitive; pair them with coaching signals.
- Too many widgets can weaken the Battle Stage; MVP should prioritize manager action.
- Real WhatsApp/payment/backend integrations are outside this lane.
- No real PowerClub or client data should be used to populate the dashboard.
- Do not promise this pilot is a final production CRM.
- Do not promise automated follow-up in Phase 1.
