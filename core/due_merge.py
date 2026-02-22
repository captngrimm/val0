from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

logger_name = "val0-bot"


def _tz() -> ZoneInfo:
    name = os.getenv("VAL0_TZ", "America/Panama").strip() or "America/Panama"
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def gcal_enabled() -> bool:
    return os.getenv("VAL0_GCAL_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


def include_unbound_events() -> bool:
    # Off by default to avoid noise. Turn on only if you want “general calendar stuff” merged too.
    return os.getenv("VAL0_GCAL_INCLUDE_UNBOUND", "0").strip().lower() in ("1", "true", "yes", "on")


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # assume local if naive
        dt = dt.replace(tzinfo=_tz())
    return dt.astimezone(timezone.utc)


def _local_label(dt_utc: datetime) -> str:
    tz = _tz()
    return dt_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M")


def _dedupe_key(item: Dict[str, Any]) -> Tuple[str, str, int]:
    """
    Deterministic-ish de-dupe:
    - case_id + normalized title + minute bucket
    - if case_id missing, use "" (still stable)
    """
    case_id = str(item.get("case_id") or "").strip()
    title = str(item.get("title") or "").strip().lower()
    due_ts = int(item.get("due_ts") or 0)
    minute_bucket = due_ts // 60
    return (case_id, title, minute_bucket)


def _parse_google_start_to_due_ts(start_str: str) -> Optional[int]:
    """
    Google returns either:
      - RFC3339 dateTime (with offset/Z)
      - date (YYYY-MM-DD) for all-day events

    Deterministic rule:
      - dateTime => use that instant
      - date (all-day) => 09:00 local time that day
    """
    if not start_str:
        return None

    tz = _tz()

    # All-day date
    if len(start_str) == 10 and start_str.count("-") == 2:
        y, m, d = start_str.split("-")
        local = datetime(int(y), int(m), int(d), 9, 0, 0, tzinfo=tz)
        return int(local.astimezone(timezone.utc).timestamp())

    # RFC3339 dateTime
    try:
        dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.astimezone(timezone.utc).timestamp())
    except Exception:
        return None


def merge_due_items(
    *,
    db_items: List[Dict[str, Any]],
    range_start_utc: datetime,
    range_end_utc: datetime,
) -> List[Dict[str, Any]]:
    """
    Merge deterministic DB due items with optional Google Calendar events (deterministically normalized).
    Output schema:
      {
        "due_ts": int,
        "due_local": "YYYY-MM-DD HH:MM",
        "due_date": "YYYY-MM-DD",
        "title": str,
        "case_id": Optional[str],
        "source": "db" | "gcal",
        "external_id": Optional[str],
      }
    """
    out: List[Dict[str, Any]] = []

    # Normalize DB items first
    for it in db_items:
        it = dict(it)
        it.setdefault("source", "db")
        it.setdefault("external_id", None)
        it["due_ts"] = int(it.get("due_ts") or 0)
        it.setdefault("due_local", _local_label(datetime.fromtimestamp(it["due_ts"], tz=timezone.utc)))
        it.setdefault("due_date", it["due_local"][:10] if it.get("due_local") else "")
        it.setdefault("case_id", it.get("case_id"))
        it.setdefault("title", it.get("title") or "(evento)")
        out.append(it)

    if not gcal_enabled():
        return sorted(out, key=lambda x: int(x.get("due_ts") or 0))

    # Pull GCAL events (normalized) using your existing core/gcal_client.py
    try:
        from core.gcal_client import get_events_between  # your file exists already
    except Exception:
        # If import fails, still return DB-only deterministically.
        return sorted(out, key=lambda x: int(x.get("due_ts") or 0))

    # Convert range to tz-aware UTC bounds
    start_utc = _to_utc(range_start_utc)
    end_utc = _to_utc(range_end_utc)

    try:
        events = get_events_between(start_utc, end_utc, limit=250)
    except Exception:
        return sorted(out, key=lambda x: int(x.get("due_ts") or 0))

    for ev in events or []:
        start_str = (ev.get("start") or "").strip()
        due_ts = _parse_google_start_to_due_ts(start_str)
        if due_ts is None:
            continue

        due_dt_utc = datetime.fromtimestamp(due_ts, tz=timezone.utc)
        # hard bound filter (deterministic)
        if due_dt_utc < start_utc or due_dt_utc > end_utc:
            continue

        title = (ev.get("summary") or "(no title)").strip()

        # We are NOT binding to cases yet (strict rules later). Keep as general unless enabled.
        case_id = None
        if not include_unbound_events():
            # default: skip unbound calendar events entirely
            continue

        out.append(
            {
                "due_ts": due_ts,
                "due_local": _local_label(due_dt_utc),
                "due_date": _local_label(due_dt_utc)[:10],
                "title": title,
                "case_id": case_id,
                "source": "gcal",
                "external_id": ev.get("id") or None,
            }
        )

    # De-dupe (prefer DB over GCAL on collision)
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for it in sorted(out, key=lambda x: (int(x.get("due_ts") or 0), str(x.get("source") or ""))):
        k = _dedupe_key(it)
        if k in seen:
            # if collision: skip gcal
            if it.get("source") == "gcal":
                continue
        seen.add(k)
        deduped.append(it)

    return sorted(deduped, key=lambda x: int(x.get("due_ts") or 0))
