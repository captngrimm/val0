const companyInput = document.querySelector("#companyInput");
const reportCompany = document.querySelector("#reportCompany");
const notesInput = document.querySelector("#notesInput");
const summaryOutput = document.querySelector("#summaryOutput");
const nextQuestionOutput = document.querySelector("#nextQuestionOutput");
const opportunityOutput = document.querySelector("#opportunityOutput");
const pilotOutput = document.querySelector("#pilotOutput");
const reportOutput = document.querySelector("#reportOutput");
const questionItems = Array.from(document.querySelectorAll("#questionList li"));

const sampleNotes = [
  "Carlos runs a service business where new requests arrive through WhatsApp, referrals, and phone calls.",
  "The owner loses time reconstructing what was promised and what needs follow-up.",
  "Current tools include messages, spreadsheets, calendar, and informal notes.",
  "The desired outcome is a simple 30/60/90 map and one first pilot that reduces manual follow-up."
].join("\n");

function companyName() {
  return companyInput.value.trim() || "Empresa X";
}

function setActiveQuestion(index) {
  questionItems.forEach((item, itemIndex) => {
    item.classList.toggle("active", itemIndex === index);
  });
}

function renderOpportunities(items) {
  opportunityOutput.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    opportunityOutput.appendChild(li);
  });
}

function startDiagnostic() {
  const company = companyName();
  reportCompany.textContent = company;
  setActiveQuestion(0);
  summaryOutput.textContent = `${company}: discovery started. Val will map the business, critical processes, manual work, bottlenecks, and the desired 30/60/90 outcome.`;
  nextQuestionOutput.textContent = "First question: what type of business is this, and where do clients or leads come from today?";
}

function summarizeNotes() {
  const company = companyName();
  const hasNotes = notesInput.value.trim().length > 0;
  summaryOutput.textContent = hasNotes
    ? `${company}: notes suggest scattered intake, manual follow-up, and a need for one narrow AI Ops pilot before implementation.`
    : `${company}: add meeting notes first, then Val can summarize facts, assumptions, and likely bottlenecks.`;
  setActiveQuestion(5);
}

function suggestQuestion() {
  nextQuestionOutput.textContent = "Suggested next question: where is the most time lost right now, and what follow-up currently depends on someone remembering it?";
  setActiveQuestion(6);
}

function detectOpportunities() {
  renderOpportunities([
    "Structure incoming requests into a review queue.",
    "Prepare follow-up drafts for human approval.",
    "Turn meeting notes into a weekly owner summary.",
    "Create a small pilot around intake and follow-up prep before expanding."
  ]);
  pilotOutput.textContent = "Recommended first pilot: AI-assisted intake and follow-up prep with human approval before any external action.";
  setActiveQuestion(7);
}

function generateReport() {
  const company = companyName();
  reportCompany.textContent = company;
  reportOutput.innerHTML = `
    <h3>Executive summary</h3>
    <p>${company} needs a practical AI Ops map that turns scattered context into one first pilot.</p>
    <h3>Current processes</h3>
    <p>Requests arrive through messages, referrals, calls, and informal notes. Follow-up is still mostly manual.</p>
    <h3>Pain points</h3>
    <p>Time is lost reconstructing promises, tracking next steps, and deciding what deserves attention first.</p>
    <h3>Opportunities</h3>
    <p>Capture meeting notes, classify opportunities, prepare follow-up drafts, and summarize weekly blockers.</p>
    <h3>Recommended pilot</h3>
    <p>Start with AI-assisted intake and follow-up prep. Keep it narrow and reviewed by a human.</p>
    <h3>30/60/90 roadmap</h3>
    <p>30 days: validate the workflow. 60 days: run the pilot. 90 days: decide whether to expand, pause, or redesign.</p>
    <h3>Limits / boundaries</h3>
    <p>Val helps structure diagnosis and pilot design. She does not replace professionals, make commitments, or implement changes without human confirmation.</p>
    <h3>Next steps</h3>
    <p>Confirm the workflow owner, choose the first-week success metric, and prepare a scoped implementation proposal.</p>
  `;
}

document.querySelector("#startButton").addEventListener("click", startDiagnostic);
document.querySelector("#sampleNotesButton").addEventListener("click", () => {
  notesInput.value = sampleNotes;
  summarizeNotes();
});
document.querySelector("#summaryButton").addEventListener("click", summarizeNotes);
document.querySelector("#questionButton").addEventListener("click", suggestQuestion);
document.querySelector("#opportunityButton").addEventListener("click", detectOpportunities);
document.querySelector("#reportButton").addEventListener("click", generateReport);
companyInput.addEventListener("input", () => {
  reportCompany.textContent = companyName();
});
