# POWERCLUB-CRM-BATTLE-01A - Fake Data Requirements V1

## 1. Purpose

Define the fake data model required to support the PowerClub CRM Battle Stage executive dashboard.

The fake dataset must make management visibility feel real enough to evaluate the concept at scale:

- 50+ advisors.
- 5 to 8 branches.
- 1,500 to 2,000 monthly lead/opportunity records.
- Enough activities, follow-ups, outcomes, and status events to support rankings, aging, branch comparison, source/channel performance, stuck opportunities, and recovered-opportunity estimates.

This is fake-data only. Do not import or infer from real PowerClub data, real socios, real advisors, real WhatsApp chats, payment records, exports, screenshots, or production client files.

## 2. Scale Requirements

| Dataset area | MVP target | Reason |
| --- | --- | --- |
| Branches | 5 to 8 fake branches | Enables branch comparison and management filters |
| Advisors | 50 to 65 fake advisors | Supports ranking, variance, coaching, and workload signals |
| Monthly lead/opportunity records | 1,500 to 2,000 | Makes executive dashboard feel management-scale |
| Converted/new socio outcomes | 300 to 500 | Supports result ranking and conversion analysis |
| Lost outcomes | 350 to 650 | Supports lost-rate and future lost-reason analysis |
| Activities | 4,000 to 8,000 | Supports daily/weekly activity, advisor activity ranking, and contact quality |
| Follow-ups | 1,500 to 2,500 | Supports pending, overdue, aging, and advisor accountability |
| Overdue follow-ups | 250 to 450 | Creates visible follow-up control problem |
| Stuck opportunities | 150 to 300 | Creates recoverable opportunity pool |
| Sources/channels | 10 to 16 | Supports source/channel performance |
| Status events | 4,000 to 7,000 | Supports funnel movement and stuck detection |
| Manager prompts | 25 to 50 generated prompt candidates | Supports daily action cards |

## 3. Required Data Shape

The fixture data should be deterministic and local. Recommended files for a future implementation:

```text
docs/demo/powerclub_crm/data/branches.json
docs/demo/powerclub_crm/data/advisors.json
docs/demo/powerclub_crm/data/leads.json
docs/demo/powerclub_crm/data/activities.json
docs/demo/powerclub_crm/data/follow_ups.json
docs/demo/powerclub_crm/data/status_events.json
docs/demo/powerclub_crm/data/sources.json
docs/demo/powerclub_crm/data/dashboard_assumptions.json
```

Do not create these fixture files in this lane unless a future implementation lane approves it.

## 4. Core Entities

### `branches`

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `branch_id` | string | Yes | Synthetic branch ID |
| `branch_name_fake` | string | Yes | Fake branch label |
| `region_fake` | string | Yes | Regional grouping |
| `manager_name_fake` | string | Yes | Synthetic manager persona |
| `monthly_target_fake` | number | Yes | Demo comparison only |
| `active_flag` | boolean | Yes | Supports filtering |

### `advisors`

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `advisor_id` | string | Yes | Synthetic advisor ID |
| `advisor_name_fake` | string | Yes | Synthetic name |
| `branch_id` | string | Yes | Branch ownership |
| `role_fake` | enum | Yes | Advisor, senior advisor, branch lead |
| `start_date_fake` | date | No | Demo tenure context |
| `monthly_target_fake` | number | Yes | Result ranking context |
| `active_flag` | boolean | Yes | Supports filters |

### `sources`

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `source_id` | string | Yes | Synthetic source ID |
| `source_name` | string | Yes | Walk-in, Instagram, referral, website, event, corporate, reactivation |
| `channel_type` | enum | Yes | Organic, paid, referral, event, corporate |
| `campaign_name_fake` | string/null | No | Fake campaign label |
| `campaign_cost_fake` | number/null | Later | Campaign ROI proxy only |
| `active_flag` | boolean | Yes | Supports filters |

### `leads`

