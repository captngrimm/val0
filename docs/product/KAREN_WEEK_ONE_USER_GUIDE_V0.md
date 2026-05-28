# KAREN_WEEK_ONE_USER_GUIDE_V0

Guía simple para Karen durante la primera semana del founder-beta de Val.

Esta guía es para probar Val con calma, usando un documento real a la vez. No es un manual técnico ni una promesa de que todo está terminado.

---

## 1. Qué Puedes Probar Esta Semana

Puedes probar Val para:

- subir un PDF real del caso
- pedir que Val lo lea/transcriba cuando sea posible
- pedir un resumen claro
- revisar qué documentos tienes registrados
- preguntar cuál fue el último documento que subiste
- pedir un nombre sugerido para un documento
- guardar ese nombre sugerido
- usar tareas y recordatorios básicos

La idea de esta semana es ver qué te sirve de verdad y qué todavía se siente confuso, largo o poco natural.

---

## 2. Flujo Recomendado Para Documentos

Después de subir un PDF, puedes probar estos mensajes:

```text
Val, transcribe este documento y hazme un resumen
```

```text
Val, qué fue lo último que subí?
```

```text
Val, resume el último documento
```

```text
Val, sugiere nombre para este documento
```

```text
Val, guarda ese nombre
```

```text
Val, qué documentos tengo?
```

Recomendación: empieza con un solo documento real del caso. Cuando ese flujo se sienta bien, probamos más.

---

## 3. Qué Significa Cada Cosa

**Documento recibido**

Val registró el archivo que subiste.

**Texto leído**

Val pudo extraer o indexar texto del documento. Eso permite pedir resumen y buscar información con más seguridad.

**Resumen disponible**

Val ya tiene un resumen guardado para ese documento.

**Necesita OCR/revisión manual**

Val registró el archivo, pero todavía no puede leerlo bien automáticamente. Puede pasar con fotos, escaneos difíciles o documentos con texto poco claro.

**Nombre sugerido**

Val propone un nombre más claro para reconocer el documento. Esto no cambia el archivo original.

**Etiquetas**

Son palabras clave para ayudarte a ubicar el documento después, por ejemplo: finca, oficio, registro, AGI, resumen, PDF.

**Archivo original intacto**

Cuando Val guarda un nombre sugerido, guarda una etiqueta o alias para mostrarlo mejor. No borra ni renombra físicamente el archivo original.

---

## 4. Qué NO Esperar Todavía

Todavía no esperes:

- subir muchos documentos a la vez
- OCR perfecto para fotos, manuscritos o escaneos difíciles
- revisión manual de letra escrita totalmente automatizada
- soporte completo para Word/DOCX en todos los casos
- que Val reemplace a una abogada o profesional
- que Val nunca se equivoque

Esto es una beta. Tu feedback es parte del producto.

---

## 5. Feedback Que Nos Ayuda

Cuando pruebes Val, dinos:

- qué parte te resultó útil
- qué respuesta se sintió demasiado larga
- qué palabra o sección te confundió
- si prefieres respuestas cortas primero y detalles solo si los pides
- si los nombres sugeridos y etiquetas te ayudan o se sienten como demasiado

También ayuda mucho decirlo así:

```text
Esto sí me sirve.
```

```text
Esto está muy largo.
```

```text
Esto no lo diría así.
```

```text
Esto me confunde.
```

---

## 6. Mensaje Corto Para WhatsApp

Karen, esta semana probemos Val con un documento real a la vez. Súbelo y dile: “Val, transcribe este documento y hazme un resumen”. Después puedes pedir “qué fue lo último que subí”, “resume el último documento”, “sugiere nombre para este documento” y “guarda ese nombre”. Lo importante es que me digas qué te sirve, qué está muy largo y qué se siente confuso. Esto es founder-beta: ya debe ayudarte, pero todavía estamos afinando contigo.

---

## 7. Notas Para Operador

- Esta guía no es runtime code.
- No cambia comportamiento del bot.
- Mantener `clients/karen/CLIENT_GROCERY.md` sin commit.
- La validación RC real todavía requiere que un PDF legal real de Karen pase el flujo completo.
- No prometer batch upload, OCR perfecto, conclusiones legales, ni soporte completo para todos los formatos.
