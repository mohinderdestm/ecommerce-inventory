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

  const canViewStaff = role === "admin" || role === "manager";
  const canManageStaff = role === "manager";

  const staffBtn = document.getElementById("staffBtn");
  const staffOverlay = document.getElementById("staffOverlay");
  const closeStaffOverlay = document.getElementById("closeStaffOverlay");
  const staffRoleBadge = document.getElementById("staffRoleBadge");
  const staffAccessNote = document.getElementById("staffAccessNote");
  const staffCreateForm = document.getElementById("staffCreateForm");
  const staffCountBadge = document.getElementById("staffCountBadge");
  const assignmentCountBadge = document.getElementById("assignmentCountBadge");
  const staffListContainer = document.getElementById("staffListContainer");
  const staffAssignmentOverview = document.getElementById(
    "staffAssignmentOverview",
  );
  const createStaffSubmitBtn = document.getElementById("createStaffSubmitBtn");

  const state = {
    staff: [],
    assignments: [],
    warehouses: [],
  };

  if (!staffBtn || !staffOverlay || !canViewStaff) {
    if (staffBtn) staffBtn.style.display = "none";
    return;
  }

  staffBtn.classList.remove("hidden");
  staffBtn.style.display = "inline-flex";
  if (staffRoleBadge) {
    staffRoleBadge.textContent = canManageStaff
      ? "Manager control enabled"
      : "Admin read-only visibility";
  }

  function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.classList.add("hidden"), 260);
    }, 2200);
  }

  function formatRoleLabel(value) {
    return String(value || "staff")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function renderAccessState() {
    if (!staffAccessNote || !staffCreateForm) return;

    if (canManageStaff) {
      staffAccessNote.classList.add("hidden");
      staffCreateForm
        .querySelectorAll("input, select, button")
        .forEach((field) => (field.disabled = false));
      return;
    }

    staffAccessNote.textContent =
      "Admin visibility is enabled here. Staff creation and assignment actions remain manager-only.";
    staffAccessNote.classList.remove("hidden");
    staffCreateForm
      .querySelectorAll("input, select, button")
      .forEach((field) => (field.disabled = true));
  }

  function renderStaffList() {
    const assignmentMap = state.assignments.reduce((map, assignment) => {
      const list = map.get(assignment.staff_id) || [];
      list.push(assignment);
      map.set(assignment.staff_id, list);
      return map;
    }, new Map());

    staffCountBadge.textContent = `${state.staff.length} members`;

    if (!state.staff.length) {
      staffListContainer.innerHTML =
        '<div class="staff-empty-state">No staff members available yet.</div>';
      return;
    }

    staffListContainer.innerHTML = state.staff
      .map((member) => {
        const assignments = assignmentMap.get(member.id) || [];
        return `
          <article class="staff-card">
            <div class="staff-card-top">
              <div>
                <h4>${member.name || "Staff Member"}</h4>
                <p>${member.email || "-"}</p>
              </div>
              <span class="staff-role-pill">${formatRoleLabel(member.role)}</span>
            </div>
            <div class="staff-card-grid">
              <span><strong>Phone:</strong> ${member.phone || "-"}</span>
              <span><strong>Status:</strong> ${member.is_active ? "Active" : "Inactive"}</span>
            </div>
            <div class="staff-chip-row">
              ${
                assignments.length
                  ? assignments
                      .map(
                        (assignment) => `
                          <span class="staff-warehouse-chip">${assignment.warehouse_name || "Warehouse"}</span>
                        `,
                      )
                      .join("")
                  : '<span class="staff-muted-chip">Unassigned</span>'
              }
            </div>
            ${
              canManageStaff
                ? `
                  <div class="staff-card-actions">
                    <button type="button" class="btn staff-delete-btn" data-staff-id="${member.id}">
                      Remove
                    </button>
                  </div>
                `
                : ""
            }
          </article>
        `;
      })
      .join("");

    if (canManageStaff) {
      staffListContainer
        .querySelectorAll(".staff-delete-btn")
        .forEach((button) => {
          button.addEventListener("click", () =>
            deleteStaffMember(button.dataset.staffId),
          );
        });
    }
  }

  function renderAssignmentOverview() {
    assignmentCountBadge.textContent = `${state.assignments.length} mappings`;

    if (!state.warehouses.length) {
      staffAssignmentOverview.innerHTML =
        '<div class="staff-empty-state">No warehouses available.</div>';
      return;
    }

    const staffMap = new Map(state.staff.map((member) => [member.id, member]));
    staffAssignmentOverview.innerHTML = state.warehouses
      .map((warehouse) => {
        const assigned = state.assignments.filter(
          (assignment) => assignment.warehouse_id === warehouse.id,
        );
        return `
          <article class="assignment-card">
            <div class="assignment-card-top">
              <div>
                <h4>${warehouse.name || "Warehouse"}</h4>
                <p>${warehouse.code || "No code"}</p>
              </div>
              <span class="assignment-count-pill">${assigned.length} staff</span>
            </div>
            <div class="assignment-chip-row">
              ${
                assigned.length
                  ? assigned
                      .map((assignment) => {
                        const member = staffMap.get(assignment.staff_id);
                        return `
                          <span class="assignment-person-chip">
                            ${member?.name || assignment.staff?.name || "Staff"}
                          </span>
                        `;
                      })
                      .join("")
                  : '<span class="staff-muted-chip">No staff assigned</span>'
              }
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadWorkspace() {
    try {
      const [staffResponse, assignmentResponse, warehouseResponse] =
        await Promise.all([
          fetch("/api/v1/staff/", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch("/api/v1/warehouse-staff/", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch("/api/v1/warehouses/", {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

      const [staff, assignments, warehouses] = await Promise.all([
        staffResponse.json(),
        assignmentResponse.json(),
        warehouseResponse.json(),
      ]);

      if (!staffResponse.ok)
        throw new Error(staff.detail || "Unable to load staff");
      if (!assignmentResponse.ok) {
        throw new Error(assignments.detail || "Unable to load assignments");
      }
      if (!warehouseResponse.ok) {
        throw new Error(warehouses.detail || "Unable to load warehouses");
      }

      state.staff = Array.isArray(staff) ? staff : [];
      state.assignments = Array.isArray(assignments) ? assignments : [];
      state.warehouses = Array.isArray(warehouses) ? warehouses : [];
      renderStaffList();
      renderAssignmentOverview();
    } catch (error) {
      staffListContainer.innerHTML = `
        <div class="staff-empty-state">${error.message || "Unable to load staff workspace."}</div>
      `;
      staffAssignmentOverview.innerHTML = "";
      showToast(error.message || "Unable to load staff workspace");
    }
  }

  async function deleteStaffMember(staffId) {
    if (!staffId || !canManageStaff) return;
    try {
      const response = await fetch(`/api/v1/staff/${staffId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to delete staff member");
      }
      showToast("Staff member removed");
      await loadWorkspace();
      if (typeof window.refreshWarehouseWorkspace === "function") {
        await window.refreshWarehouseWorkspace();
      }
    } catch (error) {
      showToast(error.message || "Unable to delete staff member");
    }
  }

  async function createStaffMember(event) {
    event.preventDefault();
    if (!canManageStaff) return;

    const formData = new FormData(staffCreateForm);
    const payload = {
      name: formData.get("name"),
      email: formData.get("email"),
      phone: formData.get("phone") || null,
      role: formData.get("role"),
    };

    try {
      createStaffSubmitBtn.disabled = true;
      createStaffSubmitBtn.textContent = "Creating...";

      const response = await fetch("/api/v1/staff/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to create staff member");
      }

      staffCreateForm.reset();
      showToast("Staff member created");
      await loadWorkspace();
      if (typeof window.refreshWarehouseWorkspace === "function") {
        await window.refreshWarehouseWorkspace();
      }
    } catch (error) {
      showToast(error.message || "Unable to create staff member");
    } finally {
      createStaffSubmitBtn.disabled = false;
      createStaffSubmitBtn.textContent = "Create Staff Member";
    }
  }

  function openOverlay() {
    staffOverlay.classList.remove("hidden");
    renderAccessState();
    loadWorkspace();
  }

  function closeOverlay() {
    staffOverlay.classList.add("hidden");
  }

  staffBtn.addEventListener("click", (event) => {
    event.preventDefault();
    openOverlay();
  });
  closeStaffOverlay?.addEventListener("click", closeOverlay);
  staffOverlay.addEventListener("click", (event) => {
    if (event.target === staffOverlay) closeOverlay();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !staffOverlay.classList.contains("hidden")) {
      closeOverlay();
    }
  });
  staffCreateForm?.addEventListener("submit", createStaffMember);

  window.refreshStaffWorkspace = loadWorkspace;
});
