# PLATFORM_ROADMAP — Val0

Purpose:
Track reusable platform-level capabilities that emerge from client work.

---

## Current platform direction

Val0 is becoming a modular personal/business operator.

The pattern:
1. Build useful capability for one client.
2. Validate it in real use.
3. Seal with commit + test + checkpoint.
4. Register it as reusable capability.
5. Generalize carefully for future clients.

---

## Sealed / active capabilities

- client_context_reader_v0
- client_ideas_v0
- grocery_list_v0
- karen_legal_case_v0
- carpeta_clara_v0
- nora_lawyer_package_v0
- mission_runner_v0

---

## Next recommended platform builds

### 1. client_capability_registry_v0

Goal:
Track which clients have which capabilities active.

Why:
Needed before client #2 so we know what can be reused.

### 2. client_template_generator_v0

Goal:
Create new client folder with CLIENT_PROFILE, CLIENT_STATUS, CLIENT_ROADMAP, CLIENT_IDEAS, CLIENT_CAPABILITIES.

Why:
Reduces manual setup for second client.

### 3. item_list_generic_v0

Goal:
Generalize Karen grocery list into reusable item-list module.

Why:
Can become grocery, inventory, materials, school list, purchase list.

### 4. grocery_metadata_v0

Goal:
Add manual price/store/location/date metadata.

Why:
Useful before photo/barcode/OCR.

### 5. idea_reuse_review_v0

Goal:
When a client gives an idea, compare it against existing capabilities and decide:
- client-specific
- reusable candidate
- platform roadmap candidate
- parking lot

Why:
Turns client feedback into product growth without chaos.
