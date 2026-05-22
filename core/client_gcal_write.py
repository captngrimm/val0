from __future__ import annotations

"""
Client-scoped Google Calendar writer.

Safety rules:
- Never uses legacy/global /etc/val0/gcal refresh token.
- Reads client token only from /etc/val0/clients/<client_id>/gcal/refresh_token.
- Requires VAL0_CLIENT_GCAL_WRITE_ENABLED=true.
- Requires a client-specific allow file:
  /etc/val0/clients/<client_id>/gcal/write_enabled
- Intended to be called only after explicit user confirmation.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

WRITE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

APP_CLIENT_SECRET_PATH = Path(
    os.getenv("VAL0_GCAL_OAUTH_CLIENT_SECRET", "/etc/val0/gcal/client_secret.json")
)

VAL0_TZ = os.getenv("VAL0_TZ", "America/Panama")


@dataclass(frozen=True)
class ClientGCalWriteResult:
    status: str
    client_id: str
    reason: str = ""
    event_id: str = ""
    html_link: str = ""
    title: str = ""
    start: str = ""
    end: str = ""
    deleted_event_id: str = ""


def _safe_client_id(client_id: str) -> str:
    safe = "".join(
        ch for ch in (client_id or "").lower()
        if ch.isalnum() or ch in ("_", "-")
    ).strip()
    return safe or "unknown"


def _client_gcal_dir(client_id: str) -> Path:
    return Path("/etc/val0/clients") / _safe_client_id(client_id) / "gcal"


def get_client_gcal_write_paths(client_id: str) -> dict[str, Path]:
    base = _client_gcal_dir(client_id)
    return {
        "base": base,
        "client_secret": APP_CLIENT_SECRET_PATH,
        "refresh_token": base / "refresh_token",
        "calendar_id": base / "calendar_id",
        "write_enabled": base / "write_enabled",
    }


def client_gcal_write_status(client_id: str) -> dict:
    cid = _safe_client_id(client_id)
    paths = get_client_gcal_write_paths(cid)

    global_enabled = os.getenv("VAL0_CLIENT_GCAL_WRITE_ENABLED", "false").lower() == "true"
    client_enabled = paths["write_enabled"].exists() and paths["write_enabled"].read_text(encoding="utf-8").strip().lower() == "true"

    missing = [
        name for name in ("client_secret", "refresh_token")
        if not paths[name].exists()
    ]

    calendar_id = "primary"
    if paths["calendar_id"].exists():
        calendar_id = paths["calendar_id"].read_text(encoding="utf-8").strip() or "primary"

    return {
        "client_id": cid,
        "provider": "google_calendar",
        "mode": "write_guarded",
        "global_write_enabled": global_enabled,
        "client_write_enabled": client_enabled,
        "ready": bool(global_enabled and client_enabled and not missing),
        "calendar_id": calendar_id,
        "missing": missing,
        "uses_legacy_global": False,
    }


def _load_client_write_creds(client_id: str) -> Credentials:
    paths = get_client_gcal_write_paths(client_id)

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
        scopes=WRITE_SCOPES,
    )


def _calendar_id(client_id: str) -> str:
    paths = get_client_gcal_write_paths(client_id)
    if paths["calendar_id"].exists():
        raw = paths["calendar_id"].read_text(encoding="utf-8").strip()
        if raw:
            return raw
    return "primary"


def create_client_event(
    client_id: str,
    title: str,
    start_dt: datetime,
    duration_minutes: int = 60,
    description: str | None = None,
    dry_run: bool = True,
) -> ClientGCalWriteResult:
    cid = _safe_client_id(client_id)
    status = client_gcal_write_status(cid)

    tz = ZoneInfo(VAL0_TZ)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tz)
    start_dt = start_dt.astimezone(tz)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    clean_title = (title or "").strip()
    if not clean_title:
        return ClientGCalWriteResult(
            status="rejected",
            client_id=cid,
            reason="missing_title",
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
        )

    if dry_run:
        return ClientGCalWriteResult(
            status="dry_run",
            client_id=cid,
            reason="dry_run_no_google_write",
            title=clean_title,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
        )

    if not status.get("ready"):
        return ClientGCalWriteResult(
            status="blocked",
            client_id=cid,
            reason=f"write_not_ready:{status}",
            title=clean_title,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
        )

    creds = _load_client_write_creds(cid)
    svc = build("calendar", "v3", credentials=creds, cache_discovery=False)

    event = {
        "summary": clean_title,
        "description": (description or "") + "\n\nCreated by Val0 with explicit user confirmation.",
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": VAL0_TZ,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": VAL0_TZ,
        },
    }

    created = svc.events().insert(
        calendarId=_calendar_id(cid),
        body=event,
    ).execute()

    return ClientGCalWriteResult(
        status="created",
        client_id=cid,
        reason="created_in_client_google_calendar",
        event_id=created.get("id") or "",
        html_link=created.get("htmlLink") or "",
        title=clean_title,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
    )



def find_client_events_by_title(
    client_id: str,
    title_query: str,
    start_dt: datetime,
    days_ahead: int = 30,
    limit: int = 10,
) -> list[dict]:
    """
    Guarded lookup for delete flow.
    Searches upcoming client calendar events by exact-ish title match.
    Does not delete anything.
    """
    cid = _safe_client_id(client_id)
    clean_query = (title_query or "").strip().lower()
    if not clean_query:
        return []

    status = client_gcal_write_status(cid)
    if not status.get("ready"):
        return []

    tz = ZoneInfo(VAL0_TZ)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tz)
    start_dt = start_dt.astimezone(tz)
    end_dt = start_dt + timedelta(days=days_ahead)

    creds = _load_client_write_creds(cid)
    svc = build("calendar", "v3", credentials=creds, cache_discovery=False)

    resp = svc.events().list(
        calendarId=_calendar_id(cid),
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=limit,
        q=title_query,
    ).execute()

    matches = []
    for ev in resp.get("items", []):
        summary = (ev.get("summary") or "").strip()
        if clean_query in summary.lower() or summary.lower() in clean_query:
            start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date") or ""
            end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date") or ""
            matches.append({
                "id": ev.get("id") or "",
                "summary": summary,
                "start": start,
                "end": end,
                "htmlLink": ev.get("htmlLink") or "",
            })

    return matches


def delete_client_event(
    client_id: str,
    event_id: str,
    dry_run: bool = True,
) -> ClientGCalWriteResult:
    """
    Guarded event deletion.
    Requires same write gates as create.
    Caller must perform human confirmation before dry_run=False.
    """
    cid = _safe_client_id(client_id)
    clean_event_id = (event_id or "").strip()

    if not clean_event_id:
        return ClientGCalWriteResult(
            status="rejected",
            client_id=cid,
            reason="missing_event_id",
        )

    status = client_gcal_write_status(cid)

    if dry_run:
        return ClientGCalWriteResult(
            status="dry_run",
            client_id=cid,
            reason="dry_run_no_google_delete",
            event_id=clean_event_id,
        )

    if not status.get("ready"):
        return ClientGCalWriteResult(
            status="blocked",
            client_id=cid,
            reason=f"write_not_ready:{status}",
            event_id=clean_event_id,
        )

    creds = _load_client_write_creds(cid)
    svc = build("calendar", "v3", credentials=creds, cache_discovery=False)

    svc.events().delete(
        calendarId=_calendar_id(cid),
        eventId=clean_event_id,
    ).execute()

    return ClientGCalWriteResult(
        status="deleted",
        client_id=cid,
        reason="deleted_from_client_google_calendar",
        event_id=clean_event_id,
        deleted_event_id=clean_event_id,
    )
