# POWERCLUB-CRM-01A - Brief Corporativo + Alcance MVP

Propósito:
Documento client-facing para preparar una conversación ejecutiva con Power Club sobre un piloto operativo de CRM, usando el Stage de Val AI Ops como superficie de consultoría y demostración.

Estado:
Borrador de propuesta para piloto. No es un contrato de implementación final, no es un reemplazo completo del CRM actual y no compromete alcance, fechas, accesos, datos ni precios hasta que la gerencia apruebe el piloto.

Nota de datos:
Este documento usa únicamente supuestos anónimos y datos generales de descubrimiento. No incluye registros reales de socios, prospectos, archivos exportados, conversaciones privadas, archivos vivos de contactos internos, credenciales ni data operativa sensible.

---

## 1. Resumen Ejecutivo

Power Club parece tener una oportunidad comercial clara: ordenar el seguimiento de prospectos y socios con un CRM operativo ligero, pensado para la forma real en que trabajan las sucursales.

Según los supuestos iniciales, Power Club opera alrededor de 10 sucursales, con un estimado de 35-45 usuarios/operadores y aproximadamente 1,500-2,000 registros al mes provenientes de Excel o exportaciones. El sistema actual parece demasiado complejo, poco alineado al proceso comercial o difícil de usar como herramienta diaria.

La fase 1 propuesta no busca reemplazar todo el software actual. Busca probar, en pequeño, una capa práctica de seguimiento: una lista clara para asesores, un flujo simple de actualización y un tablero de visibilidad gerencial para saber qué oportunidades están activas, vencidas, ganadas, perdidas o sin dueño.

Objetivo del piloto:
Reducir oportunidades perdidas por falta de seguimiento, aumentar la visibilidad gerencial y validar si Power Club necesita un CRM operativo ligero antes de considerar una implementación más grande.

Siguiente movimiento recomendado:
Hacer una reunión corta de descubrimiento con el contacto interno y luego una conversación con Gerencia General para confirmar el proceso real, seleccionar una sucursal o flujo piloto y preparar una demo con datos ficticios.

---

## 2. Resumen del Problema

Dolor principal:
Power Club puede estar perdiendo ventas, renovaciones o reactivaciones por seguimiento irregular, baja visibilidad gerencial y falta de una lista diaria clara para los asesores.

Causas probables:

- La información existe en Excel o exportaciones, pero no siempre queda claro cuál es la siguiente acción.
- Los asesores pueden trabajar desde listas separadas, mensajes, memoria o instrucciones informales.
- Los gerentes de sucursal pueden no ver a tiempo cuáles seguimientos están vencidos.
- Gerencia puede tener números generales, pero poca visibilidad sobre por qué se pierden oportunidades.
- El software actual puede tener demasiados pasos o no reflejar cómo Power Club realmente vende, renueva y recupera socios.

Impacto comercial:

- Prospectos calientes se enfrían antes de recibir seguimiento.
- Renovaciones o reactivaciones pueden quedar sin dueño.
- Los asesores pueden duplicar esfuerzos o trabajar con información desactualizada.
- Los gerentes detectan problemas tarde, cuando la oportunidad ya se perdió.
- La empresa no tiene una fuente operativa simple para priorizar acciones comerciales.

---

## 3. Supuestos del Flujo Actual

Estos supuestos deben validarse antes de cualquier implementación.

- Los registros comerciales se generan desde Excel o exportaciones del sistema actual.
- Cada sucursal tiene actividad comercial propia y asesores responsables.
- Prospectos, socios, renovaciones, pruebas, reactivaciones y oportunidades pendientes pueden aparecer mezclados en los exportes.
- El seguimiento ocurre de forma manual por llamada, mensaje, atención en sucursal u otros canales aprobados por la empresa.
- El sistema actual no funciona como lista diaria simple para todos los asesores.
- Los gerentes necesitan visibilidad por sucursal, asesor, estado y fecha de próximo seguimiento.
- Un contacto interno de confianza puede validar vocabulario, proceso real y sensibilidad antes de la reunión con Gerencia General.

Flujo anónimo de referencia:

`Exportación -> limpieza/importación -> asignar sucursal/asesor -> clasificar estado -> seguimiento diario -> actualizar resultado -> revisión gerencial -> próxima acción o cierre`

---

## 4. Usuarios Objetivo

### Gerencia General

Necesita una vista clara de salud comercial, seguimiento vencido, oportunidades perdidas, avance por sucursal y puntos donde el proceso se tranca.

### Gerentes de Sucursal

