document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token) return;

  const role = (
    localStorage.getItem("user_role") ||
    localStorage.getItem("role") ||
    "viewer"
  )
    .toLowerCase()
    .trim();
  const canViewAuditLogs = role === "admin" || role === "manager";

  const auditBtn = document.getElementById("auditBtn");
  const auditOverlay = document.getElementById("auditOverlay");
  const closeAuditOverlay = document.getElementById("closeAuditOverlay");
  const refreshAuditBtn = document.getElementById("refreshAuditBtn");
  const auditLogContainer = document.getElementById("auditLogContainer");
  const auditCountBadge = document.getElementById("auditCountBadge");

  if (!auditBtn || !auditOverlay || !canViewAuditLogs) {
    if (auditBtn) auditBtn.style.display = "none";
    return;
  }

  auditBtn.classList.remove("hidden");
  auditBtn.style.display = "inline-flex";

  function formatDate(value) {
    if (!value) return "Unknown time";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  function formatJson(value) {
    if (value === null || value === undefined) return "None";
    if (typeof value === "string") return value;
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function hasAuditValue(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === "string") return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    return true;
  }

  function renderLogs(logs) {
    auditCountBadge.textContent = `${logs.length} entries`;

    if (!logs.length) {
      auditLogContainer.innerHTML =
        '<div class="audit-empty-state">No audit logs available yet.</div>';
      return;
    }

    auditLogContainer.innerHTML = logs
      .map((log) => {
        const actorName =
          log.user?.name || log.user?.email || log.user_id || "System";
        const actorRole = log.user?.role || "system";
        const valueSections = [];

        if (hasAuditValue(log.old_value)) {
          valueSections.push(`
            <section class="audit-log-block">
              <h4>Old Value</h4>
              <pre>${escapeHtml(formatJson(log.old_value))}</pre>
            </section>
          `);
        }

        if (hasAuditValue(log.new_value)) {
          valueSections.push(`
            <section class="audit-log-block">
              <h4>New Value</h4>
              <pre>${escapeHtml(formatJson(log.new_value))}</pre>
            </section>
          `);
        }

        return `
          <article class="audit-log-card">
            <div class="audit-log-top">
              <div>
                <h3>${escapeHtml(log.action || "Unknown action")}</h3>
                <p>
                  ${escapeHtml(actorName)} | ${escapeHtml(actorRole)} | ${escapeHtml(log.entity_type || "entity")}
                  ${log.entity_id ? `| ${escapeHtml(log.entity_id)}` : ""}
                </p>
              </div>
              <div class="audit-log-meta">
                <span class="audit-meta-pill">${escapeHtml(formatDate(log.timestamp))}</span>
                <span class="audit-meta-pill">${escapeHtml(log.ip_address || "No IP")}</span>
              </div>
            </div>
            ${valueSections.length ? `<div class="audit-log-grid">${valueSections.join("")}</div>` : ""}
            <section class="audit-log-block">
              <h4>Request Metadata</h4>
              <pre>${escapeHtml(formatJson(log.request_metadata || {}))}</pre>
            </section>
          </article>
        `;
      })
      .join("");
  }

  async function loadAuditLogs() {
    auditLogContainer.innerHTML =
      '<div class="loading-state">Loading audit timeline...</div>';

    try {
      const response = await fetch("/api/v1/audit-logs/?limit=150", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to load audit logs");
      }

      renderLogs(Array.isArray(payload) ? payload : []);
    } catch (error) {
      auditLogContainer.innerHTML = `
        <div class="audit-empty-state">${escapeHtml(
          error.message || "Unable to load audit logs.",
        )}</div>
      `;
      auditCountBadge.textContent = "0 entries";
    }
  }

  function openAuditOverlay() {
    auditOverlay.classList.remove("hidden");
    loadAuditLogs();
  }

  function closeAudit() {
    auditOverlay.classList.add("hidden");
  }

  auditBtn.addEventListener("click", (event) => {
    event.preventDefault();
    openAuditOverlay();
  });
  refreshAuditBtn?.addEventListener("click", loadAuditLogs);
  closeAuditOverlay?.addEventListener("click", closeAudit);
  auditOverlay.addEventListener("click", (event) => {
    if (event.target === auditOverlay) closeAudit();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !auditOverlay.classList.contains("hidden")) {
      closeAudit();
    }
  });
});
