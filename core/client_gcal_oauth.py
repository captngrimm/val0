from __future__ import annotations

"""
Client-scoped Google Calendar OAuth skeleton.

V0 safety rules:
- Generates read-only auth URLs only.
- Does not exchange tokens yet.
- Does not write refresh tokens yet.
- Does not use legacy/global /etc/val0/gcal credentials for client status.
- OAuth client secret path may be shared app-level config for generating auth URLs,
  but user refresh tokens must be stored per-client later under:
  /etc/val0/clients/<client_id>/gcal/refresh_token
"""

import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

APP_CLIENT_SECRET_PATH = Path(
    os.getenv("VAL0_GCAL_OAUTH_CLIENT_SECRET", "/etc/val0/gcal/client_secret.json")
)

DEFAULT_REDIRECT_URI = os.getenv(
    "VAL0_GCAL_OAUTH_REDIRECT_URI",
    "http://omfgeeks.com:8080/oauth2callback",
)


@dataclass(frozen=True)
class ClientGCalOAuthLink:
    status: str
    client_id: str
    auth_url: Optional[str]
    state: Optional[str]
    scope: str
    redirect_uri: str
    reason: str = ""


def _safe_client_id(client_id: str) -> str:
    safe = "".join(
        ch for ch in (client_id or "").lower()
        if ch.isalnum() or ch in ("_", "-")
    ).strip()
    return safe or "unknown"


def _client_gcal_dir(client_id: str) -> Path:
    return Path("/etc/val0/clients") / _safe_client_id(client_id) / "gcal"


def build_client_gcal_auth_url(client_id: str) -> ClientGCalOAuthLink:
    """
    Build a Google Calendar read-only OAuth URL for a specific client.

    This function intentionally does NOT persist tokens.
    Token exchange/callback handling belongs in a later reviewed phase.
    """
    cid = _safe_client_id(client_id)

    if not APP_CLIENT_SECRET_PATH.exists():
        return ClientGCalOAuthLink(
            status="error",
            client_id=cid,
            auth_url=None,
            state=None,
            scope=" ".join(SCOPES),
            redirect_uri=DEFAULT_REDIRECT_URI,
            reason=f"missing_oauth_client_secret:{APP_CLIENT_SECRET_PATH}",
        )

    state = f"client:{cid}:{secrets.token_urlsafe(24)}"

    flow = Flow.from_client_secrets_file(
        str(APP_CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=DEFAULT_REDIRECT_URI,
    )

    auth_url, returned_state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="false",
        prompt="consent",
        state=state,
    )

    return ClientGCalOAuthLink(
        status="ok",
        client_id=cid,
        auth_url=auth_url,
        state=returned_state,
        scope=" ".join(SCOPES),
        redirect_uri=DEFAULT_REDIRECT_URI,
        reason="read_only_auth_url_generated_no_token_exchange",
    )



def parse_client_oauth_state(state: str) -> dict:
    """
    Parse and validate client OAuth state.

    Expected format:
    client:<client_id>:<random>

    V0 rules:
    - must start with client:
    - client_id must sanitize cleanly
    - random part must be present and long enough
    - returns safe structured result
    """
    raw = (state or "").strip()

    if not raw:
        return {
            "ok": False,
            "client_id": None,
            "reason": "missing_state",
        }

    parts = raw.split(":", 2)
    if len(parts) != 3 or parts[0] != "client":
        return {
            "ok": False,
            "client_id": None,
            "reason": "malformed_state",
        }

    raw_client_id = parts[1].strip()
    cid = _safe_client_id(raw_client_id)
    nonce = parts[2].strip()

    if cid == "unknown":
        return {
            "ok": False,
            "client_id": None,
            "reason": "missing_client_id",
        }

    if raw_client_id != cid:
        return {
            "ok": False,
            "client_id": cid,
            "reason": "client_id_not_canonical",
        }

    if len(nonce) < 16:
        return {
            "ok": False,
            "client_id": cid,
            "reason": "nonce_too_short",
        }

    return {
        "ok": True,
        "client_id": cid,
        "reason": "ok",
    }

def render_client_gcal_connect_message(client_id: str) -> str:
    link = build_client_gcal_auth_url(client_id)

    if link.status != "ok":
        return (
            "📅 Conectar Google Calendar\n\n"
            "Todavía no puedo generar el enlace de conexión.\n\n"
            f"Razón técnica: {link.reason}\n\n"
            "No se tocó ningún token ni calendario."
        )

    return (
        "📅 Conectar Google Calendar\n\n"
        "Puedo preparar la conexión de tu Google Calendar en modo seguro.\n\n"
        "Primero será solo lectura: Val podrá ver tus eventos para mostrarlos junto "
        "con tu agenda interna, pero no va a crear, cambiar ni borrar eventos.\n\n"
        "También será una conexión por cliente: no uso credenciales globales ni mezclo calendarios.\n\n"
        f"Enlace de autorización:\n{link.auth_url}\n\n"
        "Después de autorizar, todavía falta activar el callback seguro para guardar el token "
        "en tu carpeta de cliente."
    )