Necesitan ver qué está pendiente, qué está vencido, quién tiene cada oportunidad, qué se ganó, qué se perdió y qué requiere atención.

### Asesores / Operadores

Necesitan una cola diaria sencilla: a quién contactar, por qué, cuándo fue el último contacto, cuál es la próxima acción y cómo registrar el resultado.

### Contacto Interno de Confianza

Un contacto interno puede ayudar a validar el lenguaje interno, los pasos reales, los puntos sensibles y la mejor forma de presentar el piloto a Gerencia.

### Responsable de Datos / Administración

Necesita preparar exportaciones, revisar duplicados, mantener campos básicos y apoyar la carga manual durante el piloto.

---

## 5. Alcance MVP del CRM

Meta de fase 1:
Diseñar y validar un CRM operativo ligero que mejore el seguimiento y la visibilidad sin obligar a Power Club a una migración grande desde el primer día.

Incluido en el MVP:

- Estructura de datos ficticios para demo.
- Modelo de carga desde Excel o CSV.
- Lista de prospectos/socios/oportunidades con búsqueda y filtros.
- Asignación por sucursal y asesor.
- Estado comercial y estado de seguimiento.
- Fecha de próxima acción.
- Resultado del último contacto.
- Vista de seguimientos vencidos.
- Requisitos de tablero gerencial.
- Etapas comerciales básicas.
- Métricas de éxito del piloto.
- Proceso manual de importación/actualización.
- Brief corporativo y alcance de demo para reunión.

Objetos principales del MVP:

- Prospecto, socio u oportunidad comercial.
- Sucursal.
- Asesor.
- Tarea de seguimiento.
- Resultado o estado.
- Vista gerencial.

Definición de éxito:
El piloto es exitoso si los asesores pueden trabajar una lista diaria, los gerentes pueden ver oportunidades vencidas o sin dueño, y Gerencia puede medir si la disciplina de seguimiento mejora durante el periodo piloto.

---

## 6. Campos de Datos Sugeridos

Campos mínimos para fase 1:

- ID de registro.
- Nombre completo.
- Teléfono.
- Correo, si existe.
- Sucursal.
- Asesor asignado.
- Fuente.
- Tipo de oportunidad.
- Estado actual.
- Prioridad.
- Fecha de creación.
- Fecha de último contacto.
- Resultado del último contacto.
- Fecha de próxima acción.
- Tipo de próxima acción.
- Notas.
- Plan de interés o valor estimado, si existe.
- Motivo de cierre, si se perdió o no hay interés.

Estados sugeridos:

- Nuevo.
- Asignado.
- Contactado.
- Seguimiento programado.
- Interesado.
- Pendiente de decisión.
- Ganado.
- Perdido.
- Sin respuesta.
- Inválido/duplicado.

Tipos de oportunidad sugeridos:

- Nueva membresía.
- Renovación.
- Reactivación.
- Upgrade.
- Referido.
- Lead corporativo/grupal.
- Seguimiento de prueba.
- Otro.

Reglas de calidad de datos:

- No usar datos reales de socios o prospectos en materiales de demo.
- No incluir cédulas, información de pago, datos sensibles de salud ni notas privadas en fase 1.
- Marcar duplicados antes de asignar trabajo a asesores cuando sea posible.
- Todo registro activo debe tener un dueño y una próxima acción.

---

## 7. Flujo del Asesor / Operador

Flujo diario sugerido:

1. Abrir la lista asignada.
2. Filtrar por hoy, vencidos, prioridad alta o nuevos.
3. Revisar contexto y último resultado.
4. Contactar al prospecto o socio por el canal manual aprobado por Power Club.
5. Registrar resultado.
6. Definir próxima acción o motivo de cierre.
7. Continuar con el siguiente registro.

La vista del asesor debe responder:

- ¿A quién debo contactar ahora?
- ¿Por qué esta persona está en mi lista?
- ¿Qué pasó en el último contacto?
- ¿Qué estado debo actualizar?
- ¿Cuándo toca el próximo seguimiento?
- ¿Qué oportunidades están vencidas?

Límites para asesores:

- El sistema apoya el seguimiento; no vende automáticamente.
- Fase 1 no envía automatizaciones por WhatsApp.
- Fase 1 no toma decisiones autónomas.
- El asesor mantiene la relación, el criterio comercial y la actualización final.

---

## 8. Flujo Gerencial

Flujo diario sugerido:

1. Revisar resumen por sucursal.
2. Ver seguimientos vencidos.
3. Identificar registros sin asignar.
4. Revisar carga por asesor.
5. Detectar oportunidades estancadas.
6. Pedir acción sobre casos prioritarios.
7. Revisar resultados y motivos de cierre.

