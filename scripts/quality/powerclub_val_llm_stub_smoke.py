#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STUB = ROOT / "tools" / "powerclub_val_llm_proxy_stub.py"
VAL_DISCOVERY = ROOT / "docs" / "demo" / "powerclub_crm" / "val_discovery.html"


def load_stub():
    spec = importlib.util.spec_from_file_location("powerclub_val_llm_proxy_stub", STUB)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load powerclub Val LLM stub")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def test_stub_contract() -> None:
    assert_true(STUB.exists(), "stub exists")
    stub = load_stub()
    payload = {
        "meeting_context": {"client_or_person": "PowerClub"},
        "current_question": "¿Dónde se pierden más oportunidades?",
        "captured_response": "Se enfrían por seguimiento tardío.",
        "selected_category": "seguimiento",
        "whiteboard_state": {},
        "allowed_demo_sections": list(stub.ALLOWED_DEMO_SECTIONS),
        "guardrails": ["no real data", "Frank approves"],
    }

    unavailable = stub.handle_mentor_request(payload, env={})
    assert_true(unavailable["status"] == "unavailable", "missing env returns unavailable")
    assert_true(unavailable["mode"] == "local_fallback", "missing env returns local fallback")
    assert_true(unavailable["suggestion"]["needs_frank_confirmation"] is True, "fallback requires Frank confirmation")

    mocked = stub.handle_mentor_request(payload, env={stub.MOCK_ENV: "1"})
    assert_true(mocked["status"] == "ok", "mock mode returns ok")
    assert_true(mocked["mode"] == "mock", "mock mode labeled")
    suggestion = mocked["suggestion"]
    valid, reason = stub.validate_suggestion(suggestion)
    assert_true(valid, f"mock suggestion validates: {reason}")
    for key in stub.REQUIRED_RESPONSE_KEYS:
        assert_true(key in suggestion, f"mock suggestion has {key}")
    assert_true(suggestion["needs_frank_confirmation"] is True, "new schema requires Frank confirmation")
    assert_true(isinstance(suggestion["detected_domains"], list), "new schema detected domains list")
    assert_true(isinstance(suggestion["nodes_to_add"], list), "new schema nodes_to_add list")
    assert_true(isinstance(suggestion["business_memory_update"], dict), "new schema memory update object")

    bad = dict(suggestion)
    bad["recommended_demo_section"] = "API conectada"
    valid, reason = stub.validate_suggestion(bad)
    assert_true(not valid and "recommended_demo_section" in reason, "invalid demo section rejected")

    management_payload = dict(payload)
    management_payload["captured_response"] = (
        "Gerencia necesita ver por sucursal cuántos leads están sin contacto por más de 24 horas, "
        "quién es el asesor responsable y cuál fue el último contacto."
    )
    management_payload["selected_category"] = "metricas"
    management = stub.handle_mentor_request(management_payload, env={stub.MOCK_ENV: "1"})
    assert_true(management["status"] == "ok", "management mock returns ok")
    management_suggestion = management["suggestion"]
    assert_true(management_suggestion["recommended_demo_section"] == "Riesgo y rescate", "management example maps to risk rescue")
    assert_true("Reportes / métricas" in management_suggestion["detected_domains"], "management example detects metrics")
    assert_true("Seguimiento comercial" in management_suggestion["detected_domains"], "management example detects follow-up")
    labels = {node["label"] for node in management_suggestion["nodes_to_add"]}
    assert_true("Leads sin contacto +24h" in labels, "management example adds +24h node")
    assert_true("Último contacto" in labels, "management example adds last contact node")
    assert_true(management_suggestion["business_memory_update"]["metrica_a_validar"] == "Leads sin contacto +24h por sucursal", "management memory metric updated")


def test_frontend_integration_seam() -> None:
    text = VAL_DISCOVERY.read_text(encoding="utf-8")
    for needle in (
        "Sugerir con Val",
        "Sugerencia de Val",
        "Modo local activo",
        "VAL_LLM_ENDPOINT",
        "buildValLlmRequest",
        "validateValMentorSuggestion",
        "showValMentorSuggestion",
        "acceptValMentorSuggestion",
    ):
        assert_contains(text, needle, "frontend LLM seam")
    assert_true("OPENAI_API_KEY" not in text, "frontend has no OpenAI API key name")
    assert_true("VAL_POWERCLUB_LLM_API_KEY" not in text, "frontend has no backend secret env name")


def main() -> int:
    test_stub_contract()
    test_frontend_integration_seam()
    print("PASS: PowerClub Val LLM stub smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
