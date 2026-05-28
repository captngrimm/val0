#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.document_inventory_queries import _parse_note as inventory_parse_note  # noqa: E402
from core.document_inventory_queries import render_document_inventory_compact  # noqa: E402
from core.document_summary_queries import (  # noqa: E402
    _alias_save_confirmation_reply,
    _doc_match_keys,
    _doc_match_score,
    _extract_document_alias_save_request,
    _parse_note as summary_parse_note,
    _with_document_alias_metadata,
    build_document_naming_metadata,
    render_document_naming_metadata_suggestion,
)


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


def _agi_doc() -> dict:
    return {
        "filename": "Agi.pdf",
        "ingest_id": "20260528_000002",
        "state": "texto extraído e indexado; resumen disponible",
        "saved_summary": "📋 Resumen claro\n- El documento habla de AGI, predicciones y timelines para 2028 y 2030.",
        "text": (
            "AGI predictions and AI timeline. "
            "The document discusses artificial general intelligence, forecasts, 2028, and 2030."
        ),
    }


def _vfms_note() -> str:
    return "\n".join([
        "Documento recibido via Telegram",
        "- Archivo: Agi.pdf",
        "- VFMS ingest_id: 20260528_000002",
        "- Nota usuario: Val, transcribe este documento y hazme un resumen",
        "- Estado: texto extraído e indexado; resumen disponible",
    ])


def test_alias_save_phrases_are_recognized() -> None:
    for phrase in (
        "Val, guarda ese nombre",
        "guarda ese nombre",
        "sí, guárdalo",
        "usa ese nombre",
        "guarda ese nombre y etiquetas",
    ):
        req = _extract_document_alias_save_request(phrase)
        assert_true(req.get("kind") == "confirm", f"confirmation phrase recognized: {phrase}")

    explicit = _extract_document_alias_save_request(
        "Val, guarda AGI_Predicciones_y_Timeline_2028_2030 para agi pdf"
    )
    assert_true(explicit.get("kind") == "explicit", "explicit save recognized")
    assert_true(explicit.get("alias") == "AGI_Predicciones_y_Timeline_2028_2030", "explicit alias preserved")
    assert_true(explicit.get("target") == "agi pdf", "explicit target parsed")

    rename = _extract_document_alias_save_request(
        "Val, renombra agi pdf como AGI_Predicciones_y_Timeline_2028_2030"
    )
    assert_true(rename.get("kind") == "explicit", "rename-as save recognized")
    assert_true(rename.get("target") == "agi pdf", "rename target parsed")
    assert_true(rename.get("alias") == "AGI_Predicciones_y_Timeline_2028_2030", "rename alias parsed")


def test_alias_metadata_round_trip_and_matching() -> None:
    doc = _agi_doc()
    metadata = build_document_naming_metadata(doc, case_id="KAREN-LAND-001")
    assert_true(metadata["alias"] == "AGI_Predicciones_y_Timeline_2028_2030", "content-aware alias generated")
    assert_true("AGI" in metadata["tags"], "content-aware tag generated")

    updated = _with_document_alias_metadata(
        _vfms_note(),
        alias=metadata["alias"],
        tags=metadata["tags"],
        folder=metadata["folder"],
        why_it_matters=metadata["why_it_matters"],
    )
    parsed = summary_parse_note(updated)
    assert_true(parsed["alias"] == "AGI_Predicciones_y_Timeline_2028_2030", "summary parser reads alias")
    assert_contains(parsed["tags"], "inteligencia artificial", "summary parser reads tags")
    assert_true(_doc_match_score(_doc_match_keys(metadata["alias"]), parsed) > 0, "alias matches document")
    assert_true(_doc_match_score(_doc_match_keys("Agi.pdf"), parsed) > 0, "original filename still matches")

    inv = inventory_parse_note(updated)
    rendered = render_document_inventory_compact([
        {
            "id": 1,
            "created_at": "2026-05-28 10:00:00",
            **inv,
        }
    ])
    assert_contains(rendered, "AGI_Predicciones_y_Timeline_2028_2030", "inventory prefers alias")
    assert_contains(rendered, "Original: Agi.pdf", "inventory preserves original filename")
    assert_contains(rendered, "1 con resumen disponible", "inventory still counts summary")
    assert_not_contains(rendered, "renombré", "inventory does not claim physical rename")
    assert_not_contains(rendered, "/opt/val0", "inventory hides internal paths")


def test_confirmation_reply_is_non_destructive() -> None:
    reply = _alias_save_confirmation_reply(
        "AGI_Predicciones_y_Timeline_2028_2030",
        "Agi.pdf",
        ["AGI", "inteligencia artificial", "2028", "2030"],
    )
    assert_contains(reply, "Guardé este nombre", "save confirmation")
    assert_contains(reply, "AGI_Predicciones_y_Timeline_2028_2030", "alias shown")
    assert_contains(reply, "El archivo original sigue intacto: Agi.pdf.", "original preserved")
    assert_contains(reply, "También guardé estas etiquetas", "tags saved")
    assert_not_contains(reply, "renombré el archivo", "no destructive rename")
    assert_not_contains(reply, "CLIENT_GROCERY", "no internal file")


def test_suggestion_still_read_only_until_confirmation() -> None:
    rendered = render_document_naming_metadata_suggestion(_agi_doc(), case_id="KAREN-LAND-001")
    assert_contains(rendered, "Todavía no cambié el nombre", "suggestion remains read-only")
    assert_contains(rendered, "guardar este nombre", "confirmation next action")
    assert_not_contains(rendered, "Guardé este nombre", "suggestion does not claim save")


def test_route_priority_is_wired_before_naming_inventory() -> None:
    handle_text = _function_body(_bot_source(), "handle_text")
    alias_gate = handle_text.find("maybe_handle_document_alias_save_query")
    naming_gate = handle_text.find("maybe_handle_document_naming_metadata_query")
    inventory_query = handle_text.find("maybe_handle_document_query")

    assert_true(alias_gate >= 0, "handle_text has alias save gate")
    assert_true(naming_gate >= 0, "handle_text has naming gate")
    assert_true(alias_gate < naming_gate, "alias save beats naming suggestions")
    assert_true(inventory_query < 0 or alias_gate < inventory_query, "alias save beats inventory")


def main() -> int:
    test_alias_save_phrases_are_recognized()
    test_alias_metadata_round_trip_and_matching()
    test_confirmation_reply_is_non_destructive()
    test_suggestion_still_read_only_until_confirmation()
    test_route_priority_is_wired_before_naming_inventory()
    print("PASS: Karen document alias save smoke cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
