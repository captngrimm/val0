Data Domain Initial Provisioning — Neophyte Guide (DEMO)

WARNING — DEMONSTRATION DOCUMENT (MOCK SOURCES)

This document demonstrates VFMS Interpreter Mode behavior using mock source references.
All commands, steps, and explanations below are illustrative only and not vendor-authoritative.

When real documentation is ingested into VFMS, all mock citations will be replaced with corpus-verified references.

────────────────────────────────

Operator Level

Beginner (Neophyte)
Training wheels ON
Explanations expanded
Hard stop points enforced when information is missing

────────────────────────────────

Purpose of This Document

This guide demonstrates how an AI-assisted VFMS system helps a non-expert operator:

Follow real documentation safely

Understand what each step is doing

Avoid guessing when information is missing

Ask the right questions to customers or senior engineers

Produce professional, confidence-building output

This is not automation.
This is guided competence.

────────────────────────────────

Section A — Verified Steps (Corpus-Derived, MOCK)

This section represents what VFMS surfaces verbatim from ingested documents.
No inference, interpretation, or best-practice guessing is added here.

Step 1 — Access the system console

Connect to the Data Domain system console using the serial interface or management network.

Source:
Data Domain Installation Guide (MOCK), page 14

–––––

Step 2 — Start initial configuration

Launch the system setup wizard.

Command:
system setup

Source:
Data Domain Administration Guide (MOCK), page 27

–––––

Step 3 — Configure basic network settings

During the wizard, provide:

IP address

Netmask

Default gateway

Source:
Data Domain Networking Guide (MOCK), page 42

────────────────────────────────

Section B — Explain Like I’m New (Interpreter Mode)

What is Data Domain?

Data Domain is a storage platform designed primarily for backup and data protection.
Its defining feature is data deduplication, which drastically reduces how much disk space backups consume.

–––––

What does “deduplication” mean?

Instead of storing identical data multiple times, the system:

Breaks incoming data into chunks

Stores each unique chunk once

References that chunk wherever it appears again

This makes Data Domain extremely efficient, but also means early configuration matters.
Mistakes at setup time can affect performance, replication, or recoverability later.

–––––

Why is the setup wizard important?

The system setup wizard ensures:

Networking is consistent

System identity is established

The platform starts in a known-good state

Skipping or rushing this step is a common beginner mistake.

────────────────────────────────

Section C — Required Clarifications (HARD STOPS)

Before proceeding further, the following must be known.

Physical appliance or virtual (DDVE)?

Why this matters:
Network configuration, disk layout, and licensing differ.

Action:
Confirm with the customer or deployment documentation.

–––––

New installation or replacement / migration?

Why this matters:
Replacement systems may require:

Data migration

Replication pairing

Cutover planning

Action:
If this is a replacement, STOP and engage higher-level documentation or L2/L3 support.

–––––

Network environment details

You must have:

IP address

Subnet mask

Gateway

DNS servers

NTP servers

Why this matters:
Incorrect network or time configuration causes authentication, replication, and management failures.

STOP if any of this information is missing.

────────────────────────────────

Section D — Operator Decision Flow

Use this mental model before proceeding:

IF physical appliance AND new install
→ Continue with standard provisioning

IF virtual appliance (DDVE)
→ Switch to DDVE-specific documentation

IF replacement / migration
→ STOP
→ Escalate or follow migration procedures

IF required information is missing
→ STOP
→ Collect information before continuing

────────────────────────────────

Section E — Questions to Ask the Customer

These questions project competence and control, not ignorance:

Is this a new deployment or a replacement system?

Is this physical hardware or a virtual Data Domain?

Do you already have IP, DNS, and NTP assigned?

Will this system participate in replication?

Is there an approved maintenance window for reboots?

Asking these early prevents mistakes later.

────────────────────────────────

Section F — What This System Explicitly Does NOT Do

This VFMS + Interpreter Mode setup:

Does NOT invent commands

Does NOT assume undocumented best practices

Does NOT proceed with missing information

Does NOT automate actions without user intent

Does NOT hallucinate gaps in documentation

If something is unknown, it stops and asks.

────────────────────────────────

Section G — Skill Level Scaling (Preview)

The same source material can be rendered differently:

Beginner Mode

Full explanations

Frequent stop points

Step-by-step guidance

Intermediate Mode

Explanations collapsed

Risks highlighted

Fewer interruptions

Advanced Mode

Commands first

Assumptions listed up front

Only critical warnings shown

Same truth.
Different presentation.

────────────────────────────────

End of Demonstration Document

––––––––––––––––––––––––––––––––––