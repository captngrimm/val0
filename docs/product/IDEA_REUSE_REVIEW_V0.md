# IDEA_REUSE_REVIEW_V0 — Val0

Purpose:
Define how Val0 reviews new client ideas and decides whether they are:
- client-specific
- reusable candidate
- platform roadmap candidate
- deferred / parking lot
- unsafe or out of scope

This prevents random feature creep and turns client feedback into structured product growth.

---

## Core rule

Do not let a client idea become a feature automatically.

Every idea must pass:

capture → match → score → decision → roadmap update → client response

---

## Minimum review template

Idea Review

Client:
Raw idea:
Extracted idea:
Matched capability:
Reuse score:
Decision:
Client roadmap update:
Platform roadmap update:
Capability registry update:
Client-facing response:
Next action:

---

## Reuse score

### 0 — No match

No existing capability is close.

Action:
Keep as client idea, platform candidate, or defer.

### 1 — Weak match

Some related concept exists, but implementation would be mostly new.

Example:
Barcode scanning when only grocery list exists.

Action:
Usually defer or place in future platform roadmap.

### 2 — Medium match

Existing capability can help but needs meaningful adaptation.

Example:
Supplier follow-up tracking using reminders + ideas + meeting prep.

Action:
Candidate for client roadmap.

### 3 — Strong match

Mostly an extension of an existing capability.

Example:
Add price/store/date metadata to grocery_list_v0.

Action:
Good next patch or near-term build candidate.

### 4 — Already supported

Val can already do it or mostly do it.

Action:
Teach/demo it and update client docs if needed.

---

## Decision categories

### active_now

Capability already exists and is enabled.

Client-facing:
“Eso ya lo puedes probar así: ...”

### client_roadmap_candidate

Useful for this client but not clearly reusable yet.

Client-facing:
“Lo guardé para tu roadmap. Primero validamos si vale la pena construirlo para tu flujo.”

### reusable_candidate

Useful for this client and likely useful for future clients.

Client-facing:
“Esto se parece a una capacidad que ya existe o que puede servir para más clientes. Lo marco como candidato reusable.”

### platform_roadmap_candidate

Could become part of Val0 general platform.

Client-facing:
“Esto puede convertirse en una mejora general de Val, pero no es promesa inmediata.”

### deferred

Good idea, wrong timing.

Client-facing:
“Buena idea, pero no entra en el sprint actual. La dejo en parking para no desviarnos.”

### unsafe_or_out_of_scope

Risky, professional advice, privacy issue, or too broad.

Client-facing:
“No lo voy a prometer así porque puede ser riesgoso o demasiado amplio. Podemos buscar una versión más pequeña y segura.”

---

## Update rules

Update client roadmap when:
- the idea matters to that client
- client expects follow-up
- it may be built later

Update client capabilities when:
- capability becomes active
- capability enters testing
- capability is planned
- capability is deferred

Update platform roadmap when:
- idea is useful across multiple clients
- idea extends a reusable capability
- idea should become Val0 core platform

Update capability registry only when:
- capability is implemented or clearly defined enough
- status, limits, and reuse targets are documented

Do not add vague dreams as full capabilities.

---

## Example: grocery price tracking

Client:
Karen

Raw idea:
Val, quiero que recuerdes cuánto cuesta la leche para comparar después.

Extracted idea:
Track grocery product prices over time.

Matched capability:
grocery_list_v0

Reuse score:
3 — Strong match

Decision:
reusable_candidate + client_roadmap_candidate

Client-facing response:
“Buena idea. Esto se puede construir sobre la lista de súper que ya existe. Lo marco como próximo candidato: guardar precio, tienda y fecha para comparar después.”

---

## Example: product photo/barcode

Client:
Karen

Raw idea:
Val, ¿puedo tomar foto del producto y el código de barra?

Extracted idea:
Photo/barcode product capture.

Matched capability:
grocery_list_v0, future photo_ocr_product_v0

Reuse score:
1 — Weak match for now

Decision:
deferred + platform_roadmap_candidate

Client-facing response:
“Eso tiene sentido, pero todavía no lo pondría en la primera etapa. Primero conviene guardar precio/tienda manualmente; después agregamos foto, código de barra u OCR cuando el flujo base esté estable.”

---

## Example: business inventory

Client:
Ángel

Raw idea:
Quiero registrar productos y proveedores.

Extracted idea:
Business inventory / vendor item tracking.

Matched capability:
grocery_list_v0 as item_list_v0 candidate

Reuse score:
3 — Strong match

Decision:
reusable_candidate

Client-facing response:
“Esto se parece a una capacidad que ya tenemos funcionando como lista de productos. Podemos adaptarla a inventario/proveedores y luego extenderla con precio, cantidad y seguimiento.”

