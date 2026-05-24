#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.founder_intro import (  # noqa: E402
    INTENT_FOUNDER_PLAN,
    INTENT_LIMITATIONS,
    INTENT_ROADMAP,
    INTENT_TRIAL_GUIDANCE,
    INTENT_UNKNOWN,
    INTENT_VISION,
    INTENT_WHAT_ARE_YOU,
    INTENT_WHAT_CAN_YOU_DO,
    SUPPORTED_INTENTS,
    normalize_founder_intro_intent,
    render_founder_intro_response,
    render_founder_pricing_explanation,
    render_founder_trial_guidance,
    render_founder_vision_explanation,
)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


PRIVATE_MARKERS = (
    "Karen",
    "CASE:KAREN",
    "finca 10082",
    "VFMS",
    "/opt/val0",
    "/etc/val0",
    "token",
    "OAuth",
    "systemd",
    "8660371933",
)

UNSAFE_CLAIMS = (
    "infinite memory",
    "memoria infinita",
    "perfect OCR",
    "OCR perfecto",
    "guaranteed DOCX",
    "DOCX garantizado",
    "autonomous actions",
    "acciones autónomas",
    "acciones autonomas",
    "reemplaza a tu abogado",
    "reemplaza profesionales",
    "self-serve onboarding is ready",
    "onboarding self-serve listo",
)


def assert_safe_response(text: str, label: str) -> None:
    assert_true(text.strip(), f"{label} non-empty")
    for marker in PRIVATE_MARKERS:
        assert_not_contains(text, marker, f"{label} private marker")
    for claim in UNSAFE_CLAIMS:
        assert_not_contains(text, claim, f"{label} unsafe claim")


def main() -> int:
    for intent in sorted(SUPPORTED_INTENTS):
        rendered = render_founder_intro_response(intent)
        assert_safe_response(rendered, intent)
        assert_contains(rendered, "Val", f"{intent} mentions Val")

    trigger_cases = {
        "Val, qué eres": INTENT_WHAT_ARE_YOU,
        "Val, qué puedes hacer": INTENT_WHAT_CAN_YOU_DO,
        "Val, cuál es la visión": INTENT_VISION,
        "Val, qué no puedes hacer todavía": INTENT_LIMITATIONS,
        "Val, cómo funciona el plan founder": INTENT_FOUNDER_PLAN,
        "Val, qué viene después": INTENT_ROADMAP,
        "Val, cómo empiezo una prueba": INTENT_TRIAL_GUIDANCE,
        "esto es un bot?": INTENT_WHAT_ARE_YOU,
        "esto es solo Telegram?": INTENT_WHAT_ARE_YOU,
        "para qué sirves": INTENT_WHAT_CAN_YOU_DO,
        "qué incluye $30": INTENT_FOUNDER_PLAN,
    }
    for phrase, expected in trigger_cases.items():
        assert_equal(normalize_founder_intro_intent(phrase), expected, f"intent for {phrase}")

    unknown_intent = normalize_founder_intro_intent("Val, cuéntame algo raro")
    assert_equal(unknown_intent, INTENT_UNKNOWN, "unknown phrase intent")
    unknown_response = render_founder_intro_response(unknown_intent)
    assert_safe_response(unknown_response, "unknown response")
    assert_contains(unknown_response, "piloto guiado", "unknown safe help mentions guided pilot")

    trial = render_founder_trial_guidance()
    assert_safe_response(trial, "trial guidance")
    assert_contains(trial, "no es usarla para todo sin guía", "trial rejects unguided everything framing")
    assert_contains(trial, "piloto guiado", "trial recommends guided pilot")

    pricing = render_founder_pricing_explanation()
    assert_safe_response(pricing, "pricing")
    assert_contains(pricing, "$30/mes", "pricing mentions founder price")
    assert_contains(pricing, "custom pesado", "pricing separates heavy custom work")
    assert_contains(pricing, "integraciones", "pricing separates integrations")

    vision = render_founder_vision_explanation()
    assert_safe_response(vision, "vision")
    assert_contains(vision, "primer cockpit", "vision says first cockpit")
    assert_contains(vision, "Telegram no es todo el producto", "vision says Telegram is not product")
    assert_contains(vision, "founder-beta", "vision says founder beta")

    limitations = render_founder_intro_response(INTENT_LIMITATIONS)
    assert_safe_response(limitations, "limitations")
    assert_contains(limitations, "no debe prometer", "limitations says not to promise")
    assert_contains(limitations, "revisión humana", "limitations mentions human review")

    print("PASS: founder intro smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
