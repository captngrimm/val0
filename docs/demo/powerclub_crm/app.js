const STATUS_CLASSES = {
  Nuevo: "nuevo",
  Contactado: "contactado",
  Seguimiento: "seguimiento",
  "Cita agendada": "cita-agendada",
  Inscrito: "inscrito",
  Perdido: "perdido",
};

const leads = [
  {
    id: "PC-DEMO-001",
    name: "Mariana Rios",
    phone: "+507 6000-0101",
    branch: "Costa del Este",
    advisor: "Andrea Vega",
    interest: "Nueva membresía",
    status: "Seguimiento",
    priority: "Alta",
    lastContact: "2026-06-07",
    nextFollowUp: "2026-06-09",
    nextAction: "Llamar hoy para confirmar plan familiar.",
    notes: "Prospecto ficticio interesado en horario nocturno y clases grupales.",
    history: [
      "2026-06-05: Solicitó información de planes.",
      "2026-06-07: Se explicó plan familiar y quedó pendiente llamada.",
    ],
  },
  {
    id: "PC-DEMO-002",
    name: "Luis Paredes",
    phone: "+507 6000-0102",
    branch: "San Francisco",
    advisor: "Carlos Mendez",
    interest: "Reactivación",
    status: "Contactado",
    priority: "Media",
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-11",
    nextAction: "Enviar resumen manual de opciones y llamar en dos días.",
    notes: "Socio ficticio pausado por horario laboral. Quiere evaluar sede cercana.",
    history: [
      "2026-06-04: Registro importado desde exportación de ejemplo.",
      "2026-06-08: Contactado por llamada manual.",
    ],
  },
  {
    id: "PC-DEMO-003",
    name: "Sofia Navarro",
    phone: "+507 6000-0103",
    branch: "El Dorado",
    advisor: "Andrea Vega",
    interest: "Seguimiento de prueba",
    status: "Cita agendada",
    priority: "Alta",
    lastContact: "2026-06-08",
    nextFollowUp: "2026-06-10",
    nextAction: "Confirmar asistencia a cita de evaluación.",
    notes: "Prospecto ficticio agendado para visita; requiere seguimiento puntual.",
    history: [
      "2026-06-06: Completó prueba de cortesía ficticia.",
      "2026-06-08: Se agenda cita en sucursal.",
    ],
  },
  {
    id: "PC-DEMO-004",
    name: "Roberto Chen",
    phone: "+507 6000-0104",
    branch: "Albrook",
    advisor: "Daniela Soto",
    interest: "Renovación",
    status: "Nuevo",
    priority: "Media",
    lastContact: "Sin contacto",
    nextFollowUp: "2026-06-09",
    nextAction: "Primer contacto manual para renovación.",
    notes: "Socio ficticio con renovación pendiente en exportación de muestra.",
    history: ["2026-06-09: Registro ficticio asignado a asesora."],
  },
  {
    id: "PC-DEMO-005",
    name: "Paola Castillo",
    phone: "+507 6000-0105",
    branch: "Costa del Este",
    advisor: "Carlos Mendez",
    interest: "Upgrade",
    status: "Inscrito",
    priority: "Baja",
    lastContact: "2026-06-06",
    nextFollowUp: "2026-06-20",
    nextAction: "Seguimiento de satisfacción post-inscripción.",
    notes: "Conversión simulada para mostrar métrica de inscritos.",
    history: [
      "2026-06-03: Interés en upgrade ficticio.",
      "2026-06-06: Marcado como inscrito en demo.",
    ],
  },
  {
    id: "PC-DEMO-006",
    name: "Miguel Torres",
    phone: "+507 6000-0106",
    branch: "San Francisco",
    advisor: "Daniela Soto",
    interest: "Lead corporativo",
    status: "Perdido",
    priority: "Media",
    lastContact: "2026-06-02",
    nextFollowUp: "2026-06-06",
    nextAction: "Cerrar con motivo y revisar aprendizaje.",
    notes: "Oportunidad ficticia perdida por falta de presupuesto.",
    history: [
      "2026-06-01: Contacto inicial.",
      "2026-06-02: Indica que no seguirá este mes.",
    ],
  },
];

let selectedId = leads[0].id;
let activeFilter = "todos";

const leadList = document.querySelector("#leadList");
const recordCount = document.querySelector("#recordCount");
const operatorView = document.querySelector("#operatorView");
const managerView = document.querySelector("#managerView");
const operatorTab = document.querySelector("#operatorTab");
const managerTab = document.querySelector("#managerTab");
const branchFilter = document.querySelector("#branchFilter");
const advisorFilter = document.querySelector("#advisorFilter");

function normalizeClass(value) {
  return value.toLowerCase().replaceAll(" ", "-");
}

function isOverdue(lead) {
  return lead.nextFollowUp <= "2026-06-09" && !["Inscrito", "Perdido"].includes(lead.status);
}

function filteredLeads() {
  if (activeFilter === "vencidos") {
    return leads.filter(isOverdue);
  }
  if (activeFilter === "alta") {
    return leads.filter((lead) => lead.priority === "Alta");
  }
  if (activeFilter === "citas") {
    return leads.filter((lead) => lead.status === "Cita agendada");
  }
  return leads;
}

