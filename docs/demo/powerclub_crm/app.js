const STATUS_CLASSES = {
  Venta: "venta",
  "Promesa de compra": "promesa-de-compra",
  Seguimiento: "seguimiento",
  Ilocalizable: "ilocalizable",
  "No contacto": "no-contacto",
};

const TODAY = "2026-06-09";
const TOTAL_FAKE_RECORDS = 60;
const PLAN_OPTIONS = ["Mensual $49", "Prepagado 1 mes", "Trimestral", "Semestral", "Anual", "Otro plan"];

const leads = [
  {
    id: "PC-DEMO-001",
    name: "Socio Demo 001",
    phone: "+507 6000-0101",
    email: "socio.demo.001@example.invalid",
    branch: "Costa del Este",
    advisor: "Asesor Demo A",
    shift: "Turno mañana",
    interest: "Nueva membresía",
    lastPlan: "Sin plan anterior",
    offeredPlan: "Mensual $49",
    memberStatus: "Prospecto",
    managementStatus: "Seguimiento",
    priority: "Alta",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Prospectos junio",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-07",
    nextFollowUp: "2026-06-09",
    nextAction: "Llamar hoy para confirmar plan familiar.",
    managementNote: "Pendiente validar horario preferido.",
    notes: "Prospecto ficticio interesado en horario nocturno. El seguimiento centralizado evita depender solo del archivo por nombre.",
    history: [
      "2026-06-05: Solicitó información de planes.",
      "2026-06-07: Se explicó plan familiar y quedó pendiente llamada.",
    ],
  },
  {
    id: "PC-DEMO-002",
    name: "Socio Demo 002",
    phone: "+507 6000-0102",
    email: "socio.demo.002@example.invalid",
    branch: "San Francisco",
    advisor: "Asesor Demo B",
    shift: "Turno tarde",
    interest: "Reactivación",
    lastPlan: "Mensual $49",
    offeredPlan: "Trimestral",
    memberStatus: "Ex socio",
    managementStatus: "Promesa de compra",
    priority: "Media",
    channel: "Llamada de socio",
    sourceFile: "Archivo por nombre: Reactivaciones",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-08",
    nextAction: "Enviar resumen manual de opciones y llamar en dos días.",
    managementNote: "Quiere comparar plan trimestral con mensual.",
    notes: "Socio ficticio llamó para consultar nueva compra. Próximo paso visible para continuidad entre turnos.",
    history: [
      "2026-06-04: Registro importado desde exportación de ejemplo.",
      "2026-06-08: Contactado por llamada manual.",
    ],
  },
  {
    id: "PC-DEMO-003",
    name: "Socio Demo 003",
    phone: "+507 6000-0103",
    email: "socio.demo.003@example.invalid",
    branch: "El Dorado",
    advisor: "Asesor Demo A",
    shift: "Turno mañana",
    interest: "Seguimiento de prueba",
    lastPlan: "Sin plan anterior",
    offeredPlan: "Prepagado 1 mes",
    memberStatus: "Prospecto",
    managementStatus: "Seguimiento",
    priority: "Alta",
    channel: "Venta presencial",
    sourceFile: "Archivo por nombre: Pruebas y visitas",
    currentTools: "Laptop, correo y Google Drive",
    appointmentScheduled: true,
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-10",
    nextAction: "Confirmar asistencia a cita de evaluación.",
    managementNote: "Visita agendada en sucursal.",
    notes: "Prospecto ficticio atendido en persona; requiere historial de contacto visible para el siguiente operador.",
    history: [
      "2026-06-06: Completó prueba de cortesía ficticia.",
      "2026-06-08: Se agenda cita en sucursal.",
    ],
  },
  {
    id: "PC-DEMO-004",
    name: "Socio Demo 004",
    phone: "+507 6000-0104",
    email: "socio.demo.004@example.invalid",
    branch: "Albrook",
    advisor: "Asesor Demo C",
    shift: "Turno tarde",
    interest: "Renovación",
    lastPlan: "Semestral",
    offeredPlan: "Anual",
    memberStatus: "Socio por vencer",
    managementStatus: "No contacto",
    priority: "Media",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Renovaciones",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "Sin contacto",
    nextFollowUp: "2026-06-09",
    nextAction: "Primer contacto manual para renovación.",
    managementNote: "No se ha logrado primer contacto.",
    notes: "Socio ficticio con renovación pendiente. Aún no hay contacto registrado para el turno actual.",
    history: ["2026-06-09: Registro ficticio asignado a asesora."],
  },
  {
    id: "PC-DEMO-005",
    name: "Socio Demo 005",
    phone: "+507 6000-0105",
    email: "socio.demo.005@example.invalid",
    branch: "Costa del Este",
    advisor: "Asesor Demo B",
    shift: "Turno mañana",
    interest: "Upgrade",
    lastPlan: "Trimestral",
    offeredPlan: "Semestral",
    memberStatus: "Socio activo",
    managementStatus: "Venta",
    priority: "Baja",
    channel: "Venta presencial",
    sourceFile: "Archivo por nombre: Upgrades",
    currentTools: "Laptop, correo y Google Drive",
    appointmentScheduled: false,
    lastContact: "2026-06-06",
    nextFollowUp: "2026-06-20",
    nextAction: "Seguimiento de satisfacción post-inscripción.",
    managementNote: "Venta demo cerrada en sucursal.",
    notes: "Conversión simulada de venta presencial para mostrar trazabilidad desde asesor y sucursal.",
    history: [
      "2026-06-03: Interés en upgrade ficticio.",
      "2026-06-06: Marcado como inscrito en demo.",
    ],
  },
  {
    id: "PC-DEMO-006",
    name: "Socio Demo 006",
    phone: "+507 6000-0106",
    email: "socio.demo.006@example.invalid",
    branch: "San Francisco",
    advisor: "Asesor Demo C",
    shift: "Turno cierre",
    interest: "Lead corporativo",
    lastPlan: "Otro plan",
    offeredPlan: "Anual",
    memberStatus: "Prospecto",
    managementStatus: "Ilocalizable",
    priority: "Media",
    channel: "Celular",
    sourceFile: "Archivo por nombre: Corporativos",
    currentTools: "Correo, Google Drive y celular",
    appointmentScheduled: false,
    lastContact: "2026-06-02",
    nextFollowUp: "2026-06-06",
    nextAction: "Cerrar con motivo y revisar aprendizaje.",
    managementNote: "No responde celular en intentos demo.",
    notes: "Oportunidad ficticia no localizada por celular; queda historial para continuidad del siguiente turno.",
    history: [
      "2026-06-01: Contacto inicial.",
      "2026-06-02: Indica que no seguirá este mes.",
    ],
  },
];

