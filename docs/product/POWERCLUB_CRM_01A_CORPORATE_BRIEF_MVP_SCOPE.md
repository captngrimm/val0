# POWERCLUB-CRM-01A - Corporate Brief + MVP Scope

Purpose:
Client-facing pilot brief for a Power Club CRM discovery and MVP package using the Val AI Ops Stage as the consulting/demo surface.

Status:
Pilot proposal draft. This is not a production CRM contract, not a full SaaS build, and not an implementation commitment until scope, data access, users, timeline, and pricing are approved.

Data note:
This document uses only anonymous assumptions and high-level discovery facts. It does not include real member records, lead lists, exported files, private conversations, live Karen files, credentials, or operational client data.

---

## 1. Executive Summary

Power Club appears to have a clear commercial opportunity: a simpler CRM pilot focused on follow-up discipline, sales visibility, and branch-level accountability.

The business likely operates across around 10 branches, with an estimated 35-45 users/operators and approximately 1,500-2,000 records per month flowing from Excel/export sources. The current CRM or software environment appears too complex, too generic, or misaligned with the actual sales process.

The proposed phase 1 is not a full replacement CRM. It is a focused pilot that turns exported data into a practical follow-up workspace for operators/asesores and a visibility dashboard for management. The goal is to reduce lost sales and missed opportunities by making every lead/member opportunity visible, assigned, prioritized, followed up, and measurable.

Recommended first move:
Run a structured discovery meeting with Karen and the General Manager, confirm the real sales stages and branch workflow, then prepare a pilot demo using sample/dummy data in the Val AI Ops Stage.

---

## 2. Problem Summary

Current pain:
Sales opportunities are being lost because of poor follow-up, inconsistent next actions, and low visibility for managers.

Likely causes:

- Records exist in Excel/export files, but the next action is not always clear.
- Operators/asesores may not have a simple daily queue.
- Branch managers may not have a reliable view of overdue follow-ups.
- General management may see totals but not the operational reasons behind lost opportunities.
- Existing software may require too many steps or may not match how Power Club actually sells, renews, or recovers opportunities.

Business impact:

- Hot prospects cool down before follow-up.
- Renewals, reactivations, or pending sales may be missed.
- Operators may duplicate effort or work from outdated lists.
- Managers may discover problems only after the sale is already lost.
- The business lacks a shared source of truth for commercial action.

---

## 3. Current Flow Assumptions

These assumptions must be confirmed before implementation.

- Records are currently generated from Excel/export sources.
- Each branch has its own commercial activity and operators/asesores.
- Leads, members, renewals, trials, reactivations, or pending opportunities may be mixed across exports.
- Follow-up may happen through manual calls, messages, in-person branch activity, or informal tracking.
- The current system is not trusted as the daily operational workspace.
- Managers need visibility by branch, operator, status, and overdue action.
- Karen is the internal trusted contact who can help validate process reality before a GM meeting.

Anonymous sample flow:

`Export -> clean/import -> assign branch/operator -> classify status -> daily follow-up -> update outcome -> manager review -> next action or close`

---

## 4. Target Users

### General Manager

Needs a high-level view of commercial pipeline health, follow-up discipline, conversion risks, and branch performance.

### Branch Managers

Need to see what is pending, overdue, assigned, won/lost, and blocked for their branch.

### Operators / Asesores

Need a simple daily work queue: who to contact, why, by when, with what last context, and how to mark the result.

### Internal Trusted Contact

Karen can help validate the real workflow, vocabulary, decision path, and meeting readiness before broader presentation.

### Admin / Data Owner

Needs to prepare exports, import/update data, review duplicates, and maintain basic field quality during the pilot.

---

## 5. CRM MVP Scope

Phase 1 goal:
Create a simple pilot CRM workflow that makes follow-up visible and measurable without forcing the company into a heavy software migration.

Included in MVP:

- Anonymous/sample data structure for demo.
- Export-based intake model from Excel or CSV.
- Lead/opportunity list with search and filters.
- Branch and operator assignment.
- Sales/follow-up status.
- Next action date.
- Last contact result.
- Overdue follow-up visibility.
- Manager dashboard requirements.
- Basic pipeline stages.
- Pilot success metrics.
- Manual import/update process.
- Meeting-ready corporate brief and demo scope.

Primary MVP objects:

- Person/lead/member opportunity.
- Branch.
- Operator/asesor.
- Follow-up task.
- Outcome/status.
- Manager dashboard view.

