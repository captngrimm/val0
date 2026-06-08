from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_DIR = ROOT / "tmp" / "memory_spine_spike"
ALLOWED_FIXTURE_ROOTS = (
    ROOT / "tmp" / "memory_spine_spike",
    ROOT / "tests" / "fixtures" / "memory_spine",
)
MEMORY_SPINE_FEATURE_ENV = "VAL0_MEMORY_SPINE_EXPERIMENTAL"
MEMORY_SPINE_ENABLED_DEFAULT = False

RAW_SECRET_PATTERNS = (
    re.compile(r"\b\d{12,19}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]", re.IGNORECASE),
)


class MemorySpineError(ValueError):
    """Raised when the fixture-only memory spine guard rejects an operation."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_memory_spine_enabled(env: dict[str, str] | None = None) -> bool:
    value = (env or os.environ).get(MEMORY_SPINE_FEATURE_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _safe_id_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip()).strip("_")
    return cleaned.lower()[:80] or "fixture"


def _assert_no_raw_secrets(text: str) -> None:
    value = str(text or "")
    for pattern in RAW_SECRET_PATTERNS:
        if pattern.search(value):
            raise MemorySpineError("raw secret-like value rejected for memory fixture")


def _assert_fixture_storage_path(storage_dir: str | Path) -> Path:
    path = Path(storage_dir).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()

    allowed = False
    for allowed_root in ALLOWED_FIXTURE_ROOTS:
        allowed_resolved = allowed_root.resolve()
        if resolved == allowed_resolved or allowed_resolved in resolved.parents:
            allowed = True
            break

    if not allowed:
        raise MemorySpineError("memory spine spike writes only to fixture/temp storage")

    if "clients" in resolved.parts:
        raise MemorySpineError("memory spine spike must not write under clients")

    lowered = resolved.as_posix().lower()
    if lowered.endswith((".db", ".sqlite", ".sqlite3")) or "val0_memory" in lowered:
        raise MemorySpineError("memory spine spike must not touch production databases")

    return resolved


def _base_memory_object(
    *,
    memory_id: str,
    client_id: str,
    user_id: str,
    memory_type: str,
    title: str,
    summary: str,
    source: str,
    confidence: str,
    consent_status: str,
    confirmed_by_user: bool,
    sensitivity: str,
    status: str,
    linked_workflow: str | None,
    retrieval_tags: list[str],
    now: str | None = None,
) -> dict[str, Any]:
    _assert_no_raw_secrets(title)
    _assert_no_raw_secrets(summary)
    timestamp = now or utc_now_iso()
    return {
        "id": memory_id,
        "client_id": client_id,
        "user_id": user_id,
        "memory_type": memory_type,
        "title": title,
        "summary": summary,
        "source": source,
        "confidence": confidence,
        "consent_status": consent_status,
        "confirmed_by_user": bool(confirmed_by_user),
        "sensitivity": sensitivity,
        "status": status,
        "created_at": timestamp,
        "updated_at": timestamp,
        "expires_or_review_after": None,
        "linked_workflow": linked_workflow,
        "retrieval_tags": list(dict.fromkeys(retrieval_tags or [])),
    }


def create_memory_candidate(
    *,
    client_id: str,
    user_id: str,
    title: str,
    summary: str,
    source: str = "fixture_onboarding",
    linked_workflow: str = "daily_operator",
    retrieval_tags: list[str] | None = None,
    privacy_boundary_summary: str = "No actions are created or sent without confirmation.",
    sensitivity: str = "moderate",
    confidence: str = "medium",
    candidate_id: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    tags = retrieval_tags or ["memory_candidate", linked_workflow, "pending_confirmation"]
    memory_id = candidate_id or f"mem_candidate_{_safe_id_part(user_id)}_{_safe_id_part(linked_workflow)}"
    candidate = _base_memory_object(
        memory_id=memory_id,
        client_id=client_id,
        user_id=user_id,
        memory_type="memory_candidate",
        title=title,
        summary=summary,
        source=source,
        confidence=confidence,
        consent_status="proposed",
        confirmed_by_user=False,
        sensitivity=sensitivity,
        status="proposed",
        linked_workflow=linked_workflow,
        retrieval_tags=tags,
        now=now,
    )
    candidate["privacy_boundary"] = {
        "memory_type": "privacy_boundary",
        "summary": privacy_boundary_summary,
        "sensitivity": sensitivity,
        "consent_status": "proposed",
        "confirmed_by_user": False,
    }
    return candidate


def confirm_memory_candidate(
    candidate: dict[str, Any],
    *,
    consent_status: str,
    confirmed_by_user: bool,
    confirmed_by: str = "fixture_user_confirmation",
    now: str | None = None,
) -> dict[str, Any]:
    if consent_status != "confirmed" or not confirmed_by_user:
        raise MemorySpineError("explicit confirmed consent is required before saving confirmed memory")
    if candidate.get("memory_type") != "memory_candidate":
        raise MemorySpineError("only memory_candidate objects can be confirmed in this spike")

    timestamp = now or utc_now_iso()
    workflow = str(candidate.get("linked_workflow") or "workflow")
    confirmed = dict(candidate)
    confirmed.update(
        {
            "id": f"mem_confirmed_{_safe_id_part(candidate.get('user_id', 'fixture'))}_{_safe_id_part(workflow)}",
            "memory_type": "workflow_profile",
            "confidence": "confirmed",
            "consent_status": "confirmed",
            "confirmed_by_user": True,
            "status": "active",
            "updated_at": timestamp,
        }
    )
    confirmed["retrieval_tags"] = list(
        dict.fromkeys([*(candidate.get("retrieval_tags") or []), "confirmed_memory", "workflow_profile"])
    )
    confirmed["privacy_boundary"] = {
        **dict(candidate.get("privacy_boundary") or {}),
        "id": f"mem_boundary_{_safe_id_part(candidate.get('user_id', 'fixture'))}_{_safe_id_part(workflow)}",
        "memory_type": "privacy_boundary",
        "consent_status": "confirmed",
        "confirmed_by_user": True,
        "status": "active",
        "updated_at": timestamp,
    }
    confirmed["audit_event"] = {
        "id": f"audit_{_safe_id_part(confirmed['id'])}",
        "client_id": confirmed["client_id"],
        "user_id": confirmed["user_id"],
        "memory_type": "audit_event",
        "title": "Memory candidate confirmed",
        "summary": "Fixture user explicitly confirmed memory candidate for spike storage.",
        "source": confirmed_by,
        "confidence": "confirmed",
        "consent_status": "confirmed",
        "confirmed_by_user": True,
        "sensitivity": confirmed.get("sensitivity") or "moderate",
        "status": "active",
        "created_at": timestamp,
        "updated_at": timestamp,
        "expires_or_review_after": None,
        "linked_workflow": confirmed.get("linked_workflow"),
        "retrieval_tags": ["audit_event", "memory_confirmation", confirmed.get("linked_workflow") or "workflow"],
    }
    return confirmed


def write_confirmed_memory_fixture(confirmed_memory: dict[str, Any], storage_dir: str | Path = DEFAULT_FIXTURE_DIR) -> Path:
    if confirmed_memory.get("consent_status") != "confirmed" or not confirmed_memory.get("confirmed_by_user"):
        raise MemorySpineError("cannot write unconfirmed memory fixture")
    if confirmed_memory.get("memory_type") not in {"workflow_profile", "user_preference", "privacy_boundary"}:
        raise MemorySpineError("fixture writer only accepts confirmed memory object types")

    directory = _assert_fixture_storage_path(storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_safe_id_part(confirmed_memory['id'])}.json"
    path.write_text(json.dumps(confirmed_memory, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_confirmed_memory_fixture(memory_id: str, storage_dir: str | Path = DEFAULT_FIXTURE_DIR) -> dict[str, Any]:
    directory = _assert_fixture_storage_path(storage_dir)
    path = directory / f"{_safe_id_part(memory_id)}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("consent_status") != "confirmed" or not data.get("confirmed_by_user"):
        raise MemorySpineError("loaded fixture is not confirmed memory")
    return data


def build_memory_index_fixture(
    confirmed_memories: list[dict[str, Any]],
    storage_dir: str | Path = DEFAULT_FIXTURE_DIR,
) -> dict[str, Any]:
    directory = _assert_fixture_storage_path(storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now_iso()
    entries = []
    for memory in confirmed_memories:
        if memory.get("consent_status") != "confirmed" or not memory.get("confirmed_by_user"):
            raise MemorySpineError("index requires confirmed memory")
        entries.append(
            {
                "id": f"idx_{_safe_id_part(memory['id'])}",
                "client_id": memory["client_id"],
                "user_id": memory["user_id"],
                "memory_type": "memory_index_entry",
                "title": memory.get("title") or "",
                "summary": memory.get("summary") or "",
                "source": memory["id"],
                "confidence": memory.get("confidence") or "confirmed",
                "consent_status": memory.get("consent_status") or "confirmed",
                "confirmed_by_user": bool(memory.get("confirmed_by_user")),
                "sensitivity": memory.get("sensitivity") or "moderate",
                "status": memory.get("status") or "active",
                "created_at": timestamp,
                "updated_at": timestamp,
                "expires_or_review_after": memory.get("expires_or_review_after"),
                "linked_workflow": memory.get("linked_workflow"),
                "retrieval_tags": list(memory.get("retrieval_tags") or []),
                "fixture_path": f"{_safe_id_part(memory['id'])}.json",
            }
        )

    index = {
        "id": "memory_index_fixture",
        "memory_type": "memory_index",
        "status": "fixture_only",
        "created_at": timestamp,
        "updated_at": timestamp,
        "entries": entries,
    }
    (directory / "memory_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return index