| Field | Type | Required | Supports |
| --- | --- | --- | --- |
| `lead_id` | string | Yes | All lead widgets |
| `lead_name_fake` | string | Yes | Demo table display |
| `branch_id` | string | Yes | Branch comparison |
| `owner_advisor_id` | string | Yes | Advisor rankings and queues |
| `source_id` | string | Yes | Source/channel performance |
| `created_at` | datetime | Yes | Daily/weekly and response-time metrics |
| `status` | enum | Yes | Status distribution and funnel |
| `lead_temperature` | enum | Yes | Risk prioritization |
| `estimated_membership_value` | number | Yes | Cash/recovery estimates |
| `last_activity_at` | datetime/null | Yes | Stuck opportunities |
| `next_follow_up_at` | datetime/null | Yes | Pending/overdue detection |
| `first_contact_at` | datetime/null | Phase 2 | Response time |
| `visit_scheduled_at` | datetime/null | Yes | Funnel conversion |
| `visit_completed_at` | datetime/null | Yes | Stuck after visit |
| `converted_at` | datetime/null | Yes | Result ranking |
| `lost_at` | datetime/null | Yes | Outcome indicators |
| `lost_reason` | string/null | Phase 2 | Lost reason distribution |
| `risk_reason` | string/null | Yes | Manager prompts |

Allowed `status` values:

- `new`
- `contacted`
- `interested`
- `visit_scheduled`
- `visited`
- `converted`
- `lost`

Allowed `lead_temperature` values:

- `hot`
- `warm`
- `cold`

### `activities`

| Field | Type | Required | Supports |
| --- | --- | --- | --- |
| `activity_id` | string | Yes | Activity events |
| `lead_id` | string | Yes | Lead drilldown |
| `advisor_id` | string | Yes | Advisor activity ranking |
| `branch_id` | string | Yes | Branch activity |
| `source_id` | string | No | Source activity |
| `activity_at` | datetime | Yes | Daily/weekly activity |
| `activity_type` | enum | Yes | Activity mix |
| `activity_outcome` | enum | Yes | Contact quality |
| `meaningful_activity_flag` | boolean | Yes | Ranking quality |

Allowed `activity_type` values:

- `call`
- `message`
- `note`
- `visit_scheduled`
- `visit_completed`
- `follow_up_completed`
- `status_change`

Allowed `activity_outcome` values:

- `reached`
- `no_answer`
- `scheduled_visit`
- `completed_visit`
- `no_show`
- `converted`
- `lost`
- `note_only`

### `follow_ups`

| Field | Type | Required | Supports |
| --- | --- | --- | --- |
| `follow_up_id` | string | Yes | Follow-up queue |
| `lead_id` | string | Yes | Lead relation |
| `owner_advisor_id` | string | Yes | Advisor accountability |
| `branch_id` | string | Yes | Branch comparison |
| `due_at` | datetime | Yes | Pending/overdue/aging |
| `completed_at` | datetime/null | Yes | Completion |
| `follow_up_status` | enum | Yes | Queue filters |
| `follow_up_type` | enum | Yes | Action context |
| `overdue_hours` | number | Yes | Aging |
| `aging_bucket` | enum | Yes | Aging widget |
| `risk_reason` | string/null | Yes | Action prompts |

Allowed `follow_up_status` values:

- `pending`
- `completed`
- `overdue`
- `canceled`

Allowed `aging_bucket` values:

- `due_today`
- `1_day_late`
- `2_3_days_late`
- `4_7_days_late`
- `8_plus_days_late`

Allowed `follow_up_type` values:

- `call`
- `message`
- `visit_reminder`
- `price_objection`
- `closing`
- `reactivation`

### `status_events`

| Field | Type | Required | Supports |
| --- | --- | --- | --- |
| `status_event_id` | string | Yes | Funnel history |
| `lead_id` | string | Yes | Lead relation |
| `from_status` | enum/null | Yes | Stage transition |
| `to_status` | enum | Yes | Stage transition |
| `changed_at` | datetime | Yes | Stage timing |
| `changed_by_advisor_id` | string/null | No | Advisor context |

