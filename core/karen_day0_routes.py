from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


ROUTE_AGENDA_TOMORROW = "agenda_tomorrow"
ROUTE_CAPABILITY_WEEK = "capability_week"
ROUTE_FINCA_FACTS = "finca_facts"
ROUTE_DOCUMENT_INVENTORY = "document_inventory"
ROUTE_NEXT_ACTION = "next_action"


@dataclass(frozen=True)
class KarenDay0Route:
    name: str
    normalized: str
    confidence: float
    reason: str = ""


def normalize_karen_day0_prompt(text: str) -> str:
    """Normalize Karen Day0 demo prompts, including common voice-prefix noise."""
    norm = unicodedata.normalize("NFKD", (text or "").lower())
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = re.sub(r"[¿?¡!.,:;]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    norm = re.sub(r"^(a ver|bueno|ok|okay|oye)\s+", "", norm).strip()

    voice_prefixes = (
        r"va el",
        r"va al",
        r"vale",
        r"val",
        r"valeria",
        r"va",
    )
    changed = True
    while changed:
        changed = False
        for prefix in voice_prefixes:
            updated = re.sub(rf"^{prefix}\s+", "", norm).strip()
            if updated != norm:
                norm = updated
                changed = True

    norm = re.sub(r"^(el|al)\s+que\b", "que", norm).strip()
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def classify_karen_day0_route(text: str) -> KarenDay0Route:
    norm = normalize_karen_day0_prompt(text)
    if not norm:
        return KarenDay0Route("", norm, 0.0, "empty")

    if norm in {
        "que tengo manana",
        "que tengo para manana",
        "tengo para manana",
        "que hay manana",
        "que hay para manana",
    }:
        return KarenDay0Route(ROUTE_AGENDA_TOMORROW, norm, 0.98, "day0_tomorrow_agenda")

    if norm in {
        "que puedo hacer contigo esta semana",
        "que puedo probar contigo esta semana",
        "puedo probar contigo esta semana",
        "puedo probar val una semana",
        "puedo probar una semana",
    }:
        return KarenDay0Route(ROUTE_CAPABILITY_WEEK, norm, 0.96, "day0_week_capability")

    if (
        "finca 10082" in norm
        and any(marker in norm for marker in ("que sabes", "que tienes", "datos", "sabes de"))
    ):
        return KarenDay0Route(ROUTE_FINCA_FACTS, norm, 0.96, "day0_finca_facts")

    if norm in {
        "que documentos tengo",
        "que documentos tengo registrados",
        "documentos del caso",
        "documentos de mi caso",
    }:
        return KarenDay0Route(ROUTE_DOCUMENT_INVENTORY, norm, 0.96, "day0_document_inventory")

    if norm in {
        "que sigue para mi",
        "que sigue",
        "que hago ahora",
    }:
        return KarenDay0Route(ROUTE_NEXT_ACTION, norm, 0.92, "day0_next_action")

    return KarenDay0Route("", norm, 0.0, "no_match")
