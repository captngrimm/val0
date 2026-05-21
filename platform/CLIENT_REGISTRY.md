# CLIENT_REGISTRY — Val0 Platform

Purpose:
Central registry of Val0 clients, prospects, founder-beta candidates, and demo/test users.

This registry answers:
- Who exists?
- What client_id/folder do they use?
- What type of client are they?
- What phase are they in?
- What capabilities are active or planned?
- What is the next action?

Privacy rule:
Do not store unnecessary sensitive details here.
Keep sensitive facts inside client-specific files only when needed and consented.

---

## Status legend

- prospect: interested but not onboarded
- intake_needed: needs founder-beta intake
- setup_ready: ready for client folder/setup
- founder_beta_active: actively testing
- paused: waiting or inactive
- deferred: not now
- internal: internal/operator use

---

## Client: Karen

client_id:
karen

display_name:
Karen

client_type:
personal / legal-admin / family

phase:
founder_beta_active

folder:
clients/karen/

primary_use_case:
Family land/legal-administrative process + personal operator basics.

active_capabilities:
- client_context_reader_v0
- client_ideas_v0
- grocery_list_v0
- karen_legal_case_v0
- carpeta_clara_v0
- nora_lawyer_package_v0

testing_capabilities:
- reminders_agenda_v0
- voice_capture_v0

planned_capabilities:
- grocery_metadata_v0

deferred_capabilities:
- photo_ocr_product_v0
- barcode/nutrition facts

current_status:
Karen has been sent a controlled tester prompt for:
- what Val can do today
- grocery add/list/delete
- idea capture

next_action:
Wait for Karen feedback, then record pass/fail findings and decide next patch.

---

## Prospect: Ángel

client_id:
angel

display_name:
Ángel

client_type:
business / operations candidate

phase:
prospect

folder:
not_created_yet

primary_use_case:
To be confirmed by intake.

possible_use_cases:
- business operations
- product/vendor tracking
- follow-ups
- documents
- meetings
- client/provider process tracking

candidate_capabilities:
- client_context_reader_v0
- client_ideas_v0
- item_list_v0 candidate from grocery_list_v0
- meeting_prep_package_v0 pattern
- document_inventory_v0 pattern
- reminders_agenda_v0

next_action:
Run founder-beta intake before creating client folder.

---

## Prospect: Roy

client_id:
roy

display_name:
Roy

client_type:
business / procurement / sales candidate

phase:
prospect

folder:
not_created_yet

primary_use_case:
Possible supplier/vendor/process support, potentially related to ACP / sales / product submissions.

possible_use_cases:
- product/vendor lists
- follow-up reminders
- meeting prep
- document checklist
- procurement/admin process tracking

candidate_capabilities:
- client_context_reader_v0
- client_ideas_v0
- item_list_v0 candidate from grocery_list_v0
- meeting_prep_package_v0 pattern
- document_inventory_v0 pattern

next_action:
Run founder-beta intake if/when user decides to approach Roy.

---

## Prospect: Sol Adriana Duarte / NeWork

client_id:
sol_network

display_name:
Sol Adriana Duarte / NeWork

client_type:
business / consulting candidate

phase:
prospect

folder:
not_created_yet

primary_use_case:
To be confirmed by intake.

possible_use_cases:
- business/process mapping
- operational roadmap
- client-facing AI workflow discussion
- consulting/assessment collaboration

candidate_capabilities:
- founder-beta offer
- client intake protocol
- process mapping
- roadmap/status
- document/meeting prep

next_action:
Use Spanish founder-beta offer as conversation asset if discussing Val/Valdía business model.

---

## Internal: Frank / ValPrime / Val0 Ops

client_id:
frank_ops

display_name:
Frank / ValPrime / Val0 Ops

client_type:
internal / operator

phase:
internal

folder:
not_client_folder_yet

primary_use_case:
Operate Val0 platform development, checkpoints, mission runner, roadmap, client setup, and testing.

active_capabilities:
- mission_runner_v0
- capability_registry_v0
- client_template_generator_v0
- founder_beta_intake_protocol_v0
- founder_beta_offer_v0
- spanish_offer_v0
- karen_demo_script_v0

next_action:
Continue platform modularization and Karen feedback loop.

---

## Next registry improvements

- Add created_at / updated_at fields per client.
- Add active sprint per client.
- Add capability status per client.
- Add link to latest checkpoint.
- Add client folder existence check via Forge mission.
- Later: convert registry to YAML/JSON if automation needs structured reads.
