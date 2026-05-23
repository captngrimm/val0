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
    apply_safe_warmth,
    compare_factual_payload_preserved,
    create_response_envelope,
    envelope_summary,
    render_envelope_text,
    render_polished_fixture_response,
    safe_response_type,
    safe_style_mode,
    should_allow_polish,
    validate_polished_text,
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
        rendered_text=(
            "Modo operador diario\n\n"
            "Hoy / Agenda\n"
            "- 2026-05-23 · Revisar agenda\n\n"
            "Siguiente accion: revisar agenda.\n\n"
            "Modo: lectura solamente. No creé, cambié ni borré nada."
        ),
        allowed_style_mode="warm",
        factual_payload={"next_action": "revisar agenda", "date": "2026-05-23", "secret": "do-not-leak"},
        metadata={"raw_path": "/opt/val0/private"},
    )
    assert_true(should_allow_polish(daily), "daily operator warm allowed")
    daily_polished = render_polished_fixture_response(daily)
    assert_true(daily_polished.startswith("Te lo ordeno en corto."), "daily warm intro")
    assert_true("Siguiente paso: toma primero lo que aparece como sugerido." in daily_polished, "daily warm outro")
    assert_true("Hoy / Agenda\n- 2026-05-23 · Revisar agenda" in daily_polished, "daily factual lines unchanged")
    assert_true(compare_factual_payload_preserved(daily, daily_polished), "daily payload preserved")
    assert_true(validate_polished_text(daily, daily_polished), "daily polished validates")

    technical = create_response_envelope(
        response_id="tech-1",
        response_type="technical",
        rendered_text="Parece que pegaste un comando.",
        allowed_style_mode="warm",
        safety_flags=[SafetyFlag.TECHNICAL_CONTENT.value],
    )
    assert_false(should_allow_polish(technical), "technical denied")
    assert_equal(render_polished_fixture_response(technical), render_envelope_text(technical), "technical unchanged")

    confirmation = create_response_envelope(
        response_id="confirm-1",
        response_type="confirmation",
        rendered_text="Confirmas?",
        allowed_style_mode="warm",
        safety_flags=["confirmation_required"],
    )
    assert_false(should_allow_polish(confirmation), "confirmation denied")
    assert_equal(render_polished_fixture_response(confirmation), render_envelope_text(confirmation), "confirmation unchanged")

    action_sensitive = create_response_envelope(
        response_id="action-1",
        response_type="info",
        rendered_text="Listo.",
        allowed_style_mode="warm",
        safety_flags=["action_sensitive"],
    )
    assert_false(should_allow_polish(action_sensitive), "action sensitive denied")
    assert_equal(render_polished_fixture_response(action_sensitive), render_envelope_text(action_sensitive), "action sensitive unchanged")

    legal_no_source = create_response_envelope(
        response_id="legal-1",
        response_type="info",
        rendered_text="Resumen legal.",
        allowed_style_mode="light",
        safety_flags=["legal_sensitive"],
    )
    assert_false(should_allow_polish(legal_no_source), "legal without provenance denied")
    assert_equal(render_polished_fixture_response(legal_no_source), render_envelope_text(legal_no_source), "legal no source unchanged")

    legal_with_source = create_response_envelope(
        response_id="legal-2",
        response_type="info",
        rendered_text="Resumen legal con fuente.\nFuente: case_note #42",
        allowed_style_mode="light",
        safety_flags=["legal_sensitive"],
        legal_boundary="No sustituye revision legal.",
        provenance=[{"source_type": "case_note", "source_id": "42", "raw_path": "/secret"}],
    )
    assert_true(should_allow_polish(legal_with_source), "legal with provenance light allowed")
    legal_polished = render_polished_fixture_response(legal_with_source)
    assert_true("Fuente: case_note #42" in legal_polished, "legal source line preserved")
    assert_true("No sustituye revision legal." in legal_polished, "legal boundary preserved")
    assert_true(validate_polished_text(legal_with_source, legal_polished), "legal polished validates")

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
    assert_equal(render_polished_fixture_response(doc_no_source), render_envelope_text(doc_no_source), "document summary unchanged")

    calendar_create = create_response_envelope(
        response_id="cal-1",
        response_type="calendar",
        rendered_text="Crear cita?",
        allowed_style_mode="light",
        metadata={"operation": "create"},
    )
    assert_false(should_allow_polish(calendar_create), "calendar create denied")
    assert_equal(render_polished_fixture_response(calendar_create), render_envelope_text(calendar_create), "calendar create unchanged")

    calendar_delete = create_response_envelope(
        response_id="cal-2",
        response_type="calendar",
        rendered_text="Borrar cita?",
        allowed_style_mode="light",
        metadata={"operation": "delete"},
    )
    assert_false(should_allow_polish(calendar_delete), "calendar delete denied")
    assert_equal(render_polished_fixture_response(calendar_delete), render_envelope_text(calendar_delete), "calendar delete unchanged")

    reminder_delete = create_response_envelope(
        response_id="rem-1",
        response_type="reminder",
        rendered_text="Cancelar recordatorio?",
        allowed_style_mode="light",
        metadata={"operation": "cancel"},
    )
    assert_false(should_allow_polish(reminder_delete), "reminder mutation denied")
    assert_equal(render_polished_fixture_response(reminder_delete), render_envelope_text(reminder_delete), "reminder mutation unchanged")

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

    fake_fact = daily_polished + "\n- Nueva cita inventada con Nora."
    assert_false(validate_polished_text(daily, fake_fact), "validator rejects fake fact/action")

    changed_date = daily_polished.replace("2026-05-23", "2026-05-24")
    assert_false(validate_polished_text(daily, changed_date), "validator rejects changed date")

    changed_source = legal_polished.replace("Fuente: case_note #42", "Fuente: case_note #99")
    assert_false(validate_polished_text(legal_with_source, changed_source), "validator rejects changed source line")

    removed_boundary = legal_polished.replace("\n\nNo sustituye revision legal.", "")
    assert_false(validate_polished_text(legal_with_source, removed_boundary), "validator rejects removed legal boundary")

    unsafe_warmth = apply_safe_warmth(daily, render_envelope_text(daily)) + "\nGuardé una tarea nueva."
    assert_false(validate_polished_text(daily, unsafe_warmth), "validator rejects added action claim")

    fallback = render_polished_fixture_response(add_safety_flag(daily, "action_sensitive"))
    assert_equal(fallback, render_envelope_text(daily), "unsafe polish fallback deterministic")

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
