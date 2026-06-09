# VAL-AIOPS-DEMO-01B - Static Stage and Mock Report Renderer

## Purpose

This lane creates the first browser-visible Val AI Ops Discovery stage for founder-beta sales and diagnostic meetings. It is a local/static demo artifact, not a production app.

The goal is to let Frank show a professional Val-branded diagnostic surface instead of exposing a generic chat interface.

## Candidate Chosen

Candidate chosen: static branded web stage under `docs/demo/aiops_discovery/` plus a tiny pure Markdown report renderer in `core/aiops_report.py`.

This keeps the demo fast, inspectable, and offline-friendly while leaving runtime Telegram, persistence, memory, DB, OAuth, and production config untouched.

## Stage Location

Open:

```text
docs/demo/aiops_discovery/index.html
```

The stage includes:

- Branded header: Val AI Ops Discovery.
- Report framing: Mapa IA 30/60/90.
- Founder-beta diagnostic stage label.
- Client/company field with sample `Empresa X`.
- Start command: `Iniciar diagnostico AI Ops`.
- Guided diagnostic question list.
- Meeting notes textarea.
- Mock operator panels.
- Draft report preview.

## Mock Interaction Behavior

The static stage works without network calls or real LLM calls.

Mock controls:

- Start Diagnostic.
- Summarize Notes.
- Suggest Next Question.
- Detect Opportunities.
- Generate Draft Map.

These controls populate sample content for a generic business. They do not save data, write files, call APIs, or touch client folders.

## Guided Diagnostic Questions

The stage shows the required discovery questions:

- Business type.
- Lead/client channels.
- Critical processes.
- Manual/repetitive work.
- Tools used.
- Where time is lost.
- Current bottleneck.
- Desired 30/60/90 outcome.

## Report Artifact

The report preview is titled:

```text
Mapa IA 30/60/90 - Empresa X
```

Required sections:

- Executive summary.
- Current processes.
- Pain points.
- Opportunities.
- Recommended pilot.
- 30/60/90 roadmap.
- Limits / boundaries.
- Next steps.

## Report Renderer Behavior

`core/aiops_report.py` provides a deterministic helper:

```text
render_aiops_map_markdown(session)
```

It accepts a dict/session-like structure and returns Markdown. It does not write files, call networks, touch client data, activate memory, or create tasks/calendar/reminders.

## Boundaries

- No full SaaS.
- No production deployment.
- No Telegram runtime change.
- No DB feature.
- No memory activation.
- No real client data.
- No Open WebUI/LibreChat.
- No real LLM calls.
- No voice in this lane.
- No hidden persistence.
- No fake autonomy.
- No professional replacement claims.

Clear framing used by the stage:

```text
Val helps structure diagnosis and pilot design.
Human confirmation required before implementation.
```

## Future Smoke Coverage

Current smokes verify the static stage and renderer. Future implementation smokes should add browser-level checks only if the stage becomes more interactive or moves into a served UI.

Keep future checks focused on:

- Required branding.
- Required diagnostic questions.
- Required report sections.
- No visible generic AI provider branding.
- No network calls.
- No DB/OAuth/systemd/config changes.
- No `clients/**` writes.
- Protected live data not staged.
