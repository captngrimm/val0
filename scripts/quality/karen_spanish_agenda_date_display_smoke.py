#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.time_intelligence import render_spanish_date_for_display  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_core_spanish_date_helper() -> None:
    value = datetime(2026, 6, 2, 10, 0, tzinfo=ZoneInfo("America/Panama"))
    label = render_spanish_date_for_display(value, current_year=2026, include_time=True)
    assert_contains(label, "martes 2 de junio, 10:00 AM", "Spanish current-year date label")
    assert_not_contains(label, "Tue", "no English weekday")
    assert_not_contains(label, "2026-", "no raw ISO date")
    assert_not_contains(label, "2026", "no unnecessary current year")

    future = render_spanish_date_for_display(datetime(2027, 7, 1, 9, 0, tzinfo=ZoneInfo("America/Panama")), current_year=2026, include_time=True)
    assert_contains(future, "jueves 1 de julio de 2027, 9:00 AM", "outside-year date includes year")


def test_gcal_event_label_uses_spanish_date() -> None:
    code = (
        "import bot; "
        "print(bot._format_client_gcal_event_time('2026-06-02T10:00:00-05:00')); "
        "print(bot._format_client_gcal_event_time('2026-06-02T10:00:00-05:00', single_day=True)); "
        "print(bot._format_client_gcal_event_time('2026-06-02', single_day=True))"
    )
    result = subprocess.run(
        ["./scripts/val0py", "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_true(result.returncode == 0, f"bot gcal formatter runs: {result.stderr}")
    labels = result.stdout.strip().splitlines()[-3:]
    full_label, single_day_label, all_day_label = labels
    assert_contains(full_label, "martes 2 de junio, 10:00 AM", "Google Calendar range event Spanish label")
    assert_not_contains(full_label, "Tue", "Google Calendar range label avoids English weekday")
    assert_not_contains(full_label, "2026-", "Google Calendar range label avoids raw ISO date")
    assert_true(single_day_label == "10:00 AM", "same-day Google Calendar event shows time only")
    assert_true(all_day_label == "Todo el día", "same-day all-day Google Calendar event label")


def test_agenda_renderers_use_central_helper() -> None:
    bot_source = _read("bot.py")
    task_source = _read("core/karen_notes_tasks_visibility.py")
    assert_contains(bot_source, "render_spanish_date_for_display", "bot uses central Spanish date helper")
    assert_contains(bot_source, "_format_client_gcal_event_time", "gcal label helper exists")
    assert_contains(bot_source, "_format_karen_due_local_label", "reminder/list due label helper exists")
    assert_contains(bot_source, "Agenda de hoy — {render_spanish_date_for_display(start_local)}", "today agenda header includes Spanish date")
    assert_contains(bot_source, "Agenda de mañana — {render_spanish_date_for_display(start_local)}", "tomorrow agenda header includes Spanish date")
    assert_contains(bot_source, "single_day=single_day", "single-day gcal rows support compact labels")
    assert_contains(bot_source, "Todo el día", "all-day events use Spanish label")
    assert_contains(task_source, "_format_karen_task_due_label", "task due label helper exists")
    assert_contains(task_source, "render_spanish_date_for_display", "task view uses central Spanish date helper")

    gcal_body_start = bot_source.find("def _format_client_gcal_event_time")
    gcal_body_end = bot_source.find("\n\ndef _format_client_gcal_events_section", gcal_body_start)
    gcal_body = bot_source[gcal_body_start:gcal_body_end]
    assert_not_contains(gcal_body, "%a %d/%m", "gcal formatter no longer uses English strftime weekday")


def main() -> int:
    test_core_spanish_date_helper()
    test_gcal_event_label_uses_spanish_date()
    test_agenda_renderers_use_central_helper()
    print("PASS: Karen Spanish agenda date display smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
