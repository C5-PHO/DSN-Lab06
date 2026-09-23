const state = { token: sessionStorage.getItem("token"), documents: [] };
const contextHeaders = { "X-Device": "CORPORATIVO", "X-Location": "PERU" };

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...contextHeaders, ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "No se pudo completar la operación");
  return body;
}

function showAuthenticated(authenticated) {
  document.querySelector("#loginView").classList.toggle("hidden", authenticated);
  document.querySelector("#appView").classList.toggle("hidden", !authenticated);
}

async function loadDocuments() {
  state.documents = await api("/documentos");
  document.querySelector("#documentCount").textContent = state.documents.length;
  const body = document.querySelector("#documentsBody");
  body.innerHTML = state.documents.map(doc => `
    <tr><td><strong>${escapeHtml(doc.title)}</strong><br><span class="label">${escapeHtml(doc.description)}</span></td>
    <td>${escapeHtml(doc.department)}</td><td>${doc.confidentiality_level}</td>
    <td><span class="badge">${escapeHtml(doc.status)}</span></td>
    <td><button class="btn secondary" onclick="approve(${doc.id})">Aprobar</button></td></tr>`).join("") ||
    '<tr><td colspan="5" class="label">No hay documentos autorizados para este contexto.</td></tr>';
}

async function loadAudit() {
  const body = document.querySelector("#auditBody");
  try {
    const logs = await api("/auditoria?limit=100");
    body.innerHTML = logs.map(log => `<tr><td>${new Date(log.created_at).toLocaleString()}</td><td>${escapeHtml(log.username)}</td><td>${escapeHtml(log.action)}</td><td><span class="badge ${log.result === "PERMITIDO" ? "ok" : "danger"}">${log.result}</span></td><td>${escapeHtml(log.reason)}</td></tr>`).join("");
  } catch (error) {
    body.innerHTML = `<tr><td colspan="5" class="error">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function approve(id) {
  try { await api(`/documentos/${id}/aprobar`, { method: "POST" }); await loadDocuments(); }
  catch (error) { alert(error.message); }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" }[char]));
}

document.querySelector("#loginForm").addEventListener("submit", async event => {
  event.preventDefault();
  document.querySelector("#loginError").textContent = "";
  try {
    const data = await api("/auth/login", { method: "POST", body: JSON.stringify({ email: email.value, password: password.value }) });
    state.token = data.access_token; sessionStorage.setItem("token", state.token); showAuthenticated(true); await loadDocuments();
  } catch (error) { document.querySelector("#loginError").textContent = error.message; }
});

document.querySelector("#logout").addEventListener("click", async () => {
  try { await api("/auth/logout", { method: "POST" }); } catch (_) { /* Token may already be invalid. */ }
  state.token = null; sessionStorage.removeItem("token"); showAuthenticated(false);
});

document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", async () => {
  document.querySelectorAll("[data-view]").forEach(item => item.classList.remove("active")); button.classList.add("active");
  const isAudit = button.dataset.view === "audit";
  documentsView.classList.toggle("hidden", isAudit); auditView.classList.toggle("hidden", !isAudit);
  pageTitle.textContent = isAudit ? "Auditoría" : "Documentos";
  if (isAudit) await loadAudit(); else await loadDocuments();
}));

document.querySelector("#apiDocs").addEventListener("click", () => window.open("/docs", "_blank"));
document.querySelector("#refreshAudit").addEventListener("click", loadAudit);
document.querySelector("#newDocument").addEventListener("click", () => documentModal.classList.remove("hidden"));
document.querySelector("#closeModal").addEventListener("click", () => documentModal.classList.add("hidden"));
document.querySelector("#documentForm").addEventListener("submit", async event => {
  event.preventDefault(); documentError.textContent = "";
  try {
    await api("/documentos", { method: "POST", body: JSON.stringify({ title: docTitle.value, description: docDescription.value, department: docDepartment.value, confidentiality_level: Number(docLevel.value), status: "BORRADOR", country: docCountry.value }) });
    documentModal.classList.add("hidden"); event.target.reset(); docDepartment.value = "FINANZAS"; docCountry.value = "PERU"; await loadDocuments();
  } catch (error) { documentError.textContent = error.message; }
});

showAuthenticated(Boolean(state.token));
if (state.token) loadDocuments().catch(() => { state.token = null; sessionStorage.removeItem("token"); showAuthenticated(false); });