function createGeneratedRecords(count) {
  const branches = ["Costa del Este", "San Francisco", "El Dorado", "Albrook", "Brisas"];
  const advisors = ["Asesor Demo A", "Asesor Demo B", "Asesor Demo C", "Asesor Demo D", "Asesor Demo E", "Asesor Demo F"];
  const statuses = ["Venta", "Promesa de compra", "Seguimiento", "Ilocalizable", "No contacto"];
  const memberStatuses = ["Prospecto", "Socio activo", "Ex socio", "Socio por vencer", "Excluido"];
  const interests = ["Nueva membresía", "Reactivación", "Renovación", "Upgrade", "Seguimiento de prueba"];
  const channels = ["Celular", "Llamada de socio", "Venta presencial"];
  const priorities = ["Alta", "Media", "Baja"];

  return Array.from({ length: count }, (_, index) => {
    const number = index + 7;
    const status = statuses[index % statuses.length];
    const branch = branches[index % branches.length];
    const advisor = advisors[index % advisors.length];
    const plan = PLAN_OPTIONS[index % PLAN_OPTIONS.length];
    const lastPlan = PLAN_OPTIONS[(index + 2) % PLAN_OPTIONS.length];
    const nextDay = String(9 + (index % 12)).padStart(2, "0");
    const lastDay = String(1 + (index % 8)).padStart(2, "0");
    const padded = String(number).padStart(3, "0");

    return {
      id: `PC-DEMO-${padded}`,
      name: `Socio Demo ${padded}`,
      phone: `+507 6000-${String(100 + number).padStart(4, "0")}`,
      email: `socio.demo.${padded}@example.invalid`,
      branch,
      advisor,
      shift: index % 3 === 0 ? "Turno mañana" : index % 3 === 1 ? "Turno tarde" : "Turno cierre",
      interest: interests[index % interests.length],
      lastPlan,
      offeredPlan: plan,
      memberStatus: memberStatuses[index % memberStatuses.length],
      managementStatus: status,
      priority: priorities[index % priorities.length],
      channel: channels[index % channels.length],
      sourceFile: `Archivo por nombre: Base demo ${branch}`,
      currentTools: index % 2 === 0 ? "Correo, Google Drive y celular" : "Laptop, correo y Google Drive",
      appointmentScheduled: index % 7 === 0,
      lastContact: `2026-06-${lastDay}`,
      nextFollowUp: `2026-06-${nextDay}`,
      nextAction: status === "Venta" ? "Seguimiento de satisfacción." : "Gestionar contacto y actualizar estado.",
      managementNote: "Nota demo para seguimiento del asesor.",
      notes: "Registro ficticio generado para demostrar volumen, scroll y filtros.",
      history: [
        `2026-06-${lastDay}: Registro demo asignado.`,
        `2026-06-${lastDay}: Interacción ficticia registrada.`,
      ],
    };
  });
}

leads.push(...createGeneratedRecords(TOTAL_FAKE_RECORDS - leads.length));

let selectedId = leads[0].id;
let activeFilter = "todos";

const leadList = document.querySelector("#leadList");
const recordCount = document.querySelector("#recordCount");
const operatorView = document.querySelector("#operatorView");
const managerView = document.querySelector("#managerView");
const operatorTab = document.querySelector("#operatorTab");
const managerTab = document.querySelector("#managerTab");
const operatorAdvisorFilter = document.querySelector("#operatorAdvisorFilter");
const branchFilter = document.querySelector("#branchFilter");
const advisorFilter = document.querySelector("#advisorFilter");
const sourceFilter = document.querySelector("#sourceFilter");
const statusFilter = document.querySelector("#statusFilter");
const temperatureFilter = document.querySelector("#temperatureFilter");
const scorecardAdvisorSelect = document.querySelector("#scorecardAdvisorSelect");
const kpiExplainDrawer = document.querySelector("#kpiExplainDrawer");
const kpiExplainClose = document.querySelector("#kpiExplainClose");
const sectionOpenState = {};
const SECTION_HELP = {
  "core-kpis": "Indicadores basicos para saber si la operacion esta bajo control.",
  "advisor-productivity-kpis": "Mide ritmo de trabajo, seguimiento y actividad por asesor.",
  "sales-quality-kpis": "Mide calidad comercial: conversion, promesas, fuente y cierre.",
  "risk-recovery-kpis": "Detecta oportunidades en riesgo antes de que se pierdan.",
  "advisor-scorecard": "Resumen individual para coaching, riesgo y proxima accion.",
  "advanced-manager-insights": "Metricas mas profundas para analizar patrones y prioridades.",
  "future-bi-view": "Ejemplo conceptual de una capa BI avanzada despues del piloto.",
};

const KPI_EXPLANATIONS = {
  activeOpportunities: {
    title: "Oportunidades activas",
    meaning: "Cantidad de socios o prospectos abiertos que todavia requieren gestion comercial.",
    formula: "Oportunidades activas = registros filtrados que no estan marcados como Venta ni Perdido.",
    data: "Usa estado comercial, sucursal, asesor, canal y filtros de la muestra sintetica.",
    why: "Ayuda a ver carga real de trabajo y si una sucursal o asesor tiene demasiados casos abiertos.",
    action: "Revisar distribucion de carga, reasignar si hace falta y asegurar que cada oportunidad tenga proximo paso.",
  },
  todayFollowUps: {
    title: "Seguimientos para hoy",
    meaning: "Acciones que deben gestionarse en el corte actual de la demo.",
    formula: "Seguimientos para hoy = oportunidades abiertas con proxima accion en el dia demo.",
    data: "Usa fecha de proximo seguimiento, estado comercial y filtros activos.",
    why: "Permite dirigir el turno de trabajo antes de que los leads pierdan temperatura.",
    action: "Pedir al gerente de sucursal que confirme responsables y revise el avance antes del cierre del dia.",
  },
  conversionRate: {
    title: "Conversion rate",
    meaning: "Porcentaje de la base filtrada que termino como venta en la muestra demo.",
    formula: "Conversion rate = ventas cerradas / base filtrada.",
    data: "Usa registros sinteticos marcados como Venta y el total filtrado.",
    why: "Muestra resultado comercial, no solo actividad. Sirve para comparar sucursal, asesor y canal.",
    action: "Investigar que hacen distinto los equipos con mejor conversion y revisar los filtros con baja conversion.",
  },
  sales: {
    title: "Ventas",
    meaning: "Cantidad de cierres comerciales registrados en la muestra demo.",
    formula: "Ventas = registros filtrados con estado Venta.",
    data: "Usa estado comercial sintetico y filtros activos.",
    why: "Da una lectura directa de resultado y permite separar volumen de cierre.",
    action: "Comparar ventas con oportunidades activas, promesas y atrasos para entender si el problema es cierre o seguimiento.",
  },
  contactsPerAdvisorDay: {
    title: "Contactos / asesor / dia",
    meaning: "Ritmo promedio de contacto por asesor activo durante el periodo demo.",
    formula: "Contactos por asesor por dia = contactos registrados / asesores activos / dias del periodo.",
    data: "Usa llamadas, mensajes, visitas, asesores activos y un periodo demo de 7 dias.",
    why: "Ayuda a detectar productividad baja aunque el asesor tenga oportunidades asignadas.",
    action: "Si el ritmo cae, revisar carga, agenda, disciplina de contacto o necesidad de coaching.",
  },
  followUps: {
    title: "Seguimientos",
    meaning: "Oportunidades en conversacion o con cita, todavia sin cierre final.",
    formula: "Seguimientos = registros Contactado + Cita agendada.",
    data: "Usa estado comercial sintetico y filtros activos.",
    why: "Muestra la parte viva del embudo donde se gana o se pierde continuidad.",
    action: "Pedir proxima accion clara para cada seguimiento y separar los casos listos para cierre.",
  },
  completedToday: {
    title: "Completados hoy",
    meaning: "Actividad registrada en el dia de corte de la demo.",
    formula: "Completados hoy = actividades sinteticas registradas en el dia demo.",
    data: "Usa dia de creacion/actividad y conteo de interacciones ficticias.",
    why: "Evita confundir mucho pendiente con poca gestion: muestra trabajo ya ejecutado.",
    action: "Comparar completados contra pendientes para decidir si el equipo necesita apoyo antes del cierre.",
  },
  advisorRhythm: {
    title: "Ritmo vs sucursal",
    meaning: "Compara el ritmo de actividad del filtro actual contra el promedio de su sucursal.",
    formula: "Ritmo vs sucursal = actividad promedio filtrada / actividad promedio de sucursal.",
    data: "Usa actividades, asesores, sucursal y filtros activos de la muestra sintetica.",
    why: "Ayuda a encontrar asesores o grupos por debajo del ritmo esperado sin juzgar solo por ventas.",
    action: "Usar para coaching, redistribucion de carga o investigacion de buenas practicas.",
  },
  purchasePromises: {
    title: "Promesas de compra",
    meaning: "Leads con intencion declarada que todavia necesitan seguimiento para cerrar.",
    formula: "Promesas de compra = registros en estado Interesado dentro del filtro.",
    data: "Usa estado comercial sintetico y filtros activos.",
    why: "Son oportunidades con intencion; si no se gestionan, pueden convertirse en venta perdida.",
    action: "Priorizar contacto cercano, confirmar objeciones y pedir siguiente paso con fecha.",
  },
  branchConversion: {
    title: "Branch conversion",
    meaning: "La mejor conversion por sucursal dentro del filtro actual.",
    formula: "Branch conversion = ventas de una sucursal / registros de esa sucursal.",
    data: "Usa sucursal, ventas y total de registros sinteticos filtrados.",
    why: "Permite separar problemas de sucursal, volumen y calidad de gestion.",
    action: "Comparar sucursales: replicar practicas del mejor resultado o investigar donde cae la conversion.",
  },
  sourceQuality: {
    title: "Source quality",
    meaning: "Canal que combina mejor conversion y volumen dentro del filtro.",
    formula: "Source quality = ranking de canales por conversion, usando volumen como desempate.",
    data: "Usa canal/fuente, ventas y cantidad de registros sinteticos.",
    why: "Ayuda a decidir donde invertir energia comercial y donde un canal consume tiempo sin convertir.",
    action: "Revisar canales con alto volumen y baja conversion; reforzar los canales que si cierran.",
  },
  monthProgress: {
    title: "Avance del mes",
    meaning: "Porcentaje de la base demo que ya tiene alguna gestion registrada.",
    formula: "Avance del mes = registros gestionados / base filtrada.",
    data: "Usa registros cuyo estado ya no es Nuevo y filtros activos.",
    why: "Permite saber si el equipo esta avanzando sobre la base o acumulando trabajo sin tocar.",
    action: "Si el avance es bajo, priorizar primeros contactos y revisar capacidad por sucursal.",
  },
  overdueFollowUps: {
    title: "Seguimientos atrasados",
    meaning: "Oportunidades cuya proxima accion ya debio ocurrir en el corte demo.",
    formula: "Seguimientos atrasados = oportunidades abiertas con fecha de seguimiento anterior al dia demo.",
    data: "Usa fecha de proximo seguimiento, estado comercial y filtros activos.",
    why: "Es una de las senales mas claras de posible venta perdida por falta de control.",
    action: "Escalar los atrasos importantes, reasignar si el asesor no puede actuar y cerrar proximo paso.",
  },
  overdueRate: {
    title: "Atraso sobre abiertos",
    meaning: "Porcentaje de oportunidades abiertas que ya tienen seguimiento atrasado.",
    formula: "Atraso sobre abiertos = seguimientos atrasados / oportunidades activas.",
    data: "Usa oportunidades activas, fechas de seguimiento y estado comercial sintetico.",
    why: "Mide salud operativa: no solo cuantos atrasos existen, sino que tan grande es el problema.",
    action: "Definir umbral gerencial y revisar asesores o sucursales que superen ese limite.",
  },
  riskOpportunities: {
    title: "Oportunidades en riesgo",
    meaning: "Leads atrasados, trabados o calientes sin proximo paso claro.",
    formula: "Riesgo = atrasado o stuck opportunity o lead Hot sin gestion clara.",
    data: "Usa temperatura, atraso, estado, stuck flag y filtros de la muestra demo.",
    why: "Prioriza donde gerencia puede intervenir antes de perder una oportunidad con intencion.",
    action: "Revisar lista de riesgo, contactar hoy los Hot leads y decidir reasignacion o coaching.",
  },
  stuckOpportunities: {
    title: "Stuck opportunities",
    meaning: "Oportunidades que siguen abiertas sin desenlace claro despues de varias senales.",
    formula: "Stuck opportunities = registros abiertos marcados como trabados por reglas demo.",
    data: "Usa estado comercial, visitas, atraso y reglas sinteticas de la demo.",
    why: "Evita que el equipo acumule oportunidades que parecen vivas pero no avanzan.",
    action: "Exigir proxima accion, cerrar aprendizaje o escalar los casos de mayor prioridad.",
  },
};

