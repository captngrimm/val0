# KAREN_WEEK1_TEST_MANUAL_V0

Purpose:
Simple week-1 test guide for Karen's founder-beta pilot.

This guide explains what to test, what to expect, and what feedback to send Frank. It is not technical, not a legal guide, and not a promise that Val is the final app.

Tone:
Spanish-first, simple, read-aloud friendly, no technical jargon.

---

## Before You Start

- Usa el chat de Telegram con Val.
- Manda un comando a la vez.
- Espera que Val conteste antes de mandar el siguiente.
- Si algo se ve mal, raro o demasiado largo, copia o toma screenshot de la respuesta y mándaselo a Frank.
- No subas documentos nuevos sensibles a menos que Frank te confirme que está bien.

Regla simple:

```text
Una prueba a la vez. Si algo falla, lo marcamos y seguimos.
```

---

## Test 1: Understand Val

Prompt:

```text
Val, qué eres
```

Expected:

- Una explicación corta.
- Debe decir que Val está en founder-beta.
- Debe explicar que Val es una capa operativa personal, no solo un chat.
- No debe prometer magia, memoria infinita ni acciones autónomas.

Karen should answer:

- ¿Te quedó claro qué es Val?
- ¿Sonó raro, largo o confuso?

---

## Test 2: Capabilities

Prompt:

```text
Val, qué puedes hacer
```

Expected:

- Lista corta de workflows útiles hoy.
- Puede mencionar documentos, cronología, agenda/recordatorios, Daily Operator y preparación de reuniones.
- No debe sonar como si todo estuviera finalizado.

Karen should answer:

- ¿Cuál de esas cosas usarías primero?
- ¿Faltó algo que esperabas ver?

---

## Test 3: Documents

Prompt:

```text
Val, qué documentos tengo
```

Expected:

- Lista compacta de documentos.
- Sin IDs técnicos por defecto.
- Estados honestos: texto leído/indexado, requiere OCR/revisión, guardado, estado por revisar.
- No debe parecer un reporte técnico.

Karen should answer:

- ¿La lista se entiende?
- ¿Qué nombre de documento cambiarías para que sea más claro?
- ¿El estado de lectura/revisión se entiende?

---

## Test 4: Chronology

Prompt:

```text
Val, ordéname la cronología del caso
```

Expected:

- Cronología de eventos registrados.
- Puede mostrar fuente/provenance todavía.
- Debe organizar, no inventar.
- No debe dar conclusiones legales.

Karen should answer:

- ¿Te ayuda a recordar el caso?
- ¿Está demasiado técnico?
- ¿Falta algún evento importante que tú recuerdes?

---

## Test 5: Year Question

Prompt:

```text
Val, qué pasó en 2024
```

Expected:

- Respuesta desde el contexto registrado del caso.
- No debe contestar como historia general del mundo.
- No debe inventar hechos que no estén registrados.

Karen should answer:

- ¿Eso coincide con lo que recuerdas?
- ¿Falta algo importante?
- ¿La respuesta fue clara?

---

## Test 6: Daily Operator

Prompt:

```text
Val, qué hago hoy
```

Expected:

- Resumen diario compacto.
- Debe enfocarse en agenda, próximo pendiente y documentos/revisión si aplica.
- No debe ser un reporte larguísimo.
- No debe decir "dame detalles del 1" todavía.

Karen should answer:

- ¿Esto te sirve como resumen del día?
- ¿Está corto o todavía largo?
- ¿Te ayudó a saber por dónde empezar?

---

## Test 7: Tomorrow

Prompt:

```text
Val, qué tengo mañana
```

Expected:

- Agenda o recordatorios de mañana si están configurados.
- No debe confundirse con documentos o cronología.
- No debe prometer acceso a calendarios que no estén configurados.

Karen should answer:

- ¿Esto te ayuda a prepararte?
- ¿La respuesta fue clara?

---

## Test 8: Lawyer Prep

Prompt:

```text
Val, prepárame para hablar con la abogada
```

Expected:

- Checklist.
- Preguntas sugeridas.
- Documentos a tener listos.
- Pendiente antes de la reunión.
- Límite legal/profesional claro.
- No debe dar conclusiones legales.

Karen should answer:

- ¿Esto te ayuda antes de hablar con Nora/abogada?
- ¿Qué pregunta agregarías?
- ¿Qué documento te gustaría que Val mencionara mejor?

---

## Optional: Full Daily Summary

Prompt:

```text
Val, dame el resumen completo de hoy
```

Expected:

- Vista más larga solo si quieres más detalle.
- Puede tener más contexto que el Daily Operator compacto.
- No es el modo recomendado si solo quieres saber qué hacer rápido.

Karen should answer:

- ¿Esto es útil o demasiado largo?
- ¿Prefieres el compacto o el completo?

---

## Optional: Upload / Document Test

Solo hacer esto con un archivo de prueba inofensivo o un documento que Frank apruebe.

Qué esperar:

- Un PDF/texto limpio puede ser más fácil de leer.
- Una foto o screenshot puede requerir OCR/revisión.
- Si Val dice que necesita OCR/revisión, eso es esperado. No es fallo si lo dice claramente.

After upload prompt:

```text
Val, qué documentos tengo
```

Karen should answer:

- ¿Apareció el documento?
- ¿El estado fue claro?
- ¿Val dijo honestamente si faltaba OCR/revisión?

---

## Feedback Format For Karen

Después de probar, mándale esto a Frank:

```text
Me ayudó:

Me confundió:

Muy largo:

Faltó:

Prioridad próxima:
```

También sirve mandar screenshots con una nota corta:

```text
Esta respuesta me sirvió.
```

```text
Esta respuesta me confundió.
```

```text
Esto esperaba que saliera diferente.
```

---

## What Not To Test Yet

No probar todavía como si ya estuviera listo:

- Carpetas/folders como Finca, Proyectos, Pendientes.
- OCR/foto-a-texto perfecto.
- Lectura confiable de cualquier DOCX o foto.
- Conclusiones legales.
- Acciones autónomas.
- Conversación abierta full tipo ChatGPT para cualquier tema.
- Producto final listo para todo.

Frase simple:

```text
Si no está listo, no lo forzamos. Lo marcamos para roadmap.
```

---

## End-Of-Week Review

Al final de la semana, Frank y Karen deciden:

- Keep: qué se queda porque sí ayudó.
- Adjust: qué hay que mejorar.
- Pause: qué no conviene usar todavía.
- Rescope: qué se volvió más grande o delicado.

Pick next priority:

- OCR/foto-a-texto.
- Carpetas.
- Agenda unificada.
- Mejores nombres de documentos.
- Detail drilldown: "dame detalles del 2".

Goal:

```text
Que Val ayude en un flujo real, sin fingir que ya es producto final.
```

