from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REPORT_SECTIONS = (
    "Executive Summary",
    "Current Processes",
    "Pain Points",
    "Opportunities",
    "Recommended Pilot",
    "30/60/90 Roadmap",
    "Limits / Boundaries",
    "Next Steps",
)


DEFAULT_LIMITS = (
    "Val helps structure diagnosis and pilot design; she does not replace "
    "professional judgment or operate the business autonomously.",
    "Human confirmation is required before implementation, outreach, calendar "
    "changes, reminders, tasks, or operational commitments.",
    "This draft is based on the information provided in the meeting and should "
    "be validated with the business owner before action.",
)


def _clean_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _clean_list(value: Any, fallback: Sequence[str]) -> list[str]:
    if isinstance(value, str):
        items = [line.strip(" -") for line in value.splitlines()]
    elif isinstance(value, Sequence):
        items = [str(item).strip() for item in value]
    else:
        items = []
    cleaned = [item for item in items if item]
    return cleaned or list(fallback)


def _bullet_list(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _roadmap(session: Mapping[str, Any]) -> list[str]:
    roadmap = session.get("roadmap")
    if isinstance(roadmap, Mapping):
        return [
            f"30 days: {_clean_text(roadmap.get('30'), 'Validate the first pilot and define baseline metrics.')}",
            f"60 days: {_clean_text(roadmap.get('60'), 'Run the pilot with a small operating loop and weekly review.')}",
            f"90 days: {_clean_text(roadmap.get('90'), 'Decide whether to expand, pause, or redesign the workflow.')}",
        ]
    return [
        "30 days: map the current workflow, validate the bottleneck, and define the pilot success metric.",
        "60 days: run the first pilot with human review before any external action.",
        "90 days: review results and decide whether to expand into a second workflow.",
    ]


def render_aiops_map_markdown(session: Mapping[str, Any]) -> str:
    """Render a deterministic AI Ops discovery report draft.

    This renderer is intentionally pure: it reads a session-like mapping and
    returns Markdown. It does not write files, call networks, touch clients, or
    activate memory.
    """

    company = _clean_text(session.get("company"), "Empresa X")
    business_type = _clean_text(session.get("business_type"), "business type still to validate")
    bottleneck = _clean_text(session.get("bottleneck"), "main bottleneck still to validate")
    desired_outcome = _clean_text(session.get("desired_outcome"), "a clearer 30/60/90 operating plan")
    recommended_pilot = _clean_text(
        session.get("recommended_pilot"),
        "a small AI Ops pilot around intake, follow-up, or administrative capture",
    )

    processes = _clean_list(
        session.get("current_processes"),
        (
            "Lead/client intake and follow-up",
            "Manual tracking of critical requests",
            "Administrative review before decisions",
        ),
    )
    pain_points = _clean_list(
        session.get("pain_points"),
        (
            "Important details are spread across tools or messages.",
            "Repetitive follow-up depends on manual attention.",
            "The team lacks a simple operating map for the next pilot.",
        ),
    )
    opportunities = _clean_list(
        session.get("opportunities"),
        (
            "Structure incoming requests into a review queue.",
            "Prepare follow-up drafts for human approval.",
            "Generate weekly operating summaries from meeting notes.",
        ),
    )
    next_steps = _clean_list(
        session.get("next_steps"),
        (
            "Confirm the first workflow owner and success metric.",
            "Choose the smallest pilot that can be tested in one week.",
            "Review risks and boundaries before implementation.",
        ),
    )
    limits = _clean_list(session.get("limits"), DEFAULT_LIMITS)

    lines = [
        f"# Mapa IA 30/60/90 - {company}",
        "",
        "## Executive Summary",
        (
            f"{company} appears to need a practical AI Ops diagnostic for a "
            f"{business_type}. The current bottleneck is {bottleneck}. The "
            f"recommended direction is {recommended_pilot}, with the 30/60/90 "
            f"outcome focused on {desired_outcome}."
        ),
        "",
        "## Current Processes",
        _bullet_list(processes),
        "",
        "## Pain Points",
        _bullet_list(pain_points),
        "",
        "## Opportunities",
        _bullet_list(opportunities),
        "",
        "## Recommended Pilot",
        (
            f"Start with {recommended_pilot}. Keep the pilot narrow, observable, "
            "and reviewed by a human before implementation decisions are made."
        ),
        "",
        "## 30/60/90 Roadmap",
        _bullet_list(_roadmap(session)),
        "",
        "## Limits / Boundaries",
        _bullet_list(limits),
        "",
        "## Next Steps",
        _bullet_list(next_steps),
        "",
    ]
    return "\n".join(lines)


def sample_aiops_session() -> dict[str, Any]:
    return {
        "company": "Empresa X",
        "business_type": "service business with manual admin follow-up",
        "bottleneck": "requests arrive through several channels and follow-up is inconsistent",
        "desired_outcome": "one clear pilot that reduces manual tracking within 30 days",
        "current_processes": [
            "New requests arrive through messages, referrals, and calls.",
            "Follow-up is tracked manually.",
            "Admin details are reviewed after the meeting instead of during the workflow.",
        ],
        "pain_points": [
            "Time is lost reconstructing what was promised.",
            "Important follow-up depends on memory.",
            "There is no simple weekly view of opportunities and blockers.",
        ],
        "opportunities": [
            "Capture meeting notes into a structured opportunity list.",
            "Draft follow-up messages for human review.",
            "Create a weekly AI Ops summary for the owner.",
        ],
        "recommended_pilot": "AI-assisted intake and follow-up prep",
        "next_steps": [
            "Validate the intake channels and follow-up owner.",
            "Define what a successful one-week pilot means.",
            "Prepare an implementation proposal with clear human approval points.",
        ],
    }