const EXECUTIVE_RECORDS = 1800;
const EXECUTIVE_ADVISOR_COUNT = 56;
const EXECUTIVE_BRANCHES = ["Costa del Este", "San Francisco", "El Dorado", "Albrook", "Brisas", "Via Brasil"];
const EXECUTIVE_SOURCES = ["Instagram", "Facebook", "Walk-in", "Referido", "Web", "Corporativo", "Evento", "Reactivacion", "Llamada entrante", "Promocion"];
const EXECUTIVE_STATUSES = ["Nuevo", "Contactado", "Interesado", "Cita agendada", "Visitado", "Venta", "Perdido"];
const TEMPERATURES = ["Hot", "Warm", "Cold"];
const AVERAGE_MEMBERSHIP_VALUE_FAKE = 69;
const WEEK_DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"];

const executiveAdvisors = Array.from({ length: EXECUTIVE_ADVISOR_COUNT }, (_, index) => {
  const number = index + 1;
  return {
    id: `advisor_demo_${String(number).padStart(3, "0")}`,
    name: `Asesor Demo ${String(number).padStart(2, "0")}`,
    branch: EXECUTIVE_BRANCHES[index % EXECUTIVE_BRANCHES.length],
  };
});

const executiveLeads = Array.from({ length: EXECUTIVE_RECORDS }, (_, index) => {
  const advisor = executiveAdvisors[index % executiveAdvisors.length];
  const branch = advisor.branch;
  const source = EXECUTIVE_SOURCES[(index * 3 + Math.floor(index / 11)) % EXECUTIVE_SOURCES.length];
  const status = EXECUTIVE_STATUSES[(index * 5 + Math.floor(index / 17)) % EXECUTIVE_STATUSES.length];
  const temperature = TEMPERATURES[(index + (status === "Interesado" ? 0 : 1)) % TEMPERATURES.length];
  const day = 1 + (index % 28);
  const followUpOffset = (index % 13) - 6;
  const followUpDay = Math.max(1, Math.min(28, 9 + followUpOffset));
  const isOverdue = followUpDay < 9 && status !== "Venta" && status !== "Perdido";
  const isStuck = status !== "Venta" && status !== "Perdido" && (index % 10 === 0 || (status === "Visitado" && index % 4 === 0));
  const value = AVERAGE_MEMBERSHIP_VALUE_FAKE + (index % 5) * 10;
  const activities = 1 + (index % 6) + (status === "Venta" ? 2 : 0);

  return {
    id: `lead_demo_${String(index + 1).padStart(4, "0")}`,
    name: `Prospecto Demo ${String(index + 1).padStart(4, "0")}`,
    branch,
    advisorId: advisor.id,
    advisor: advisor.name,
    source,
    status,
    temperature,
    createdDay: day,
    nextFollowUpDay: followUpDay,
    overdueHours: isOverdue ? (9 - followUpDay) * 24 + (index % 8) * 3 : 0,
    agingBucket: isOverdue
      ? followUpDay <= 1
        ? "8+ dias"
        : followUpDay <= 5
          ? "4-7 dias"
          : followUpDay <= 7
            ? "2-3 dias"
            : "1 dia"
      : "Hoy",
    isOverdue,
    isStuck,
    isDueToday: followUpDay === 9 && status !== "Venta" && status !== "Perdido",
    estimatedValue: value,
    activities,
    calls: 1 + (index % 4),
    messages: 1 + (index % 5),
    visits: status === "Cita agendada" || status === "Visitado" || status === "Venta" ? 1 : 0,
  };
});

const executiveActivitiesByDay = WEEK_DAYS.map((day, index) => ({
  day,
  count: executiveLeads.reduce((sum, lead) => sum + (lead.createdDay % 7 === index ? lead.activities : 0), 0),
}));

function normalizeClass(value) {
  return value.toLowerCase().replaceAll(" ", "-");
}

function needsFollowUp(lead) {
  return lead.nextFollowUp < TODAY && lead.managementStatus !== "Venta";
}

function isPending(lead) {
  return ["Seguimiento", "No contacto", "Ilocalizable", "Promesa de compra"].includes(lead.managementStatus);
}

function isManaged(lead) {
  return lead.managementStatus !== "No contacto";
}

function countStatus(rows, status) {
  return rows.filter((lead) => lead.managementStatus === status).length;
}