Flujo semanal sugerido:

- Comparar actividad y conversión por sucursal.
- Revisar motivos de oportunidades perdidas.
- Identificar registros sin contacto.
- Ajustar asignaciones o cadencia de seguimiento.
- Elevar problemas de proceso a Gerencia General.

La vista gerencial debe responder:

- ¿Qué sucursal tiene mayor riesgo de seguimiento vencido?
- ¿Qué asesores tienen más carga o poca actividad registrada?
- ¿Qué oportunidades se están envejeciendo?
- ¿Qué se está perdiendo y por qué?
- ¿Qué cambió desde la semana pasada?

---

## 9. Requisitos del Dashboard

El dashboard de fase 1 debe priorizar claridad y acción, no complejidad.

Tarjetas principales:

- Oportunidades activas.
- Registros nuevos del periodo.
- Seguimientos para hoy.
- Seguimientos vencidos.
- Oportunidades ganadas.
- Oportunidades perdidas.
- Oportunidades sin respuesta.
- Registros sin asignar.

Filtros requeridos:

- Rango de fecha.
- Sucursal.
- Asesor.
- Estado.
- Tipo de oportunidad.
- Prioridad.

Tablas o gráficos recomendados:

- Pipeline por estado.
- Seguimientos vencidos por sucursal.
- Carga por asesor.
- Resultados por semana.
- Motivos de pérdida.
- Antigüedad de oportunidades.
- Desempeño por fuente, si el dato es confiable.

Métricas del piloto:

- Porcentaje de registros activos con asesor asignado.
- Porcentaje de registros activos con próxima acción.
- Cantidad de seguimientos vencidos.
- Volumen de intentos de contacto.
- Movimiento de ganadas/perdidas por semana.
- Registros cerrados con motivo claro.

---

## 10. Roadmap 30/60/90

### Primeros 30 días - Descubrimiento + estructura del piloto

- Confirmar flujo por sucursal, roles y vocabulario comercial.
- Revisar estructura de exportación con campos ficticios.
- Definir campos mínimos requeridos.
- Preparar demo con datos ficticios.
- Diseñar flujo del asesor y flujo gerencial.
- Validar requisitos del dashboard con el contacto interno y Gerencia General.
- Escoger una sucursal o grupo pequeño para piloto.
- Definir métricas de éxito.

### Días 31-60 - Piloto operativo controlado

- Ejecutar piloto con data aprobada y preparada manualmente.
- Capacitar asesores y gerente del grupo piloto.
- Monitorear uso de la lista diaria.
- Revisar semanalmente seguimientos vencidos y cambios de estado.
- Ajustar campos, estados y filtros.
- Documentar problemas de proceso y calidad de datos.

### Días 61-90 - Decisión y plan de expansión

- Revisar resultados del piloto.
- Comparar visibilidad antes/después.
- Decidir si se continúa, se pausa o se expande.
- Preparar plan de rollout por sucursales si el piloto funciona.
- Estimar soporte necesario para 35-45 usuarios.
- Separar requisitos de producción de lo validado en fase 1.

---

## 11. Propuesta de Piloto

Piloto recomendado:

- Duración: 4-6 semanas.
- Alcance: 1-2 sucursales o un flujo comercial específico.
- Usuarios: 5-10 asesores/operadores iniciales más un gerente revisor.
- Datos: muestra ficticia para demo; subconjunto aprobado de exportación solo después de confirmar alcance.
- Proceso: importación/actualización manual desde Excel/CSV; sin integración viva con backend en fase 1.
- Salida: especificación de CRM operativo ligero, flujo de asesores, flujo gerencial, requisitos de dashboard, reporte de hallazgos y recomendación de expansión.

Metas del piloto:

- Reducir oportunidades invisibles u olvidadas.
- Aumentar registros con dueño y próxima acción.
- Dar a gerentes una vista confiable de seguimientos vencidos.
- Validar si Power Club necesita un CRM operativo ligero, una capa de proceso sobre herramientas existentes o una implementación más profunda después.

Entregables del piloto:

- Mapa de flujo confirmado.
- Diccionario de campos.
- Modelo de estados.
- Flujo del asesor.
- Flujo gerencial.
- Especificación de dashboard.
- Reporte de métricas del piloto.
- Recomendación de implementación 30/60/90.

---

## 12. Opciones de Precio

Los precios son referenciales y deben confirmarse después del descubrimiento.

### Opción A - Descubrimiento + Brief de Demo

