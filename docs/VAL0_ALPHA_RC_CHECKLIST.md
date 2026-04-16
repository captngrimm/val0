# VAL0 — ALPHA RC CHECKLIST

## Objetivo
Confirmar que Val0 está lo bastante estable, útil y presentable para comenzar alpha controlada con testers reales.

No buscamos perfección.
Buscamos:
- no hacer el ridículo
- no romper confianza rápido
- capturar feedback útil
- aprender con uso real

---

## 1. Criterio general de release candidate

Val0 se considera lista para alpha controlada si:

- mantiene conversación normal sin sentirse rota
- continuidad corta funciona lo suficiente como para sentirse distinta de un chat básico
- recordatorios funcionan en flujo normal
- agenda/calendario no da vergüenza
- voz funciona lo suficiente como para sumar y no restar
- el sistema de captura (`/bug`, `/feedback`, `/idea`, `/reports`) funciona bien
- la explicación para testers es clara y honesta
- no depende de magia, ni de promesas falsas, ni de memoria infinita fingida

---

## 2. Release gates obligatorios

### A. Estabilidad básica
- [ ] servicio arriba
- [ ] bot responde por texto
- [ ] no hay errores obvios al primer contacto
- [ ] no hay crashes visibles en flujo normal

### B. Continuidad
- [ ] "¿Qué estábamos haciendo?" responde algo útil
- [ ] "Sigue." responde algo útil
- [ ] "Convierte eso en 3 pasos." responde algo útil
- [ ] continuidad no se rompe feo en follow-up básico

### C. Recordatorios
- [ ] crear recordatorio funciona
- [ ] listar recordatorios funciona
- [ ] cancelar recordatorio funciona
- [ ] mensajes se sienten claros y humanos

### D. Agenda / calendario
- [ ] "¿Qué tengo mañana?" devuelve algo coherente
- [ ] "agenda mañana ..." crea evento
- [ ] errores de calendario no se sienten catastróficos
- [ ] no hay wording vergonzoso o demasiado técnico

### E. Voz
- [ ] nota de voz entra bien
- [ ] transcripción llega bien
- [ ] /voice on funciona
- [ ] /voice off funciona
- [ ] respuesta por voz, si aplica, se siente útil y no gimmick

### F. Feedback loop
- [ ] /bug funciona
- [ ] /feedback funciona
- [ ] /idea funciona
- [ ] /reports funciona
- [ ] los reportes se pueden revisar con sentido

### G. Framing alpha
- [ ] pitch corto listo
- [ ] demo flow listo
- [ ] tester guide listo
- [ ] invite en español listo
- [ ] checklist en español listo

---

## 3. Qué NO debe pasar en tester #1

Si cualquiera de estas pasa, no estamos listos para alpha abierta:

- pérdida total del hilo en una prueba básica
- recordatorios claramente rotos
- agenda claramente rota
- voz claramente rota
- tono demasiado raro o demasiado robótico en primeras interacciones
- mensajes que prometen memoria o autonomía que no existen
- flujo de feedback roto
- errores que obliguen a explicar arquitectura para defender el sistema

---

## 4. Qué sí aceptamos en alpha

Estas cosas todavía pueden existir sin bloquear alpha controlada:

- continuidad imperfecta a veces
- tono no siempre perfecto
- memoria limitada
- necesidad ocasional de repetir una instrucción
- pequeños bugs no críticos
- rough edges normales de producto temprano

La condición es:
que el sistema siga sintiéndose útil, vivo y recuperable.

---

## 5. Pass / Fail de alpha RC

## PASS
Val0:
- hace trabajo real
- reduce fricción
- se puede demoear sin vergüenza
- permite aprender de testers
- deja ganas de volver a usarla

## FAIL
Val0:
- se siente frágil
- se cae en funciones centrales
- obliga a demasiada explicación para justificar errores
- rompe confianza en voz / reminders / agenda / continuidad

---

## 6. Regla de decisión

Si cumple la mayoría de los release gates y no cae en un trust-killer:
**sale a alpha controlada.**

Si falla en un trust-killer:
**se corrige antes de exponerla.**

---

## 7. Próximo paso después de cada sesión de prueba

Después de cada prueba:
1. revisar `/reports`
2. anotar top 3 fricciones
3. decidir:
   - fix now
   - fix later
   - acceptable for alpha
4. actualizar criterio de readiness

---

## 8. Meta real de esta alpha

La meta no es impresionar.
La meta es validar que:

**Val0 ya hace trabajo real, ya ahorra fricción, y ya se siente viva.**

