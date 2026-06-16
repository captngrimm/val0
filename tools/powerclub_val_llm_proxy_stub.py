#!/usr/bin/env python3
from __future__ import annotations

"""
PowerClub Val Mentor backend/proxy stub.

This is a safe scaffold, not a production service:
- no API key is accepted from the browser
- no real provider call is implemented
- no persistence or database
- mock mode is explicit through VAL_POWERCLUB_LLM_MOCK_ENABLED
- missing provider key returns a safe unavailable response
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


PROMPT_CAPSULE_DOC = "docs/product/POWERCLUB_CRM_VAL_LLM_PROMPT_CAPSULE_02E_V1.md"
API_KEY_ENV = "VAL_POWERCLUB_LLM_API_KEY"
MOCK_ENV = "VAL_POWERCLUB_LLM_MOCK_ENABLED"
ALLOWED_DEMO_SECTIONS = {
    "Vista gerencial",
    "Riesgo y rescate",
    "Ficha del asesor",
    "Cola del asesor",
    "Templates / dictado",
    "Scope freeze / piloto",
}
REQUIRED_RESPONSE_KEYS = {
    "val_message",
    "summary",
    "detected_pain",
    "follow_up_question",
    "whiteboard_cards",
    "recommended_demo_section",
    "risk_flags",
    "next_step",
    "confidence",
    "needs_frank_confirmation",
}


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def safe_unavailable_response(reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "mode": "local_fallback",
        "reason": reason,
        "suggestion": {
            "val_message": "Modo local activo. Val puede seguir con reglas determinísticas y Frank mantiene control de la reunión.",
            "summary": "Backend LLM no disponible; usar captura local y whiteboard determinístico.",
            "detected_pain": "unknown",
            "follow_up_question": "¿Qué punto conviene confirmar antes de avanzar?",
            "whiteboard_cards": [],
            "recommended_demo_section": "Vista gerencial",
            "risk_flags": ["No usar LLM si backend o configuración no están listos."],
            "next_step": "Continuar con modo local y confirmar alcance antes de prometer capacidades.",
            "confidence": "low",
            "needs_frank_confirmation": True,
        },
    }


def category_to_demo(category: str) -> tuple[str, str]:
    normalized = (category or "").strip().lower()
    if normalized in {"seguimiento", "riesgo"}:
        return "Riesgo y rescate", "¿Cuántas oportunidades se enfrían por falta de contacto a tiempo?"
    if normalized in {"asesor", "flujo asesor"}:
        return "Cola del asesor", "¿Qué tendría que hacer el asesor en menos clics?"
    if normalized in {"datos", "fuentes", "data"}:
        return "Scope freeze / piloto", "¿De dónde saldría la base aprobada para el piloto?"
    if normalized in {"alcance", "piloto"}:
        return "Scope freeze / piloto", "¿Esto entra en V1 o queda para fase dos?"
    if normalized in {"visibilidad", "gerencial"}:
        return "Vista gerencial", "¿Qué necesita ver gerencia cada mañana para decidir dónde actuar?"
    return "Vista gerencial", "¿Qué señal debe confirmar gerencia antes de avanzar?"


def mock_suggestion(payload: dict[str, Any]) -> dict[str, Any]:
    captured = str(payload.get("captured_response") or "").strip()
    category = str(payload.get("selected_category") or "unknown").strip() or "unknown"
    demo_section, follow_up = category_to_demo(category)
    summary = captured or "No hay respuesta capturada todavía."
    return {
        "val_message": f"Si entiendo bien, esto apunta a {category}. Antes de seguir, conviene confirmar impacto y responsable.",
        "summary": summary,
        "detected_pain": category,
        "follow_up_question": follow_up,
        "whiteboard_cards": [
            {
                "lane": "Señales / patrones",
                "title": "Señal para validar",
                "body": summary,
                "category": category,
            }
        ] if captured else [],
        "recommended_demo_section": demo_section,
        "risk_flags": ["Sugerencia mock; Frank debe confirmar antes de usar."],
        "next_step": "Frank confirma la lectura y decide si mostrar la sección recomendada.",
        "confidence": "medium" if captured else "low",
        "needs_frank_confirmation": True,
    }


def validate_suggestion(suggestion: dict[str, Any]) -> tuple[bool, str]:
    missing = REQUIRED_RESPONSE_KEYS.difference(suggestion)
    if missing:
        return False, f"missing keys: {sorted(missing)}"
    if suggestion.get("recommended_demo_section") not in ALLOWED_DEMO_SECTIONS:
        return False, "recommended_demo_section not allowed"
    if suggestion.get("needs_frank_confirmation") is not True:
        return False, "needs_frank_confirmation must be true"
    if not isinstance(suggestion.get("whiteboard_cards"), list):
        return False, "whiteboard_cards must be a list"
    if not isinstance(suggestion.get("risk_flags"), list):
        return False, "risk_flags must be a list"
    return True, "ok"


def handle_mentor_request(payload: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    if truthy(env.get(MOCK_ENV)):
        suggestion = mock_suggestion(payload)
        valid, reason = validate_suggestion(suggestion)
        if not valid:
            return safe_unavailable_response(f"mock response invalid: {reason}")
        return {
            "status": "ok",
            "mode": "mock",
            "prompt_capsule": PROMPT_CAPSULE_DOC,
            "suggestion": suggestion,
        }

    if not env.get(API_KEY_ENV):
        return safe_unavailable_response(f"{API_KEY_ENV} missing")

    return safe_unavailable_response("real provider call is not implemented in this scaffold")


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            mode = "mock" if truthy(os.getenv(MOCK_ENV)) else "unavailable"
            self._json(200, {"status": "ok", "service": "powerclub-val-llm-stub", "mode": mode})
            return
        self._json(404, {"status": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/powerclub/val/mentor-suggest":
            self._json(404, {"status": "not_found"})
            return
        length = min(int(self.headers.get("Content-Length", "0") or 0), 24_000)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, safe_unavailable_response("invalid JSON"))
            return
        body = handle_mentor_request(payload)
        self._json(200 if body.get("status") == "ok" else 503, body)


def main() -> int:
    host = os.getenv("VAL_POWERCLUB_LLM_STUB_HOST", "127.0.0.1")
    port = int(os.getenv("VAL_POWERCLUB_LLM_STUB_PORT", "8765"))
    server = HTTPServer((host, port), Handler)
    print(f"PowerClub Val LLM stub listening on http://{host}:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
