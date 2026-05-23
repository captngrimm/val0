#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.conversation_router import (
    ConversationIntent,
    classify_deterministic_intent,
    normalize_message,
)


CASES = (
    ("cd /opt/val0 && git status", ConversationIntent.TECHNICAL_PASTE),
    ("Val, ¿qué tengo mañana?", ConversationIntent.AGENDA_QUERY),
    ("Val, tengo cita con Mabel mañana a las 6pm", ConversationIntent.CALENDAR_CREATE_CANDIDATE),
    ("Val, borra cita con Mabel", ConversationIntent.CALENDAR_DELETE_CANDIDATE),
    ("Val, agrega leche al super", ConversationIntent.GROCERY_CANDIDATE),
    ("qué datos tienes de la finca", ConversationIntent.LEGAL_FINCA_CANDIDATE),
)


def main() -> int:
    failures = []

    for text, expected in CASES:
        message = normalize_message(text)
        got = classify_deterministic_intent(message)
        if got != expected:
            failures.append((text, expected, got))

    if failures:
        print("FAIL: conversation router smoke mismatches")
        for text, expected, got in failures:
            print(f"- {text!r}: expected={expected.value} got={got.value}")
        return 1

    print(f"PASS: {len(CASES)} conversation router smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
