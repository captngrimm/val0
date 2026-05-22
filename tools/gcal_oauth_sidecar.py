from __future__ import annotations

"""
Val0 Google Calendar OAuth sidecar.

Safety behavior:
- /health returns service status.
- /oauth2callback validates state and code presence.
- Default mode is preview-only.
- Real token exchange only runs when VAL0_GCAL_OAUTH_EXCHANGE_ENABLED=1.
- No authorization code echo.
- No token echo.
"""

import os

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse

from core.client_gcal_oauth import (
    render_client_oauth_callback_exchange_result,
    render_client_oauth_callback_exchange_result,
)

app = FastAPI(title="Val0 GCal OAuth Sidecar", version="0.2.0")


def exchange_enabled() -> bool:
    return os.getenv("VAL0_GCAL_OAUTH_EXCHANGE_ENABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    mode = "exchange-enabled" if exchange_enabled() else "preview-only"
    return f"OK val0-gcal-oauth {mode}"


@app.get("/oauth2callback", response_class=PlainTextResponse)
def oauth2callback(
    state: str = Query(default=""),
    code: str | None = Query(default=None),
) -> str:
    # Never echo code. Preview path only receives boolean presence.
    if not exchange_enabled():
        return render_client_oauth_callback_exchange_result(
            state=state,
            code_present=bool(code),
        )

    # Exchange path receives code internally, but render/result must never echo it.
    return render_client_oauth_callback_exchange_result(
        state=state,
        code=code or "",
    )
