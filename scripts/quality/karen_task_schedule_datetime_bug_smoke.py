#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import parse_karen_task_schedule_for_tomorrow  # noqa: E402


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def _bot_source() -> str:
    return (REPO_ROOT / "bot.py").read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    for marker in (f"async def {name}", f"def {name}"):
        start = source.find(marker)
        if start >= 0:
            break
    else:
        raise AssertionError(f"missing function {name}")
    next_def = source.find("\ndef ", start + 1)
    next_async_def = source.find("\nasync def ", start + 1)
    stops = [pos for pos in (next_def, next_async_def) if pos > start]
    end = min(stops) if stops else len(source)
    return source[start:end]


def test_tomorrow_helper_does_not_use_bad_datetime_pattern() -> None:
    helper = _function_body(_bot_source(), "_tomorrow_panama_date")
    assert_not_contains(helper, "datetime.datetime", "helper avoids module/class collision")

    namespace = {"timedelta": timedelta}
    exec(helper, namespace)
    expected = (datetime.now(ZoneInfo("America/Panama")) + timedelta(days=1)).date().isoformat()
    assert_true(namespace["_tomorrow_panama_date"]() == expected, "helper returns tomorrow in Panama")


def test_schedule_route_handles_without_datetime_attribute_error() -> None:
    parsed = parse_karen_task_schedule_for_tomorrow("Val, pon la tarea 1 para mañana")
    assert_true(parsed and parsed["number"] == 1, "schedule phrase recognized")

    schedule = _function_body(_bot_source(), "maybe_handle_karen_task_schedule_for_tomorrow")
    assert_contains(schedule, "Listo. Puse esta tarea para mañana", "success reply path exists")
    assert_contains(schedule, "upsert_commitment", "read-only task conversion path exists")
    assert_not_contains(schedule, "datetime.datetime", "schedule path avoids bad datetime pattern")
    assert_not_contains(schedule, "Draft follow-up", "does not fall through to draft follow-up")
    assert_not_contains(schedule, "vencimientos", "does not fall through to deadlines")
    assert_not_contains(schedule, "Documentos", "does not fall through to documents")
    assert_not_contains(schedule, "pendiente auxiliar", "does not expose internal language")


def main() -> int:
    test_tomorrow_helper_does_not_use_bad_datetime_pattern()
    test_schedule_route_handles_without_datetime_attribute_error()
    print("PASS: Karen task schedule datetime bug smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