Success definition:
The pilot is successful if operators can work a daily list, managers can see overdue and high-value opportunities, and leadership can identify whether follow-up discipline improves within the pilot period.

---

## 6. Suggested Data Fields

Minimum fields for phase 1:

- Record ID.
- Full name.
- Phone.
- Email, if available.
- Branch.
- Assigned operator/asesor.
- Source.
- Opportunity type.
- Current status.
- Priority.
- Created date.
- Last contact date.
- Last contact result.
- Next action date.
- Next action type.
- Notes.
- Estimated value or plan interest, if available.
- Close reason, when lost or not interested.

Suggested status values:

- New.
- Assigned.
- Contacted.
- Follow-up scheduled.
- Interested.
- Pending decision.
- Won.
- Lost.
- No response.
- Invalid/duplicate.

Suggested opportunity types:

- New membership.
- Renewal.
- Reactivation.
- Upgrade.
- Referral.
- Corporate/group lead.
- Trial follow-up.
- Other.

Data quality rules:

- No real customer data in demo materials.
- No private IDs, payment details, health data, or sensitive personal notes in phase 1.
- Duplicates should be flagged before operator assignment where possible.
- Every active record should have one owner and one next action.

---

## 7. Operator / Asesor Workflow

Daily operator workflow:

1. Open assigned queue.
2. Filter by due today, overdue, high priority, or new.
3. Review record context and last note.
4. Contact prospect/member through the existing approved manual channel.
5. Update result.
6. Set next action date or close reason.
7. Move to the next assigned record.

Operator view should answer:

- Who do I contact next?
- Why is this person in my queue?
- What happened last time?
- What status should I update?
- When should I follow up again?
- Which opportunities are overdue?

Operator guardrails:

- The system supports follow-up; it does not sell automatically.
- Phase 1 does not send WhatsApp automation.
- Phase 1 does not make autonomous decisions.
- Operators remain responsible for relationship context and final updates.

---

## 8. Manager Workflow

Daily manager workflow:

1. Review branch pipeline summary.
2. Check overdue follow-ups.
3. Identify unassigned records.
4. Review operator workload.
5. Spot stalled opportunities.
6. Ask for action on priority records.
7. Review outcomes and close reasons.

Weekly manager workflow:

- Compare branch activity and conversion.
- Review lost reasons.
- Identify records with no contact.
- Adjust assignments or follow-up cadence.
- Escalate process issues to GM.

Manager view should answer:

- Which branch has the highest follow-up risk?
- Which operators are overloaded or inactive?
- Which opportunities are aging?
- What is being lost and why?
- What changed since last week?

---

## 9. Dashboard Requirements

Phase 1 dashboard should prioritize visibility over complexity.

Core dashboard cards:

- Total active opportunities.
- New records this period.
- Due today.
- Overdue follow-ups.
- Won opportunities.
- Lost opportunities.
- No-response opportunities.
- Unassigned records.

Required filters:

- Date range.
- Branch.
- Operator/asesor.
- Status.
- Opportunity type.
- Priority.

Recommended charts/tables:

- Pipeline by status.
- Overdue follow-ups by branch.
- Operator workload.
- Outcomes by week.
- Lost reasons.
- Aging report.
- Source performance, if source data is reliable.

Pilot metrics:

- Percentage of active records with assigned owner.
- Percentage of active records with next action date.
- Overdue follow-up count.
- Contact attempt volume.
- Win/loss movement by week.
- Records closed with clear reason.

---

## 10. 30/60/90 Roadmap

### First 30 Days - Discovery + Pilot Structure

- Confirm branch workflow, user roles, and status vocabulary.
- Review sample export structure.
- Define minimum required fields.
- Build dummy/sample demo view.
- Create operator workflow and manager workflow.
- Validate dashboard requirements with Karen and GM.
- Choose one pilot branch or small user group.
- Define pilot success metrics.

### Days 31-60 - Controlled Pilot

- Run pilot with manually prepared/imported export data.
- Train pilot operators and manager.
- Monitor daily queue usage.
- Review overdue follow-ups and status updates weekly.
- Adjust fields, statuses, and dashboard filters.
- Document process gaps and data quality issues.

### Days 61-90 - Decision + Expansion Plan

- Review pilot results.
- Compare before/after follow-up visibility.
- Decide whether to continue, pause, or expand.
- Prepare branch rollout plan if successful.
- Estimate support load for 35-45 users.
- Define production requirements separately from phase 1.

