# PowerClub CRM Battle 02F.1 - Val LLM Browser Test Harness

## Purpose

Create a safe one-origin browser test path for Val Discovery so Frank can test `Sugerir con Val` against the mock backend without CORS, split ports, or static-file confusion.

This is a local test harness only. It is not a production service, does not call a real LLM, does not store data, and does not require API keys.

## Harness File

`tools/powerclub_val_demo_server.py`

The harness:

- serves static files from `docs/demo/powerclub_crm`
- serves `/index.html`
- serves `/val_discovery.html`
- handles `/powerclub/val/mentor-suggest` with the existing safe stub logic
- handles `/health` and `/powerclub/val/health`
- requires `VAL_POWERCLUB_LLM_MOCK_ENABLED=1` to return mock suggestions
- returns safe fallback/unavailable behavior if mock mode is disabled

## Start Command

From the repo root:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

Default local origin:

`http://127.0.0.1:8765`

Optional port override:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 VAL_POWERCLUB_DEMO_SERVER_PORT=8766 python3 tools/powerclub_val_demo_server.py
```

## URLs To Open

Main CRM demo:

`http://127.0.0.1:8765/index.html`

Val Discovery Stage:

`http://127.0.0.1:8765/val_discovery.html`

Health check:

`http://127.0.0.1:8765/powerclub/val/health`

## Browser Test Steps

1. Start the harness with mock mode enabled.
2. Open `http://127.0.0.1:8765/val_discovery.html`.
3. Switch to Operator Mode.
4. Confirm the Val Mentor drawer exists: `Val Mentor / sugerencia controlada`.
5. Type or capture a short response, for example:
   `El seguimiento llega tarde y las oportunidades se enfrían.`
6. Optional: select the category `Seguimiento`.
7. Click `Sugerir con Val`.
8. Expected:
   - the request reaches the same-origin mock endpoint
   - status indicates mock suggestion or controlled suggestion received
   - `Sugerencia de Val` shows a structured recommendation
   - `Usar y organizar` and `Ignorar` become available
9. Click `Usar y organizar`.
10. Expected:
    - Val updates the visible message
    - the recommended demo section updates
    - Frank remains in control
    - nothing is persisted
11. Repeat and click `Ignorar`.
12. Expected:
    - pending suggestion clears
    - no whiteboard or recommendation is forced

## Backend Unavailable Fallback Test

Start without mock mode:

```bash
python3 tools/powerclub_val_demo_server.py
```

Then open Val Discovery and click `Sugerir con Val`.

Expected:

- no crash
- UI falls back to deterministic local mode
- status shows local fallback / `Modo local activo`
- Frank can continue the meeting

## How To Stop

In the terminal running the harness:

`Ctrl+C`

## Automated Smoke

Run:

```bash
python3 scripts/quality/powerclub_val_demo_server_smoke.py
```

The smoke starts the harness on an ephemeral local port, checks health, serves `val_discovery.html`, posts a mock mentor request, validates the response, and shuts the server down.

## Security Boundaries

- no real API keys
- no frontend secrets
- no external LLM call
- no OpenAI browser call
- no persistence
- no database
- no real PowerClub data
- no recording
- no production service
- no systemd
- mock/test only
- deterministic fallback remains available

## Known Limitations

- This harness is for local browser testing only.
- It does not implement auth, rate limiting, deployment, logging policy, or provider integration.
- Mock responses are deterministic scaffolding, not real AI.
- A future controlled LLM lane must add a real backend/proxy, server-side prompt capsule, provider secret management, schema validation, and QA.

## Pass Criteria

This lane passes when:

- Frank can open Val Discovery from the same origin as the mock endpoint
- `Sugerir con Val` reaches `/powerclub/val/mentor-suggest`
- Frank can accept or ignore the mock suggestion
- fallback works when mock mode is disabled
- automated smokes pass
- no production/runtime service is changed
