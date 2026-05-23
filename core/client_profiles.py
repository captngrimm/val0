from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from core.client_identity import KAREN_CHAT_ID, client_profile as legacy_client_profile


WORKFLOW_CALENDAR = "calendar"
WORKFLOW_REMINDERS = "reminders"
WORKFLOW_DOCUMENTS = "documents"
WORKFLOW_TIMELINE = "timeline"
WORKFLOW_DAILY_OPERATOR = "daily_operator"
WORKFLOW_LEGAL_CASE = "legal_case"
WORKFLOW_GROCERIES = "groceries"
WORKFLOW_RESPONSE_ENVELOPE = "response_envelope"

KNOWN_WORKFLOWS = {
    WORKFLOW_CALENDAR,
    WORKFLOW_REMINDERS,
    WORKFLOW_DOCUMENTS,
    WORKFLOW_TIMELINE,
    WORKFLOW_DAILY_OPERATOR,
    WORKFLOW_LEGAL_CASE,
    WORKFLOW_GROCERIES,
    WORKFLOW_RESPONSE_ENVELOPE,
}


@dataclass(frozen=True)
class ClientProfile:
    client_id: str
    display_name: str
    vocative: str
    language: str
    chat_ids: tuple[int, ...] = ()
    enabled_workflows: tuple[str, ...] = ()
    active_case_id: str = ""
    calendar_status: str = "unknown"
    feature_flags: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowAccessDecision:
    allowed: bool
    client_id: str
    workflow: str
    reason: str
    safety_level: str
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_client_id(value: Any) -> str:
    raw = str(value or "").strip().lower()
    return "".join(ch for ch in raw if ch.isalnum() or ch in ("_", "-"))


def normalize_workflow(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    raw = re.sub(r"[^a-z0-9_]+", "", raw)
    return raw


def _build_karen_profile() -> ClientProfile:
    legacy = legacy_client_profile("karen")
    workflows = tuple(sorted(KNOWN_WORKFLOWS))
    return ClientProfile(
        client_id=normalize_client_id(legacy.get("client_id")),
        display_name=str(legacy.get("display_name") or "").strip(),
        vocative=str(legacy.get("vocative") or "").strip(),
        language="es",
        chat_ids=(int(KAREN_CHAT_ID),),
        enabled_workflows=workflows,
        active_case_id="KAREN-LAND-001",
        calendar_status="client_scoped",
        feature_flags={
            "client_zero": True,
            "runtime_route_wiring": False,
        },
        metadata={
            "profile_source": "client_identity_legacy_fixture",
            "registry_version": "v0",
        },
    )


_KAREN_PROFILE = _build_karen_profile()

_CLIENT_PROFILES: dict[str, ClientProfile] = {
    _KAREN_PROFILE.client_id: _KAREN_PROFILE,
}


def get_client_profile(client_id: Any) -> ClientProfile | None:
    cid = normalize_client_id(client_id)
    if not cid:
        return None
    return _CLIENT_PROFILES.get(cid)


def get_client_profile_for_chat(chat_id: int | str | None) -> ClientProfile | None:
    if chat_id is None:
        return None
    try:
        chat_int = int(chat_id)
    except (TypeError, ValueError):
        return None
    for profile in _CLIENT_PROFILES.values():
        if chat_int in profile.chat_ids:
            return profile
    return None


def is_known_client(client_id: Any) -> bool:
    return get_client_profile(client_id) is not None


def workflow_enabled(client_id: Any, workflow: Any) -> bool:
    profile = get_client_profile(client_id)
    if not profile:
        return False
    normalized = normalize_workflow(workflow)
    if normalized not in KNOWN_WORKFLOWS:
        return False
    return normalized in profile.enabled_workflows


def require_workflow_access(client_id: Any, workflow: Any) -> WorkflowAccessDecision:
    cid = normalize_client_id(client_id)
    normalized_workflow = normalize_workflow(workflow)
    profile = get_client_profile(cid)
    if not profile:
        return WorkflowAccessDecision(
            allowed=False,
            client_id=cid,
            workflow=normalized_workflow,
            reason="unknown_client",
            safety_level="deny",
        )
    if normalized_workflow not in KNOWN_WORKFLOWS:
        return WorkflowAccessDecision(
            allowed=False,
            client_id=profile.client_id,
            workflow=normalized_workflow,
            reason="unknown_workflow",
            safety_level="deny",
        )
    if normalized_workflow not in profile.enabled_workflows:
        return WorkflowAccessDecision(
            allowed=False,
            client_id=profile.client_id,
            workflow=normalized_workflow,
            reason="workflow_disabled",
            safety_level="deny",
        )
    return WorkflowAccessDecision(
        allowed=True,
        client_id=profile.client_id,
        workflow=normalized_workflow,
        reason="workflow_enabled",
        safety_level="allow_profile_scoped",
        metadata={"registry_version": str(profile.metadata.get("registry_version") or "v0")},
    )


def safe_client_profile_summary(profile: ClientProfile | None) -> dict[str, Any]:
    if not profile:
        return {}
    return {
        "client_id": profile.client_id,
        "display_name": profile.display_name,
        "language": profile.language,
        "chat_id_count": len(profile.chat_ids),
        "enabled_workflows": list(profile.enabled_workflows),
        "active_case_id": profile.active_case_id,
        "calendar_status": profile.calendar_status,
        "feature_flags": dict(profile.feature_flags),
        "known_client": True,
    }
