#!/usr/bin/env python3
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import bot  # noqa: E402
from core.time_intelligence import (  # noqa: E402
    TimeDisplayPreference,
    infer_today_when_future,
    parse_spanish_clock_time,
    parse_spanish_relative_minutes,
    render_time_for_display,
    roll_forward_ambiguous_today_time,
)


def assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main():
    assert_eq(bot._parse_karen_time_phrase("para las 9:20"), (9, 20), "9:20 preserves minutes")
    assert_eq(bot._parse_karen_time_phrase("registralo a las 9 y 20"), (9, 20), "9 y 20 preserves minutes")
    assert_eq(bot._parse_karen_time_phrase("a las 3 de la tarde"), (15, 0), "3 de la tarde")
    assert_eq(bot._parse_karen_time_phrase("a las 10 de la noche"), (22, 0), "10 de la noche")
    assert_eq(bot._parse_karen_time_phrase("a las 13:30"), (13, 30), "military 13:30")
    assert_eq(parse_spanish_clock_time("9:20"), (9, 20), "core bare 9:20")
    assert_eq(parse_spanish_clock_time("9 y 20"), (9, 20), "core bare 9 y 20")
    assert_eq(parse_spanish_clock_time("3 de la tarde"), (15, 0), "core 3 de la tarde")
    assert_eq(parse_spanish_clock_time("10 de la noche"), (22, 0), "core 10 de la noche")
    assert_eq(parse_spanish_clock_time("13:30"), (13, 30), "core 13:30")

    relative_now = dt.datetime(2026, 6, 1, 9, 0, 0, tzinfo=ZoneInfo("America/Panama"))
    assert_eq(parse_spanish_relative_minutes("en media hora llamar", now=relative_now).minutes, 30, "media hora")
    assert_eq(parse_spanish_relative_minutes("en una hora llamar", now=relative_now).minutes, 60, "una hora")
    assert_eq(parse_spanish_relative_minutes("en una hora y media llamar", now=relative_now).minutes, 90, "una hora y media")
    assert_eq(parse_spanish_relative_minutes("en 25 minutos llamar", now=relative_now).minutes, 25, "N minutos")
    assert_eq(parse_spanish_relative_minutes("dentro de 2 horas llamar", now=relative_now).minutes, 120, "N horas")

    fake_now = dt.datetime(2026, 6, 1, 9, 0, 0, tzinfo=ZoneInfo("America/Panama"))
    parsed = bot._parse_karen_natural_reminder_request(
        "Val recuérdame en una hora y media recoger a David",
        now=fake_now,
    )
    assert parsed is not None
    assert_eq(parsed["date"].isoformat(), "2026-06-01", "relative date")
    assert_eq(parsed["time"], (10, 30), "una hora y media -> +90 minutes")
    assert_eq(parsed["title"], "recoger a david", "relative title cleanup")

    evening_now = dt.datetime(2026, 6, 1, 18, 16, 0, tzinfo=ZoneInfo("America/Panama"))
    exact = bot._parse_karen_natural_reminder_request(
        "Val recuérdame hoy a las 9:20 prueba exacta",
        now=evening_now,
    )
    assert exact is not None
    assert_eq(exact["date"].isoformat(), "2026-06-01", "exact today date")
    assert_eq(exact["time"], (21, 20), "past ambiguous 9:20 rolls to PM")
    assert_eq(exact["title"], "prueba exacta", "exact time title cleanup")

    night = bot._parse_karen_natural_reminder_request(
        "Val recuérdame a las 10 de la noche prueba nocturna",
        now=evening_now,
    )
    assert night is not None
    assert_eq(night["date"].isoformat(), "2026-06-01", "night no-date infers today")
    assert_eq(night["time"], (22, 0), "10 de la noche -> 22:00")
    assert_eq(night["title"], "prueba nocturna", "night title cleanup")

    afternoon_now = dt.datetime(2026, 6, 1, 10, 53, 0, tzinfo=ZoneInfo("America/Panama"))
    rolled = roll_forward_ambiguous_today_time((9, 20), afternoon_now.date(), "hoy a las 9:20", afternoon_now)
    assert_eq(rolled, (21, 20), "core ambiguous today rolls to PM")
    explicit_am = roll_forward_ambiguous_today_time((9, 20), afternoon_now.date(), "hoy a las 9:20 am", afternoon_now)
    assert_eq(explicit_am, (9, 20), "core explicit AM does not roll")
    explicit_24h = roll_forward_ambiguous_today_time((9, 20), afternoon_now.date(), "hoy a las 13:30", afternoon_now)
    assert_eq(explicit_24h, (9, 20), "core explicit 24h marker does not alter supplied tuple")
    inferred_date, inferred_time = infer_today_when_future((22, 0), "a las 10 de la noche", afternoon_now)
    assert_eq(inferred_date.isoformat(), "2026-06-01", "core no-date future infers today")
    assert_eq(inferred_time, (22, 0), "core no-date future keeps time")

    no_date_night = bot._parse_karen_natural_reminder_request(
        "Val recuérdame a las 10 de la noche prueba nocturna v2",
        now=afternoon_now,
    )
    assert no_date_night is not None
    assert_eq(no_date_night["date"].isoformat(), "2026-06-01", "no-date future night infers today")
    assert_eq(no_date_night["time"], (22, 0), "no-date future night time")
    assert_eq(no_date_night["title"], "prueba nocturna v2", "no-date night title cleanup")

    pending = bot._parse_karen_pending_reminder_reply("Para las 9:20")
    assert_eq(pending["time"], (9, 20), "pending Para las 9:20")

    display_dt = dt.datetime(2026, 6, 1, 21, 20, 0, tzinfo=ZoneInfo("America/Panama"))
    assert_eq(render_time_for_display(display_dt, TimeDisplayPreference.TWENTY_FOUR_HOUR), "21:20", "24h display")
    assert_eq(render_time_for_display(display_dt, TimeDisplayPreference.TWELVE_HOUR), "9:20 PM", "12h display")

    print("PASS: Karen reminder time parser smoke passed.")


if __name__ == "__main__":
    main()
