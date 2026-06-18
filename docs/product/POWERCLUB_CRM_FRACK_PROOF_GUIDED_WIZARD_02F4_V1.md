# PowerClub CRM Battle 02F.4 - Frack-Proof Guided Wizard

## Why 02F.3 Still Failed Browser UX

02F.3 added a state-driven primary action, but the page still exposed too much cockpit structure.

Frank could still see or copy too many competing sections:

- setup
- Val presence
- ring and audio controls
- raw action buttons
- Val Mentor drawer
- Discovery guiado
- categories
- capture advanced
- observations
- whiteboard
- notes
- local summary

The feature worked, but it was not frack-proof. Frank still had to understand the cockpit.

## 02F.4 UX Decision

Presentation Mode is now a guided wizard first.

The top experience is one dominant card:

- one current step
- one instruction
- one working area
- one primary button
- small secondary options only when needed

The old cockpit remains available, but it is no longer the GM-facing mental model.

## Five-Step Wizard

### Step 1 - Preguntar

Instruction:

`AHORA: haz esta pregunta al cliente.`

Primary button:

`Ya pregunté / capturar respuesta`

The card shows the current Val question.

### Step 2 - Capturar

Instruction:

`AHORA: escribe o dicta lo que respondió el cliente.`

Primary button:

`Capturar respuesta`

The card shows one response textarea.

### Step 3 - Sugerir

Instruction:

`AHORA: pide sugerencia a Val.`

Primary button:

`Sugerir con Val`

The card shows the captured response and detected category indirectly through the Val suggestion flow.

### Step 4 - Aprobar y organizar

Instruction:

`AHORA: revisa. Si está bien, usa y organiza.`

Primary button:

`Usar y organizar`

Secondary:

- `Ignorar`
- `Editar`

Frank approval remains required.

### Step 5 - Recomendar / avanzar

Instruction:

`AHORA: muestra la sección recomendada o avanza.`

Primary button:

`Mostrar recomendación / avanzar`

The card shows the organized result:

`Listo. Val organizó la respuesta como Seguimiento. Demo recomendado: Riesgo y rescate. Siguiente pregunta: ...`

## One-Primary-Button Rule

The wizard should always answer:

`What do I click now?`

There is one dominant primary button per state.

Secondary buttons remain visually smaller:

- Editar
- Ignorar
- Avanzado / cockpit

## Hidden Advanced Cockpit

Presentation Mode hides cockpit complexity by default:

- setup fields
- agenda
- usage notes
- guardrails
- Q&A seguro
- voice/audio controls
- ring toggle/debug
- categories
- capture advanced
- raw notes/decisions/risks
- full whiteboard
- technical mock/backend status

Operator Mode can still reveal these tools.

## ArcX Mapping

ArcX remains contextual:

- Center / `NumpadEnter`: primary button of the current wizard step
- Right / `Numpad6`: advance only when safe
- Left / `Numpad4`: correct / safe step back
- Up / `Numpad8`: rephrase current question
- Down / `Numpad2`: summary / close

The visible hint is:

`Centro = botón principal · → avanzar · ← corregir · ↑ reformular · ↓ resumen`

## Browser QA Checklist

Start harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Open:

`http://127.0.0.1:8765/val_discovery.html`

Public harness when active:

`http://167.172.239.59:8767/val_discovery.html`

Check:

- Presentation Mode starts with one dominant wizard card.
- No setup/audio/debug/backend language dominates the page.
- Step 1 shows `PASO 1 DE 5`.
- Primary button says `Ya pregunté / capturar respuesta`.
- Step 2 shows one response textarea.
- Step 3 primary button says `Sugerir con Val`.
- Step 4 primary button says `Usar y organizar`.
- Step 5 shows the organized result and recommended demo section.
- `Avanzado / cockpit` switches to Operator Mode for deeper tools.
- Browser harness still reaches `/powerclub/val/mentor-suggest`.

## Remaining Limitations

- No real LLM provider.
- No avatar.
- No voice implementation.
- No persistence.
- No real PowerClub data.
- No production service.
- No systemd or deployment change.
- Frank remains operator and approver.

## Do Not Do Yet

- Do not add API keys.
- Do not call external LLMs from the browser.
- Do not add real STT/recording.
- Do not promise production CRM behavior.
- Do not expose technical cockpit controls as the GM-facing flow.
