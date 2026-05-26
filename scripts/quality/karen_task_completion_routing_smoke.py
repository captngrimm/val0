#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_notes_tasks_visibility import auxiliary_task_items_from_lines, render_karen_tasks_view  # noqa: E402


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


def _normalize_like_bot(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[¿?¡!.,:;]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"^(val|valeria|vale)\s+", "", text).strip()


def test_completion_phrases_are_covered() -> None:
    completion = _function_body(_bot_source(), "maybe_handle_karen_task_completion")
    marker_match = re.search(r"completion_markers\s*=\s*\((?P<body>.*?)\)", completion, flags=re.S)
    assert_true(marker_match is not None, "completion marker tuple exists")
    markers = re.findall(r'"([^"]+)"', marker_match.group("body"))

    phrases = (
        "Val marca la tarea 1 como hecha.",
        "marca la tarea 1 como hecha",
        "marca como hecha la tarea 1",
        "ya hice la tarea 1",
        "cierra la tarea 1",
        "completa la tarea 1",
    )
    for phrase in phrases:
        norm = _normalize_like_bot(phrase)
        assert_true(any(marker in norm for marker in markers), f"completion phrase recognized: {phrase}")

    normalizer = _function_body(_bot_source(), "_normalize_task_completion_request")
    assert_contains(normalizer, r"marca\s+la\s+tarea", "normalizer handles mark-task-as-done word order")
    assert_contains(normalizer, r"cierra\s+la\s+tarea", "normalizer handles close task")
    assert_contains(normalizer, r"completa\s+la\s+tarea", "normalizer handles complete task")


def test_task_completion_runs_before_draft_followup() -> None:
    source = _bot_source()
    for function_name in ("handle_text", "_process_text_pipeline"):
        body = _function_body(source, function_name)
        completion_gate = body.find("maybe_handle_karen_task_completion")
        draft_call = body.find("draftfollowup_cmd")
        assert_true(completion_gate >= 0, f"{function_name} has task completion gate")
        if draft_call >= 0:
            assert_true(completion_gate < draft_call, f"{function_name} checks completion before draft follow-up")

    completion = _function_body(source, "maybe_handle_karen_task_completion")
    assert_not_contains(completion, "draftfollowup_cmd", "completion path does not call draft follow-up")
    assert_not_contains(completion, "Draft follow-up", "completion path does not include draft copy")


def test_read_only_task_copy_and_task_view_language() -> None:
    completion = _function_body(_bot_source(), "maybe_handle_karen_task_completion")
    assert_contains(completion, "Esa tarea está guardada como pendiente sin fecha", "read-only task reply is plain")
    assert_contains(completion, "convertirla a tarea formal para cerrarla", "read-only task closure limitation is plain")
    assert_not_contains(completion, "pendiente auxiliar", "read-only reply avoids internal label")
    assert_not_contains(completion, "CLIENT_GROCERY", "read-only reply avoids internal source")

    rendered = render_karen_tasks_view([], auxiliary_tasks=auxiliary_task_items_from_lines([
        "- pedir al topógrafo cotización",
    ]))
    assert_contains(rendered, "pedir al topógrafo cotización", "task view still shows pending task")
    assert_not_contains(rendered, "auxiliar", "task view does not expose auxiliary wording")


def main() -> int:
    test_completion_phrases_are_covered()
    test_task_completion_runs_before_draft_followup()
    test_read_only_task_copy_and_task_view_language()
    print("PASS: Karen task completion routing smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
