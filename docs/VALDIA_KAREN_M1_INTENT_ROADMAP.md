# Valdía / Karen Client-Zero — Mes 1 Intent Roadmap

Fecha base: 2026-05-19  
Branch: karen-client-zero-mvp-2026-05-25  
Estado actual sellado: `edec7be Add Karen natural intent router v0`

## Objetivo del producto

Valdía no debe ser solo un bot del caso de la finca.  
La finca es el primer caso real para probar el músculo de una operadora personal.

Meta: que Karen pueda hablarle a Val por texto o voz de forma natural sobre:

- caso/finca/legal
- documentos
- citas
- recordatorios
- agenda
- escuela/familia
- supermercado/listas
- trabajo/pendientes
- vida diaria

Val debe interpretar intención y ejecutar herramientas internas sin exigir frases exactas.

## Modelo mental

Karen habla natural:

> “Tengo que llevar papeles a Nora, ayúdame.”

Val debe:

1. Detectar intención.
2. Identificar herramienta/capacidad.
3. Ejecutar o pedir el dato mínimo faltante.
4. Guardar información estructurada.
5. Ofrecer seguimiento útil.

No queremos “menú Atari”.  
Queremos “operadora con herramientas”.

## Estado actual

### Sellado

- `a3ffe43 Polish Karen natural lawyer prep flow`
- `edec7be Add Karen natural intent router v0`

### Router actual

Archivo:

- `core/karen_intent_router.py`

Intents detectados en v0:

- `prepare_lawyer`
- `review_missing`
- `organize_documents`
- `list_documents`
- `agenda_today`
- `agenda_tomorrow`
- `agenda_week`
- `reminder_create`
- `reminder_list`
- `next_action`
- `unknown`

Conexión viva inicial en `bot.py`:

- `prepare_lawyer`
- `review_missing`
- `organize_documents`

## Antes del 25 de mayo — objetivo realista

Karen debe poder probar Val como founder-beta útil en su caso y vida básica.

### P0 antes del 25

1. Legal/finca estable
   - preparar paquete Nora
   - revisar faltantes
   - organizar documentos
   - consultar hechos básicos: finca, herederos, datos registrales

2. Voz usable
   - notas de voz entran al pipeline
   - frases naturales caen en intents correctos en flujos principales

3. Recordatorios básicos
   - crear recordatorios
   - listar recordatorios
   - pedir hora si falta dato

4. Agenda básica
   - “qué tengo hoy”
   - “qué tengo mañana”
   - “qué tengo esta semana”

5. Captura de eventos
   - “Registra que hoy hablé con Nora”
   - guardar evento estructurado por área/caso

6. UX no Atari
   - menos “dime exactamente…”
   - más “entiendo, hago esto”
   - si falta un dato, preguntar solo ese dato

## Mes 1 pagado — objetivo

“Val me ayuda a no perder cosas.”

Capacidades esperadas:

| Área | Capacidad |
|---|---|
| Legal/finca | paquete, faltantes, eventos, documentos, preguntas |
| Agenda | hoy/mañana/semana, citas básicas |
| Recordatorios | crear, listar, confirmar, seguimiento básico |
| Escuela/familia | registrar pendientes/eventos |
| Supermercado | listas simples y compras recurrentes manuales |
| Trabajo/personal | tareas y pendientes básicos |
| Voz | entrada natural usable |
| Memoria | guardar eventos y preferencias simples |

## Mes 2 — objetivo

“Val empieza a recordar contexto entre áreas.”

Capacidades:

- mejores intents multi-área
- “qué tengo pendiente” unificado
- contexto por dominio: legal, escuela, súper, trabajo, familia
- eventos y tareas con follow-up sugerido
- mejores respuestas naturales sin menú

## Mes 3 — objetivo

“Val empieza a operar ciclos.”

Ejemplo:

1. Karen registra cita con Nora.
2. Val pregunta hora si falta.
3. Val ofrece recordatorio antes.
4. Val ofrece follow-up después.
5. Después de la cita pregunta qué pasó.
6. Guarda resumen, próximos pasos y documentos faltantes.

Capacidades:

- follow-up post-cita
- pre-cita checklist
- rutinas simples
- listas recurrentes
- contexto reutilizable por LLM/router

## Datos que debemos guardar desde ya

Cada captura debe intentar guardar:

- `domain`: legal, agenda, supermercado, escuela, trabajo, familia, personal
- `intent`: acción detectada
- `raw_text`: lo que dijo Karen
- `normalized_text`: texto normalizado
- `entities`: personas, fechas, lugares, documentos
- `due_at`: si hay fecha/hora
- `followup_at`: si Val debe preguntar después
- `source`: text, voice, document, manual
- `confidence`: alta/media/baja
- `status`: open, done, cancelled, pending_info

## Próximos intents candidatos

### Legal/documentos

- `prepare_lawyer`
- `review_missing`
- `organize_documents`
- `list_documents`
- `ask_case_fact`
- `register_case_event`

### Agenda/recordatorios

- `agenda_today`
- `agenda_tomorrow`
- `agenda_week`
- `reminder_create`
- `reminder_list`
- `appointment_capture`
- `appointment_followup`

### Vida diaria

- `grocery_add`
- `grocery_list`
- `school_event`
- `work_task`
- `personal_task`
- `daily_pending_summary`

## Próximo bloque técnico sugerido

1. Conectar `list_documents` al router v0.
2. Conectar agenda/reminders al router solo si no rompe gates existentes.
3. Crear captura estructurada de evento/cita:
   - fecha/hora
   - persona
   - dominio
   - follow-up sugerido
