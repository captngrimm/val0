#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOT = (ROOT / "bot.py").read_text(encoding="utf-8")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


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


def test_name_guard_covers_live_phrases() -> None:
    body = function_body("maybe_handle_karen_name_language_guard")
    for phrase in (
        "que apodo me tienes registrado",
        "cual es mi apodo registrado",
        "cual es mi nombre registrado",
    ):
        assert_contains(body, phrase, f"name query covers {phrase}")
    for phrase in ("apodo", "llamar", "oficial", "tany"):
        assert_contains(body, phrase, f"name change guard covers {phrase}")
    assert_contains(body, "Tu apodo registrado es: Tany", "query response uses Tany")
    assert_contains(body, "te voy a llamar Tany", "change response confirms Tany")
    assert_contains(body, "upsert_fact", "preferred name/language stored as fact, not case note")
    assert_contains(body, "preferred_name", "preferred name fact updated")
    assert_not_contains(body, "no puede", "does not claim nickname cannot change")
    assert_not_contains(body, "no puedo cambiar", "does not refuse nickname change")
    legacy = "Ins" + "anity"
    assert_not_contains(body, legacy, "does not leak legacy nickname")


def test_spanish_guard_covers_live_phrases() -> None:
    body = function_body("maybe_handle_karen_name_language_guard")
    for phrase in (
        "responde en espanol",
        "respondeme en espanol",
        "hablame en espanol",
    ):
        assert_contains(body, phrase, f"Spanish guard covers {phrase}")
    assert_contains(body, "preferred_language", "Spanish guard stores language preference")
    assert_contains(body, 'fact_value="es"', "Spanish guard stores Spanish")
    assert_contains(body, "Te respondo en español", "Spanish response is Spanish")
    assert_not_contains(body, "from now on", "Spanish guard does not reply in English")
    assert_not_contains(body, "case_notes", "Spanish guard does not store case facts")
    assert_not_contains(body, "insert_case", "Spanish guard does not store case facts")


def test_route_order_beats_legacy_and_llm_paths() -> None:
    handle = function_body("handle_text")
    pipeline = function_body("_process_text_pipeline")
    for body, label in ((handle, "handle_text"), (pipeline, "pipeline")):
        guard_idx = body.find("maybe_handle_karen_name_language_guard")
        gcal_idx = body.find("maybe_handle_karen_gcal_create_confirmation_first")
        assert_true(guard_idx >= 0, f"{label} has early name/language guard")
        assert_true(gcal_idx >= 0 and guard_idx < gcal_idx, f"{label} guard runs before later route gates")
    pipeline = function_body("_process_text_pipeline")
    assert_true(
        pipeline.find("maybe_handle_karen_name_language_guard") < pipeline.find("call_val_openai"),
        "deterministic guard appears before LLM gateway in pipeline",
    )


def main() -> int:
    test_name_guard_covers_live_phrases()
    test_spanish_guard_covers_live_phrases()
    test_route_order_beats_legacy_and_llm_paths()
    print("PASS: Karen natural name/language guard smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
