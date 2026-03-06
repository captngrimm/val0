from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

logger = logging.getLogger("val0-bot")

# Phase 1 hardening: strict case binding pattern
CASE_BIND_RE = re.compile(r"\bCASE:(\d+)\b", re.IGNORECASE)


def _tz() -> ZoneInfo:
    name = os.getenv("VAL0_TZ", "America/Panama").strip() or "America/Panama"
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def gcal_enabled() -> bool:
    return os.getenv("VAL0_GCAL_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


def include_unbound_events() -> bool:
    # Phase 1: OFF by default to avoid noise. Enable only for testing/general calendar inclusion.
    return os.getenv("VAL0_GCAL_INCLUDE_UNBOUND", "0").strip().lower() in ("1", "true", "yes", "on")


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tz())
    return dt.astimezone(timezone.utc)


def _local_label(dt_utc: datetime) -> str:
    tz = _tz()
    return dt_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M")


def _norm_title(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _title_hash(s: str) -> str:
    # short stable fingerprint for logs (avoid leaking full titles)
    h = hashlib.sha1(_norm_title(s).encode("utf-8")).hexdigest()
    return h[:10]


def _dedupe_key(item: Dict[str, Any]) -> Tuple[str, str, int]:
    """
    Deterministic-ish de-dupe:
    - case_id + normalized title + minute bucket
    - if case_id missing, use "" (still stable)
    """
    case_id = str(item.get("case_id") or "").strip()
    title = _norm_title(str(item.get("title") or ""))
    due_ts = int(item.get("due_ts") or 0)
    minute_bucket = due_ts // 60
    return (case_id, title, minute_bucket)


def _dedupe_key_public(item: Dict[str, Any]) -> str:
    # log-safe key representation (hash title)
    case_id = str(item.get("case_id") or "").strip()
    due_ts = int(item.get("due_ts") or 0)
    minute_bucket = due_ts // 60
    th = _title_hash(str(item.get("title") or ""))
    return f"case={case_id or '-'} titleh={th} minbucket={minute_bucket}"


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


def _extract_case_id_from_title(title: str) -> Optional[str]:
    """
    Phase 1 hardening: strict case binding pattern CASE:<digits>.
    Returns case_id string if present, else None.
    """
    if not title:
        return None
    m = CASE_BIND_RE.search(title)
    if not m:
        return None
    return m.group(1)


def merge_due_items(
    *,
    db_items: List[Dict[str, Any]],
    range_start_utc: datetime,
    range_end_utc: datetime,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge deterministic DB due items with optional Google Calendar events.

    Returns:
    {
      "items": [...],
      "conflicts": [...]
    }

    items schema:
    {
      "due_ts": int,
      "due_local": "YYYY-MM-DD HH:MM",
      "due_date": "YYYY-MM-DD",
      "title": str,
      "case_id": Optional[str],
      "source": "db" | "gcal",
      "external_id": Optional[str],
    }

    conflicts schema:
    {
      "case_id": str,
      "due_date": str,
      "db_due_local": str,
      "gcal_due_local": str,
      "db_title": str,
      "gcal_title": str,
      "kind": "time" | "title" | "both",
    }
    """
    out: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    # --- Normalize DB items first ---
    # Build an index for conflict detection: (case_id, due_date) -> list[db_item]
    db_index: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

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

        case_id = str(it.get("case_id") or "").strip()
        due_date = str(it.get("due_date") or "").strip()
        if case_id and due_date:
            db_index.setdefault((case_id, due_date), []).append(it)

    if not gcal_enabled():
        return {
            "items": sorted(out, key=lambda x: int(x.get("due_ts") or 0)),
            "conflicts": [],
        }

    # Pull GCAL events (normalized)
    try:
        from core.gcal_client import get_events_between
    except Exception as e:
        logger.info("[MERGE] gcal_import_fail err=%s", type(e).__name__)
        return {
            "items": sorted(out, key=lambda x: int(x.get("due_ts") or 0)),
            "conflicts": [],
        }

    start_utc = _to_utc(range_start_utc)
    end_utc = _to_utc(range_end_utc)

    try:
        events = get_events_between(start_utc, end_utc, limit=250)
    except Exception as e:
        logger.info("[MERGE] gcal_fetch_fail err=%s", type(e).__name__)
        return {
            "items": sorted(out, key=lambda x: int(x.get("due_ts") or 0)),
            "conflicts": [],
        }

    # Phase 1: strict unbound handling + merge stats
    allow_unbound = include_unbound_events()
    total_ev = 0
    kept_bound = 0
    kept_unbound = 0
    dropped_unbound = 0
    dropped_oob = 0
    dropped_no_ts = 0

    # Phase 1: conflict detection stats (DB vs GCAL)
    conflict_total = 0
    conflict_time = 0
    conflict_title = 0
    conflict_samples: List[str] = []  # log-safe samples (no titles)

    for ev in events or []:
        total_ev += 1

        start_str = (ev.get("start") or "").strip()
        due_ts = _parse_google_start_to_due_ts(start_str)
        if due_ts is None:
            dropped_no_ts += 1
            continue

        due_dt_utc = datetime.fromtimestamp(due_ts, tz=timezone.utc)
        if due_dt_utc < start_utc or due_dt_utc > end_utc:
            dropped_oob += 1
            continue

        title = (ev.get("summary") or "(no title)").strip()
        case_id = _extract_case_id_from_title(title)
        if total_ev <= 5:
            logger.info(
                "[MERGE] ev_dbg start=%s titleh=%s bound=%s",
                start_str,
                _title_hash(title),
                case_id or "-",
            )

        due_date = _local_label(due_dt_utc)[:10]

        if case_id is None:
            if not allow_unbound:
                dropped_unbound += 1
                continue
            kept_unbound += 1
        else:
            kept_bound += 1

        # --- Conflict detection (Phase 1): if DB has same case_id + due_date, compare ---
        db_candidates = db_index.get((case_id, due_date)) or []
        if db_candidates:
            # Compare against the first DB candidate deterministically
            db_sorted = sorted(
                db_candidates,
                key=lambda x: (int(x.get("due_ts") or 0), _norm_title(str(x.get("title") or ""))),
            )
            db_it = db_sorted[0]

            db_ts = int(db_it.get("due_ts") or 0)
            g_ts = int(due_ts)
            delta_min = abs(db_ts - g_ts) // 60

            db_title = str(db_it.get("title") or "(evento)")
            gcal_title = title

            db_th = _title_hash(db_title)
            g_th = _title_hash(gcal_title)

            time_mismatch = (db_ts != g_ts)
            title_mismatch = (db_th != g_th)

            if time_mismatch or title_mismatch:
                conflict_total += 1
                if time_mismatch:
                    conflict_time += 1
                if title_mismatch:
                    conflict_title += 1

                if len(conflict_samples) < 3:
                    conflict_samples.append(
                        f"case={case_id} date={due_date} dmin={delta_min} db_titleh={db_th} gcal_titleh={g_th}"
                    )

                conflicts.append(
                    {
                        "case_id": str(case_id or ""),
                        "due_date": due_date,
                        "db_due_local": _local_label(datetime.fromtimestamp(db_ts, tz=timezone.utc)),
                        "gcal_due_local": _local_label(due_dt_utc),
                        "db_title": db_title,
                        "gcal_title": gcal_title,
                        "kind": "both" if (time_mismatch and title_mismatch) else ("time" if time_mismatch else "title"),
                    }
                )

        out.append(
            {
                "due_ts": due_ts,
                "due_local": _local_label(due_dt_utc),
                "due_date": due_date,
                "title": title,
                "case_id": case_id,
                "source": "gcal",
                "external_id": ev.get("id") or None,
            }
        )

    logger.info(
        "[MERGE] gcal_stats total=%d bound=%d unbound_kept=%d unbound_dropped=%d oob_dropped=%d no_ts_dropped=%d include_unbound=%s",
        total_ev,
        kept_bound,
        kept_unbound,
        dropped_unbound,
        dropped_oob,
        dropped_no_ts,
        "1" if allow_unbound else "0",
    )

    if conflict_total:
        logger.info(
            "[MERGE] conflict_stats total=%d time=%d title=%d samples=%s",
            conflict_total,
            conflict_time,
            conflict_title,
            conflict_samples,
        )
    else:
        logger.info("[MERGE] conflict_stats total=0")

    # --- De-dupe (prefer DB over GCAL on collision) + refined logs ---
    deduped: List[Dict[str, Any]] = []
    seen = set()

    gcal_skipped_collisions = 0
    collision_samples: List[str] = []  # log-safe

    for it in sorted(out, key=lambda x: (int(x.get("due_ts") or 0), str(x.get("source") or ""))):
        k = _dedupe_key(it)
        if k in seen:
            if it.get("source") == "gcal":
                gcal_skipped_collisions += 1
                if len(collision_samples) < 3:
                    collision_samples.append(_dedupe_key_public(it))
            continue
        seen.add(k)
        deduped.append(it)

    logger.info(
        "[MERGE] dedupe_stats gcal_skipped=%d sample=%s",
        gcal_skipped_collisions,
        collision_samples,
    )

    return {
        "items": sorted(deduped, key=lambda x: int(x.get("due_ts") or 0)),
        "conflicts": conflicts,
    }
