# /opt/val0/core/gcal_write.py

from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# -------------------------
# CONFIG
# -------------------------

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CLIENT_SECRET_PATH = Path("/etc/val0/gcal/client_secret.json")
REFRESH_TOKEN_PATH = Path("/etc/val0/gcal/refresh_token")
CAL_ID_PATH = Path("/etc/val0/gcal/calendar_id")

VAL0_TZ = os.getenv("VAL0_TZ", "America/Panama")

# Safety switch
WRITE_ENABLED = os.getenv("VAL0_CALENDAR_WRITE_ENABLED", "false").lower() == "true"


# -------------------------
# AUTH
# -------------------------

def _load_creds() -> Credentials:
    refresh_token = REFRESH_TOKEN_PATH.read_text().strip()
    data = json.loads(CLIENT_SECRET_PATH.read_text())

    web = data.get("web") or data.get("installed") or {}

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=web.get("token_uri") or "https://oauth2.googleapis.com/token",
        client_id=web.get("client_id"),
        client_secret=web.get("client_secret"),
        scopes=SCOPES,
    )


def _get_service():
    creds = _load_creds()
    return build("calendar", "v3", credentials=creds)


# -------------------------
# CREATE EVENT
# -------------------------

def create_event(
    title: str,
    start_dt: datetime,
    duration_minutes: int = 60,
    description: str | None = None,
) -> dict:

    if not WRITE_ENABLED:
        return {
            "status": "dry_run",
            "title": title,
            "start": start_dt.isoformat(),
        }

    service = _get_service()

    tz = ZoneInfo(VAL0_TZ)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event = {
        "summary": f"[VAL0] {title}",
        "description": (description or "") + "\n\nCreated by Val",
        "start": {
            "dateTime": start_dt.astimezone(tz).isoformat(),
            "timeZone": VAL0_TZ,
        },
        "end": {
            "dateTime": end_dt.astimezone(tz).isoformat(),
            "timeZone": VAL0_TZ,
        },
    }

    created = service.events().insert(
        calendarId=CAL_ID_PATH.read_text().strip(),
        body=event,
    ).execute()

    return {
        "status": "created",
        "id": created.get("id"),
        "link": created.get("htmlLink"),
    }

