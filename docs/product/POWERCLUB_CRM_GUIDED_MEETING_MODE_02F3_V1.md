# PowerClub CRM Battle 02F.3 - Guided Meeting Mode

## Orchestrator Decision

POWERCLUB 02F.3 is approved.

This lane promotes Val Discovery from an operator cockpit toward a guided meeting flow for Karen/GM review.

## Before / After UX Problem

Before:

- too many panels competed for Frank's attention
- Val Mentor worked technically, but felt like another drawer
- Frank needed to understand where to click next
- the GM-facing experience risked looking like an engineering cockpit

After:

- the page guides Frank through one primary action per state
- Presentation Mode hides technical controls and backend/mock language
- Operator Mode still keeps advanced tools available
- Frank remains the operator and approver
- Val feels more like a meeting guide, not a panel waiting for commands

## Guided Meeting Flow

Approved flow:

1. Val asks.
2. Client answers.
3. Frank captures.
4. Val suggests.
5. Frank approves.
6. Val organizes.
7. Val recommends what to show.
8. Frank advances.

The screen is organized around three meeting zones:

- `VAL DICE`: current Val message and discovery framing
- `RESPUESTA DEL CLIENTE`: response capture plus one dominant primary action
- `QUÉ HAGO AHORA`: one bold instruction for Frank

## Guided State Machine

| State | Instruction | Primary action | ArcX center action |
| --- | --- | --- | --- |
| `ask` | Haz esta pregunta. | Val pregunta | Ask current question |
| `capture` | Escribe o dicta la respuesta. | Capturar respuesta | Focus/capture response |
| `suggest` | Pide sugerencia a Val. | Sugerir con Val | Request controlled suggestion |
| `review` | Revisa y usa/ignora la sugerencia. | Usar y organizar | Approve and organize |
| `organize` | Organiza manualmente si hace falta. | Organizar en whiteboard | Place captured signal |
| `recommend` | Muestra la recomendación o avanza. | Mostrar recomendación / avanzar | Advance safely |
| `close` | Revisa o copia el resumen. | Generar resumen | Generate/show local summary |

The page keeps legacy internal states such as `intro`, `confirm`, and `summary` for compatibility, but the GM flow should be explained with the states above.

## Primary Action Rules

- One button is visually dominant for the current state.
- Secondary actions remain smaller: `Editar`, `Ignorar`, `Avanzado`.
- Frank must approve before Val organizes a suggestion.
- The UI should never imply that Val autonomously decides, commits scope, or operates PowerClub.
- If the mock/backend is unavailable, the flow falls back to deterministic local behavior.

## After Approval

After `Usar y organizar`, the screen shows a clear success block:

`Listo. Val organizó la respuesta como Seguimiento. Demo recomendado: Riesgo y rescate. Siguiente pregunta: ¿Cuántas oportunidades se enfrían por falta de contacto a tiempo?`

Then the primary action becomes:

`Mostrar recomendación / avanzar`

## ArcX Alignment

ArcX remains contextual:

- Center / `NumpadEnter`: current primary action
- Right / `Numpad6`: advance only when safe
- Left / `Numpad4`: correct / safe step back
- Up / `Numpad8`: rephrase
- Down / `Numpad2`: summary / close

The center action now follows the same state as the visible primary button.

## Presentation Mode vs Operator Mode

Presentation Mode:

- intended for the GM-facing meeting
- keeps the guided flow visible
- hides debug, STT, voice tuning, backend/mock explanations, and technical controls
- uses client-safe wording: Val Discovery, reunión guiada, señales detectadas, recomendación, siguiente paso

Operator Mode:

- keeps advanced tools available for Frank
- includes categories, capture advanced, safe Q&A, voice fallback, ArcX debug, and guardrails
- keeps Val Mentor / guided meeting as the default open flow

## Browser Test Script

Start the local harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

`http://127.0.0.1:8765/val_discovery.html`

For Frank's public test host, use the active harness URL:

`http://167.172.239.59:8767/val_discovery.html`

Test:

1. Start in Presentation Mode.
2. Click the dominant primary action to have Val ask.
3. Type a client response, for example:
   `El seguimiento llega tarde y las oportunidades se enfrían.`
4. Click the dominant primary action to capture.
5. Click the dominant primary action to request Val suggestion.
6. Confirm the screen shows review state.
7. Click `Usar y organizar`.
8. Confirm:
   - whiteboard receives a card
   - success block appears
   - recommended demo section is visible
   - primary action becomes `Mostrar recomendación / avanzar`
9. Press right / `Numpad6` or click the primary action to advance.
10. Switch to Operator Mode only if advanced tools are needed.

## Known Limitations

- The suggestion path is still mock/local deterministic unless a safe backend is separately scoped.
- Browser voice and STT are not part of this lane.
- No real PowerClub data is connected.
- No persistence or recording exists.
- Browser QA still depends on Frank's actual machine and the active harness URL.

## What Not To Do Yet

- Do not connect a real LLM provider.
- Do not add avatar or voice implementation.
- Do not expose backend/API/mock complexity in the GM-facing flow.
- Do not add API keys to the browser.
- Do not add persistence, auth, systemd, or production service behavior.
- Do not imply Val is autonomous, human, or production-ready.