function operatorRows() {
  const advisor = operatorAdvisorFilter.value || leads[0].advisor;
  return leads.filter((lead) => lead.advisor === advisor);
}

function filteredLeads() {
  const assignedRows = operatorRows();
  if (activeFilter === "pendientes") {
    return assignedRows.filter(isPending);
  }
  if (activeFilter === "alta") {
    return assignedRows.filter((lead) => lead.priority === "Alta");
  }
  if (activeFilter === "citas") {
    return assignedRows.filter((lead) => lead.appointmentScheduled);
  }
  return assignedRows;
}

function statusPill(status) {
  return `<span class="status-pill ${STATUS_CLASSES[status]}">${status}</span>`;
}

function renderLeadList() {
  const rows = filteredLeads();
  const assignedRows = operatorRows();
  recordCount.textContent = `${rows.length} registros`;
  document.querySelector("#operatorAssignedMetric").textContent = assignedRows.length;
  document.querySelector("#operatorManagedMetric").textContent = assignedRows.filter(isManaged).length;
  document.querySelector("#operatorPendingMetric").textContent = assignedRows.filter(isPending).length;
  document.querySelector("#operatorSalesMetric").textContent = countStatus(assignedRows, "Venta");
  document.querySelector("#operatorPromisesMetric").textContent = countStatus(assignedRows, "Promesa de compra");
  document.querySelector("#operatorFollowUpsMetric").textContent = countStatus(assignedRows, "Seguimiento");
  document.querySelector("#operatorUnreachableMetric").textContent = countStatus(assignedRows, "Ilocalizable");
  document.querySelector("#operatorNoContactMetric").textContent = countStatus(assignedRows, "No contacto");

  if (!rows.some((lead) => lead.id === selectedId) && rows[0]) {
    selectedId = rows[0].id;
  }

  leadList.innerHTML = rows
    .map(
      (lead) => `
        <button class="lead-card ${lead.id === selectedId ? "active" : ""}" type="button" data-id="${lead.id}">
          <div class="lead-top">
            <strong>${lead.name}</strong>
            ${statusPill(lead.managementStatus)}
          </div>
          <div class="lead-meta">
            <span>${lead.branch}</span>
            <span>${lead.advisor} · ${lead.shift}</span>
          </div>
          <div class="lead-meta">
            <span>Último: ${lead.lastContact}</span>
            <span>Próximo: ${lead.nextFollowUp}</span>
          </div>
          <div class="lead-meta">
            <span>Prioridad ${lead.priority}</span>
            <span>Estado socio: ${lead.memberStatus}</span>
          </div>
          <div class="lead-meta">
            <span>Estado de gestión: ${lead.managementStatus}</span>
            <span>${lead.channel}</span>
          </div>
        </button>
      `
    )
    .join("");
}

function renderDetail() {
  const lead = leads.find((item) => item.id === selectedId) || leads[0];
  const [nextActionDate, nextActionText] = lead.nextAction.includes(" - ")
    ? lead.nextAction.split(" - ")
    : [lead.nextFollowUp, lead.nextAction];
  document.querySelector("#detailName").textContent = lead.name;
  document.querySelector("#detailPhone").textContent = `Celular: ${lead.phone}`;
  document.querySelector("#detailEmail").textContent = `Correo electrónico: ${lead.email}`;
  document.querySelector("#detailBranch").textContent = lead.branch;
  document.querySelector("#detailAdvisor").textContent = lead.advisor;
  document.querySelector("#detailShift").textContent = lead.shift;
  document.querySelector("#detailInterest").textContent = lead.interest;
  document.querySelector("#detailLastPlan").textContent = lead.lastPlan;
  document.querySelector("#detailOfferedPlan").textContent = lead.offeredPlan;
  document.querySelector("#detailMemberStatus").textContent = lead.memberStatus;
  document.querySelector("#detailManagementStatus").textContent = lead.managementStatus;
  document.querySelector("#detailLastContact").textContent = lead.lastContact;
  document.querySelector("#detailNextAction").textContent = `${lead.nextFollowUp} - ${lead.nextAction}`;
  document.querySelector("#detailChannel").textContent = lead.channel;
  document.querySelector("#detailSourceFile").textContent = lead.sourceFile;
  document.querySelector("#detailTools").textContent = lead.currentTools;
  document.querySelector("#detailNotes").textContent = lead.notes;
  document.querySelector("#nextActionInput").value = nextActionText;
  document.querySelector("#nextActionDateInput").value = nextActionDate || lead.nextFollowUp;
  document.querySelector("#managementNoteInput").value = lead.managementNote;
  document.querySelector("#offeredPlanSelect").value = lead.offeredPlan;

  const priority = document.querySelector("#detailPriority");
  priority.textContent = `Prioridad ${lead.priority}`;
  priority.className = `priority-pill ${normalizeClass(lead.priority)}`;

  document.querySelector("#detailHistory").innerHTML = lead.history.map((item) => `<li>${item}</li>`).join("");

  document.querySelectorAll(".status-actions button").forEach((button) => {
    button.classList.toggle("active", button.dataset.managementStatus === lead.managementStatus);
  });
}

function populateFilters() {
  const branches = ["Todas", ...EXECUTIVE_BRANCHES];
  const advisors = ["Todos", ...executiveAdvisors.map((advisor) => advisor.name)];
  const operatorAdvisors = [...new Set(leads.map((lead) => lead.advisor))];
  operatorAdvisorFilter.innerHTML = operatorAdvisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  operatorAdvisorFilter.value = operatorAdvisors[0] || "";
  branchFilter.innerHTML = branches.map((branch) => `<option value="${branch}">${branch}</option>`).join("");
  advisorFilter.innerHTML = advisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
  sourceFilter.innerHTML = ["Todos", ...EXECUTIVE_SOURCES].map((source) => `<option value="${source}">${source}</option>`).join("");
  statusFilter.innerHTML = ["Todos", ...EXECUTIVE_STATUSES].map((status) => `<option value="${status}">${status}</option>`).join("");
  temperatureFilter.innerHTML = ["Todas", ...TEMPERATURES].map((temperature) => `<option value="${temperature}">${temperature}</option>`).join("");
  selectedId = operatorRows()[0]?.id || leads[0].id;
}

function managerRows() {
  return executiveLeads.filter((lead) => {
    const branchOk = branchFilter.value === "Todas" || lead.branch === branchFilter.value;
    const advisorOk = advisorFilter.value === "Todos" || lead.advisor === advisorFilter.value;
    const sourceOk = sourceFilter.value === "Todos" || lead.source === sourceFilter.value;
    const statusOk = statusFilter.value === "Todos" || lead.status === statusFilter.value;
    const temperatureOk = temperatureFilter.value === "Todas" || lead.temperature === temperatureFilter.value;
    return branchOk && advisorOk && sourceOk && statusOk && temperatureOk;
  });
}

function branchRowsForBreakdown() {
  return executiveLeads.filter((lead) => branchFilter.value === "Todas" || lead.branch === branchFilter.value);
}

function progressPercent(rows) {
  if (!rows.length) {
    return 0;
  }
  const managed = rows.filter((lead) => lead.status !== "Nuevo").length;
  return Math.round((managed / rows.length) * 100);
}

function formatMoney(value) {
  return `$${Math.round(value).toLocaleString("en-US")}`;
}

function pct(part, total) {
  return total ? Math.round((part / total) * 100) : 0;
}

function statusCount(rows, status) {
  return rows.filter((lead) => lead.status === status).length;
}

function isAtRisk(lead) {
  return lead.isOverdue || lead.isStuck || (lead.temperature === "Hot" && !lead.isDueToday && lead.status !== "Venta" && lead.status !== "Perdido");
}

function recoveryProbability(lead) {
  if (lead.isStuck && lead.status === "Visitado") return 0.3;
  if (lead.temperature === "Hot") return 0.35;
  if (lead.temperature === "Warm") return 0.2;
  return 0.05;
}

