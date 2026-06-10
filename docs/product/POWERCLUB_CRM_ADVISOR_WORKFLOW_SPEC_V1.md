# PowerClub CRM Advisor Workflow Spec V1

## Purpose

This spec defines the advisor/operator side of the PowerClub CRM pilot demo. The executive dashboard gives management visibility; the advisor workflow gives the daily user a simple queue, quick actions, and a personal progress view.

This is a pilot/demo concept using synthetic data only. It is not a final production CRM, does not connect to real PowerClub data, does not automate WhatsApp, and does not add backend behavior in this lane.

## Product Framing

The advisor experience should answer one practical question: "Who should I contact next, what should I do, and how do I record the result quickly?"

The interface should feel helpful, not punitive. Advisors should see their own progress and next work, not a peer leaderboard by default. Peer comparison can be evaluated later only if leadership explicitly requests it and the coaching culture supports it.

## Mobile-First Layout

The mobile-first layout should prioritize one active client at a time:

1. Advisor selector or assigned advisor context.
2. "Next client" card with name, branch, priority, interest, last contact, and next follow-up.
3. Manual action buttons: Call and WhatsApp manual.
4. Quick outcome buttons.
5. Fast note field.
6. Next follow-up date/time.
7. Save and next.
8. "Mi progreso" card below or above the queue depending on screen height.

Mobile screens should avoid dense tables, manager charts, peer rankings, and long forms. The advisor should be able to complete the common workflow with one thumb and minimal scrolling.

## Desktop-Friendly Layout

On desktop, the same workflow can sit beside the assigned client list:

- Left column: advisor selector, personal progress, next-client queue, filters, assigned client list.
- Right column: selected client detail, editable follow-up form, status buttons, notes, context, and history.

Desktop should not become a manager dashboard. It remains an execution surface for daily follow-up.

## Next-Client Queue

The queue should sort conceptually by:

- Overdue follow-ups first.
- Today's follow-ups next.
- High-priority opportunities.
- Promises of purchase requiring confirmation.
- Recent inbound interest.

Phase 1 can show a simple fake queue and selected current client. Real queue rules must be finalized during discovery and scope freeze.

## Client Summary Card

The current client card should show only the minimum useful context:

- Client/prospect display name.
- Branch.
- Advisor.
- Interest type.
- Priority.
- Current management status.
- Last contact.
- Next follow-up.
- Plan offered or relevant offer.
- Short context note.

Do not overload the card with every field from the database or import file.

## Manual Action Buttons

Phase 1 should show the actions as manual/conceptual:

- Call button: indicates the advisor should call the client manually.
- WhatsApp button: indicates the advisor may use the existing manual WhatsApp workflow.

This lane does not include real call integration, WhatsApp automation, message sending, templates, or communication logs.

## Quick Outcome Buttons

The advisor should be able to record the result quickly:

- No respondió
- Interesado
- Promesa de compra
- Compró
- Reagendar
- No interesado

These buttons should update the visible management status in the demo. Final status definitions and reporting mapping must be confirmed with PowerClub during discovery.

## Fast Notes

The note field should be short and fast:

- One text area.
- No required long narrative.
- Useful placeholders or examples if needed.
- Save with the current client and move to the next.

The goal is continuity: another advisor or manager should understand what happened without reading a long essay.

## Dictation Guidance

Phase 1 should rely on native device tools:

- Windows users can use native dictation, such as `Win+H`.
- Mobile users can use the keyboard microphone when available.
- No custom speech-to-text is included in phase 1.

Custom transcription, AI note cleanup, or voice commands can be considered later only if the pilot proves the need and the data/privacy rules are approved.

## Follow-Up Scheduling

The advisor should be able to set:

- Next follow-up date.
- Next follow-up time in later phases if PowerClub wants time-based queueing.
- Next action text.

The demo can show date-only scheduling. Time slots, reminders, and calendar-style behavior should be scoped separately.

## Save And Next

The primary action should be "Guardar y siguiente":

- Save the selected outcome.
- Save the quick note.
- Save the next follow-up date/time.
- Move to the next client in the advisor's queue.

The demo can simulate this in the browser only. A real implementation needs approved storage, field definitions, and user permissions.

## Minimal Required Fields

Recommended minimum fields for phase 1:

- Record ID.
- Client/prospect display name.
- Branch.
- Assigned advisor.
- Phone/contact channel indicator.
- Lead/source channel.
- Interest type.
- Management status.
- Member/prospect status.
- Priority.
- Last contact date.
- Next follow-up date.
- Next action.
- Offered plan.
- Management note.
- Outcome timestamp in a real implementation.

Avoid making too many fields mandatory. Too many required fields will slow advisors down and reduce adoption.

## Mi Progreso / Personal Performance View

The advisor should see a simple personal view, not a heavy manager dashboard:

- My follow-ups completed today.
- My pending follow-ups.
- My overdue follow-ups.
- My conversion rate.
- My closed sales.
- My promises to buy.
- My daily contact rhythm.
- My progress toward goal.

Friendly status examples:

- Vas bien.
- Atento a seguimientos atrasados.
- Necesitas subir ritmo hoy.
- Buen avance, sigue así.

This view should help the advisor self-correct during the day. It should not default to peer ranking or branch leaderboard behavior.

## Advisor Friction Risks

Risks to manage:

- Too many mandatory fields.
- Too much manager language in the advisor view.
- Peer ranking that feels punitive.
- Slow workflow after every call.
- Duplicate entry if advisors still need to update spreadsheets separately.
- Confusion between member status and management status.
- Promising automated messaging before the pilot has approved rules.
- Making advisors search instead of giving them the next recommended client.

## What Not To Overload

Do not overload phase 1 with:

- Full manager analytics.
- Peer comparison leaderboard in the advisor view.
- Real WhatsApp automation.
- Payment integration.
- Custom mobile app.
- Custom speech-to-text.
- Full configurable workflow builder.
- Unlimited statuses or reports.
- Production SLA claims.

## MVP vs Phase 2 vs Later

MVP:

- Assigned advisor queue.
- Current client card.
- Manual call and WhatsApp action indicators.
- Quick outcome buttons.
- Fast notes.
- Next follow-up date.
- Save and next.
- Simple "Mi progreso" card.
- Synthetic-data demo only.

Phase 2:

- Approved real fields and imports.
- Time-based follow-up scheduling.
- Manager-approved status taxonomy.
- Basic reminder rules.
- Better queue prioritization.
- Optional team/branch comparison if leadership wants it.
- Advisor coaching prompts based on approved formulas.

Later:

- Approved communication integrations.
- AI note cleanup or summary assist.
- Voice input enhancements beyond native device dictation.
- Advanced role permissions.
- Production reporting pipeline.
- Mobile app if browser/mobile web is not enough.

## Battle Stage Prototype Notes

The static demo can safely include:

- Fake next-client queue.
- Current client card.
- Large manual action buttons.
- Quick outcome buttons.
- Notes box.
- Follow-up date.
- Save and next.
- "Mi progreso" mini card.

All data remains fake and synthetic. The prototype should explicitly avoid implying real calls, real WhatsApp automation, backend persistence, or final production behavior.
