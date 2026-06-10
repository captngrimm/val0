# POWERCLUB-CRM-01B - Demo Estática Dummy de CRM

Propósito:
Crear una demo web estática y client-facing para mostrar cómo podría sentirse un CRM operativo ligero para Power Club durante un piloto operativo.

Ubicación:

```text
docs/demo/powerclub_crm/index.html
```

No requiere servidor. Se puede abrir directamente en el navegador.

---

## Qué Muestra

La demo presenta tres niveles de lectura:

- Vista asesor/operador: lista diaria asignada a cada asesor, con socios/prospectos, sucursal, turno, canal, estado de gestión, prioridad, último contacto, historial y próximo paso.
- Vista gerente de sucursal: totales para una sucursal seleccionada, breakdown por asesor y lectura de quién tiene más ventas, pendientes, no contacto o ilocalizables.
- Vista gerente general: macro totales de todas las sucursales, comparación por sucursal y entrada conceptual a una sucursal para ver detalle por asesor.

La demo usa branding de reunión:

- Val AI Ops Discovery.
- Isthmus Dynamics / Honest AI Ops.
- Power Club CRM Pilot / CRM Operativo Ligero.

---

## Datos

Todos los datos son ficticios y anónimos.

La demo incluye una nota visible:

```text
Demo con datos ficticios. No usa información real de Power Club.
```

Los nombres, teléfonos, sucursales, asesores, estados, notas e historial de interacción son muestras inventadas para explicar el flujo. No representan socios reales, prospectos reales ni operaciones reales de Power Club.

La demo genera alrededor de 60 registros ficticios para que la lista se sienta más real y permita demostrar scroll, filtros, conteos por asesor y lectura gerencial.

---

## Flujo de Asesores

Insight operativo usado:
Los operadores trabajan por turnos. El punto de partida actual es abrir laptop, correo, Google Drive y archivos establecidos por nombre; luego se gestiona contacto por celular, llamadas de socios o ventas presenciales. La demo no copia conversaciones ni datos reales: solo usa este patrón operativo de forma paraphraseada.

La vista de asesores permite mostrar:

- Lista de socios/prospectos.
- Socios asignados por asesor.
- Mini-dashboard acumulado del asesor: Total asignados, Total gestionados, Pendientes por gestionar, Ventas, Promesas de compra, Seguimiento, Ilocalizables y No contacto.
- Celular y correo electrónico con valores placeholder.
- Estado socio.
- Estado de gestión.
- Último plan adquirido.
- Plan ofrecido como dropdown con valores de ejemplo.
- Sucursal.
- Asesor asignado.
- Turno del operador.
- Herramientas actuales: correo, Google Drive y celular.
- Archivo actual por nombre como dolor de estado actual.
- Canal: celular, llamada de socio o venta presencial.
- Último contacto.
- Fecha de próximo seguimiento.
- Prioridad.
- Ficha de detalle.
- Notas.
- Historial de interacción.
- Próxima acción.
- Botones editables de Estado de gestión para conversación de demo.
- Campos fillable de Próxima acción, Fecha próxima acción y Nota de gestión.

Planes de ejemplo:

- Mensual $49.
- Prepagado 1 mes.
- Trimestral.
- Semestral.
- Anual.
- Otro plan.

Estado socio se mantiene separado de Estado de gestión. En los registros ficticios puede aparecer `Excluido` para mostrar casos de muestra del flujo.

Clarificación comercial:
Estado socio describe la relación de membresía o cliente. Estado de gestión describe el proceso de venta, seguimiento o contacto que maneja el asesor. No son el mismo campo.

Valores visibles de Estado de gestión:

- Venta.
- Promesa de compra.
- Seguimiento.
- Ilocalizable.
- No contacto.

Los botones de Estado de gestión son interactivos dentro del navegador, pero solo modifican el arreglo local de demo mientras la página está abierta. No guardan datos, no llaman APIs y no escriben archivos.

El valor del piloto es centralizar seguimiento, historial de contacto y próximo paso visible para que exista continuidad entre turnos, incluso si el proceso actual inicia desde correo, Google Drive y archivos por nombre.

Los campos de archivo por nombre, correo, Google Drive y celular aparecen como Contexto actual. No se presentan como campos finales del CRM, sino como transición desde el proceso actual hacia seguimiento centralizado.

---

## Flujo Gerencial

La vista de gerente de sucursal permite mostrar:

- Totales de la sucursal seleccionada.
- Breakdown por asesor dentro de esa sucursal.
- Qué asesor tiene más ventas.
- Qué asesor tiene más pendientes.
- Qué asesor tiene más No contacto.
- Qué asesor tiene más Ilocalizables.
- Señales para coaching y necesidades de apoyo.

La vista de gerente general permite mostrar:

- Macro totales de todas las sucursales.
- Comparación por sucursal.
- Entrada conceptual a una sucursal para revisar el detalle por asesor.
- Señales para decisiones de coaching, staffing, salidas o bonos.

