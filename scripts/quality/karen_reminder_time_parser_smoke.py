#!/usr/bin/env python3
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import bot  # noqa: E402


def assert_eq(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main():
    assert_eq(bot._parse_karen_time_phrase("para las 9:20"), (9, 20), "9:20 preserves minutes")
    assert_eq(bot._parse_karen_time_phrase("registralo a las 9 y 20"), (9, 20), "9 y 20 preserves minutes")
    assert_eq(bot._parse_karen_time_phrase("a las 3 de la tarde"), (15, 0), "3 de la tarde")
    assert_eq(bot._parse_karen_time_phrase("a las 10 de la noche"), (22, 0), "10 de la noche")
    assert_eq(bot._parse_karen_time_phrase("a las 13:30"), (13, 30), "military 13:30")

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
    assert_eq(night["time"], (22, 0), "10 de la noche -> 22:00")
    assert_eq(night["title"], "prueba nocturna", "night title cleanup")

    pending = bot._parse_karen_pending_reminder_reply("Para las 9:20")
    assert_eq(pending["time"], (9, 20), "pending Para las 9:20")

    print("PASS: Karen reminder time parser smoke passed.")


if __name__ == "__main__":
    main()
