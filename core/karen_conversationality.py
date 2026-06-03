from __future__ import annotations

import re


KAREN_CLIENT_IDS = {"karen", "client-zero"}

KAREN_BANNED_CONVERSATIONALITY_LEAKS = (
    "bajar de peso",
    "task_high",
    "memoria pura",
)


_SAFE_OPENINGS: dict[str, tuple[str, ...]] = {
    "agenda": (
        "Tany, te dejo la agenda ordenada.",
        "Tany, aquí va la agenda, sin mezclar peras con expedientes.",
    ),
    "tasks": (
        "Tany, aquí van tus tareas pendientes.",
        "Tany, te separo lo accionable para que no se vuelva sopa.",
    ),
    "reminders": (
        "Tany, estos son los recordatorios que tengo vivos.",
        "Tany, aquí van tus recordatorios, limpios y numerados.",
    ),
}


def _is_karen_client(client_id: str | None) -> bool:
    return str(client_id or "").strip().lower() in KAREN_CLIENT_IDS


def _surface_group(surface: str) -> str:
    value = str(surface or "").strip().lower()
    if value.startswith("agenda"):
        return "agenda"
    if value.startswith("task"):
        return "tasks"
    if value.startswith("reminder"):
        return "reminders"
    return value


def _stable_variant(options: tuple[str, ...], key: str) -> str:
    if not options:
        return ""
    idx = sum(ord(ch) for ch in str(key or "")) % len(options)
    return options[idx]


def render_karen_safe_opening(client_id: str | None, *, surface: str) -> str:
    """
    Deterministic, non-LLM conversationality for Karen read/list responses.

    This helper does not decide routes, mutate state, or alter facts. It only
    adds a small opening line for safe read-only surfaces.
    """
    if not _is_karen_client(client_id):
        return ""
    group = _surface_group(surface)
    opening = _stable_variant(_SAFE_OPENINGS.get(group, ()), surface)
    for banned in KAREN_BANNED_CONVERSATIONALITY_LEAKS:
        if banned in opening.lower():
            return ""
    return opening


def add_karen_safe_opening(text: str, client_id: str | None, *, surface: str) -> str:
    body = str(text or "").strip()
    opening = render_karen_safe_opening(client_id, surface=surface)
    if not opening:
        return body
    if re.match(r"^\s*Tany[,.]", body):
        return body
    return f"{opening}\n\n{body}" if body else opening