function groupBy(rows, key) {
  return rows.reduce((groups, row) => {
    const groupKey = row[key];
    groups[groupKey] = groups[groupKey] || [];
    groups[groupKey].push(row);
    return groups;
  }, {});
}

function advisorStats(rows) {
  const grouped = groupBy(rows, "advisor");
  return Object.entries(grouped).map(([advisor, advisorRows]) => {
    const converted = statusCount(advisorRows, "Venta");
    const open = advisorRows.filter((lead) => lead.status !== "Venta" && lead.status !== "Perdido").length;
    const overdue = advisorRows.filter((lead) => lead.isOverdue).length;
    const activity = advisorRows.reduce((sum, lead) => sum + lead.activities + lead.calls + lead.messages + lead.visits, 0);
    return {
      advisor,
      branch: advisorRows[0].branch,
      assigned: advisorRows.length,
      activity,
      converted,
      open,
      overdue,
      risk: advisorRows.filter(isAtRisk).length,
      conversion: pct(converted, advisorRows.length),
      value: advisorRows.reduce((sum, lead) => sum + (lead.status === "Venta" ? lead.estimatedValue : 0), 0),
    };
  });
}

function renderBars(containerId, rows, labelKey, valueKey, detail) {
  if (!rows.length) {
    document.querySelector(containerId).innerHTML = `<article><div><strong>Sin datos para este filtro</strong><span>Ajuste filtros de demo</span></div><div class="bar-track"><span style="width: 5%"></span></div></article>`;
    return;
  }
  const max = Math.max(...rows.map((row) => row[valueKey]), 1);
  document.querySelector(containerId).innerHTML = rows
    .map((row) => `
      <article>
        <div>
          <strong>${row[labelKey]}</strong>
          <span>${detail(row)}</span>
        </div>
        <div class="bar-track"><span style="width: ${Math.max(5, Math.round((row[valueKey] / max) * 100))}%"></span></div>
      </article>
    `)
    .join("");
}

function renderStatusDonut(rows) {
  const statusColors = {
    Nuevo: "#a4adb5",
    Contactado: "#286aa6",
    Interesado: "#c46d1e",
    "Cita agendada": "#6b58a8",
    Visitado: "#11715f",
    Venta: "#0f8b62",
    Perdido: "#9d3d34",
  };
  const total = Math.max(rows.length, 1);
  let cursor = 0;
  const segments = EXECUTIVE_STATUSES.map((status) => {
    const count = statusCount(rows, status);
    const start = cursor;
    const end = cursor + (count / total) * 360;
    cursor = end;
    return `${statusColors[status]} ${start}deg ${end}deg`;
  });
  document.querySelector("#statusDonut").style.background = `conic-gradient(${segments.join(", ")})`;
  document.querySelector("#statusDonutTotal").textContent = rows.length.toLocaleString("en-US");
}

function renderMiniBars(containerId, rows, labelKey, valueKey) {
  if (!rows.length) {
    document.querySelector(containerId).innerHTML = `<div><span>Sin datos</span><strong>0</strong><i><b style="width: 4%"></b></i></div>`;
    return;
  }
  const max = Math.max(...rows.map((row) => row[valueKey]), 1);
  document.querySelector(containerId).innerHTML = rows
    .map(
      (row) => `
        <div>
          <span>${row[labelKey]}</span>
          <strong>${row[valueKey]}</strong>
          <i><b style="width: ${Math.max(8, Math.round((row[valueKey] / max) * 100))}%"></b></i>
        </div>
      `
    )
    .join("");
}

