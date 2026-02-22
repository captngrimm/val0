from __future__ import annotations

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json
from typing import List, Dict, Any, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CLIENT_SECRET_PATH = Path("/etc/val0/gcal/client_secret.json")
REFRESH_TOKEN_PATH  = Path("/etc/val0/gcal/refresh_token")
CAL_ID_PATH         = Path("/etc/val0/gcal/calendar_id")

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

def _default_calendar_id() -> str:
    try:
        cid = CAL_ID_PATH.read_text().strip()
        return cid or "primary"
    except FileNotFoundError:
        return "primary"

def get_events_between(
    start_dt: datetime,
    end_dt: datetime,
    calendar_id: Optional[str] = None,
    tz: str = "America/Panama",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Returns normalized events list:
      [{ "start": "...", "end": "...", "summary": "...", "htmlLink": "..."}]
    """
    if calendar_id is None:
        calendar_id = _default_calendar_id()

    # Ensure tz-aware
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=ZoneInfo(tz))
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=ZoneInfo(tz))

    creds = _load_creds()
    svc = build("calendar", "v3", credentials=creds)

    resp = svc.events().list(
        calendarId=calendar_id,
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=limit,
    ).execute()

    out: List[Dict[str, Any]] = []
    for e in resp.get("items", []) or []:
        start = (e.get("start", {}).get("dateTime") or e.get("start", {}).get("date") or "")
        end = (e.get("end", {}).get("dateTime") or e.get("end", {}).get("date") or "")
        out.append({
            "start": start,
            "end": end,
            "summary": e.get("summary") or "(no title)",
            "htmlLink": e.get("htmlLink") or "",
        })
    return out
