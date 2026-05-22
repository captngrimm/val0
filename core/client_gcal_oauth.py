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


def preview_client_oauth_callback(state: str, code_present: bool) -> dict:
    """
    Validate an OAuth callback request without exchanging tokens.

    V0 safety behavior:
    - validates state
    - checks whether code is present
    - does NOT call Google
    - does NOT write refresh tokens
    - does NOT log secrets
    - returns a safe structured preview
    """
    parsed = parse_client_oauth_state(state)

    if not parsed.get("ok"):
        return {
            "ok": False,
            "client_id": parsed.get("client_id"),
            "status": "rejected",
            "reason": parsed.get("reason"),
            "would_exchange_token": False,
            "would_store_token": False,
        }

    if not code_present:
        return {
            "ok": False,
            "client_id": parsed.get("client_id"),
            "status": "rejected",
            "reason": "missing_authorization_code",
            "would_exchange_token": False,
            "would_store_token": False,
        }

    return {
        "ok": True,
        "client_id": parsed.get("client_id"),
        "status": "validated_preview_only",
        "reason": "state_valid_code_present_no_token_exchange",
        "would_exchange_token": False,
        "would_store_token": False,
        "target_token_path": str(_client_gcal_dir(parsed.get("client_id")) / "refresh_token"),
        "mode": "read_only",
    }


def render_client_oauth_callback_preview(state: str, code_present: bool) -> str:
    """
    Render a safe human-readable callback preview.

    No secrets. No code echo. No token exchange.
    """
    result = preview_client_oauth_callback(state, code_present)

    if not result.get("ok"):
        return (
            "📅 Google Calendar OAuth callback\n\n"
            "Estado: rechazado\n"
            f"Razón: {result.get('reason')}\n\n"
            "No se intercambió token y no se guardó nada."
        )

    return (
        "📅 Google Calendar OAuth callback\n\n"
        "Estado: validado en modo preview.\n"
        f"Cliente: {result.get('client_id')}\n"
        "Modo: solo lectura\n\n"
        "No se intercambió token y no se guardó nada todavía.\n"
        f"Ruta futura del token: {result.get('target_token_path')}"
    )

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
