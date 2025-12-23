📄 VFMS_INTERPRETER_MODE.md

Version: v0.1
Status: Draft (Foundational)

1. Purpose

Interpreter Mode defines how an AI assistant (e.g., Val) may assist an operator using VFMS without compromising accuracy, auditability, or safety.

The goal is to bridge the gap between expert-authored documentation and novice or intermediate operators, while preventing hallucinated commands, invented configurations, or unsafe assumptions.

Interpreter Mode is explicitly opt-in and operates on top of VFMS outputs.

2. Design Principles
2.1 Truth First

All vendor-specific facts, commands, and sequences must originate from the VFMS corpus.

Interpreter Mode may not invent authoritative steps.

2.2 Explicit Uncertainty

When required information is missing, the system must:

stop forward execution

surface the uncertainty

convert it into questions or branches

2.3 Human-in-Control

The operator always decides:

what level of explanation they want

when to proceed

when to escalate or verify externally

3. Output Structure (Mandatory)

Every Interpreter Mode response must contain the following sections in order:

A. Verified Steps (Corpus-Sourced)

Content in this section:

Exact commands

Required sequences

Vendor-defined behavior

Rules:

Every item must be traceable to the VFMS corpus

Citations must include document name and location (page, section, or chunk ID)

No inference or extrapolation allowed

B. Explain Like I’m New (AI Coaching)

Purpose:

Reduce cognitive load for inexperienced operators

Allowed content:

Plain-language explanations of concepts

Why a step exists

What problem the step prevents

Common beginner mistakes

Restrictions:

No new commands

No configuration values

Educational only

C. Uncertainty & Required Clarifications

This section is mandatory when assumptions exist.

The AI must:

Identify missing or ambiguous prerequisites

Explain why each unknown matters

Convert gaps into actionable questions

Example prompts:

“Ask the customer whether this is a physical appliance or virtual.”

“Confirm network bonding mode before proceeding.”

If critical information is missing, the AI must explicitly recommend pausing execution.

D. Operator Flow (Decision Tree)

Purpose:

Prevent blind execution

Format:

IF / THEN branches

STOP points when information is insufficient

Clear escalation paths

Example:

IF new installation → follow Path A  
IF replacement / migration → follow Path B  
IF unknown → STOP and collect required information

4. Experience Levels (Training Wheels Toggle)

Interpreter Mode supports explicit operator experience levels:

4.1 Beginner (Neophyte)

Full explanations

Aggressive uncertainty detection

Conservative stop points

High question density

4.2 Intermediate

Assumes core technical literacy

Explanations collapsed or optional

Still flags uncertainty

Checklist-oriented

4.3 Advanced

Commands and sequences first

Minimal explanation

Critical uncertainty only

Assumptions explicitly listed at top

The operator may switch levels per task.

5. Allowed vs Forbidden Behavior
Allowed

Explain concepts

Generate clarification questions

Suggest safe checkpoints

Recommend escalation

Say “insufficient data”

Forbidden

Invent commands or flags

Guess configuration values

Mask uncertainty

Mix inferred guidance into verified steps

Present “best practices” as vendor facts

6. Relationship to VFMS

VFMS provides truth and grounding

Interpreter Mode provides context, explanation, and safety

Interpreter Mode may never bypass VFMS constraints

Interpreter Mode is a consumer of VFMS, not a replacement.

7. Intended Use Cases

Neophyte operator enablement

On-the-job training

Safe troubleshooting

Customer-facing confidence

Knowledge transfer without tribal loss

8. Non-Goals

Interpreter Mode does not:

Perform autonomous actions

Monitor systems

Recommend changes without user initiation

Replace human judgment