Métricas visibles:

- Total asignados.
- Total gestionados.
- Socios asignados.
- Ventas.
- Promesas de compra.
- Seguimientos.
- No contacto.
- Ilocalizables.
- Pendientes por gestionar.
- Avance del mes / corte medio mes.
- Distribución por sucursal.
- Breakdown por asesor dentro de la sucursal seleccionada.
- Lista de No contacto / Ilocalizables / Promesas de compra.

El objetivo es explicar visibilidad gerencial: cuántos socios están asignados, qué ventas y promesas existen, qué asesores tienen pendientes, qué sucursal necesita atención y dónde hay no contacto, ilocalizables o promesas de compra que requieren gestión.

Actualización Battle 01B:
La vista gerencial ahora funciona como dashboard ejecutivo de inteligencia operacional, usando datos sintéticos agregados para representar 56 asesores, 6 sucursales y 1,800 registros mensuales conceptuales. La pantalla no renderiza cada registro en una tabla masiva; muestra totales, rankings y listas priorizadas para una conversación ejecutiva.

Widgets ejecutivos incluidos:

- Executive KPI strip.
- Advisor activity ranking.
- Advisor result ranking.
- Pending follow-ups.
- Overdue follow-ups expresados como seguimiento atrasado.
- Follow-up aging.
- Status distribution / embudo comercial.
- Branch comparison.
- Source/channel performance.
- Daily/weekly activity.
- Stuck opportunities.
- Recovered opportunity / avoided lost sales estimate.
- Manager action prompts.
- Manager View Options para congelar la primera vista gerencial del piloto.

Narrativa comercial:

```text
PowerClub puede perder dinero cuando los leads no reciben seguimiento. El dashboard muestra quién está actuando, dónde hay seguimiento atrasado, qué sucursal requiere atención y qué oportunidad aún puede rescatarse.
```

Los valores de oportunidad recuperable son estimaciones ficticias basadas en supuestos de demo. No representan ingresos reales, desempeño real ni resultados reales de Power Club.

Actualización Battle 01D:
La vista gerencial incluye una sección consultiva llamada `Configure su vista gerencial` con cuatro opciones de alcance:

- Follow-up Control View.
- Advisor Performance View.
- Branch Comparison View.
- Recovery Opportunities View.

Cada opción explica qué muestra, a quién ayuda, qué decisión soporta y por qué importa financieramente. La intención es facilitar una conversación de scope freeze antes de proponer el piloto.

---

## Ciclo Mensual

La demo representa un ciclo mensual conceptual:

- Carga mensual de base/listado.
- Gestión durante el mes.
- Cierre mensual.
- Reporte final mensual.
- Historial mensual archivado.

Controles visibles de demo:

- Exportar gestión a Excel.
- Generar reporte mensual.
- Cerrar mes / guardar cierre mensual.

Estos controles son visuales y conceptuales. No exportan archivos, no guardan datos, no llaman APIs y no prometen comportamiento de producción.

Texto visible:

```text
Demo: exportación y cierre mensual representados de forma conceptual.
En piloto real, el cierre mensual podría guardar resultados y permitir descarga Excel.
```

---

## Modelo de Visibilidad por Rol

Modelo conceptual de permisos para el piloto:

- Asesor / operador: ve solo sus registros asignados.
- Gerente de sucursal: ve su sucursal y sus asesores.
- Gerente general: ve todas las sucursales y puede entrar a una sucursal.

No hay autenticación real ni login en esta demo. Es una representación estática del modelo de visibilidad esperado.

---

## Límites

Esta demo no incluye:

- Datos reales de Power Club.
- Datos vivos de clientes.
- Backend.
- APIs.
- Autenticación.
- Persistencia.
- Exportación real de archivos.
- Integración de pagos.
- Automatización por WhatsApp.
- Promesa de CRM de producción.
- Migración de históricos.
- Integraciones en tiempo real.
- Cambios a bot.py, core/** o clients/**.

La demo es una herramienta de conversación para una reunión. Sirve para alinear lenguaje, flujo y alcance del piloto antes de cualquier implementación.

---

## Cómo Usarla en Reunión

Secuencia sugerida:

1. Abrir `docs/demo/powerclub_crm/index.html`.
2. Señalar la nota de datos ficticios.
3. Mostrar la vista de asesores y explicar la lista diaria.
4. Abrir una ficha de socio/prospecto.
5. Cambiar un estado para mostrar el flujo operativo.
6. Pasar a vista gerencial.
7. Filtrar por sucursal o asesor.
8. Cerrar con la pregunta: qué flujo real conviene pilotear primero.

Frase de posicionamiento:

```text
Esto no reemplaza el CRM actual hoy. Es una demo para visualizar un piloto operativo: seguimiento más claro para asesores y visibilidad gerencial para reducir oportunidades perdidas.
```
