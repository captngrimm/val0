#!/usr/bin/env python3
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.response_envelope import (  # noqa: E402
    ResponseType,
    SafetyFlag,
    StyleMode,
    add_safety_flag,
    create_response_envelope,
    envelope_summary,
    render_envelope_text,
    safe_response_type,
    safe_style_mode,
    should_allow_polish,
)


def assert_true(value, label):
    if not value:
        raise AssertionError(label)


def assert_false(value, label):
    if value:
        raise AssertionError(label)


def assert_equal(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main():
    daily = create_response_envelope(
        response_id="daily-1",
        client_id="client-a",
        source_route="karen_daily_operator_v0",
        response_type="daily_operator",
        rendered_text="Modo operador diario\n\nSiguiente accion: revisar agenda.",
        allowed_style_mode="warm",
        factual_payload={"next_action": "revisar agenda", "secret": "do-not-leak"},
        metadata={"raw_path": "/opt/val0/private"},
    )
    assert_true(should_allow_polish(daily), "daily operator warm allowed")

    technical = create_response_envelope(
        response_id="tech-1",
        response_type="technical",
        rendered_text="Parece que pegaste un comando.",
        allowed_style_mode="warm",
        safety_flags=[SafetyFlag.TECHNICAL_CONTENT.value],
    )
    assert_false(should_allow_polish(technical), "technical denied")

    confirmation = create_response_envelope(
        response_id="confirm-1",
        response_type="confirmation",
        rendered_text="Confirmas?",
        allowed_style_mode="warm",
        safety_flags=["confirmation_required"],
    )
    assert_false(should_allow_polish(confirmation), "confirmation denied")

    action_sensitive = create_response_envelope(
        response_id="action-1",
        response_type="info",
        rendered_text="Listo.",
        allowed_style_mode="warm",
        safety_flags=["action_sensitive"],
    )
    assert_false(should_allow_polish(action_sensitive), "action sensitive denied")

    legal_no_source = create_response_envelope(
        response_id="legal-1",
        response_type="info",
        rendered_text="Resumen legal.",
        allowed_style_mode="light",
        safety_flags=["legal_sensitive"],
    )
    assert_false(should_allow_polish(legal_no_source), "legal without provenance denied")

    legal_with_source = create_response_envelope(
        response_id="legal-2",
        response_type="info",
        rendered_text="Resumen legal con fuente.",
        allowed_style_mode="light",
        safety_flags=["legal_sensitive"],
        provenance=[{"source_type": "case_note", "source_id": "42", "raw_path": "/secret"}],
    )
    assert_true(should_allow_polish(legal_with_source), "legal with provenance light allowed")

    legal_too_warm = create_response_envelope(
        response_id="legal-3",
        response_type="info",
        rendered_text="Resumen legal con fuente.",
        allowed_style_mode="warm",
        safety_flags=["legal_sensitive"],
        provenance=[{"source_type": "case_note", "source_id": "42"}],
    )
    assert_false(should_allow_polish(legal_too_warm), "legal warm denied")

    doc_no_source = create_response_envelope(
        response_id="doc-1",
        response_type="document_summary",
        rendered_text="Documento dice...",
        allowed_style_mode="light",
    )
    assert_false(should_allow_polish(doc_no_source), "document summary without source denied")

    calendar_create = create_response_envelope(
        response_id="cal-1",
        response_type="calendar",
        rendered_text="Crear cita?",
        allowed_style_mode="light",
        metadata={"operation": "create"},
    )
    assert_false(should_allow_polish(calendar_create), "calendar create denied")

    calendar_delete = create_response_envelope(
        response_id="cal-2",
        response_type="calendar",
        rendered_text="Borrar cita?",
        allowed_style_mode="light",
        metadata={"operation": "delete"},
    )
    assert_false(should_allow_polish(calendar_delete), "calendar delete denied")

    reminder_delete = create_response_envelope(
        response_id="rem-1",
        response_type="reminder",
        rendered_text="Cancelar recordatorio?",
        allowed_style_mode="light",
        metadata={"operation": "cancel"},
    )
    assert_false(should_allow_polish(reminder_delete), "reminder mutation denied")

    with_boundary = create_response_envelope(
        response_id="boundary-1",
        response_type="info",
        rendered_text="Texto deterministico.",
        legal_boundary="No sustituye revision legal.",
    )
    assert_equal(
        render_envelope_text(with_boundary),
        "Texto deterministico.\n\nNo sustituye revision legal.",
        "render preserves deterministic text plus boundary",
    )
    assert_equal(render_envelope_text(daily), daily.rendered_text, "render preserves deterministic text")

    flagged = add_safety_flag(daily, "no_polish")
    assert_false(should_allow_polish(flagged), "added no_polish flag denied")

    assert_equal(safe_response_type("bad type"), "info", "bad response type fallback")
    assert_equal(safe_style_mode("too much"), "none", "bad style mode fallback")

    summary = envelope_summary(daily)
    summary_text = str(summary)
    assert_false("do-not-leak" in summary_text, "summary no factual payload leak")
    assert_false("/opt/val0" in summary_text, "summary no metadata path leak")
    assert_equal(summary["provenance_count"], 0, "summary provenance count")
    assert_true(summary["polish_allowed"], "summary polish allowed")

    provenance_summary = envelope_summary(legal_with_source)
    assert_false("/secret" in str(provenance_summary), "summary no provenance raw path")
    assert_equal(provenance_summary["provenance_count"], 1, "summary provenance count sourced")

    print("PASS: response envelope smoke cases passed.")


if __name__ == "__main__":
    main()