function renderFutureBiPreview(rows, activeRows, riskRows, sourceRows, advisorRows) {
  const branchRows = Object.entries(groupBy(rows, "branch"))
    .map(([branch, branchLeads]) => ({
      branch,
      count: branchLeads.length,
      conversion: pct(statusCount(branchLeads, "Venta"), branchLeads.length),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 4);
  const advisorPreviewRows = [...advisorRows]
    .sort((a, b) => b.conversion - a.conversion || b.converted - a.converted)
    .slice(0, 4)
    .map((row) => ({
      advisor: row.advisor.replace("Asesor Demo ", "A"),
      score: row.conversion,
    }));
  const sourceTrendRows = sourceRows.slice(0, 6).map((row, index) => ({
    source: row.source,
    conversion: row.conversion,
    height: Math.max(18, 34 + row.conversion + index * 4),
  }));
  const riskRate = pct(riskRows.length, activeRows.length);

  renderMiniBars("#biBranchBars", branchRows, "branch", "count");
  renderMiniBars("#biAdvisorBars", advisorPreviewRows, "advisor", "score");
  document.querySelector("#biBranchLeader").textContent = branchRows[0] ? `${branchRows[0].count} regs.` : "-";
  document.querySelector("#biAdvisorLeader").textContent = advisorPreviewRows[0] ? `${advisorPreviewRows[0].score}%` : "-";
  document.querySelector("#biRiskRate").textContent = `${riskRate}%`;
  document.querySelector("#biRiskGauge").style.width = `${Math.max(4, Math.min(100, riskRate))}%`;
  document.querySelector("#biRiskLabel").textContent = `${riskRows.length.toLocaleString("en-US")} registros sinteticos priorizados`;
  document.querySelector("#biSourceLeader").textContent = sourceTrendRows[0] ? sourceTrendRows[0].source : "-";
  document.querySelector("#biSourceTrend").innerHTML = sourceTrendRows
    .map((row) => `<span style="height: ${Math.min(110, row.height)}px"><b>${row.conversion}%</b></span>`)
    .join("");
}

function advisorDemoCode(advisorName) {
  const number = advisorName.match(/\d+/)?.[0] || "000";
  return `PC-ADV-${String(number).padStart(3, "0")}`;
}

function advisorActionPrompt(row, avgDaysWithoutContact) {
  if (!row) return "Seleccione un asesor para ver la accion recomendada.";
  if (row.overdue >= 5 || avgDaysWithoutContact >= 3) {
    return "Accion recomendada: revisar atrasos hoy, confirmar proximo paso y reasignar carga si el asesor no puede actuar.";
  }
  if (row.risk >= 8) {
    return "Accion recomendada: hacer coaching corto sobre leads en riesgo y exigir cierre de proxima accion por oportunidad.";
  }
  if (row.conversion < 8 && row.assigned >= 12) {
    return "Accion recomendada: revisar calidad de contacto y comparar guion con asesores de mejor conversion.";
  }
  if (row.conversion >= 14) {
    return "Accion recomendada: documentar practica del asesor y replicarla con el equipo de sucursal.";
  }
  return "Accion recomendada: mantener seguimiento diario y revisar que las promesas de compra no queden sin contacto.";
}

function renderAdvisorScorecard(rows, advisorRows, baselineAdvisorRows) {
  const orderedAdvisors = [...advisorRows].sort((a, b) => b.risk - a.risk || b.overdue - a.overdue || b.activity - a.activity);
  const previousValue = scorecardAdvisorSelect.value;
  scorecardAdvisorSelect.innerHTML = orderedAdvisors.length
    ? orderedAdvisors.map((row) => `<option value="${row.advisor}">${row.advisor} - ${row.branch}</option>`).join("")
    : `<option value="">Sin asesores</option>`;
  scorecardAdvisorSelect.value = orderedAdvisors.some((row) => row.advisor === previousValue)
    ? previousValue
    : orderedAdvisors[0]?.advisor || "";

  const selected = advisorRows.find((row) => row.advisor === scorecardAdvisorSelect.value) || orderedAdvisors[0];
  const advisorLeadRows = selected ? rows.filter((lead) => lead.advisor === selected.advisor) : [];
  const active = advisorLeadRows.filter((lead) => lead.status !== "Venta" && lead.status !== "Perdido").length;
  const pending = advisorLeadRows.filter((lead) => lead.isDueToday).length;
  const overdueRows = advisorLeadRows.filter((lead) => lead.isOverdue);
  const avgDaysWithoutContact = overdueRows.length
    ? overdueRows.reduce((sum, lead) => sum + lead.overdueHours / 24, 0) / overdueRows.length
    : 0;
  const contactPace = advisorLeadRows.length
    ? Math.round(advisorLeadRows.reduce((sum, lead) => sum + lead.calls + lead.messages + lead.visits, 0) / 7)
    : 0;
  const branchBaseline = selected
    ? baselineAdvisorRows.filter((row) => row.branch === selected.branch)
    : [];
  const branchAverage = branchBaseline.length
    ? branchBaseline.reduce((sum, row) => sum + row.activity, 0) / branchBaseline.length
    : selected?.activity || 0;
  const vsBranch = branchAverage && selected ? Math.round((selected.activity / branchAverage) * 100) : 0;
  const status = selected && (selected.overdue >= 5 || selected.risk >= 8)
    ? "Requiere atencion"
    : selected && selected.conversion >= 14
      ? "Buen desempeno"
      : "Monitorear";

  document.querySelector("#scoreAdvisorName").textContent = selected ? selected.advisor : "Sin asesor";
  document.querySelector("#scoreAdvisorMeta").textContent = selected ? `${selected.branch} - ${advisorDemoCode(selected.advisor)}` : "-";
  document.querySelector("#scoreAdvisorStatus").textContent = status;
  document.querySelector("#scoreActiveMetric").textContent = active.toLocaleString("en-US");
  document.querySelector("#scorePendingMetric").textContent = pending.toLocaleString("en-US");
  document.querySelector("#scoreOverdueMetric").textContent = overdueRows.length.toLocaleString("en-US");
  document.querySelector("#scoreContactsMetric").textContent = contactPace.toLocaleString("en-US");
  document.querySelector("#scoreConversionMetric").textContent = `${selected ? selected.conversion : 0}%`;
  document.querySelector("#scoreSalesMetric").textContent = selected ? selected.converted.toLocaleString("en-US") : "0";
  document.querySelector("#scorePromisesMetric").textContent = statusCount(advisorLeadRows, "Interesado").toLocaleString("en-US");
  document.querySelector("#scoreAvgNoContactMetric").textContent = avgDaysWithoutContact.toFixed(1);
  document.querySelector("#scoreVsBranchMetric").textContent = `${vsBranch}%`;
  document.querySelector("#scoreVsBranchBar").style.width = `${Math.max(4, Math.min(100, vsBranch))}%`;
  document.querySelector("#scoreActionPrompt").textContent = advisorActionPrompt(selected, avgDaysWithoutContact);
}

function renderManager() {
  const rows = managerRows();
  const activeRows = rows.filter((lead) => lead.status !== "Venta" && lead.status !== "Perdido");
  const dueTodayRows = rows.filter((lead) => lead.isDueToday);
  const overdueRows = rows.filter((lead) => lead.isOverdue);
  const riskRows = rows.filter(isAtRisk);
  const recoverable = riskRows.reduce((sum, lead) => sum + lead.estimatedValue * recoveryProbability(lead), 0);
  const atRiskValue = riskRows.reduce((sum, lead) => sum + lead.estimatedValue, 0);
  const recoverableRate = pct(recoverable, atRiskValue);
  const activeAdvisorCount = Math.max(new Set(rows.map((lead) => lead.advisor)).size, 1);
  const totalContacts = rows.reduce((sum, lead) => sum + lead.calls + lead.messages + lead.visits, 0);
  const contactPace = Math.round(totalContacts / activeAdvisorCount / 7);
  const completedToday = rows.filter((lead) => lead.createdDay === 9).reduce((sum, lead) => sum + lead.activities, 0);
  const avgDaysWithoutContact = overdueRows.length
    ? overdueRows.reduce((sum, lead) => sum + lead.overdueHours / 24, 0) / overdueRows.length
    : 0;

  document.querySelector("#assignedMetric").textContent = activeRows.length.toLocaleString("en-US");
  document.querySelector("#pendingMetric").textContent = dueTodayRows.length.toLocaleString("en-US");
  document.querySelector("#promisesMetric").textContent = statusCount(rows, "Interesado").toLocaleString("en-US");
  document.querySelector("#salesMetric").textContent = statusCount(rows, "Venta").toLocaleString("en-US");
  document.querySelector("#conversionMetric").textContent = `${pct(statusCount(rows, "Venta"), rows.length)}%`;
  document.querySelector("#followUpsMetric").textContent = rows.filter((lead) => lead.status === "Contactado" || lead.status === "Cita agendada").length.toLocaleString("en-US");
  document.querySelector("#contactPaceMetric").textContent = contactPace.toLocaleString("en-US");
  document.querySelector("#completedTodayMetric").textContent = completedToday.toLocaleString("en-US");
  document.querySelector("#noContactMetric").textContent = overdueRows.length.toLocaleString("en-US");
  document.querySelector("#unreachableMetric").textContent = riskRows.length.toLocaleString("en-US");
  document.querySelector("#overdueRateCardMetric").textContent = `${pct(overdueRows.length, activeRows.length)}%`;
  document.querySelector("#stuckCountMetric").textContent = rows.filter((lead) => lead.isStuck).length.toLocaleString("en-US");
  document.querySelector("#atRiskValueMetric").textContent = formatMoney(atRiskValue);
  document.querySelector("#recoverableValueMetric").textContent = formatMoney(recoverable);
  document.querySelector("#riskCountMetric").textContent = riskRows.length.toLocaleString("en-US");
  document.querySelector("#hotRiskMetric").textContent = riskRows.filter((lead) => lead.temperature === "Hot").length.toLocaleString("en-US");
  document.querySelector("#avgNoContactMetric").textContent = avgDaysWithoutContact.toFixed(1);
  document.querySelector("#recoveryNarrativeValue").textContent = `${riskRows.length.toLocaleString("en-US")} registros priorizados por reglas ficticias.`;
  document.querySelector("#riskModelLabel").textContent = `${recoverableRate}% del valor base ficticio`;
  document.querySelector("#riskModelBar").style.width = `${Math.max(4, Math.min(100, recoverableRate))}%`;
  document.querySelector("#conversionVisualMetric").textContent = `${pct(statusCount(rows, "Venta"), rows.length)}%`;
  document.querySelector("#overdueRateMetric").textContent = `${pct(overdueRows.length, activeRows.length)}%`;
  document.querySelector("#riskRateMetric").textContent = `${pct(riskRows.length, activeRows.length)}%`;
  renderStatusDonut(rows);

  const monthProgress = progressPercent(rows);
  document.querySelector("#monthProgressMetric").textContent = `${monthProgress}%`;
  document.querySelector("#monthProgressLabel").textContent = `${rows.filter((lead) => lead.status !== "Nuevo").length} de ${rows.length} gestionados`;
  document.querySelector("#monthProgressBar").style.width = `${monthProgress}%`;

  const branchNames = [...new Set(rows.map((lead) => lead.branch))];
  const bestBranchConversion = branchNames
    .map((branch) => {
      const branchRows = rows.filter((lead) => lead.branch === branch);
      return {
        branch,
        conversion: pct(statusCount(branchRows, "Venta"), branchRows.length),
      };
    })
    .sort((a, b) => b.conversion - a.conversion)[0];
  document.querySelector("#branchConversionMetric").textContent = bestBranchConversion ? `${bestBranchConversion.conversion}%` : "0%";
  document.querySelector("#branchTableBody").innerHTML = branchNames.length
    ? branchNames
        .map((branch) => {
          const branchRows = rows.filter((lead) => lead.branch === branch);
          const branchRisk = branchRows.filter(isAtRisk).length;
          return `
            <tr>
              <td>${branch}</td>
              <td>${branchRows.length}</td>
              <td>${statusCount(branchRows, "Venta")}</td>
              <td>${statusCount(branchRows, "Interesado")}</td>
              <td>${statusCount(branchRows, "Contactado") + statusCount(branchRows, "Cita agendada")}</td>
              <td>${branchRows.filter((lead) => lead.isOverdue).length}</td>
              <td>${branchRisk}</td>
              <td>${branchRows.filter((lead) => lead.isDueToday).length}</td>
              <td>${formatMoney(branchRows.reduce((sum, lead) => sum + lead.estimatedValue, 0))}</td>
            </tr>
          `;
        })
        .join("")
    : `<tr><td colspan="9">Sin datos para este filtro.</td></tr>`;

  const breakdownRows = rows;
  const advisorRows = advisorStats(breakdownRows);
  const baselineAdvisorRows = advisorStats(branchRowsForBreakdown());
  const selectedActivityAverage = advisorRows.length
    ? advisorRows.reduce((sum, row) => sum + row.activity, 0) / advisorRows.length
    : 0;
  const baselineActivityAverage = baselineAdvisorRows.length
    ? baselineAdvisorRows.reduce((sum, row) => sum + row.activity, 0) / baselineAdvisorRows.length
    : selectedActivityAverage;
  const rhythmVsBranch = baselineActivityAverage ? Math.round((selectedActivityAverage / baselineActivityAverage) * 100) : 0;
  const coachingAlerts = advisorRows.filter((row) => row.risk >= 8 || row.overdue >= 5 || (row.assigned >= 12 && row.conversion < 8)).length;
  document.querySelector("#rhythmMetric").textContent = `${rhythmVsBranch}%`;
  document.querySelector("#activityVsBranchMetric").textContent = `${rhythmVsBranch}%`;
  document.querySelector("#coachingAlertsMetric").textContent = coachingAlerts.toLocaleString("en-US");
  renderAdvisorScorecard(rows, advisorRows, baselineAdvisorRows);
  document.querySelector("#advisorTableBody").innerHTML = advisorRows.length
    ? advisorRows
        .sort((a, b) => b.assigned - a.assigned)
        .slice(0, 24)
        .map((row) => {
          const advisorLeadRows = breakdownRows.filter((lead) => lead.advisor === row.advisor);
          return `
            <tr>
              <td>${row.advisor}</td>
              <td>${row.assigned}</td>
              <td>${row.converted}</td>
              <td>${statusCount(advisorLeadRows, "Interesado")}</td>
              <td>${statusCount(advisorLeadRows, "Contactado")}</td>
              <td>${row.overdue}</td>
              <td>${row.risk}</td>
              <td>${advisorLeadRows.filter((lead) => lead.isDueToday).length}</td>
              <td>${row.conversion}%</td>
            </tr>
          `;
        })
        .join("")
    : `<tr><td colspan="9">Sin datos para este filtro.</td></tr>`;

  const topBy = (key) => advisorRows.reduce((best, row) => (!best || row[key] > best[key] ? row : best), null);
  const topSales = topBy("converted");
  const topPending = topBy("open");
  const topNoContact = topBy("overdue");
  const topUnreachable = topBy("risk");
  document.querySelector("#coachingSummary").innerHTML = [
    ["Mas ventas", topSales, "converted"],
    ["Mas pendientes", topPending, "open"],
    ["Mas atraso", topNoContact, "overdue"],
    ["Mas riesgo", topUnreachable, "risk"],
  ]
    .map(([label, row, key]) => `<article><span>${label}</span><strong>${row ? row.advisor : "-"}</strong><p>${row ? row[key] : 0} registros</p></article>`)
    .join("");

  document.querySelector("#activityRankingList").innerHTML = [...advisorRows]
    .sort((a, b) => b.activity - a.activity)
    .slice(0, 8)
    .map((row, index, list) => {
      const maxActivity = Math.max(list[0]?.activity || 1, 1);
      const width = Math.max(8, Math.round((row.activity / maxActivity) * 100));
      return `<li><div><strong>${row.advisor}</strong><span>${row.activity} actividades - ${row.branch}</span></div><b class="rank-index">${index + 1}</b><i class="rank-bar"><span style="width: ${width}%"></span></i></li>`;
    })
    .join("") || "<li>Sin datos para este filtro.</li>";

  document.querySelector("#resultRankingList").innerHTML = [...advisorRows]
    .sort((a, b) => b.converted - a.converted || b.conversion - a.conversion)
    .slice(0, 8)
    .map((row, index, list) => {
      const maxConverted = Math.max(list[0]?.converted || 1, 1);
      const width = Math.max(8, Math.round((row.converted / maxConverted) * 100));
      return `<li><div><strong>${row.advisor}</strong><span>${row.converted} ventas - ${row.conversion}% conversion</span></div><b class="rank-index">${index + 1}</b><i class="rank-bar"><span style="width: ${width}%"></span></i></li>`;
    })
    .join("") || "<li>Sin datos para este filtro.</li>";

  document.querySelector("#riskList").innerHTML = riskRows
    .slice(0, 8)
    .map((lead) => `<li><strong>${lead.advisor}</strong> - ${lead.branch}. ${lead.name} en ${lead.status}; ${lead.isOverdue ? `${lead.overdueHours}h de atraso` : "sin proximo paso claro"}.</li>`)
    .join("") || "<li>No hay oportunidades en riesgo para este filtro.</li>";

  document.querySelector("#pendingFollowUpsList").innerHTML = dueTodayRows
    .slice(0, 7)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.advisor} - ${lead.branch} - ${lead.temperature}</span></li>`)
    .join("") || "<li>No hay pendientes para hoy con este filtro.</li>";

  document.querySelector("#overdueFollowUpsList").innerHTML = overdueRows
    .sort((a, b) => b.overdueHours - a.overdueHours)
    .slice(0, 7)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.overdueHours}h - ${lead.advisor} - ${formatMoney(lead.estimatedValue)}</span></li>`)
    .join("") || "<li>No hay seguimiento atrasado con este filtro.</li>";

  const agingRows = ["Hoy", "1 dia", "2-3 dias", "4-7 dias", "8+ dias"].map((bucket) => ({
    label: bucket,
    count: rows.filter((lead) => lead.agingBucket === bucket).length,
  }));
  renderBars("#agingChart", agingRows, "label", "count", (row) => `${row.count} seguimientos`);

  const funnelRows = EXECUTIVE_STATUSES.map((status) => ({
    label: status,
    count: statusCount(rows, status),
  }));
  renderBars("#statusFunnel", funnelRows, "label", "count", (row) => `${row.count} registros`);

  const sourceRows = Object.entries(groupBy(rows, "source"))
    .map(([source, sourceRows]) => ({
      source,
      count: sourceRows.length,
      converted: statusCount(sourceRows, "Venta"),
      conversion: pct(statusCount(sourceRows, "Venta"), sourceRows.length),
    }))
    .sort((a, b) => b.conversion - a.conversion || b.count - a.count)
    .slice(0, 8);
  const bestSource = sourceRows[0];
  document.querySelector("#sourceQualityMetric").textContent = bestSource ? bestSource.source : "-";
  document.querySelector("#channelQualityMetric").textContent = bestSource ? `${bestSource.source} (${bestSource.conversion}%)` : "-";
  renderBars("#sourcePerformance", sourceRows, "source", "count", (row) => `${row.converted} ventas - ${row.conversion}% conversion`);
  renderFutureBiPreview(rows, activeRows, riskRows, sourceRows, advisorRows);

  const maxActivity = Math.max(...executiveActivitiesByDay.map((item) => item.count), 1);
  document.querySelector("#activityTrend").innerHTML = executiveActivitiesByDay
    .map((item) => `
      <article>
        <span style="height: ${Math.max(16, Math.round((item.count / maxActivity) * 120))}px"></span>
        <strong>${item.day}</strong>
        <em>${item.count}</em>
      </article>
    `)
    .join("");

  document.querySelector("#stuckOpportunitiesList").innerHTML = rows
    .filter((lead) => lead.isStuck)
    .slice(0, 8)
    .map((lead) => `<li><strong>${lead.name}</strong><span>${lead.status} - ${lead.branch} - rescatar ${formatMoney(lead.estimatedValue * recoveryProbability(lead))}</span></li>`)
    .join("") || "<li>No hay stuck opportunities para este filtro.</li>";

  const weakestBranch = Object.entries(groupBy(rows, "branch"))
    .map(([branch, branchRows]) => ({ branch, overdue: branchRows.filter((lead) => lead.isOverdue).length, total: branchRows.length }))
    .sort((a, b) => pct(b.overdue, b.total) - pct(a.overdue, a.total))[0];
  const noisySource = sourceRows.sort((a, b) => b.count - a.count || a.conversion - b.conversion)[0];
  const topRiskAdvisor = topUnreachable;
  document.querySelector("#managerActionPrompts").innerHTML = [
    ["Rescatar hoy", `${riskRows.filter((lead) => lead.temperature === "Hot").length} hot leads en riesgo. Priorizar llamadas manuales y reasignacion si el asesor no puede actuar.`],
    ["Coaching de asesor", `${topRiskAdvisor ? topRiskAdvisor.advisor : "-"} concentra riesgo. Revisar calidad de contacto y seguimiento atrasado.`],
    ["Inspeccionar sucursal", `${weakestBranch ? weakestBranch.branch : "-"} muestra mayor tasa de atraso. Revisar carga y disciplina de seguimiento.`],
    ["Revisar canal", `${noisySource ? noisySource.source : "-"} genera volumen. Validar si convierte o consume tiempo de asesores.`],
    ["Cerrar ciclo", `${rows.filter((lead) => lead.status === "Visitado" && lead.isStuck).length} visitas sin desenlace. Exigir proxima accion.`],
  ]
    .map(([title, copy]) => `<article><span>${title}</span><strong>${copy}</strong></article>`)
    .join("");
}