---

## 11. Pilot Proposal

Recommended pilot:

- Duration: 4-6 weeks.
- Scope: 1-2 branches or one focused commercial workflow.
- Users: 5-10 initial users/operators plus one manager reviewer.
- Data: anonymized sample for demo; approved export subset for pilot only after scope confirmation.
- Process: manual import/update from Excel/CSV, no live backend integration.
- Output: simple CRM workspace specification, dashboard requirements, pilot workflow, findings report, and expansion recommendation.

Pilot goals:

- Reduce invisible or forgotten opportunities.
- Increase records with clear owner and next action.
- Give managers a reliable overdue follow-up view.
- Validate whether Power Club needs a custom lightweight CRM, a better process layer on existing tools, or a deeper implementation later.

Pilot deliverables:

- Confirmed workflow map.
- Field dictionary.
- Status model.
- Operator workflow.
- Manager workflow.
- Dashboard specification.
- Pilot metric report.
- 30/60/90 implementation recommendation.

---

## 12. Pricing Options

Pricing is illustrative and should be confirmed after discovery.

### Option A - Discovery + Demo Brief

- Scope: process discovery, sample data model, executive brief, meeting-ready demo structure.
- Suggested price: USD 750-1,500.
- Best for: validating fit before committing to a pilot.

### Option B - 4-6 Week Pilot

- Scope: discovery, pilot structure, sample/import workflow, operator/manager workflows, dashboard requirements, weekly review, final recommendation.
- Suggested price: USD 2,500-5,000 setup/project fee.
- Optional support: USD 500-1,500/month during pilot, depending on meeting cadence and user count.
- Best for: proving value with a limited branch/user group.

### Option C - Post-Pilot Expansion

- Scope: production planning, broader rollout, stronger data operations, training, support model, and possible implementation build.
- Suggested price: custom quote after pilot.
- Best for: expanding only after the pilot shows operational value.

Pricing boundary:
Phase 1 pricing does not include a full SaaS platform, payment processing, live WhatsApp automation, real-time integrations, backend engineering, or enterprise support unless separately scoped.

---

## 13. Boundaries / What Phase 1 Does NOT Include

Phase 1 does not include:

- Real Power Club data in public or demo files.
- Karen live files.
- Full SaaS product build.
- Backend implementation.
- Payment integration.
- WhatsApp automation.
- Autonomous sales decisions.
- Replacement of current staff or management judgment.
- Migration of all historical records.
- Complex permissions model.
- OAuth/token work.
- Systemd/runtime deployment.
- Broad Val0 runtime refactor.
- Real-time integration with existing CRM/software.
- Production-grade analytics warehouse.
- Legal, accounting, compliance, or regulated data processing advice.

Phase 1 is a pilot and consulting package. Production CRM scope must be separately approved after discovery.

---

## 14. Meeting Questions for Karen / GM

Questions for Karen before the GM meeting:

- What exact problem would make the GM say "this is worth trying"?
- Which branch or team would be best for a low-risk pilot?
- What words do operators actually use for leads, members, renewals, and follow-ups?
- Which export is safest to discuss structurally without exposing real data?
- What does the current software fail to show clearly?
- Who owns follow-up today?
- What is the most common reason opportunities are lost?
- What would be politically sensitive to avoid in the first meeting?
- Should the first demo be in Spanish, English, or mixed?

Questions for the General Manager:

- How many branches should be included in the first pilot?
- Which commercial workflow loses the most value today?
- What are the top 3 statuses leadership needs to see every day?
- What is the current record volume by month and branch?
- What fields exist in the Excel/export today?
- What follow-up cadence should operators follow?
- What is considered a successful contact?
- What lost reasons should be tracked?
- Who should approve field/status changes?
- What decision metric determines pilot success?

---

## 15. Next Recommended Step

Prepare a 30-45 minute discovery meeting with Karen first, then a GM-facing demo conversation.

Suggested sequence:

1. Confirm current export structure using dummy field names only.
2. Confirm branch/operator workflow and sales status vocabulary.
3. Select the safest pilot slice: one branch, one workflow, or one opportunity type.
4. Build a meeting-ready sample using anonymous records.
5. Present the pilot as a focused visibility and follow-up system, not a final production CRM.

Recommended meeting close:

```text
The first step is not to replace your CRM. The first step is to prove whether a simpler follow-up layer can recover lost opportunities and give management better visibility within a small, measurable pilot.
```