function statusPill(status) {
  return `<span class="status-pill ${STATUS_CLASSES[status]}">${status}</span>`;
}

function renderLeadList() {
  const rows = filteredLeads();
  recordCount.textContent = `${rows.length} registros`;
  leadList.innerHTML = rows
    .map(
      (lead) => `
        <button class="lead-card ${lead.id === selectedId ? "active" : ""}" type="button" data-id="${lead.id}">
          <div class="lead-top">
            <strong>${lead.name}</strong>
            ${statusPill(lead.status)}
          </div>
          <div class="lead-meta">
            <span>${lead.branch}</span>
            <span>${lead.advisor}</span>
          </div>
          <div class="lead-meta">
            <span>Último: ${lead.lastContact}</span>
            <span>Próximo: ${lead.nextFollowUp}</span>
          </div>
          <div class="lead-meta">
            <span>Prioridad ${lead.priority}</span>
            <span>${lead.interest}</span>
          </div>
        </button>
      `
    )
    .join("");
}

function renderDetail() {
  const lead = leads.find((item) => item.id === selectedId) || leads[0];
  document.querySelector("#detailName").textContent = lead.name;
  document.querySelector("#detailPhone").textContent = `Teléfono: ${lead.phone}`;
  document.querySelector("#detailBranch").textContent = lead.branch;
  document.querySelector("#detailAdvisor").textContent = lead.advisor;
  document.querySelector("#detailInterest").textContent = lead.interest;
  document.querySelector("#detailLastContact").textContent = lead.lastContact;
  document.querySelector("#detailNextAction").textContent = `${lead.nextFollowUp} - ${lead.nextAction}`;
  document.querySelector("#detailNotes").textContent = lead.notes;

  const priority = document.querySelector("#detailPriority");
  priority.textContent = `Prioridad ${lead.priority}`;
  priority.className = `priority-pill ${normalizeClass(lead.priority)}`;

  document.querySelector("#detailHistory").innerHTML = lead.history.map((item) => `<li>${item}</li>`).join("");

  document.querySelectorAll(".status-actions button").forEach((button) => {
    button.classList.toggle("active", button.dataset.status === lead.status);
  });
}

function populateFilters() {
  const branches = ["Todas", ...new Set(leads.map((lead) => lead.branch))];
  const advisors = ["Todos", ...new Set(leads.map((lead) => lead.advisor))];
  branchFilter.innerHTML = branches.map((branch) => `<option value="${branch}">${branch}</option>`).join("");
  advisorFilter.innerHTML = advisors.map((advisor) => `<option value="${advisor}">${advisor}</option>`).join("");
}

function managerRows() {
  return leads.filter((lead) => {
    const branchOk = branchFilter.value === "Todas" || lead.branch === branchFilter.value;
    const advisorOk = advisorFilter.value === "Todos" || lead.advisor === advisorFilter.value;
    return branchOk && advisorOk;
  });
}

function renderManager() {
  const rows = managerRows();
  document.querySelector("#openLeadsMetric").textContent = rows.filter((lead) => !["Inscrito", "Perdido"].includes(lead.status)).length;
  document.querySelector("#overdueMetric").textContent = rows.filter(isOverdue).length;
  document.querySelector("#appointmentsMetric").textContent = rows.filter((lead) => lead.status === "Cita agendada").length;
  document.querySelector("#conversionsMetric").textContent = rows.filter((lead) => lead.status === "Inscrito").length;

  const branchNames = [...new Set(rows.map((lead) => lead.branch))];
  document.querySelector("#branchTableBody").innerHTML = branchNames
    .map((branch) => {
      const branchRows = rows.filter((lead) => lead.branch === branch);
      return `
        <tr>
          <td>${branch}</td>
          <td>${branchRows.filter((lead) => !["Inscrito", "Perdido"].includes(lead.status)).length}</td>
          <td>${branchRows.filter(isOverdue).length}</td>
          <td>${branchRows.filter((lead) => lead.status === "Cita agendada").length}</td>
          <td>${branchRows.filter((lead) => lead.status === "Inscrito").length}</td>
        </tr>
      `;
    })
    .join("");

  const risks = rows.filter((lead) => isOverdue(lead) || lead.priority === "Alta").slice(0, 5);
  document.querySelector("#riskList").innerHTML = risks
    .map((lead) => `<li><strong>${lead.name}</strong> - ${lead.branch}, ${lead.advisor}. Próxima acción: ${lead.nextAction}</li>`)
    .join("");
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

document.querySelectorAll(".status-actions button").forEach((button) => {
  button.addEventListener("click", () => {
    const lead = leads.find((item) => item.id === selectedId);
    lead.status = button.dataset.status;
    lead.history = [`Demo: estado marcado como ${lead.status}.`, ...lead.history];
    renderLeadList();
    renderDetail();
    renderManager();
  });
});

operatorTab.addEventListener("click", () => switchView("operator"));
managerTab.addEventListener("click", () => switchView("manager"));
branchFilter.addEventListener("change", renderManager);
advisorFilter.addEventListener("change", renderManager);

populateFilters();
renderLeadList();
renderDetail();
renderManager();
