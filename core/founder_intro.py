from __future__ import annotations

import re
import unicodedata
from typing import Any


INTENT_WHAT_ARE_YOU = "what_are_you"
INTENT_WHAT_CAN_YOU_DO = "what_can_you_do"
INTENT_VISION = "vision"
INTENT_LIMITATIONS = "limitations"
INTENT_FOUNDER_PLAN = "founder_plan"
INTENT_ROADMAP = "roadmap"
INTENT_TRIAL_GUIDANCE = "trial_guidance"
INTENT_UNKNOWN = "unknown"

SUPPORTED_INTENTS = {
    INTENT_WHAT_ARE_YOU,
    INTENT_WHAT_CAN_YOU_DO,
    INTENT_VISION,
    INTENT_LIMITATIONS,
    INTENT_FOUNDER_PLAN,
    INTENT_ROADMAP,
    INTENT_TRIAL_GUIDANCE,
}


def _normalize_text(text: Any) -> str:
    raw = str(text or "").strip().lower()
    decomposed = unicodedata.normalize("NFKD", raw)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_text)


def normalize_founder_intro_intent(text: Any) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return INTENT_UNKNOWN

    if any(
        phrase in normalized
        for phrase in (
            "que no puedes",
            "que no haces",
            "que falta",
            "que falta construir",
            "que no esta listo",
            "que no esta ready",
            "puedes leer todo",
            "limitaciones",
            "limites",
        )
    ):
        return INTENT_LIMITATIONS

    if any(
        phrase in normalized
        for phrase in (
            "plan founder",
            "plan fundador",
            "precio founder",
            "precio fundador",
            "cuanto cuesta",
            "que incluye 30",
            "$30",
            "30/mes",
        )
    ):
        return INTENT_FOUNDER_PLAN

    if any(
        phrase in normalized
        for phrase in (
            "trial",
            "prueba",
            "piloto",
            "como empiezo",
            "como comienzo",
            "como probar",
            "puedo probar",
            "por donde empiezo",
        )
    ):
        return INTENT_TRIAL_GUIDANCE

    if any(
        phrase in normalized
        for phrase in (
            "que viene despues",
            "roadmap",
            "hoja de ruta",
            "proximos pasos",
            "que van a construir",
        )
    ):
        return INTENT_ROADMAP

    if any(
        phrase in normalized
        for phrase in (
            "vision",
            "cual es la vision",
            "idea grande",
            "largo plazo",
            "hacia donde va",
        )
    ):
        return INTENT_VISION

    if any(
        phrase in normalized
        for phrase in (
            "que puedes hacer",
            "que haces",
            "para que sirves",
            "que incluye",
            "como me ayudas",
        )
    ):
        return INTENT_WHAT_CAN_YOU_DO

    if any(
        phrase in normalized
        for phrase in (
            "que eres",
            "que eres tu",
            "esto es un bot",
            "eres un bot",
            "que es val",
            "quien eres",
            "solo telegram",
            "es solo telegram",
        )
    ):
        return INTENT_WHAT_ARE_YOU

    return INTENT_UNKNOWN


def render_founder_vision_explanation(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Val es una capa operativa personal en founder-beta. Hoy empieza por Telegram "
        "porque es el primer cockpit práctico: rápido para capturar, responder y organizar. "
        "Pero Telegram no es todo el producto.\n\n"
        "La visión es una Val que ayude a ordenar memoria, documentos, recordatorios, "
        "decisiones, workflows y próximos pasos, con límites claros y uso guiado."
    )


def render_founder_limitations(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Todavía hay límites importantes. Val no debe prometer memoria mágica o sin límites, "
        "lectura perfecta de fotos, automatización completa de DOCX, acciones sin confirmación, "
        "ni sustituir criterio profesional.\n\n"
        "Tampoco es onboarding listo para que cualquiera lo configure solo. Si algo está guardado "
        "pero no leído, Val debe decirlo; si necesita revisión humana, también."
    )


def render_founder_pricing_explanation(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Para Friends & Family, el plan Val0 Personal founder puede mantenerse en $30/mes "
        "para uso personal. Ese precio no sube solo porque Val mejore con capacidades "
        "reutilizables.\n\n"
        "Las mejoras que fortalecen el producto pueden tratarse como R&D. Lo que queda aparte "
        "es custom pesado: integraciones, urgencias, negocio/equipo, dashboards, migraciones "
        "o soporte intensivo."
    )


def render_founder_trial_guidance(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Sí 😌 De hecho, lucky day: estás justo en el grupito founder que nos va a ayudar "
        "a probar Val en la vida real.\n\n"
        "Esta semana puedes usarla para agenda, recordatorios, documentos, finca/caso, "
        "próximos pasos y feedback. Es un piloto guiado: la forma segura de probar Val "
        "no es usarla para todo sin guía, ni que Val finja que ya lo hace todo, sino ver "
        "qué te sirve de verdad, qué confunde y qué debemos mejorar.\n\n"
        "Y si algo todavía está en roadmap, te lo voy a decir claro. Sin humo, sin magia barata."
    )


def _render_what_are_you(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Soy Val: una capa operativa personal en founder-beta. Hoy vivo primero en Telegram "
        "porque es el cockpit más práctico para empezar, pero no soy solo Telegram.\n\n"
        "La idea es ayudarte a no perder el hilo: memoria operativa, documentos, recordatorios, "
        "decisiones, workflows y próximos pasos, con límites claros."
    )


def _render_what_can_you_do(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Hoy Val puede ayudar en flujos concretos: recordatorios, tareas, notas, documentos, "
        "estado de uploads, cronologías, Daily Operator, preparación de reuniones y calendario "
        "con confirmaciones.\n\n"
        "No todo está habilitado para todos los chats. Depende de configuración, permisos y del "
        "workflow que se haya escogido para el piloto."
    )


def _render_roadmap(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "El roadmap va en dos capas. Una es la ruta general de Val: mejor memoria estructurada, "
        "mejor manejo de documentos, cronologías, Daily Operator y futuras interfaces más allá "
        "del primer cockpit.\n\n"
        "La otra es tu roadmap individual: elegir un workflow real, usarlo, ver dónde ayuda, "
        "y convertir lo reutilizable en mejora de producto."
    )


def _render_unknown_help(*, audience: str = "founder_user", language: str = "es") -> str:
    return (
        "Puedo explicarte Val en partes: qué soy, qué puedo hacer hoy, cuál es la visión, "
        "qué límites tengo, cómo funciona el plan founder o cómo empezar con un piloto guiado."
    )


def render_founder_intro_response(
    intent: Any,
    *,
    audience: str = "founder_user",
    language: str = "es",
) -> str:
    normalized = str(intent or "").strip().lower()
    if normalized == INTENT_WHAT_ARE_YOU:
        return _render_what_are_you(audience=audience, language=language)
    if normalized == INTENT_WHAT_CAN_YOU_DO:
        return _render_what_can_you_do(audience=audience, language=language)
    if normalized == INTENT_VISION:
        return render_founder_vision_explanation(audience=audience, language=language)
    if normalized == INTENT_LIMITATIONS:
        return render_founder_limitations(audience=audience, language=language)
    if normalized == INTENT_FOUNDER_PLAN:
        return render_founder_pricing_explanation(audience=audience, language=language)
    if normalized == INTENT_ROADMAP:
        return _render_roadmap(audience=audience, language=language)
    if normalized == INTENT_TRIAL_GUIDANCE:
        return render_founder_trial_guidance(audience=audience, language=language)
    return _render_unknown_help(audience=audience, language=language)
