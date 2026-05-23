from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Iterable


PRIORITIES = {"urgent", "high", "normal", "low"}
STATUSES = {
    "pending",
    "today",
    "done",
    "blocked",
    "needs_review",
    "ready",
    "unknown",
}
ITEM_LIST_FIELDS = (
    "calendar_items",
    "reminders",
    "tasks",
    "pending_actions",
    "case_priorities",
    "document_items",
    "timeline_items",
)


@dataclass(frozen=True)
class DailyOperatorItem:
    item_id: str
    item_type: str
    title: str
    description: str = ""
    due_at: str | None = None
    source_type: str = ""
    source_id: str = ""
    priority: str = "normal"
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DailyOperatorSnapshot:
    client_id: str
    case_id: str
    snapshot_date: str
    calendar_items: tuple[DailyOperatorItem, ...] = ()
    reminders: tuple[DailyOperatorItem, ...] = ()
    tasks: tuple[DailyOperatorItem, ...] = ()
    pending_actions: tuple[DailyOperatorItem, ...] = ()
    case_priorities: tuple[DailyOperatorItem, ...] = ()
    document_items: tuple[DailyOperatorItem, ...] = ()
    timeline_items: tuple[DailyOperatorItem, ...] = ()
    suggested_next_action: str = ""
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_operator_priority(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "critical": "urgent",
        "critico": "urgent",
        "crítico": "urgent",
        "urgente": "urgent",
        "alta": "high",
        "medio": "normal",
        "medium": "normal",
        "normal": "normal",
        "baja": "low",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in PRIORITIES else "normal"


def normalize_operator_status(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "open": "pending",
        "abierto": "pending",
        "pendiente": "pending",
        "hoy": "today",
        "complete": "done",
        "completed": "done",
        "hecho": "done",
        "cerrado": "done",
        "bloqueado": "blocked",
        "review": "needs_review",
        "revision": "needs_review",
        "revisión": "needs_review",
        "listo": "ready",
        "lista": "ready",
        "unknown": "unknown",
    }
    normalized = aliases.get(raw, raw)
    return normalized if normalized in STATUSES else "unknown"


def _today_text(snapshot_date: str | date | datetime | None) -> str:
    if isinstance(snapshot_date, datetime):
        return snapshot_date.date().isoformat()
    if isinstance(snapshot_date, date):
        return snapshot_date.isoformat()
    raw = str(snapshot_date or "").strip()
    return raw[:10] if raw else date.today().isoformat()


def _item_from_any(value: Any, fallback_type: str) -> DailyOperatorItem | None:
    if value is None:
        return None
    if isinstance(value, DailyOperatorItem):
        return DailyOperatorItem(
            item_id=value.item_id,
            item_type=value.item_type or fallback_type,
            title=value.title,
            description=value.description,
            due_at=value.due_at,
            source_type=value.source_type,
            source_id=value.source_id,
            priority=normalize_operator_priority(value.priority),
            status=normalize_operator_status(value.status),
            metadata=dict(value.metadata or {}),
        )

    if isinstance(value, dict):
        title = str(value.get("title") or value.get("summary") or value.get("text") or "").strip()
        if not title:
            return None
        item_id = str(value.get("item_id") or value.get("id") or value.get("source_id") or title).strip()
        return DailyOperatorItem(
            item_id=item_id,
            item_type=str(value.get("item_type") or fallback_type).strip() or fallback_type,
            title=title,
            description=str(value.get("description") or "").strip(),
            due_at=str(value.get("due_at") or value.get("due_at_utc") or value.get("event_date") or "").strip() or None,
            source_type=str(value.get("source_type") or value.get("source") or fallback_type).strip(),
            source_id=str(value.get("source_id") or value.get("id") or "").strip(),
            priority=normalize_operator_priority(value.get("priority")),
            status=normalize_operator_status(value.get("status")),
            metadata=dict(value.get("metadata") or {}),
        )

    title = str(value).strip()
    if not title:
        return None
    return DailyOperatorItem(
        item_id=title,
        item_type=fallback_type,
        title=title,
        source_type=fallback_type,
        source_id=title,
    )


def _items(values: Iterable[Any] | None, fallback_type: str) -> tuple[DailyOperatorItem, ...]:
    out: list[DailyOperatorItem] = []
    seen = set()
    for value in values or ():
        item = _item_from_any(value, fallback_type)
        if not item:
            continue
        key = (item.item_type, item.item_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return tuple(out)


def build_daily_operator_snapshot(
    *,
    client_id: str = "",
    case_id: str = "",
    snapshot_date: str | date | datetime | None = None,
    calendar_items: Iterable[Any] | None = None,
    reminders: Iterable[Any] | None = None,
    tasks: Iterable[Any] | None = None,
    pending_actions: Iterable[Any] | None = None,
    case_priorities: Iterable[Any] | None = None,
    document_items: Iterable[Any] | None = None,
    timeline_items: Iterable[Any] | None = None,
    suggested_next_action: str = "",
    warnings: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> DailyOperatorSnapshot:
    snapshot = DailyOperatorSnapshot(
        client_id=str(client_id or "").strip(),
        case_id=str(case_id or "").strip(),
        snapshot_date=_today_text(snapshot_date),
        calendar_items=_items(calendar_items, "calendar"),
        reminders=_items(reminders, "reminder"),
        tasks=_items(tasks, "task"),
        pending_actions=_items(pending_actions, "pending_action"),
        case_priorities=_items(case_priorities, "case_priority"),
        document_items=_items(document_items, "document"),
        timeline_items=_items(timeline_items, "timeline"),
        suggested_next_action=str(suggested_next_action or "").strip(),
        warnings=tuple(str(w).strip() for w in (warnings or ()) if str(w or "").strip()),
        metadata=dict(metadata or {}),
    )
    if snapshot.suggested_next_action:
        return snapshot
    return DailyOperatorSnapshot(
        **{
            **snapshot.__dict__,
            "suggested_next_action": choose_suggested_next_action(snapshot),
        }
    )


def filter_today_items(items: Iterable[DailyOperatorItem], snapshot_date: str | date | datetime | None) -> list[DailyOperatorItem]:
    today = _today_text(snapshot_date)
    out = []
    for item in items or ():
        due = str(item.due_at or "").strip()
        status = normalize_operator_status(item.status)
        if due.startswith(today) or status == "today":
            out.append(item)
    return out


def choose_suggested_next_action(snapshot: DailyOperatorSnapshot) -> str:
    today_candidates = []
    for field in ("calendar_items", "reminders", "tasks"):
        today_candidates.extend(filter_today_items(getattr(snapshot, field), snapshot.snapshot_date))

    ranked_groups = (
        today_candidates,
        list(snapshot.pending_actions),
        list(snapshot.case_priorities),
        list(snapshot.document_items),
        list(snapshot.timeline_items),
    )
    priority_rank = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    status_penalty = {"blocked": 1, "done": 9}

    for group in ranked_groups:
        candidates = [
            item for item in group
            if normalize_operator_status(item.status) != "done"
        ]
        if not candidates:
            continue
        candidates.sort(
            key=lambda item: (
                priority_rank.get(normalize_operator_priority(item.priority), 2),
                status_penalty.get(normalize_operator_status(item.status), 0),
                str(item.due_at or "9999-99-99"),
                item.title,
            )
        )
        return candidates[0].title
    return ""


def _safe_item(item: DailyOperatorItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "item_type": item.item_type,
        "title": item.title,
        "description": item.description,
        "due_at": item.due_at,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "priority": normalize_operator_priority(item.priority),
        "status": normalize_operator_status(item.status),
    }


def safe_daily_operator_summary(snapshot: DailyOperatorSnapshot) -> dict[str, Any]:
    return {
        "client_id": snapshot.client_id,
        "case_id": snapshot.case_id,
        "snapshot_date": snapshot.snapshot_date,
        "calendar_items": [_safe_item(item) for item in snapshot.calendar_items],
        "reminders": [_safe_item(item) for item in snapshot.reminders],
        "tasks": [_safe_item(item) for item in snapshot.tasks],
        "pending_actions": [_safe_item(item) for item in snapshot.pending_actions],
        "case_priorities": [_safe_item(item) for item in snapshot.case_priorities],
        "document_items": [_safe_item(item) for item in snapshot.document_items],
        "timeline_items": [_safe_item(item) for item in snapshot.timeline_items],
        "suggested_next_action": snapshot.suggested_next_action,
        "warnings": list(snapshot.warnings),
        "created_at": snapshot.created_at,
    }
