from __future__ import annotations

"""
Client-scoped Google Calendar read-only client.

V0 safety rules:
- Read-only only.
- Never uses legacy/global user refresh tokens.
- Reads user refresh tokens only from /etc/val0/clients/<client_id>/gcal/.
- Uses app-level OAuth client secret for token refresh.
- If client token/config is missing, returns not_connected.
- No write methods in this module.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

APP_CLIENT_SECRET_PATH = Path(
    os.getenv("VAL0_GCAL_OAUTH_CLIENT_SECRET", "/etc/val0/gcal/client_secret.json")
)


@dataclass(frozen=True)
class ClientGCalReadResult:
    status: str
    client_id: str
    calendar_id: Optional[str]
    events: List[Dict[str, Any]]
    reason: str = ""


def _safe_client_id(client_id: str) -> str:
    safe = "".join(
        ch for ch in (client_id or "").lower()
        if ch.isalnum() or ch in ("_", "-")
    ).strip()
    return safe or "unknown"


def _client_gcal_dir(client_id: str) -> Path:
    return Path("/etc/val0/clients") / _safe_client_id(client_id) / "gcal"


def get_client_gcal_paths(client_id: str) -> Dict[str, Path]:
    base = _client_gcal_dir(client_id)
    return {
        "base": base,
        # App-level OAuth client secret. User refresh tokens remain per-client.
        "client_secret": APP_CLIENT_SECRET_PATH,
        "refresh_token": base / "refresh_token",
        "calendar_id": base / "calendar_id",
    }


def client_gcal_status(client_id: str) -> Dict[str, Any]:
    paths = get_client_gcal_paths(client_id)
    missing = [
        name for name in ("client_secret", "refresh_token")
        if not paths[name].exists()
    ]

    calendar_id = None
    if paths["calendar_id"].exists():
        calendar_id = paths["calendar_id"].read_text(encoding="utf-8").strip() or None

    return {
        "client_id": _safe_client_id(client_id),
        "status": "connected" if not missing else "not_connected",
        "provider": "google_calendar",
        "mode": "read_only",
        "calendar_id": calendar_id or "primary",
        "base_path": str(paths["base"]),
        "missing": missing,
        "uses_legacy_global": False,
    }


def _load_client_creds(client_id: str) -> Credentials:
    paths = get_client_gcal_paths(client_id)

    if not paths["client_secret"].exists():
        raise FileNotFoundError(f"Missing client_secret.json for client {client_id}")
    if not paths["refresh_token"].exists():
        raise FileNotFoundError(f"Missing refresh_token for client {client_id}")

    refresh_token = paths["refresh_token"].read_text(encoding="utf-8").strip()
    data = json.loads(paths["client_secret"].read_text(encoding="utf-8"))
    web = data.get("web") or data.get("installed") or {}

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=web.get("token_uri") or "https://oauth2.googleapis.com/token",
        client_id=web.get("client_id"),
        client_secret=web.get("client_secret"),
        scopes=SCOPES,
    )


def _calendar_id(client_id: str) -> str:
    paths = get_client_gcal_paths(client_id)
    if paths["calendar_id"].exists():
        raw = paths["calendar_id"].read_text(encoding="utf-8").strip()
        if raw:
            return raw
    return "primary"


def get_client_events_between(
    client_id: str,
    start_dt: datetime,
    end_dt: datetime,
    tz: str = "America/Panama",
    limit: int = 20,
) -> ClientGCalReadResult:
    cid = _safe_client_id(client_id)
    status = client_gcal_status(cid)

    if status["status"] != "connected":
        return ClientGCalReadResult(
            status="not_connected",
            client_id=cid,
            calendar_id=status.get("calendar_id"),
            events=[],
            reason="client_specific_google_calendar_not_connected",
        )

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=ZoneInfo(tz))
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=ZoneInfo(tz))

    cal_id = _calendar_id(cid)
    creds = _load_client_creds(cid)
    svc = build("calendar", "v3", credentials=creds)

    resp = svc.events().list(
        calendarId=cal_id,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=limit,
    ).execute()

    events: List[Dict[str, Any]] = []
    for e in resp.get("items", []) or []:
        start = (e.get("start", {}).get("dateTime") or e.get("start", {}).get("date") or "")
        end = (e.get("end", {}).get("dateTime") or e.get("end", {}).get("date") or "")
        events.append({
            "id": e.get("id") or "",
            "start": start,
            "end": end,
            "summary": e.get("summary") or "(no title)",
            "htmlLink": e.get("htmlLink") or "",
            "source": "google_calendar",
            "client_id": cid,
        })

    return ClientGCalReadResult(
        status="ok",
        client_id=cid,
        calendar_id=cal_id,
        events=events,
        reason="",
    )
