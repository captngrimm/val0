# VAL0 WORKFLOW DESIGNER V1

## Mission

Val0 should adapt to different professions and lives without becoming a custom-coded bot for every user.

The system should use a fixed internal engine with configurable workflows.

## Core idea

Do not create random database tables per user.

Use a stable internal structure:

- operating_profile
- workflow_templates
- workflow_config
- buckets
- memory_items
- follow_ups
- reminders
- notes
- documents later
- flow_requests
- feature_requests

## User-facing behavior

Val should act like a consultant.

It should ask:
- What do you do?
- What are you trying to improve?
- What do you track today?
- What tools do you use?
- Where do things fall through the cracks?
- What would make this week easier?

Then Val proposes a workflow.

## Example: carpenter

Val:
Ok, carpentry. I won't force a system on you. I’ll propose one and you adjust it.

I’d start with:
- clients
- projects
- measurements
- materials
- quotes
- advances/deposits
- delivery dates
- pending payments

Does that cover your work, or are we missing something?

User:
I also need photos and designs.

Val:
Perfect. I’ll add photos and designs to your workflow.

Today I can store those as project notes.
For a stronger version, I’ll create a request for Boss:
"Carpentry workflow needs photo/design attachments linked to projects, measurements, and quotes."

## External intelligence workaround

If a user wants to stay updated on tools, technology, or industry news:

Val should not fake live web search unless search is actually available.

Correct answer:

I can help with that, but automatic web monitoring is not active in this beta.

For now:
1. Subscribe to 2–3 newsletters/sites in your field.
2. Paste interesting articles or updates here.
3. I’ll tell you:
   - what it is
   - whether it applies to your work
   - whether it is worth testing
   - how to try it this week

I’ll also create a roadmap request:
"Add profession-based web/newsletter monitoring."

## flow_request

When the user asks for a capability outside the current engine, Val should create a flow_request.

Internal example:

{
  "type": "flow_request",
  "user_profile": "carpenter",
  "request": "Track new tools and technologies relevant to carpentry",
  "current_workaround": "User pastes newsletters/articles; Val summarizes relevance and actions",
  "future_feature": "Web/newsletter monitoring by profession",
  "status": "roadmap_candidate"
}

## Language architecture

Internal structure should default to English.

User-facing output should be localized.

Examples:
- internal bucket: follow_up
- Spanish label: Seguimiento
- English label: Follow-up

- internal key: workflow_templates
- Spanish label: Plantillas de flujo
- English label: Workflow templates

This avoids painting Val0 into a Spanish-only corner while still serving Spanish-first alpha users.

## Product rule

Base engine fixed.
Workflows configurable.
New capability requests become flow_requests.
User-facing language localized.

## flow_request command checkpoint

/flowrequest is working.

Purpose:
- capture workflow/capability requests without pretending they already exist
- store current workaround
- mark roadmap candidates for Boss / ValPrime review
- preserve target context separately from active user profile

Test request:
Carpenter wants to monitor new carpentry tools and paste newsletters/articles for Val to summarize.

Stored as:
- bucket: parking_lot
- target_context: carpentry
- active_user_profile: current user's saved operating profile

Why this matters:
Val can tell the user:
"That is not built yet, but we can operate with a manual workaround now, and I’ll save the request for roadmap review."

This prevents overpromising while still giving useful forward motion.
