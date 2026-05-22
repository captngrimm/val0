from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ClientCalendarConfig:
    client_id: str
    provider: str
    connection_status: str
    calendar_id: Optional[str]
    token_ref: Optional[str]
    read_enabled: bool
    write_enabled: bool
    notes: str = ""


def _client_gcal_dir(client_id: str) -> Path:
    safe = "".join(ch for ch in (client_id or "").lower() if ch.isalnum() or ch in ("_", "-")).strip()
    if not safe:
        safe = "unknown"
    return Path("/etc/val0/clients") / safe / "gcal"


def get_client_calendar_config(client_id: str) -> ClientCalendarConfig:
    """
    Resolve calendar connection status for a client.

    V0 rule:
    - Do not use the legacy/global /etc/val0/gcal as a client calendar.
    - Only report connected if client-specific token/config exists.
    - Secrets are stored outside repo under /etc/val0/clients/<client_id>/gcal/.
    """
    cid = (client_id or "").strip().lower() or "unknown"

    try:
        from core.client_gcal_read import client_gcal_status

        status = client_gcal_status(cid)
        token_ref = str(Path(status.get("base_path", "")) / "refresh_token")

        if status.get("status") != "connected":
            missing = ", ".join(status.get("missing") or [])
            return ClientCalendarConfig(
                client_id=cid,
                provider="google_calendar",
                connection_status="not_connected",
                calendar_id=None,
                token_ref=token_ref,
                read_enabled=False,
                write_enabled=False,
                notes=(
                    "Client-specific Google Calendar is not connected. "
                    f"Missing: {missing or 'unknown'}. "
                    f"uses_legacy_global={status.get('uses_legacy_global')}"
                ),
            )

        return ClientCalendarConfig(
            client_id=cid,
            provider="google_calendar",
            connection_status="connected",
            calendar_id=status.get("calendar_id") or "primary",
            token_ref=token_ref,
            read_enabled=True,
            write_enabled=False,
            notes=(
                "Client-specific Google Calendar read-only connection found. "
                f"uses_legacy_global={status.get('uses_legacy_global')}"
            ),
        )
    except Exception as e:
        gcal_dir = _client_gcal_dir(cid)
        return ClientCalendarConfig(
            client_id=cid,
            provider="google_calendar",
            connection_status="error",
            calendar_id=None,
            token_ref=str(gcal_dir / "refresh_token"),
            read_enabled=False,
            write_enabled=False,
            notes=f"Client calendar status check failed: {e}",
        )


def render_client_calendar_status(client_id: str) -> str:
    cfg = get_client_calendar_config(client_id)

    if cfg.connection_status != "connected":
        return (
            "📅 Calendario\n\n"
            "Todavía no tengo conectado tu Google Calendar.\n\n"
            "Puedo revisar recordatorios internos de Val, pero para ver tu agenda real "
            "necesito conectar tu calendario primero.\n\n"
            "Modo seguro preparado: conexión por cliente, solo lectura primero, "
            "sin usar credenciales globales."
        )

    write_label = "activada" if cfg.write_enabled else "desactivada por seguridad"
    return (
        "📅 Calendario\n\n"
        f"Proveedor: Google Calendar\n"
        f"Estado: conectado\n"
        f"Lectura: activada\n"
        f"Escritura: {write_label}\n"
        f"Calendario: {cfg.calendar_id or 'primary'}"
    )
