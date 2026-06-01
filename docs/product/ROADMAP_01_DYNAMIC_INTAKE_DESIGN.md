# ROADMAP-01 Dynamic Roadmap Intake Design

## Purpose

Dynamic roadmap intake converts newsletters, articles, raw ideas, client feedback, Codex findings, and reading notes into roadmap signals.

The goal is not to execute every interesting idea. The goal is to:

- detect useful signals
- preserve valuable ideas
- prevent random inputs from derailing the active sprint
- separate immediate blockers from future roadmap material
- keep Val0 aligned with the Personal OS mission

This is a design document only. It does not implement ingestion automation.

## Inputs

The intake lane may eventually evaluate:

- AI newsletters
- articles
- user ideas
- Karen/client feedback
- Codex findings
- OPEL events
- ValPrime parking lot items
- Obsidian/visual vault future exports

## Output Decision Categories

Each intake item should receive one primary category:

- `NO_CHANGE`
- `PARKING_LOT`
- `ROADMAP_UPDATE_CANDIDATE`
- `ACTIVE_SPRINT_INTERRUPT`
- `RESEARCH_REQUIRED`
- `PRODUCT_POSITIONING_SIGNAL`
- `TECH_DEBT_SIGNAL`
- `CLIENT_VALUE_SIGNAL`

Multiple secondary tags are allowed, but the primary category should drive the next action.

## Scoring Model

Score each signal from 0 to 5:

| Field | Meaning |
| --- | --- |
| `relevance_to_mission` | Fit with Val0 / Personal OS mission |
| `user_value` | Expected value to user or client |
| `urgency` | Time sensitivity |
| `implementation_effort` | Build cost or operational burden |
| `dependency_risk` | External/API/architecture risk |
| `trust_or_safety_impact` | Privacy, safety, reliability, or trust impact |
| `current_sprint_fit` | Fit with the active sprint |

High value plus low sprint fit usually means parking lot or roadmap candidate, not immediate interruption.

## Required Response Format For Intake Chat

Use this format when evaluating a pasted newsletter, article, idea, or feedback item:

```text
Summary:
- ...

Key signals:
- ...

Relevance to Val0 / Personal OS:
- ...

Roadmap impact:
- ...

Suggested destination:
- NO_CHANGE / PARKING_LOT / ROADMAP_UPDATE_CANDIDATE / ACTIVE_SPRINT_INTERRUPT / RESEARCH_REQUIRED / PRODUCT_POSITIONING_SIGNAL / TECH_DEBT_SIGNAL / CLIENT_VALUE_SIGNAL

Recommended next action:
- ...

Do not change current sprint unless:
- ...

Save target:
- ...
```

## Guardrails

- Do not auto-update roadmap without explicit approval.
- Do not let newsletters derail active sprint unless urgent and high impact.
- Separate facts from speculation.
- Cite/source if available in future.
- Do not ingest sensitive client data into public docs.
- Preserve source excerpt only if safe and copyright-aware; prefer summary.
- If an item affects Karen/client-zero, confirm whether it belongs in client-private notes or public product docs.
- If an item is exciting but not urgent, park it.

## Integration With Existing Source-of-Truth

The intake evaluator should compare signals against:

- `docs/product/VAL0_MASTER_MILESTONE_MAP.md`
- `docs/product/VAL0_SOURCE_OF_TRUTH_INDEX.md`
- `docs/product/VAL0_DOCS_VALUE_MAP.md`
- ValPrime checkpoint / parking lot
- OPEL event log
- Optional future Obsidian visual graph or vault export

The evaluator should not treat a pasted source as higher authority than these source-of-truth files.

## Future Phases

- ROADMAP-02: Idea Registry schema
- ROADMAP-03: ValPrime parking lot extraction
- ROADMAP-04: Newsletter paste intake prompt
- ROADMAP-05: Daily synthesis / "Milkshake Time"
- ROADMAP-06: Roadmap update proposal generator
- ROADMAP-07: Obsidian export/index

## Runtime Note

This design changes no runtime behavior. It does not wire ChatGPT, Gmail, newsletters, Obsidian, OPEL, or ValPrime into Val0 automation.
