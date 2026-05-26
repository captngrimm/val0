#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import render_document_inventory_compact  # noqa: E402
from core.founder_intro import render_founder_trial_guidance  # noqa: E402
from core.karen_day0_routes import (  # noqa: E402
    ROUTE_AGENDA_TOMORROW,
    ROUTE_CAPABILITY_WEEK,
    ROUTE_DOCUMENT_INVENTORY,
    ROUTE_FINCA_FACTS,
    ROUTE_NEXT_ACTION,
    classify_karen_day0_route,
)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() not in text.lower():
        raise AssertionError(f"{label}: missing {needle!r} in {text!r}")


def assert_not_contains(text: str, needle: str, label: str) -> None:
    if needle.lower() in text.lower():
        raise AssertionError(f"{label}: unexpected {needle!r} in {text!r}")


def test_route(prompt: str, expected: str) -> None:
    route = classify_karen_day0_route(prompt)
    assert_equal(route.name, expected, prompt)


def main() -> int:
    for prompt in (
        "Val, qué tengo mañana?",
        "va el que tengo mañana",
        "vale qué tengo mañana",
        "val que tengo mañana",
        "qué tengo mañana",
    ):
        test_route(prompt, ROUTE_AGENDA_TOMORROW)

    for prompt in (
        "Val, qué puedo hacer contigo esta semana?",
        "qué puedo hacer contigo esta semana",
        "qué puedo probar contigo esta semana",
    ):
        test_route(prompt, ROUTE_CAPABILITY_WEEK)

    for prompt in (
        "Val, qué sabes de la finca 10082?",
        "qué sabes de la finca 10082",
        "va al que sabes de la finca 10082",
    ):
        test_route(prompt, ROUTE_FINCA_FACTS)

    for prompt in (
        "Val, qué documentos tengo?",
        "qué documentos tengo",
        "documentos del caso",
    ):
        test_route(prompt, ROUTE_DOCUMENT_INVENTORY)

    test_route("Val, qué sigue para mí?", ROUTE_NEXT_ACTION)

    agenda_marker = "📅 Agenda de mañana\n\n🌐 Google Calendar"
    assert_contains(agenda_marker, "Agenda", "agenda marker")
    assert_contains(agenda_marker, "Google Calendar", "agenda source marker")

    capability = render_founder_trial_guidance()
    assert_contains(capability, "Esta semana", "capability says this week")
    assert_contains(capability, "puedes usarla", "capability explains use")

    finca = "Datos básicos de la finca / caso:\nFinca: 10082\nTomo/Rollo: 316\nFolio: 308"
    assert_contains(finca, "Finca: 10082", "finca facts marker")

    documents = render_document_inventory_compact([
        {
            "id": 1,
            "created_at": "2026-05-25 10:00:00",
            "filename": "foto_finca.jpg",
            "caption": "",
            "state": "guardado; requiere revisión",
            "raw": "",
            "has_caption": False,
        }
    ])
    assert_contains(documents, "Documentos", "document inventory marker")
    assert_contains(documents, "necesitan OCR/revisión", "document OCR marker")

    next_action_marker = "Siguiente acción sugerida\n- Próximo pendiente"
    assert_contains(next_action_marker, "Siguiente", "next action marker")
    assert_contains(next_action_marker, "Próximo", "next action next marker")
    assert_not_contains(next_action_marker, "roadmap", "next action is not roadmap")

    print("PASS: Karen Day0 route smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