function openKpiExplanation(kpiKey) {
  const detail = KPI_EXPLANATIONS[kpiKey];
  if (!detail) return;
  document.querySelector("#kpiExplainTitle").textContent = detail.title;
  document.querySelector("#kpiExplainMeaning").textContent = detail.meaning;
  document.querySelector("#kpiExplainFormula").textContent = detail.formula;
  document.querySelector("#kpiExplainData").textContent = `${detail.data} Todo es fake/sintetico para demo; no usa datos reales de Power Club.`;
  document.querySelector("#kpiExplainWhy").textContent = detail.why;
  document.querySelector("#kpiExplainAction").textContent = detail.action;
  kpiExplainDrawer.classList.add("open");
  kpiExplainDrawer.setAttribute("aria-hidden", "false");
}

function closeKpiExplanation() {
  kpiExplainDrawer.classList.remove("open");
  kpiExplainDrawer.setAttribute("aria-hidden", "true");
}

function setCollapsibleState(section, button, body, isOpen) {
  section.classList.toggle("collapsed", !isOpen);
  button.setAttribute("aria-expanded", String(isOpen));
  body.hidden = !isOpen;
  sectionOpenState[section.dataset.collapseId] = isOpen;
}

function initializeCollapsibleSections() {
  document.querySelectorAll("[data-collapse-id]").forEach((section) => {
    if (section.dataset.collapseReady === "true") return;
    const id = section.dataset.collapseId;
    const label = section.dataset.collapseLabel || "Seccion";
    const help = SECTION_HELP[id] || "Abrir o cerrar esta seccion.";
    const isPanel = section.classList.contains("panel");
    const heading = isPanel ? section.querySelector(":scope > .panel-heading") : section.querySelector(":scope > h3");
    if (!heading) return;
    heading.title = help;

    const body = document.createElement("div");
    body.className = "collapse-body";
    body.id = `${id}-body`;

    const reference = isPanel ? heading : heading.nextElementSibling;
    let node = isPanel ? heading.nextElementSibling : reference;
    while (node) {
      const next = node.nextElementSibling;
      body.appendChild(node);
      node = next;
    }

    const button = document.createElement("button");
    button.className = "collapse-toggle";
    button.type = "button";
    button.setAttribute("aria-controls", body.id);
    button.title = help;
    button.innerHTML = `<span class="collapse-chevron" aria-hidden="true"></span><span>${label}</span>`;

    if (isPanel) {
      heading.appendChild(button);
      section.appendChild(body);
    } else {
      const header = document.createElement("div");
      header.className = "collapse-section-header";
      section.insertBefore(header, heading);
      header.appendChild(heading);
      header.appendChild(button);
      section.appendChild(body);
    }

    const defaultOpen = section.dataset.defaultOpen !== "false";
    const initialOpen = Object.prototype.hasOwnProperty.call(sectionOpenState, id) ? sectionOpenState[id] : defaultOpen;
    setCollapsibleState(section, button, body, initialOpen);

    const toggleSection = () => {
      setCollapsibleState(section, button, body, button.getAttribute("aria-expanded") !== "true");
    };

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleSection();
    });

    heading.addEventListener("click", (event) => {
      if (event.target.closest("select, button, input, textarea, a, [data-kpi]")) return;
      toggleSection();
    });

    section.dataset.collapseReady = "true";
  });
}

