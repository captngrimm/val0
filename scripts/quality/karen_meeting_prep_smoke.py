#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.karen_meeting_prep import (
    looks_like_karen_meeting_prep_request,
    render_karen_meeting_prep_checklist,
)


def test_lawyer_prep_prompts_match():
    prompts = (
        "Val, prepárame para hablar con la abogada",
        "Val, preparame para hablar con Nora",
        "Val, prepárame para hablar con el advisor",
    )
    for prompt in prompts:
        assert looks_like_karen_meeting_prep_request(prompt), prompt


def test_unrelated_document_routes_do_not_match():
    prompts = (
        "Val, qué documentos tengo",
        "Val, dame el inventario técnico de documentos",
        "Val, ordéname la cronología del caso",
        "Val, resumen de documentos",
    )
    for prompt in prompts:
        assert not looks_like_karen_meeting_prep_request(prompt), prompt


def test_lawyer_prep_copy_is_checklist_not_dump():
    rendered = render_karen_meeting_prep_checklist("Val, prepárame para hablar con la abogada")

    assert "Prep para hablar con la abogada" in rendered
    assert "Objetivo de la reunión" in rendered
    assert "Documentos a tener a mano" in rendered
    assert "Preguntas sugeridas" in rendered
    assert "Pendiente antes de la reunión" in rendered
    assert "no sustituye criterio legal o profesional" in rendered

    forbidden = (
        "Resumen grounded de documentos",
        "VFMS",
        "Registro: #",
        "CASE:",
    )
    for token in forbidden:
        assert token not in rendered, token


def test_advisor_copy_uses_advisor_label():
    rendered = render_karen_meeting_prep_checklist("Val, prepárame para hablar con el advisor")
    assert "Prep para hablar con el advisor" in rendered
    assert "no sustituye criterio legal o profesional" in rendered


def main():
    test_lawyer_prep_prompts_match()
    test_unrelated_document_routes_do_not_match()
    test_lawyer_prep_copy_is_checklist_not_dump()
    test_advisor_copy_uses_advisor_label()
    print("PASS: Karen meeting prep smoke cases passed.")


if __name__ == "__main__":
    main()
