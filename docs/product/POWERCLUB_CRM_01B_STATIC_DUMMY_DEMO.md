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

La demo presenta dos vistas principales:

- Vista asesores: lista diaria de socios, prospectos y oportunidades comerciales con sucursal, asesor, estado, prioridad, último contacto y próximo seguimiento.
- Vista gerencial: filtros por sucursal y asesor, métricas de seguimiento y una tabla simple para ver riesgo operativo.

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

---

## Flujo de Asesores

La vista de asesores permite mostrar:

- Lista de socios/prospectos.
- Estados comerciales.
- Sucursal.
- Asesor asignado.
- Último contacto.
- Fecha de próximo seguimiento.
- Prioridad.
- Ficha de detalle.
- Notas.
- Historial de interacción.
- Próxima acción.

Estados visibles:

- Nuevo.
- Contactado.
- Seguimiento.
- Cita agendada.
- Inscrito.
- Perdido.

Los botones de estado son interactivos dentro del navegador, pero solo modifican el arreglo local de demo mientras la página está abierta. No guardan datos, no llaman APIs y no escriben archivos.

---

## Flujo Gerencial

La vista gerencial permite mostrar:

- Filtro por sucursal.
- Filtro por asesor.
- Leads abiertos.
- Seguimientos vencidos.
- Citas agendadas.
- Conversiones simuladas.
- Tabla por sucursal.
- Lista de oportunidades que requieren atención.

El objetivo es explicar visibilidad gerencial: qué está vencido, quién tiene carga, qué sucursal necesita atención y qué oportunidades deben revisarse.

---

## Límites

Esta demo no incluye:

- Datos reales de Power Club.
- Datos vivos de clientes.
- Backend.
- APIs.
- Autenticación.
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
