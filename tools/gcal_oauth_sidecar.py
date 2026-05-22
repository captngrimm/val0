from __future__ import annotations

"""
Val0 Google Calendar OAuth preview-only sidecar.

Phase A behavior:
- /health returns service status.
- /oauth2callback validates state and code presence.
- No Google token exchange.
- No token storage.
- No secret/code logging.
"""

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse

from core.client_gcal_oauth import render_client_oauth_callback_preview

app = FastAPI(title="Val0 GCal OAuth Sidecar", version="0.1.0-preview")


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    return "OK val0-gcal-oauth preview-only"


@app.get("/oauth2callback", response_class=PlainTextResponse)
def oauth2callback(
    state: str = Query(default=""),
    code: str | None = Query(default=None),
) -> str:
    # Never echo code. We only pass boolean presence into preview logic.
    return render_client_oauth_callback_preview(
        state=state,
        code_present=bool(code),
    )