- Alcance: descubrimiento del proceso, modelo de datos de muestra, brief ejecutivo y estructura de demo para reunión.
- Precio sugerido: USD 750-1,500.
- Mejor para: validar si vale la pena pasar a piloto.

### Opción B - Piloto de 4-6 Semanas

- Alcance: descubrimiento, estructura del piloto, flujo de carga manual, flujos asesor/gerencia, requisitos de dashboard, revisión semanal y recomendación final.
- Precio sugerido: USD 2,500-5,000 como fee de proyecto.
- Soporte opcional: USD 500-1,500/mes durante el piloto, según frecuencia de reuniones y cantidad de usuarios.
- Mejor para: probar valor con un grupo limitado antes de escalar.

### Opción C - Expansión Después del Piloto

- Alcance: planificación de producción, rollout por sucursales, operación de datos, capacitación, soporte y posible desarrollo adicional.
- Precio sugerido: cotización a medida después del piloto.
- Mejor para: expandir solo si el piloto demuestra valor operativo.

Límite de precio:
La fase 1 no incluye plataforma completa, procesamiento de pagos, automatización viva por WhatsApp, integraciones en tiempo real, desarrollo backend ni soporte empresarial salvo que se cotice por separado.

---

## 13. Límites / Lo Que Fase 1 NO Incluye

Fase 1 no incluye:

- Datos reales de Power Club en archivos públicos o materiales de demo.
- Archivos vivos de contactos internos.
- Construcción de una plataforma completa.
- Implementación backend.
- Integración de pagos.
- Automatización por WhatsApp.
- Decisiones comerciales autónomas.
- Reemplazo del criterio de asesores, gerentes o Gerencia General.
- Migración completa de históricos.
- Modelo complejo de permisos.
- Trabajo con OAuth, tokens o credenciales.
- Despliegue systemd/runtime.
- Refactor amplio del runtime de Val0.
- Integración en tiempo real con el CRM/software actual.
- Data warehouse o analítica avanzada de producción.
- Asesoría legal, contable, financiera, médica o regulatoria.

Fase 1 es un piloto operativo y paquete consultivo. El alcance de producción debe aprobarse por separado después del descubrimiento.

---

## 14. Preguntas de Reunión para Contacto Interno / Gerencia General

Preguntas para el contacto interno antes de la reunión con Gerencia:

- ¿Qué problema concreto haría que Gerencia diga "esto vale la pena probarlo"?
- ¿Qué sucursal o equipo sería mejor para un piloto de bajo riesgo?
- ¿Qué palabras usan internamente para prospectos, socios, renovaciones, reactivaciones y seguimientos?
- ¿Qué exportación se puede revisar estructuralmente sin exponer datos reales?
- ¿Qué no muestra bien el software actual?
- ¿Quién es dueño del seguimiento hoy?
- ¿Cuál es la razón más común de oportunidades perdidas?
- ¿Qué temas pueden ser sensibles en la primera reunión?
- ¿La primera demo debe ser en español completo o con algunos términos técnicos en inglés?

Preguntas para Gerencia General:

- ¿Cuántas sucursales conviene incluir en el primer piloto?
- ¿Qué flujo comercial pierde más valor hoy?
- ¿Cuáles son los 3 estados que Gerencia necesita ver todos los días?
- ¿Cuál es el volumen real de registros por mes y por sucursal?
- ¿Qué campos existen hoy en Excel/exportación?
- ¿Qué cadencia de seguimiento deberían cumplir los asesores?
- ¿Qué cuenta como contacto exitoso?
- ¿Qué motivos de pérdida vale la pena medir?
- ¿Quién debe aprobar cambios de campos o estados?
- ¿Qué métrica define si el piloto funcionó?

---

## 15. Siguiente Paso Recomendado

Preparar una reunión de descubrimiento de 30-45 minutos con el contacto interno primero, y luego una conversación de demo con Gerencia General.

Secuencia sugerida:

1. Confirmar estructura actual de exportación usando campos ficticios.
2. Confirmar flujo por sucursal, asesores y estados comerciales.
3. Seleccionar el piloto más seguro: una sucursal, un flujo o un tipo de oportunidad.
4. Preparar una muestra de reunión con registros anónimos.
5. Presentar el piloto como una capa de seguimiento y visibilidad gerencial, no como reemplazo final del CRM.

Cierre recomendado para la reunión:

```text
El primer paso no es reemplazar todo el CRM. El primer paso es probar si una capa simple de seguimiento puede recuperar oportunidades perdidas y dar mejor visibilidad gerencial en un piloto pequeño y medible.
```
