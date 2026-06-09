# VAL-AIOPS-DEMO-01D - Voice Lite Wow Layer

## Purpose

Add a lightweight Voice Lite layer to the static Val AI Ops Discovery stage so Frank can trigger short, polished spoken moments during a business diagnostic demo.

This is demo polish only. It is not a voice backend, avatar, full duplex voice system, local LLM lane, runtime Telegram change, memory feature, persistence feature, or production deployment.

## Candidate Chosen

Candidate chosen: browser-native text-to-speech only, using `speechSynthesis` and `SpeechSynthesisUtterance` when available.

Speech input is intentionally skipped in this lane. The demo does not need microphone permission, and avoiding speech recognition keeps the stage safer, simpler, and more reliable for meetings.

## Stage Location

Open directly in a browser:

```text
docs/demo/aiops_discovery/index.html
```

## Voice Controls Added

The stage now includes a small `Voice Lite` panel with:

- Speak Intro.
- Speak First Question.
- Speak Opportunity Summary.
- Speak Pilot Recommendation.
- Stop Voice.

Voice does not autoplay. Frank must click a button.

## Required Spoken Moments

Intro:

```text
Perfecto, Boss. Estamos iniciando un diagnóstico AI Ops para Carlos. Carlos, un gusto. Te haré unas preguntas cortas para entender cómo opera tu negocio, dónde se pierde tiempo y qué proceso tendría más sentido automatizar primero.
```

First question:

```text
Primera pregunta: ¿qué tipo de negocio tienes y por dónde llegan normalmente tus clientes o leads?
```

Opportunity summary:

```text
Estoy viendo posibles oportunidades en captura de leads, seguimiento manual y visibilidad del estado de cada oportunidad.
```

Pilot recommendation:

```text
Mi recomendación inicial es empezar con un piloto pequeño: seguimiento de leads y recordatorios de próxima acción. Es medible, útil y no promete automatizar todo desde el primer día.
```

## TTS Behavior

When the browser supports Web Speech text-to-speech:

- Clicking a voice button cancels any current utterance.
- Val speaks the selected short line.
- Status changes to `Speaking...` while speech is active.
- Status returns to `Voice ready` when speech ends.
- `Stop Voice` cancels speech and sets status to `Stopped`.

## Graceful Fallback

If the browser does not support text-to-speech:

```text
Voice not supported in this browser
```

The rest of the static stage still works.

## Commercial Boundaries

- Voice supports the meeting; it does not dominate it.
- No autoplay.
- No microphone permission.
- No external voice service.
- No network calls.
- No real LLM calls.
- No fake autonomy.
- No professional replacement claims.
- No visible provider branding.

## Implementation Scope

Files touched:

- `docs/demo/aiops_discovery/index.html`
- `docs/demo/aiops_discovery/styles.css`
- `docs/demo/aiops_discovery/app.js`
- `scripts/quality/aiops_demo_voice_lite_smoke.py`

No runtime files, client files, database files, OAuth/systemd/config, Telegram routes, or memory code are touched.

## Smoke Behavior

The smoke verifies:

- Voice Lite controls exist.
- Required voice phrases exist in static files.
- Stop Voice exists.
- Voice status strings exist.
- No provider branding appears in the visible static stage.
- No network-call markers are present.
- Protected live data is not staged.
