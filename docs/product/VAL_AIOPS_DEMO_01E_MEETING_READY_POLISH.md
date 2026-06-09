# VAL-AIOPS-DEMO-01E - Meeting-Ready Polish

## Purpose

This lane makes the static Val AI Ops Discovery stage easier to use in a live meeting: Frank can open it quickly, run the Carlos demo flow, try Voice Lite if available, continue cleanly if voice fails, and copy or print the generated Mapa IA 30/60/90.

The stage remains static/offline. There is no production runtime change, Telegram route change, DB, OAuth, systemd, memory activation, real LLM call, network call, or real client data feature.

## Candidate Chosen

Candidate chosen: keep the static stage and add lightweight browser-native meeting controls:

- Demo Mode Checklist.
- Copy Report.
- Print / Save as PDF.
- Clipboard fallback guidance.
- Voice fallback line.
- Final Frank talk track.
- Do-not-say list.

## How To Open

Open directly in a browser:

```text
docs/demo/aiops_discovery/index.html
```

No server is required.

## Carlos Demo Flow

1. Set the company field to `Carlos` or `Empresa Carlos`.
2. Click `Start Diagnostic` / `Iniciar diagnostico AI Ops`.
3. Click `Load sample notes` or paste the Carlos sample notes.
4. Click `Summarize Notes`.
5. Click `Suggest Next Question`.
6. Click `Detect Opportunities`.
7. Click `Generate Draft Map`.
8. Try `Speak Intro` or `Speak First Question` if the browser supports Voice Lite.
9. Click `Copy Report` or `Print / Save as PDF`.

## Voice Fallback Line

If voice fails, Frank can say:

```text
La voz depende del navegador; la parte importante es el diagnóstico y el mapa.
```

## Copy / Export Behavior

`Copy Report` uses `navigator.clipboard.writeText` when available.

If the browser blocks clipboard access or the clipboard API is unavailable, the stage selects the report text and shows:

```text
Clipboard blocked. Report text selected; copy it manually.
```

or:

```text
Clipboard unavailable. Report text selected; copy it manually.
```

`Print / Save as PDF` calls the browser print dialog with `window.print()`. No PDF dependency is added.

## Final Frank Talk Track

Opening:

```text
Este es un stage interno de Val AI Ops Discovery. Lo uso para estructurar diagnósticos, detectar oportunidades y producir un Mapa IA 30/60/90.
```

Transition:

```text
No estamos prometiendo automatizar todo. Primero buscamos el proceso más rentable para un piloto pequeño y medible.
```

Close:

```text
El siguiente paso sería convertir este mapa en un piloto de una semana con una métrica clara.
```

## Do Not Say

- "Esto reemplaza a tu equipo."
- "Val automatiza todo."
- "Esto es ChatGPT."
- "La IA decide sola."
- "No necesitamos revisar tus procesos."

## Report Sections To Verify

The preview and generated draft map must include:

- Executive summary.
- Current processes.
- Pain points.
- Opportunities.
- Recommended pilot.
- 30/60/90 roadmap.
- Limits / boundaries.
- Next steps.

## Boundaries

- No fake autonomy.
- No professional replacement claims.
- No visible provider branding in the static stage.
- No real client data unless manually approved.
- No hidden persistence.
- No network calls.
- No real LLM calls.
- No voice backend.
- No full SaaS.

## Meeting-Ready Notes

Keep the demo simple. The point is not to show every possible feature. The point is to show that Val can structure a business conversation, identify a useful first pilot, and produce a concrete 30/60/90 map that leads naturally to a paid diagnostic or one-week pilot.
