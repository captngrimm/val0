from __future__ import annotations

# Client contact registry v0. Keep client-specific contact data out of bot.py.
EMAIL_CONTACTS = {
    "miguel": "franklin.miranda.c@gmail.com",
    "frank": "franklin.miranda.c@gmail.com",
    "boss": "franklin.miranda.c@gmail.com",
    "karen": "karenmm20@gmail.com",
}


def get_email_contact(name: str | None) -> str | None:
    return EMAIL_CONTACTS.get((name or "").strip().lower())
