#!/usr/bin/env python3
from __future__ import annotations

"""
PowerClub Val Mentor backend/proxy stub.

This is a safe scaffold, not a production service:
- no API key is accepted from the browser
- no real provider call is implemented in this lane
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
PROVIDER_ENV = "VAL_POWERCLUB_LLM_PROVIDER"
MODEL_ENV = "VAL_POWERCLUB_LLM_MODEL"
ALLOWED_DEMO_SECTIONS = {
    "Vista gerencial",
    "Riesgo y rescate",
    "Ficha del asesor",
    "Cola del asesor",
    "Templates / dictado",
    "Scope freeze / piloto",
}
ALLOWED_PROCESS_DOMAINS = {
    "Estructura del negocio",
    "Personas / roles",
    "Ventas / leads",
    "Seguimiento comercial",
    "Canales / herramientas",
    "Reportes / métricas",
    "Procesos / operación",
    "Dolores / riesgos",
    "Roadmap / piloto",
}
REQUIRED_RESPONSE_KEYS = {
    "val_message",
    "val_says",
    "summary",
    "detected_pain",
    "detected_domains",
    "follow_up_question",
    "next_question",
    "whiteboard_cards",
    "nodes_to_add",
    "nodes_to_update",
    "business_memory_update",
    "recommended_demo_section",
    "risk_flags",
    "out_of_scope",
    "out_of_scope_response",
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
            "val_says": "Modo local activo. Val puede seguir con reglas determinísticas y Frank mantiene control de la reunión.",
            "summary": "Backend LLM no disponible; usar captura local y whiteboard determinístico.",
            "detected_pain": "unknown",
            "detected_domains": [],
            "follow_up_question": "¿Qué punto conviene confirmar antes de avanzar?",
            "next_question": "¿Qué punto conviene confirmar antes de avanzar?",
            "whiteboard_cards": [],
            "nodes_to_add": [],
            "nodes_to_update": [],
            "business_memory_update": {
                "estructura": "por validar",
                "roles": "por validar",
                "canales": "por validar",
                "dolor_principal": "por validar",
                "metrica_a_validar": "por validar",
                "vista_recomendada": "Vista gerencial",
                "proxima_pregunta": "¿Qué punto conviene confirmar antes de avanzar?",
                "roadmap_piloto": "por validar",
            },
            "recommended_demo_section": "Vista gerencial",
            "risk_flags": ["No usar LLM si backend o configuración no están listos."],
            "out_of_scope": False,
            "out_of_scope_response": "",
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


def contains_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)


def scoped_domains(captured: str, category: str) -> list[str]:
    lower = captured.lower()
    domains: list[str] = []

    def add(domain: str) -> None:
        if domain not in domains:
            domains.append(domain)

    if contains_any(lower, {"sucursal", "sucursales", "sede", "sedes", "gimnasio", "ubicacion", "ubicación", "region", "región"}):
        add("Estructura del negocio")
    if contains_any(lower, {"asesor", "asesores", "vendedor", "vendedores", "responsable", "gerencia", "gerente", "supervisor", "operador"}):
        add("Personas / roles")
    if contains_any(lower, {"lead", "leads", "prospecto", "prospectos", "oportunidad", "oportunidades"}):
        add("Ventas / leads")
    if contains_any(lower, {"seguimiento", "contacto", "ultimo contacto", "último contacto", "24 horas", "+24", "sin contacto", "atrasado", "atrasados"}):
        add("Seguimiento comercial")
    if contains_any(lower, {"whatsapp", "llamada", "llamadas", "instagram", "facebook", "excel", "crm"}):
        add("Canales / herramientas")
    if contains_any(lower, {"gerencia necesita ver", "reporte", "reportes", "dashboard", "kpi", "métrica", "metrica", "por sucursal", "ranking", "tasa", "cuántos", "cuantos"}):
        add("Reportes / métricas")
    if contains_any(lower, {"asigna", "asignación", "asignacion", "atiende", "escala", "registra", "proceso"}):
        add("Procesos / operación")
    if contains_any(lower, {"perdido", "perdidos", "pierden", "sin contacto", "riesgo", "atrasado", "atrasados", "falta"}):
        add("Dolores / riesgos")
    if contains_any(lower, {"piloto", "fase", "alcance", "roadmap", "implementación", "implementacion"}):
        add("Roadmap / piloto")
    if category in {"seguimiento", "riesgo"}:
        add("Seguimiento comercial")
        add("Dolores / riesgos")
    if category in {"visibilidad", "metricas"}:
        add("Reportes / métricas")
    return domains or ["Procesos / operación"]


def node(domain: str, label: str, detail: str = "") -> dict[str, str]:
    return {"domain": domain, "label": label, "detail": detail}


def scoped_nodes(captured: str, domains: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    lower = captured.lower()
    nodes: list[dict[str, str]] = []
    updates: list[dict[str, str]] = []
    if "por sucursal" in lower or "sucursal" in lower:
        nodes.append(node("Estructura del negocio", "Por sucursal", "La vista debe segmentar riesgo y seguimiento por sede."))
    if "24" in lower or "+24" in lower or "más de 24" in lower or "mas de 24" in lower:
        nodes.append(node("Reportes / métricas", "Leads sin contacto +24h", "Indicador de oportunidades en riesgo."))
    if "asesor responsable" in lower or ("asesor" in lower and "responsable" in lower):
        updates.append({"domain": "Personas / roles", "match": "asesor", "label": "Asesor responsable"})
        nodes.append(node("Personas / roles", "Asesor responsable", "Dueño operativo del próximo contacto."))
    elif "asesor" in lower or "asesores" in lower:
        nodes.append(node("Personas / roles", "Asesores", "Rol operativo del seguimiento."))
    if "último contacto" in lower or "ultimo contacto" in lower:
        nodes.append(node("Seguimiento comercial", "Último contacto", "Campo clave para medir antigüedad del seguimiento."))
    if "whatsapp" in lower:
        nodes.append(node("Canales / herramientas", "WhatsApp", "Canal crítico del seguimiento comercial."))
    if "lead" in lower or "leads" in lower:
        nodes.append(node("Ventas / leads", "Leads en seguimiento", "Oportunidades que requieren dueño, estado y próximo paso."))
    if not nodes:
        primary = domains[0] if domains else "Procesos / operación"
        nodes.append(node(primary, captured[:72] or "Señal capturada", "Señal para validar en discovery."))
    return nodes, updates


def is_out_of_scope(captured: str) -> bool:
    lower = captured.lower()
    return contains_any(lower, {"inventario", "nómina", "nomina", "contabilidad", "erp", "pagos completos", "rrhh"})


def mock_suggestion(payload: dict[str, Any]) -> dict[str, Any]:
    captured = str(payload.get("captured_response") or "").strip()
    category = str(payload.get("selected_category") or "unknown").strip() or "unknown"
    summary = captured or "No hay respuesta capturada todavía."
    domains = scoped_domains(captured, category)
    nodes, updates = scoped_nodes(captured, domains)
    out_of_scope = is_out_of_scope(captured)
    if out_of_scope:
        demo_section = "Scope freeze / piloto"
        follow_up = "¿Esto debe quedar como posible fase dos fuera del piloto comercial?"
        val_says = "Eso se puede evaluar como fase posterior, pero no está dentro del piloto actual. Para esta reunión estoy enfocada en seguimiento comercial, visibilidad gerencial y rescate de oportunidades."
        detected_pain = "alcance"
    elif "Leads sin contacto +24h" in {item["label"] for item in nodes}:
        demo_section = "Riesgo y rescate"
        follow_up = "¿Cada cuánto necesita gerencia revisar esta vista: diario, semanal o por alerta?"
        val_says = "Estoy entendiendo una necesidad de reporte gerencial de riesgo: leads sin contacto por más de 24 horas, por sucursal y con asesor responsable."
        detected_pain = "seguimiento"
    elif "Seguimiento comercial" in domains:
        demo_section = "Riesgo y rescate"
        follow_up = "¿Qué umbral convierte una oportunidad en riesgo: 24 horas, 48 horas o una regla por tipo de lead?"
        val_says = "Estoy entendiendo un dolor de seguimiento comercial. Conviene validar umbral de atraso, responsable y frecuencia de revisión."
        detected_pain = "seguimiento"
    elif "Reportes / métricas" in domains:
        demo_section = "Vista gerencial"
        follow_up = "¿Qué tres indicadores necesita ver gerencia cada mañana para decidir dónde actuar?"
        val_says = "Estoy entendiendo una necesidad de visibilidad gerencial. Esto puede convertirse en una vista ejecutiva si Frank confirma campos y frecuencia."
        detected_pain = "visibilidad"
    else:
        demo_section, follow_up = category_to_demo(category)
        val_says = f"Si entiendo bien, esto apunta a {category}. Antes de seguir, conviene confirmar impacto, responsable y frecuencia."
        detected_pain = category
    memory = {
        "estructura": "por sucursal" if any(item["domain"] == "Estructura del negocio" for item in nodes) else "por validar",
        "roles": "Asesor responsable" if any(item.get("label") == "Asesor responsable" for item in nodes) else "por validar",
        "canales": "WhatsApp" if any(item.get("label") == "WhatsApp" for item in nodes) else "por validar",
        "dolor_principal": "Seguimiento comercial" if "Seguimiento comercial" in domains else "por validar",
        "metrica_a_validar": "Leads sin contacto +24h por sucursal" if "Leads sin contacto +24h" in {item["label"] for item in nodes} else "por validar",
        "vista_recomendada": demo_section,
        "proxima_pregunta": follow_up,
        "roadmap_piloto": "Vista de riesgo/rescate para seguimiento comercial" if demo_section == "Riesgo y rescate" else "por validar",
    }
    return {
        "val_message": val_says,
        "val_says": val_says,
        "summary": summary,
        "detected_pain": detected_pain,
        "detected_domains": domains,
        "follow_up_question": follow_up,
        "next_question": follow_up,
        "whiteboard_cards": [
            {
                "lane": "Señales / patrones",
                "title": nodes[0]["label"] if nodes else "Señal para validar",
                "body": summary,
                "category": detected_pain,
            }
        ] if captured else [],
        "nodes_to_add": nodes if captured else [],
        "nodes_to_update": updates,
        "business_memory_update": memory,
        "recommended_demo_section": demo_section,
        "risk_flags": ["Sugerencia mock; Frank debe confirmar antes de usar."] + (["Solicitud fuera de alcance del piloto actual."] if out_of_scope else []),
        "out_of_scope": out_of_scope,
        "out_of_scope_response": val_says if out_of_scope else "",
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
    if not set(suggestion.get("detected_domains") or []).issubset(ALLOWED_PROCESS_DOMAINS):
        return False, "detected_domains contains unsupported domain"
    if suggestion.get("needs_frank_confirmation") is not True:
        return False, "needs_frank_confirmation must be true"
    if not isinstance(suggestion.get("whiteboard_cards"), list):
        return False, "whiteboard_cards must be a list"
    if not isinstance(suggestion.get("nodes_to_add"), list):
        return False, "nodes_to_add must be a list"
    if not isinstance(suggestion.get("nodes_to_update"), list):
        return False, "nodes_to_update must be a list"
    if not isinstance(suggestion.get("business_memory_update"), dict):
        return False, "business_memory_update must be an object"
    if not isinstance(suggestion.get("risk_flags"), list):
        return False, "risk_flags must be a list"
    if suggestion.get("out_of_scope") not in {True, False}:
        return False, "out_of_scope must be boolean"
    return True, "ok"


def handle_mentor_request(payload: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    provider = (env.get(PROVIDER_ENV) or "").strip().lower()
    if truthy(env.get(MOCK_ENV)) or provider == "mock":
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

    model = env.get(MODEL_ENV, "unset")
    return safe_unavailable_response(f"provider-ready seam only; real provider call not implemented for provider={provider or 'unset'} model={model}")


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
