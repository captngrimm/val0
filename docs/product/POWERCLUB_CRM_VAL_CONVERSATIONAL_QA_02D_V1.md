# PowerClub CRM Battle 02D - Val Conversational Intro + Safe Q&A Capsule

## Purpose

This lane adds a controlled conversational layer to Val Discovery Mode so Frank can answer basic GM/Karen questions without improvising and without adding a real LLM.

The Q&A capsule is scripted, local, deterministic, and operator-assisted. It does not call OpenAI, ChatGPT, a backend, or any external service.

## What Val Can Answer

The safe Q&A capsule supports:

- Val, preséntate.
- ¿Qué puedes hacer?
- ¿Esto es parte del CRM?
- ¿Esto es ChatGPT?
- ¿Cómo ayuda a PowerClub?
- ¿Por qué Val / Valeria?
- Empecemos discovery.

If Frank types a question that does not match the local capsule, Val responds:

> Todavía no tengo esa respuesta en este modo. Frank puede tomar esa pregunta y la dejamos como pendiente.

Unknown questions are treated as pending follow-up, not as free-form AI generation.

## Presentation Mode Access

Presentation Mode now supports:

- `P` hotkey: Val introduces herself.
- `Q` hotkey: Val gives a safe Q&A/capability response.
- Radial command entries for `P` and `Q`.

This lets Frank respond to "what is this?" without opening the full operator interface.

## Operator Mode Access

Operator Mode includes a `Q&A seguro de Val` drawer with:

- quick Q&A buttons
- optional typed question input
- local keyword matching
- safe fallback to pending questions

Typed matching handles phrases such as:

- "qué eres"
- "qué puedes hacer"
- "es parte del CRM"
- "es ChatGPT"
- "cómo ayuda a PowerClub"
- "por qué Val"
- "empecemos discovery"

## ArcX / Hotkey Layer

Existing hotkeys remain:

- `V` - Val pregunta
- `C` - Confirmar respuesta
- `O` - Organizar whiteboard
- `R` - Generar resumen
- `N` - Siguiente pregunta
- `M` - Presentación / Operador
- `H` - Radial menu
- `Esc` - Cerrar radial menu

New optional hotkeys:

- `P` - Val preséntate
- `Q` - Q&A / pregunta rápida

Suggested ArcX adjustment:

- Keep the 02C.6 command mapping.
- If Frank wants a more conversational ring profile, map long press or a secondary mode to `P` and `Q`.

## Persona Boundaries

Val may sound calm, useful, and lightly warm. Val must not imply:

- she is human
- she has feelings
- she is sentient
- she knows private context unless Frank entered it
- she is fully autonomous
- she already operates PowerClub
- she is connected to real PowerClub data

Preferred framing:

> Val is an internal Isthmus Dynamics meeting cockpit in development. It helps guide discovery, structure decisions, and organize next steps.

## Why Real LLM Is Deferred

Real LLM behavior is deferred because the GM meeting needs safety, clarity, and trust before open-ended generation.

Reasons to defer:

- no API keys should exist in browser code
- client questions may touch scope, pricing, privacy, or production claims
- real data approval is not in place
- deterministic fallback is safer for a first executive meeting
- Frank should control what is said in the room

## Future LLM Upgrade Path

A future LLM version should use:

- secure backend/proxy only
- no API key in browser
- prompt capsule for PowerClub discovery
- allowed topics and explicit refusal behavior
- audit/privacy boundaries
- deterministic local fallback
- meeting-safe disclaimers

The LLM should assist with phrasing, summarization, and next-question suggestions. It should not claim autonomy, record meetings silently, or make production commitments.

## What Frank Can Say

> "Val can answer a few safe scripted questions today. This version is not using ChatGPT in the browser. We kept it controlled for the meeting. Later, if PowerClub wants a real copilot layer, we would scope that through a secure backend and approved data sources."

## What Frank Should Not Say

- "Val understands everything automatically."
- "Val is ChatGPT connected to PowerClub."
- "Val is production-ready."
- "Val is listening to the meeting."
- "Val can answer anything."

## Guardrails

- No fake LLM claims.
- No OpenAI/ChatGPT API.
- No external services.
- No backend.
- No persistence.
- No recording or audio storage.
- No real PowerClub data.
- No production promise.
- No human/AGI framing.
- Frank remains operator.
- Val Discovery Stage remains separate from the PowerClub CRM Demo.
