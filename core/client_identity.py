from __future__ import annotations

KAREN_CHAT_ID = 8660371933


def resolve_client_id(chat_id: int | str | None) -> str:
    if str(chat_id) == str(KAREN_CHAT_ID):
        return "karen"
    return ""


def client_profile(client_id: str | None) -> dict[str, str]:
    if client_id == "karen":
        return {
            "client_id": "karen",
            "display_name": "Karen",
            "vocative": "Insanity",
        }
    return {}


def client_vocative(client_id: str | None, prefix: str = ", ") -> str:
    profile = client_profile(client_id)
    vocative = profile.get("vocative")
    if not vocative:
        return ""
    return f"{prefix}{vocative}"
