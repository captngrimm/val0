# CAPABILITY_REGISTRY — Val0 Platform

Purpose:
Central inventory of Val0 reusable capabilities.

This registry answers:
- What can Val0 do?
- Which client first validated it?
- Which clients use it?
- Is it reusable?
- What files/modules are involved?
- What are the current limits?
- What should be generalized next?

---

## Capability: client_context_reader_v0

Human name:
Client roadmap/status/context reader.

Status:
sealed

First validated client:
Karen

Clients using:
- Karen

What it does:
- Answers what Val can do today.
- Answers what comes next.
- Answers whether current sprint/status is on track.
- Reads CLIENT_* files for client-specific context.

Reusable for:
- personal clients
- corporate clients
- founder-beta onboarding
- client status reports

Core files/modules:
- core/client_context_reader.py
- clients/<client_id>/CLIENT_PROFILE.md
- clients/<client_id>/CLIENT_STATUS.md
- clients/<client_id>/CLIENT_ROADMAP.md
- clients/<client_id>/CLIENT_IDEAS.md

Known limits:
- currently still partially Karen-specific in tone/content
- client_id routing is not fully generalized yet

Next generalization:
- client registry
- dynamic client_id resolution
- reusable client template generator

---

## Capability: client_ideas_v0

Human name:
Client idea intake and backlog.

Status:
sealed

First validated client:
Karen

Clients using:
- Karen

What it does:
- Captures client ideas from natural language.
- Stores ideas in CLIENT_IDEAS.md.
- Can list saved ideas.
- Prevents selftest from writing fake ideas.

Reusable for:
- roadmap intake
- client feedback loop
- product discovery
- founder-beta iteration

Core files/modules:
- core/client_context_reader.py
- clients/<client_id>/CLIENT_IDEAS.md

Known limits:
- no automatic reuse scoring yet
- no platform-level idea promotion yet

Next generalization:
- idea classification
- reusable capability matching
- client notification protocol

---

## Capability: grocery_list_v0

Human name:
Grocery / item list memory.

Status:
sealed

First validated client:
Karen

Clients using:
- Karen

What it does:
- Adds grocery/list items.
- Shows saved list.
- Deletes items from list.
- Supports shortcuts like “quitar café” when item exists.

Reusable for:
- grocery lists
- basic inventory
- purchase lists
- materials lists
- recurring item tracking

Core files/modules:
- core/client_context_reader.py
- clients/<client_id>/CLIENT_GROCERY.md
- bot.py priority gate

Known limits:
- currently writes to Karen-specific CLIENT_GROCERY.md
- no price/store/aisle metadata yet
- no photo/barcode/OCR yet
- no quantities/categories yet

Next generalization:
- item_list_v0 generic module
- grocery_metadata_v0: price, store, aisle/location, date
- client_id-aware storage

---

## Capability: karen_legal_case_v0

Human name:
Karen land/family legal-administrative case support.

Status:
active

First validated client:
Karen

Clients using:
- Karen

What it does:
- Supports land/finca/family legal-admin context.
- Tracks case facts and case-oriented questions.
- Helps prepare summaries and next actions.

Reusable for:
- legal/admin case tracking
- family process tracking
- document-heavy workflows

Core files/modules:
- core/karen_case_facts.py
- core/karen_case_status.py
- core/karen_recent_activity.py
- clients/karen/*

Known limits:
- Karen-specific
- should not be generalized blindly as legal advice
- must preserve legal boundary language

Next generalization:
- case_memory_v0
- document_case_context_v0
- consultative next-action protocol

---

## Capability: carpeta_clara_v0

Human name:
Document organization onboarding.

Status:
active

First validated client:
Karen

Clients using:
- Karen

What it does:
- Guides user through organizing scattered case documents.
- Creates document inventory flow.
- Helps reduce chaos before lawyer/client meetings.

Reusable for:
- document onboarding
- admin workflows
- client file collection
- case prep

Core files/modules:
- core/karen_next_action.py
- document inventory handlers in bot.py

Known limits:
- Karen-specific language
- OCR/photo ingestion not complete

Next generalization:
- document_inventory_v0
- upload/photo/OCR pipeline later

---

## Capability: nora_lawyer_package_v0

Human name:
Nora lawyer prep package.

Status:
sealed for Karen

First validated client:
Karen

Clients using:
- Karen

What it does:
- Prepares a clear package/checklist/questions for Nora.
- Helps Karen organize what to bring to lawyer meeting.

Reusable for:
- meeting prep pattern
- advisor/consultant prep
- checklist generation

Core files/modules:
- core/karen_lawyer_package.py
- core/karen_lawyer_questions.py

Known limits:
- specific to Karen/Nora
- should not be treated as generic legal advice

Next generalization:
- meeting_prep_package_v0

---

## Capability: mission_runner_v0

Human name:
Safe mission runner / operator checks.

Status:
sealed

First validated client:
Val0 operations

Clients using:
- internal ops

What it does:
- Runs approved Forge mission packs.
- Avoids long pasted command blocks.
- Writes clean output for Launchpad.
- Supports checkpoint/context/health checks.

Reusable for:
- Val0 ops
- future client health checks
- deployment validation

Core files/modules:
- /home/forge/LAUNCHPAD/run_safe_mission.sh
- /usr/local/bin/mission
- /home/forge/LAUNCHPAD/packs/*
- /home/forge/LAUNCHPAD/missions/*

Known limits:
- currently Forge-side, not product-facing
- no client-facing dashboard yet

Next generalization:
- mission templates
- client-specific health checks
