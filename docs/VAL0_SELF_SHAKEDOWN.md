# VAL0 — SELF SHAKEDOWN

## Objetivo
Hacer pruebas internas disciplinadas antes de poner Val0 frente a testers reales.

Este documento sirve para:
- simular uso real
- detectar vergüenzas antes de Monday
- probar lo más crítico sin inventar nuevos features
- separar claramente lo que ya está bien de lo que todavía duele

---

## 1. Modos de prueba

Hay dos tipos de prueba obligatorios:

### A. Fresh-user simulation
Simular un usuario nuevo, idealmente con:
- otra cuenta de Telegram
- otro chat_id
- cero contexto previo

Esto prueba:
- primera impresión
- claridad de onboarding
- que el sistema no dependa de memoria vieja
- si realmente se entiende solo

### B. Existing-user regression
Probar desde el chat habitual.

Esto prueba:
- que no rompimos flujos existentes
- continuidad
- follow-ups
- reminders
- agenda
- voz
- feedback loop

Ambos tipos importan.

---

## 2. Qué probar en fresh-user simulation

### 1. Primera impresión
Preguntar algo natural, por ejemplo:
- "Hola"
- "Ayúdame a organizar algo"
- "Necesito acordarme de algo mañana"

Observar:
- si suena viva
- si suena útil
- si no suena rara o corporativa

### 2. Continuidad básica
Después de algunos mensajes:
- "¿Qué estábamos haciendo?"
- "Sigue."
- "Convierte eso en 3 pasos."

Observar:
- si mantiene suficiente hilo
- si devuelve algo accionable
- si no se vuelve genérica

### 3. Reminder
- crear un recordatorio real
- listar recordatorios
- cancelar uno

Observar:
- claridad
- UX
- si se entiende sin explicación extra

### 4. Calendario
- "¿Qué tengo mañana?"
- "agenda mañana 3pm llamada de prueba"

Observar:
- si responde con claridad
- si crea bien
- si el read path devuelve cosas coherentes

### 5. Voz
- enviar una nota de voz
- activar /voice on
- probar /voice off

Observar:
- si transcribe bien
- si modo voz responde bien
- si suma o solo hace show

### 6. Feedback loop
Probar:
- /bug
- /feedback
- /idea
- /reports

Observar:
- si el flujo guía bien
- si se persiste bien
- si el review sirve

---

## 3. Qué probar en existing-user regression

### 1. Continuidad de trabajo
- "¿Qué estábamos haciendo?"
- "Sigue."
- "No, la prioridad real."
- "Convierte eso en 3 pasos."

### 2. Bertha / drift
Intentar desviarla:
- Obsidian
- watch UX
- ideas laterales

Observar:
- si empuja de vuelta
- si no se enreda
- si el tono ayuda en vez de molestar

### 3. Reminders / agenda / voz
Repetir flujos clave desde el chat vivo.

### 4. Captura real
Usar:
- /bug
- /feedback
- /idea

Como si fueras tester real.

---

## 4. Checklist rápido de cada sesión

En cada sesión preguntar:

- [ ] ¿Se sintió útil?
- [ ] ¿Se sintió viva?
- [ ] ¿Ahorró tiempo?
- [ ] ¿Redujo fricción?
- [ ] ¿Mantuvo el hilo?
- [ ] ¿Reminders estuvieron bien?
- [ ] ¿Agenda estuvo bien?
- [ ] ¿Voz estuvo bien?
- [ ] ¿Hubo algún momento vergonzoso?
- [ ] ¿Hubo algún trust-killer?

---

## 5. Clasificación de hallazgos

Cada hallazgo debe caer en una de estas:

### A. Trust-killer
Rompe confianza rápido.
Ejemplos:
- reminder roto
- agenda rota
- voz totalmente rota
- pérdida grave del hilo
- wording muy malo en primera impresión

### B. Alta fricción
No mata el producto, pero molesta mucho.
Ejemplos:
- follow-up raro
- demasiado texto
- tono raro
- UX poco clara

### C. Menor / tolerable
Se puede dejar para después.
Ejemplos:
- wording mejorable
- detalle cosmético
- una respuesta no ideal pero no dañina

---

## 6. Qué hacer después de cada self-shakedown

1. Registrar lo encontrado con:
- /bug
- /feedback
- /idea

2. Revisar:
- /reports

3. Hacer lista corta:
- fix now
- fix soon
- acceptable for alpha

4. No abrir side quests.

---

## 7. Regla central

No estamos probando para demostrar que Val0 es perfecta.

Estamos probando para confirmar que:
- ya sirve
- ya reduce fricción
- ya se siente viva
- no se rompe feo en lo central

---

## 8. Meta antes de Monday

Antes de Monday, debemos llegar a esto:

- al menos una prueba fresh-user
- al menos una prueba existing-user
- al menos un pass completo de:
  - continuidad
  - reminders
  - agenda
  - voz
  - feedback loop
- top issues clasificados
- trust-killers resueltos o explícitamente conocidos

Si llegamos ahí, Monday ya no será improvisación.
Será shakedown real con mejores probabilidades.

