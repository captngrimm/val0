from __future__ import annotations

import re
import unicodedata
from typing import Any


ADAPTIVE_INTAKE_STATE_KEY = "adaptive_intake_state"
_STAGE_PERMISSION = "adaptive_intake_permission"
_STAGE_DOMAIN = "adaptive_intake_domain"
_STAGE_FOLLOWUP = "adaptive_intake_followup"


def _strip_accents(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def normalize_adaptive_intake_text(text: str) -> str:
    value = _strip_accents(text).lower()
    value = re.sub(r"[¿?¡!.,:;]+", " ", value)
    value = re.sub(r"\b(?:valeria|vale|val|va\s+el|bal|pal)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _chat_data(context: Any) -> dict[str, Any]:
    chat_data = getattr(context, "chat_data", None)
    if isinstance(chat_data, dict):
        return chat_data
    return {}


def _set_state(context: Any, stage: str, **extra: Any) -> None:
    chat_data = _chat_data(context)
    if chat_data is not getattr(context, "chat_data", None):
        return
    chat_data[ADAPTIVE_INTAKE_STATE_KEY] = {"stage": stage, **extra}


def clear_adaptive_intake_state(context: Any) -> None:
    _chat_data(context).pop(ADAPTIVE_INTAKE_STATE_KEY, None)


def get_adaptive_intake_state(context: Any) -> dict[str, Any]:
    state = _chat_data(context).get(ADAPTIVE_INTAKE_STATE_KEY)
    return state if isinstance(state, dict) else {}


def is_adaptive_intake_trigger(text: str) -> bool:
    norm = normalize_adaptive_intake_text(text)
    if not norm:
        return False
    triggers = (
        "no se que necesito",
        "ayudame a empezar",
        "estoy perdida",
        "estoy perdido",
        "tengo demasiadas cosas",
        "no se por donde empezar",
    )
    return any(trigger in norm for trigger in triggers)


def classify_adaptive_intake_confirmation(text: str) -> str | None:
    norm = normalize_adaptive_intake_text(text)
    if not norm:
        return None
    if norm in {"no", "no quiero", "no quiero responder", "prefiero no", "no gracias"} or any(
        marker in norm for marker in ("no quiero responder", "prefiero no", "no gracias")
    ):
        return "refuse"
    if norm in {"si", "dale", "ok", "okay", "vamos", "correcto", "va", "listo"} or any(
        marker in norm for marker in ("dale", "vamos", "correcto")
    ):
        return "confirm"
    return None


def looks_like_too_broad(text: str) -> bool:
    norm = normalize_adaptive_intake_text(text)
    return norm in {"todo", "todos", "todo me sirve", "todo eso", "todo lo anterior"} or "todo me sirve" in norm


def classify_adaptive_intake_domain(text: str) -> str | None:
    norm = normalize_adaptive_intake_text(text)
    if not norm:
        return None
    if looks_like_too_broad(text):
        return "too_broad"
    domains = (
        ("time_day", ("tiempo", "dia", "agenda", "organizar mi dia", "calendario")),
        ("work", ("trabajo", "laboral", "turno", "oficina")),
        ("home_family", ("casa", "familia", "hogar", "hijos")),
        ("money_bills", ("dinero", "pagos", "cuentas", "facturas", "recibos")),
        ("documents_admin", ("documentos", "admin", "administrativo", "papeles", "caso")),
        ("clients_business", ("clientes", "cliente", "negocio", "ventas", "seguimiento")),
        ("ideas_projects", ("ideas", "proyectos", "proyecto")),
        ("routines_habits", ("rutinas", "rutina", "habitos", "hábitos", "habito", "hábito")),
    )
    for domain, markers in domains:
        if any(marker in norm for marker in markers):
            return domain
    return None


def render_adaptive_intake_permission_reply() -> str:
    return (
        "Te puedo hacer 2 o 3 preguntas rápidas para ubicarte mejor. "
        "No guardo nada sin que tú me confirmes. ¿Empezamos?"
    )


def render_adaptive_intake_domain_question() -> str:
    return (
        "Perfecto. ¿Dónde sientes más desorden ahora: tiempo/día, trabajo, casa/familia, "
        "dinero/pagos, documentos, clientes/negocio, ideas/proyectos o rutinas?\n\n"
        "Todavía no guardo nada ni creo acciones."
    )


def render_adaptive_intake_refusal_reply() -> str:
    return (
        "Perfecto, no pasa nada. Podemos seguir con ejemplos generales o escoger un flujo manualmente. "
        "No guardo nada y no activo tareas, recordatorios ni eventos."
    )


def render_adaptive_intake_too_broad_reply() -> str:
    return (
        "Total, pero si empezamos con todo nos ahogamos elegante. Escogemos uno primero: "
        "tiempo/día, trabajo, casa/familia, dinero/pagos, documentos, clientes/negocio, ideas/proyectos o rutinas.\n\n"
        "Todavía no guardo nada ni creo acciones."
    )


def render_adaptive_intake_domain_followup(domain: str) -> str:
    replies = {
        "time_day": "¿Dónde viven tus pendientes ahora: calendario, WhatsApp, notas, papel o en tu cabeza?",
        "work": "¿Qué tipo de trabajo haces y qué se te complica más: horarios, pendientes, seguimiento, cansancio, pagos o cosas que se olvidan?",
        "home_family": "¿Qué se te desordena más en casa/familia: compras, citas, pagos, tareas, rutinas o cosas que otros dependen de que recuerdes?",
        "money_bills": "¿El problema es recordar pagos, ordenar recibos, fechas límite o revisar qué falta pagar?",
        "documents_admin": "¿Qué quieres ordenar primero: documentos personales, un caso, contratos, recibos o algo administrativo?",
        "clients_business": "¿Qué se pierde más con clientes/negocio: próximo paso, fecha, contexto, promesa, cobro o seguimiento?",
        "ideas_projects": "¿Quieres capturar ideas, ordenarlas por proyecto o convertirlas en próximos pasos?",
        "routines_habits": "¿La rutina que quieres ordenar es diaria, semanal o mensual, y qué parte falla: empezar, recordar, cerrar o revisar?",
    }
    return f"{replies.get(domain, replies['time_day'])}\n\nNo guardo nada todavía; solo estoy entendiendo el primer flujo."


def render_adaptive_intake_followup_response(domain: str, text: str) -> str:
    norm = normalize_adaptive_intake_text(text)
    if domain == "work" and any(marker in norm for marker in ("cajera", "cajero")):
        return (
            "Perfecto. Entonces no te voy a vender un flujo de clientes si eso no aplica. "
            "Para tu caso podríamos empezar con horarios, pendientes, recordatorios, dinero/pagos "
            "o rutina después del turno. ¿Qué parte te pesa más?\n\n"
            "Todavía no guardo nada ni creo tareas, recordatorios ni eventos."
        )
    return (
        "Perfecto. Con eso ya puedo orientar mejor el primer flujo sin inventar de más. "
        "Mi recomendación sería escoger una parte pequeña para probar una semana y ajustar con tu feedback.\n\n"
        "Todavía no guardo nada ni creo tareas, recordatorios ni eventos."
    )


async def maybe_handle_adaptive_intake(update: Any, context: Any, text: str) -> bool:
    if not update or not getattr(update, "message", None):
        return False

    state = get_adaptive_intake_state(context)
    stage = state.get("stage")

    if stage == _STAGE_PERMISSION:
        decision = classify_adaptive_intake_confirmation(text)
        if decision == "confirm":
            _set_state(context, _STAGE_DOMAIN)
            await update.message.reply_text(render_adaptive_intake_domain_question())
            return True
        if decision == "refuse":
            clear_adaptive_intake_state(context)
            await update.message.reply_text(render_adaptive_intake_refusal_reply())
            return True
        return False

    if stage == _STAGE_DOMAIN:
        decision = classify_adaptive_intake_confirmation(text)
        if decision == "refuse":
            clear_adaptive_intake_state(context)
            await update.message.reply_text(render_adaptive_intake_refusal_reply())
            return True
        domain = classify_adaptive_intake_domain(text)
        if domain == "too_broad":
            await update.message.reply_text(render_adaptive_intake_too_broad_reply())
            return True
        if domain:
            _set_state(context, _STAGE_FOLLOWUP, domain=domain)
            await update.message.reply_text(render_adaptive_intake_domain_followup(domain))
            return True
        return False

    if stage == _STAGE_FOLLOWUP:
        decision = classify_adaptive_intake_confirmation(text)
        if decision == "refuse":
            clear_adaptive_intake_state(context)
            await update.message.reply_text(render_adaptive_intake_refusal_reply())
            return True
        if looks_like_too_broad(text):
            await update.message.reply_text(render_adaptive_intake_too_broad_reply())
            return True
        clear_adaptive_intake_state(context)
        await update.message.reply_text(render_adaptive_intake_followup_response(str(state.get("domain") or ""), text))
        return True

    if not is_adaptive_intake_trigger(text):
        return False
    _set_state(context, _STAGE_PERMISSION)
    await update.message.reply_text(render_adaptive_intake_permission_reply())
    return True
