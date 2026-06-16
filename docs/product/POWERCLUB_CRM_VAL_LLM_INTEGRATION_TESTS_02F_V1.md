# PowerClub CRM Battle 02F - Val LLM Integration Tests

## Purpose

Document automated and manual validation for the controlled Val Mentor backend-ready seam.

The current lane uses a safe stub/mock and frontend fallback. It does not call a real LLM.

## Automated Smoke

Command:

```bash
python3 scripts/quality/powerclub_val_llm_stub_smoke.py
python3 scripts/quality/powerclub_val_demo_server_smoke.py
```

Checks:

- backend/proxy stub file exists
- missing env returns safe unavailable response
- mock env returns structured response
- response validates against required schema
- invalid demo section is rejected
- frontend contains the Operator Mode integration seam
- frontend does not expose API key env names
- local browser harness serves Val Discovery and the mock endpoint from one origin
- mock mentor endpoint returns a valid structured suggestion through the harness

## Existing Required Smokes

Also run:

```bash
python3 scripts/quality/powerclub_crm_static_demo_smoke.py
python3 scripts/quality/markdown_docs_inventory_smoke.py
git diff --check
```

## Manual Test - Backend Unavailable Fallback

1. Open `docs/demo/powerclub_crm/val_discovery.html`.
2. Switch to Operator Mode.
3. Open `Val Mentor / sugerencia controlada`.
4. Click `Sugerir con Val` without running the stub.
5. Expected:
   - no crash
   - status shows `Modo local activo`
   - a deterministic local suggestion appears
   - `Usar sugerencia` and `Ignorar` become available

## Manual Test - Mock Response Path

1. Start the one-origin browser harness:

```bash
VAL_POWERCLUB_LLM_MOCK_ENABLED=1 python3 tools/powerclub_val_demo_server.py
```

2. Open `http://127.0.0.1:8765/val_discovery.html`.
3. Switch to Operator Mode.
4. Capture a short response in Val Discovery.
5. Click `Sugerir con Val`.
6. Accept or ignore the suggestion.
7. Expected:
   - status says mock suggestion received
   - response includes Val message, summary, follow-up, risk, and recommended demo section
   - Frank must still click `Usar sugerencia`

The older two-server path remains possible, but the combined harness is preferred because it avoids port and CORS confusion.

## Manual Test - Invalid Response Fallback

Simulate a backend response missing a required key or using an unapproved demo section.

Expected:

- frontend rejects it
- status returns to local fallback
- meeting flow remains usable

## Manual Test - Frank Approval Flow

1. Generate local or mock suggestion.
2. Click `Usar sugerencia`.
3. Expected:
   - Val says the approved suggestion
   - recommended CRM section updates
   - next suggested question updates
   - observation states Frank approved it
4. Click `Ignorar` on a new suggestion.
5. Expected:
   - pending suggestion clears
   - no whiteboard or recommendation is forced

## Manual Test - Guardrails

Confirm:

- no API key in browser
- no direct OpenAI/LLM URL in HTML
- no real PowerClub data required
- no persistence
- no recording
- no automatic whiteboard write from LLM
- deterministic local mode remains available

## Known Limitations

- Static file opening may not reach the stub endpoint without the local demo harness.
- The stub is not production auth.
- The stub does not call a real LLM.
- Provider integration, secrets, rate limits, and deployment are future scope.
- Browser fetch errors are expected when backend is not running; fallback is the success condition.

## Pass Criteria

This lane passes when:

- automated smoke passes
- frontend fallback works
- mock contract is schema-valid
- no key/secret appears in the frontend
- Frank approval remains required
- existing static demo and markdown smokes pass