4. Crear primer flujo post-cita:
   - “Tengo cita con Nora hoy a las 3”
   - Val pregunta si quiere recordatorio antes y seguimiento después.

## Regla de producto

No responder con comandos cuando Val puede ejecutar.

Malo:

> “Pide: Val, prepárame el paquete…”

Bueno:

> “Perfecto, te preparo el paquete.”

Si falta dato:

> “Dale. ¿A qué hora es la cita?”


---

## Founder-client / modelo reusable

Karen es client-zero personal.  
El primer cliente corporativo será corporate-client-zero.

La idea no es construir cada Val desde cero. Cada cliente enseña un flujo real y ese flujo se convierte en capacidad reusable de Valdía.

### Patrón Borg / capacidades reusables

Cada implementación debe dejar algo reutilizable:

| Cliente | Aprendizaje | Capacidad reusable |
|---|---|---|
| Karen | legal/finca/documentos/citas | documentos, citas, recordatorios, paquetes, follow-up |
| Cliente personal 2 | escuela/supermercado/familia | listas, rutinas, tareas familiares |
| Ángel / corporativo | procesos comerciales/proveedores/clientes | mapa de procesos, seguimiento, reportes, pipeline |
| Corporate client 2 | operaciones internas | roles, responsables, dashboards, integraciones |

No vendemos solo “un bot”.  
Vendemos implementación, memoria estructurada, roadmap y operación.

## Client Roadmap / Wizard / Idea Intake

Cada Val cliente debe poder responder preguntas como:

- “¿Qué puedes hacer hoy?”
- “¿Qué viene después?”
- “¿Estamos a tiempo?”
- “¿Cuándo podremos tener supermercado/agenda/follow-up?”
- “Tengo una idea para que Val me ayude con X.”
- “¿Eso entra en el roadmap?”

### Comportamiento esperado

Cuando el cliente dé una idea, Val debe:

1. Capturar la idea.
2. Clasificarla por dominio.
3. Decir si ya existe, si está planeada o si es nueva.
4. Ubicarla tentativamente en roadmap.
5. Guardarla para revisión de ValPrime/admin.

Ejemplo:

> “Val, se me ocurrió que me ayudes con supermercado.”

Respuesta ideal:

> “Buena idea. Eso entra en supermercado/listas. Hoy puedo registrar listas simples; en Mes 1 podemos guardar listas recurrentes manuales; en Mes 2 podríamos empezar a sugerir qué revisar antes de ir al súper. La dejo como idea del roadmap.”

## ValPrime como fuente de verdad

ValPrime debe actuar como cockpit central para:

- clientes
- roadmaps
- checkpoints
- ideas
- entregables
- límites
- estado actual
- próximos pasos

Cada Val cliente debe usar una vista limitada de su propio contexto.

Regla de privacidad:

- La Val de Karen no debe ver datos de otros clientes.
- La Val corporativa no debe ver datos de Karen.
- ValPrime/admin puede coordinar roadmap y estado general.
- Las capacidades reusables se comparten como código/patrón, no como datos privados.

## Oferta comercial sugerida

### Diagnóstico inicial

Precio sugerido: $150

Entregables:

- mapa de procesos
- dolores principales
- oportunidades AI
- quick wins
- roadmap 30/60/90/180 días
- stack sugerido
- propuesta de implementación

### Implementación Val personalizada

Precio founder sugerido: $300/mes

Incluye:

- Val personalizada al cliente
- memoria estructurada
- flujos iniciales
- seguimiento
- roadmap vivo
- ajustes por feedback
- coordinación técnica básica

Opción comercial recomendada:

> El diagnóstico de $150 se acredita al primer mes de implementación si el cliente decide continuar.

## Objeción: “¿Por qué no uso ChatGPT?”

Respuesta:

ChatGPT es una herramienta general.  
Val es una implementación operativa personalizada.

ChatGPT conversa muy bien, pero el cliente tiene que explicarle todo y diseñar el sistema solo.  
Val se configura alrededor de sus procesos, documentos, pendientes, agenda, roadmap y memoria estructurada.

No vendemos acceso a AI.  
Vendemos convertir desorden operativo en un sistema que recuerda, organiza y empuja próximos pasos.

## Objeción: “¿Por qué no espero seis meses?”

Respuesta:

Puede esperar. Pero si espera seis meses, su Val empieza de cero.

Entrar temprano permite:

- precio founder
- acompañamiento cercano
- influencia en roadmap
- memoria acumulada desde el día uno
- procesos mapeados antes de que la herramienta esté más madura
- quick wins tempranos

Frase clave:

> No estás pagando solo por lo que Val hace hoy. Estás comprando que tu operación empiece a convertirse en sistema desde hoy.

## Roadmap extendido a 6 meses

| Mes | Foco | Resultado esperado |
|---|---|---|
| Mes 1 | utilidad básica | recordatorios, documentos, agenda básica, eventos, roadmap, memoria inicial |
| Mes 2 | multi-área | legal, escuela, supermercado, trabajo, citas, tareas |
| Mes 3 | ciclos/follow-up | pre/post cita, seguimiento, próximos pasos, contexto por dominio |
| Mes 4 | conversación contextual | más naturalidad dentro del contexto del cliente |
| Mes 5 | operación recurrente | reportes, backlog, decisiones, patrones, responsables |
| Mes 6 | memoria ampliada-ready | estructura lista para ingestión grande / “memoria infinita” cuando esté disponible |

## Posicionamiento final

Val no compite contra ChatGPT como chat genérico.  
Val compite contra el caos operacional del cliente.

ChatGPT = inteligencia general.  
Val = inteligencia operativa personalizada.

