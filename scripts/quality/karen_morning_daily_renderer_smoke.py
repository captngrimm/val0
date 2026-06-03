#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r}")


def function_body(name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = BOT.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = BOT.find("\ndef ", start + 1)
    next_async = BOT.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async) if pos > start]
    end = min(stops) if stops else len(BOT)
    return BOT[start:end]


def main() -> int:
    morning = function_body("_generate_morning_brief_det")
    tick = function_body("morning_daily_tick")

    assert_not_contains(morning, "📋 Daily (", "morning renderer avoids old Daily wrapper")
    assert_not_contains(tick, "📋 Daily ({date})", "morning tick sends summary directly")
    assert_contains(tick, "msg = summary", "morning tick uses final renderer output")
    assert_contains(morning, "Agenda de hoy", "morning renderer uses clean agenda header")
    assert_contains(morning, "render_spanish_date_for_display", "morning renderer uses central Spanish date display")
    assert_not_contains(morning, 'header=f"📋 Hoy ({date}):"', "morning renderer avoids duplicate Hoy heading")
    assert_not_contains(morning, "_render_due_grouped", "morning renderer avoids old grouped terms copy")
    assert_not_contains(morning, "términos / eventos ese día", "morning renderer avoids old warning count copy")
    assert_contains(morning, "⏰ Recordatorios de Val", "morning renderer has Val reminders section")
    assert_contains(morning, "⚖️ Caso / términos", "morning renderer has case events section")
    assert_not_contains(morning, "2026-", "morning renderer has no raw current-year ISO display literal")
    assert_not_contains(BOT, "CLIENT_GROCERY.md", "morning Daily patch does not reference client grocery data")

    print("PASS: Karen morning Daily renderer smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
