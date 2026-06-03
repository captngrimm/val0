from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "America/Panama"
SPANISH_WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
SPANISH_MONTHS = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


class TimeDisplayPreference(str, Enum):
    """User-facing time display preferences.

    Internal storage should remain normalized datetime/UTC. This preference is
    only for rendering confirmations or list views.
    """

    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"
    NATURAL_SPANISH = "natural_spanish"


@dataclass(frozen=True)
class RelativeTimeResult:
    minutes: int
    time_parts: tuple[int, int]
    local_date: dt.date
    due_local: dt.datetime


def normalize_spanish_time_text(text: str) -> str:
    value = (text or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[¿?¡!.,;]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _small_number_word_to_int(token: str) -> int | None:
    token = normalize_spanish_time_text(token)
    if token.isdigit():
        return int(token)
    return {
        "cero": 0,
        "uno": 1,
        "una": 1,
        "primer": 1,
        "primero": 1,
        "dos": 2,
        "segundo": 2,
        "tres": 3,
        "tercero": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
        "once": 11,
        "doce": 12,
        "trece": 13,
        "catorce": 14,
        "quince": 15,
        "veinte": 20,
        "treinta": 30,
        "cuarenta": 40,
        "cincuenta": 50,
        "sesenta": 60,
    }.get(token)


def parse_spanish_clock_time(text: str) -> tuple[int, int] | None:
    """
    Parse natural Spanish clock phrases.

    Supports:
    - a las 9:20
    - a las 9 y 20
    - para las 9:20
    - 9:20
    - 3 de la tarde
    - 10 de la noche
    - 13 / 13:30 military-style
    """
    norm = normalize_spanish_time_text(text)
    patterns = [
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*"
        r"(?P<hour>\d{1,2})"
        r"(?:(?::|\s+y\s+|\s+con\s+)(?P<minute>\d{1,2}))?"
        r"\s*(?P<ampm>am|pm|a\s*m|p\s*m)?"
        r"\s+de\s+la\s+(?P<daypart>manana|tarde|noche)\b",
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*"
        r"(?P<hour>\d{1,2})"
        r"(?:(?::|\s+y\s+|\s+con\s+)(?P<minute>\d{1,2}))?"
        r"\s*(?P<ampm>am|pm|a\s*m|p\s*m)?\b",
    ]

    match = None
    for pattern in patterns:
        match = re.search(pattern, norm)
        if match:
            break
    if not match:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    ampm = (match.group("ampm") or "").replace(" ", "")
    daypart = match.groupdict().get("daypart")

    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    elif not ampm and daypart in ("tarde", "noche") and 1 <= hour <= 11:
        hour += 12

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


def spanish_time_phrase_is_explicit_period(text: str) -> bool:
    """Return True when the user explicitly constrained AM/PM/daypart/24h."""
    norm = normalize_spanish_time_text(text)
    if re.search(r"\b(?:am|pm|a\s*m|p\s*m)\b", norm):
        return True
    if re.search(r"\bde\s+la\s+(?:manana|tarde|noche)\b", norm):
        return True
    match = re.search(
        r"\b(?:a\s+las?|a\s+la|para\s+las?|para\s+la)?\s*(?P<hour>\d{1,2})(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\b",
        norm,
    )
    if match:
        try:
            return int(match.group("hour")) >= 13
        except Exception:
            return False
    return False


def roll_forward_ambiguous_today_time(
    time_parts: tuple[int, int] | None,
    target_date: dt.date | None,
    text: str,
    now_local: dt.datetime | None,
) -> tuple[int, int] | None:
    """
    If an ambiguous 1-11 clock time for today has already passed, interpret it
    as PM only when that PM candidate is still later today.

    Explicit AM/PM, daypart, and 24h times are never silently changed.
    """
    if not time_parts or target_date is None or now_local is None:
        return time_parts
    if target_date != now_local.date():
        return time_parts
    if spanish_time_phrase_is_explicit_period(text):
        return time_parts

    hour, minute = time_parts
    if not (1 <= int(hour) <= 11):
        return time_parts

    candidate = dt.datetime(target_date.year, target_date.month, target_date.day, int(hour), int(minute), 0, tzinfo=now_local.tzinfo)
    if candidate > now_local:
        return time_parts

    pm_candidate = candidate + dt.timedelta(hours=12)
    if pm_candidate.date() == target_date and pm_candidate > now_local:
        return pm_candidate.hour, pm_candidate.minute

    return time_parts


def infer_today_when_future(
    time_parts: tuple[int, int] | None,
    text: str,
    now_local: dt.datetime,
) -> tuple[dt.date | None, tuple[int, int] | None]:
    """Infer today for no-date reminders when the resolved time is still future."""
    if not time_parts:
        return None, time_parts

    inferred_time = roll_forward_ambiguous_today_time(time_parts, now_local.date(), text, now_local)
    if not inferred_time:
        return None, time_parts
    inferred_dt = dt.datetime(
        now_local.year,
        now_local.month,
        now_local.day,
        int(inferred_time[0]),
        int(inferred_time[1]),
        0,
        tzinfo=now_local.tzinfo,
    )
    if inferred_dt > now_local:
        return now_local.date(), inferred_time
    return None, time_parts


def strip_spanish_time_phrase_from_title(title: str) -> str:
    """Remove recognized Spanish time phrases from a reminder title."""
    patterns = [
        r"\b(?:hoy\s+)?(?:a\s+las?|a\s+la|para\s+las?|para\s+la)\s*\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\s*(?:am|pm|a\s*m|p\s*m)?\s+de\s+la\s+(?:manana|mañana|tarde|noche)\b",
        r"\b\d{1,2}\s+de\s+la\s+(?:manana|mañana|tarde|noche)\b",
        r"\b(?:hoy\s+)?(?:a\s+las?|a\s+la|para\s+las?|para\s+la)\s*\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})?\s*(?:am|pm|a\s*m|p\s*m)?\b",
        r"\b\d{1,2}(?:(?::|\s+y\s+|\s+con\s+)\d{1,2})\s*(?:am|pm|a\s*m|p\s*m)?\b",
        r"\b\d{1,2}\s*(?:am|pm|a\s*m|p\s*m)\b",
    ]
    cleaned = title or ""
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned)
    cleaned = re.sub(r"\bde\s+la\s+(?:manana|mañana|tarde|noche)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" .,:;")


def parse_spanish_relative_minutes(
    text: str,
    *,
    now: dt.datetime | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> RelativeTimeResult | None:
    norm = normalize_spanish_time_text(text)
    tz = ZoneInfo(timezone_name)
    base_now = now or dt.datetime.now(tz)
    if getattr(base_now, "tzinfo", None) is None:
        base_now = base_now.replace(tzinfo=tz)
    else:
        base_now = base_now.astimezone(tz)

    minutes: int | None = None
    if re.search(r"\b(?:en|dentro\s+de)\s+(?:media\s+hora|medio\s+hora)\b", norm):
        minutes = 30
    elif re.search(r"\b(?:en|dentro\s+de)\s+(?:una|1)\s+hora\s+y\s+media\b", norm):
        minutes = 90
    else:
        hour_match = re.search(
            r"\b(?:en|dentro\s+de)\s+(?P<num>\d{1,2}|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)\s+horas?\b",
            norm,
        )
        if hour_match:
            hours = _small_number_word_to_int(hour_match.group("num"))
            if hours and hours >= 1:
                minutes = int(hours) * 60

    if minutes is None:
        minute_match = re.search(
            r"\b(?:en|dentro\s+de)\s+(?P<num>\d{1,3}|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|veinte|treinta|cuarenta|cincuenta|sesenta)\s+minutos?\b",
            norm,
        )
        if not minute_match:
            return None
        parsed_minutes = _small_number_word_to_int(minute_match.group("num"))
        if not parsed_minutes or parsed_minutes < 1:
            return None
        minutes = int(parsed_minutes)

    due_local = base_now + dt.timedelta(minutes=int(minutes))
    return RelativeTimeResult(
        minutes=int(minutes),
        time_parts=(due_local.hour, due_local.minute),
        local_date=due_local.date(),
        due_local=due_local,
    )


def render_time_for_display(value: dt.datetime, preference: TimeDisplayPreference | str = TimeDisplayPreference.NATURAL_SPANISH) -> str:
    """Render a datetime for users without changing stored normalized datetime."""
    pref = TimeDisplayPreference(preference)
    if pref == TimeDisplayPreference.TWENTY_FOUR_HOUR:
        return value.strftime("%H:%M")
    if pref == TimeDisplayPreference.TWELVE_HOUR:
        return value.strftime("%I:%M %p").lstrip("0")

    hour = value.hour
    minute = value.minute
    if minute:
        base = value.strftime("%I:%M %p").lstrip("0")
    else:
        base = value.strftime("%I %p").lstrip("0")
    suffix = "de la mañana"
    if 12 <= hour < 18:
        suffix = "de la tarde"
    elif hour >= 18:
        suffix = "de la noche"
    return f"{base} ({suffix})"


def render_spanish_date_for_display(
    value: dt.date | dt.datetime,
    *,
    current_year: int | None = None,
    include_time: bool = False,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> str:
    """Render a user-facing Spanish date label without changing stored values."""
    tz = ZoneInfo(timezone_name)
    if isinstance(value, dt.datetime):
        local_value = value
        if local_value.tzinfo is not None:
            local_value = local_value.astimezone(tz)
        date_value = local_value.date()
    else:
        local_value = None
        date_value = value

    if current_year is None:
        current_year = dt.datetime.now(tz).year

    weekday = SPANISH_WEEKDAYS[date_value.weekday()]
    month = SPANISH_MONTHS[date_value.month]
    label = f"{weekday} {date_value.day} de {month}"
    if date_value.year != int(current_year):
        label = f"{label} de {date_value.year}"

    if include_time and local_value is not None:
        label = f"{label}, {local_value.strftime('%I:%M %p').lstrip('0')}"
    return label