function switchView(view) {
  const managerActive = view === "manager";
  operatorView.classList.toggle("active-view", !managerActive);
  operatorView.hidden = managerActive;
  managerView.hidden = !managerActive;
  operatorTab.classList.toggle("active", !managerActive);
  managerTab.classList.toggle("active", managerActive);
  operatorTab.setAttribute("aria-selected", String(!managerActive));
  managerTab.setAttribute("aria-selected", String(managerActive));
  if (managerActive) {
    renderManager();
  }
}

leadList.addEventListener("click", (event) => {
  const card = event.target.closest(".lead-card");
  if (!card) return;
  selectedId = card.dataset.id;
  renderLeadList();
  renderDetail();
});

document.querySelectorAll(".chip").forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    document.querySelectorAll(".chip").forEach((chip) => chip.classList.toggle("active", chip === button));
    renderLeadList();
  });
});

document.querySelectorAll("[data-kpi]").forEach((card) => {
  card.setAttribute("role", "button");
  card.setAttribute("aria-label", `Explicar KPI: ${card.querySelector(".metric-head > span:not(.metric-icon):not(.help-dot)")?.textContent || "metrica"}`);
  card.addEventListener("click", () => openKpiExplanation(card.dataset.kpi));
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openKpiExplanation(card.dataset.kpi);
    }
  });
});

kpiExplainClose.addEventListener("click", closeKpiExplanation);
kpiExplainDrawer.addEventListener("click", (event) => {
  if (event.target === kpiExplainDrawer) {
    closeKpiExplanation();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeKpiExplanation();
  }
});

operatorAdvisorFilter.addEventListener("change", () => {
  selectedId = operatorRows()[0]?.id || leads[0].id;
  renderLeadList();
  renderDetail();
});

document.querySelectorAll(".status-actions button").forEach((button) => {
  button.addEventListener("click", () => {
    const lead = leads.find((item) => item.id === selectedId);
    lead.managementStatus = button.dataset.managementStatus;
    lead.history = [`Demo: Estado de gestión marcado como ${lead.managementStatus}.`, ...lead.history];
    renderLeadList();
    renderDetail();
    renderManager();
  });
});

document.querySelector("#offeredPlanSelect").addEventListener("change", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.offeredPlan = event.target.value;
  renderDetail();
});

document.querySelector("#nextActionInput").addEventListener("input", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.nextAction = event.target.value;
  renderLeadList();
});

document.querySelector("#nextActionDateInput").addEventListener("change", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.nextFollowUp = event.target.value;
  renderLeadList();
  renderManager();
});

document.querySelector("#managementNoteInput").addEventListener("input", (event) => {
  const lead = leads.find((item) => item.id === selectedId);
  lead.managementNote = event.target.value;
});

operatorTab.addEventListener("click", () => switchView("operator"));
managerTab.addEventListener("click", () => switchView("manager"));
branchFilter.addEventListener("change", renderManager);
advisorFilter.addEventListener("change", renderManager);
sourceFilter.addEventListener("change", renderManager);
statusFilter.addEventListener("change", renderManager);
temperatureFilter.addEventListener("change", renderManager);
scorecardAdvisorSelect.addEventListener("change", renderManager);

populateFilters();
initializeCollapsibleSections();
renderLeadList();
renderDetail();
renderManager();