### `dashboard_assumptions`

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `average_membership_value_fake` | number | Yes | Pipeline/recovery estimates |
| `hot_recovery_probability_fake` | number | Yes | Suggested 0.35 |
| `warm_recovery_probability_fake` | number | Yes | Suggested 0.20 |
| `stuck_after_visit_probability_fake` | number | Yes | Suggested 0.30 |
| `cold_recovery_probability_fake` | number | Yes | Suggested 0.05 |
| `aging_probability_decay_fake` | object | Yes | Lowers probability by aging bucket |
| `currency_label_fake` | string | Yes | Demo display only |

## 5. Required Scenario Distribution

The fake data should intentionally show contrast:

- One top-performing branch with balanced activity and conversion.
- One high-volume branch with weak follow-up discipline.
- One low-volume branch with strong conversion.
- One branch with strong source quality but advisor backlog.
- At least 5 top advisors with strong activity and results.
- At least 5 high-activity/low-conversion advisors.
- At least 5 low-activity advisors.
- At least 5 advisors with high overdue follow-up rates.
- At least 3 sources with high volume but weak conversion.
- At least 3 sources with lower volume but strong conversion.
- At least 100 hot leads with overdue or stuck risk.
- At least 50 visited leads with no outcome after 2 days.

## 6. Metric Coverage Matrix

| Metric/widget | Required fake entities | Notes |
| --- | --- | --- |
| Advisor activity ranking | `advisors`, `activities` | Needs meaningful vs low-value activities |
| Advisor result ranking | `advisors`, `leads`, `status_events` | Needs converted/lost distribution |
| Pending follow-ups | `follow_ups`, `leads`, `advisors` | Needs due dates across today/week |
| Overdue follow-ups | `follow_ups`, `leads`, `advisors` | Needs overdue hours and temperatures |
| Follow-up aging | `follow_ups` | Needs aging buckets |
| Status distribution | `leads`, `status_events` | Needs current status and history |
| Branch comparison | `branches`, `advisors`, `leads`, `follow_ups`, `activities` | Needs enough records per branch |
| Source/channel performance | `sources`, `leads`, `status_events` | Needs mixed source quality |
| Daily/weekly activity | `activities` | Needs activity dates across demo period |
| Stuck opportunities | `leads`, `activities`, `follow_ups`, `status_events` | Needs no-next-step and no-movement examples |
| Conversion indicators | `leads`, `status_events` | Needs stage timestamps |
| Recovered opportunity estimate | `leads`, `follow_ups`, `dashboard_assumptions` | Needs fake value and probability |
| Manager action prompts | All entities | Generated from risk conditions |

## 7. Fake Recovery Estimate Rules

Use clearly fake assumptions:

```text
base_recoverable_value =
  sum(estimated_membership_value for overdue_or_stuck_leads)

estimated_recovered_opportunity =
  sum(estimated_membership_value * recovery_probability_fake per lead)
```

Recommended probabilities:

- Hot overdue lead: 35%.
- Warm overdue lead: 20%.
- Stuck after visit: 30%.
- Cold overdue lead: 5%.

Recommended aging decay:

- Due today: no decay.
- 1 day late: multiply probability by 0.85.
- 2-3 days late: multiply probability by 0.65.
- 4-7 days late: multiply probability by 0.40.
- 8+ days late: multiply probability by 0.20.

Every dashboard display must label this as fake/demo estimation.

## 8. Data Safety Rules

- Use synthetic IDs only: `advisor_demo_001`, `lead_demo_0001`, `branch_demo_01`.
- Use synthetic names only.
- Do not use real phone numbers, emails, chat IDs, payment IDs, member IDs, or personal identifiers.
- Do not use real PowerClub branch/advisor/member lists.
- Do not use real WhatsApp text or screenshots.
- Do not connect to backend services.
- Do not write to `clients/**`.
- Do not use production config, OAuth, tokens, or systemd.

## 9. Future Fixture Acceptance Criteria

When a future lane creates actual fake fixture files, the dataset passes if:

- It contains 50+ advisors.
- It contains 1,500 to 2,000 monthly lead/opportunity records.
- It supports every MVP widget in the executive dashboard requirements.
- It creates believable ranking variance across advisors, branches, and sources.
- It includes enough overdue/stuck records for recovery estimates.
- It includes clear fake-data labels in any visible UI.
- It contains no real PowerClub/client data.
