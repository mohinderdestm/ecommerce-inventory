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
  const canViewWarehouses = role === "admin" || role === "manager";
  const canManageWarehouseStaff = role === "manager";

  const warehouseBtn = document.getElementById("warehouseBtn");
  const warehouseOverlay = document.getElementById("warehouseOverlay");
  const closeWarehouseOverlay = document.getElementById(
    "closeWarehouseOverlay",
  );
  const warehouseContainer = document.getElementById("warehouseContainer");

  const addWarehouseBtn = document.getElementById("addWarehouseBtn");
  const addWarehouseOverlay = document.getElementById("addWarehouseOverlay");
  const closeAddWarehouseOverlay = document.getElementById(
    "closeAddWarehouseOverlay",
  );
  const addWarehouseForm = document.getElementById("addWarehouseForm");

  const stockOverlay = document.getElementById("stockOverlay");
  const closeStockOverlay = document.getElementById("closeStockOverlay");
  const stockListContainer = document.getElementById("stockListContainer");
  const warehouseDetailHeader = document.getElementById(
    "warehouseDetailHeader",
  );

  const openAssignStockBtn = document.getElementById("openAssignStockBtn");
  const assignStockOverlay = document.getElementById("assignStockOverlay");
  const closeAssignStockOverlay = document.getElementById(
    "closeAssignStockOverlay",
  );
  const assignStockForm = document.getElementById("assignStockForm");
  const assignWarehouseIdInput = document.getElementById("assignWarehouseId");

  const openTransferBtn = document.getElementById("openTransferBtn");
  const transferOverlay = document.getElementById("transferOverlay");
  const closeTransferOverlay = document.getElementById("closeTransferOverlay");
  const transferForm = document.getElementById("transferForm");
  const toWarehouseSelect = document.getElementById("toWarehouseSelect");
  const fromWarehouseIdInput = document.getElementById("fromWarehouseId");

  const openAssignStaffBtn = document.getElementById("openAssignStaffBtn");
  const assignStaffOverlay = document.getElementById("assignStaffOverlay");
  const closeAssignStaffOverlay = document.getElementById(
    "closeAssignStaffOverlay",
  );
  const assignStaffWarehouseMeta = document.getElementById(
    "assignStaffWarehouseMeta",
  );
  const assignStaffOptions = document.getElementById("assignStaffOptions");
  const assignedWarehouseStaffList = document.getElementById(
    "assignedWarehouseStaffList",
  );
  const assignedWarehouseStaffCount = document.getElementById(
    "assignedWarehouseStaffCount",
  );
  const assignStaffSelectionBadge = document.getElementById(
    "assignStaffSelectionBadge",
  );
  const saveWarehouseStaffBtn = document.getElementById(
    "saveWarehouseStaffBtn",
  );

  const state = {
    warehouses: [],
    products: [],
    currentWarehouseStock: [],
    activeWarehouse: null,
    staff: [],
    currentAssignments: [],
  };

  if (!warehouseBtn || !canViewWarehouses) {
    if (warehouseBtn) warehouseBtn.style.display = "none";
    return;
  }

  warehouseBtn.classList.remove("hidden");
  warehouseBtn.style.display = "inline-flex";

  if (openAssignStaffBtn) {
    openAssignStaffBtn.classList.toggle("hidden", !canManageWarehouseStaff);
    openAssignStaffBtn.style.display = canManageWarehouseStaff
      ? "inline-flex"
      : "none";
  }

  function safe(value, fallback = "N/A") {
    return value === undefined ||
      value === null ||
      value === "" ||
      value === "null"
      ? fallback
      : value;
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

  function showUIMessage(elementId, message, type = "success") {
    const messageBox = document.getElementById(elementId);
    if (!messageBox) return;
    messageBox.textContent = message;
    messageBox.className = `ui-message ${type}`;
    messageBox.classList.remove("hidden");
    setTimeout(() => messageBox.classList.add("hidden"), 2800);
  }

  function showOverlay(overlay) {
    if (!overlay) return;
    overlay.classList.remove("hidden");
    overlay.style.display = "flex";
  }

  function hideOverlay(overlay) {
    if (!overlay) return;
    overlay.classList.add("hidden");
    overlay.style.display = "none";
  }

  function renderAssignedStaffPreview(staffList = []) {
    if (!staffList.length) {
      return '<span class="staff-muted-chip">No staff assigned yet</span>';
    }
    return staffList
      .map(
        (member) => `
          <span class="staff-warehouse-chip">
            ${member.name || "Staff"}${member.role ? ` | ${String(member.role).replace(/_/g, " ")}` : ""}
          </span>
        `,
      )
      .join("");
  }

  async function fetchProducts() {
    try {
      const response = await fetch("/api/v1/products/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      state.products = Array.isArray(payload) ? payload : [];
    } catch {
      state.products = [];
    }
  }

  async function fetchStaffDirectory() {
    if (!canManageWarehouseStaff && role !== "admin") {
      state.staff = [];
      return [];
    }

    const response = await fetch("/api/v1/staff/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Unable to load staff list");
    }
    state.staff = Array.isArray(payload) ? payload : [];
    return state.staff;
  }

  async function fetchWarehouseAssignments(warehouseId) {
    const response = await fetch(`/api/v1/warehouse-staff/${warehouseId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Unable to load warehouse staff");
    }
    state.currentAssignments = Array.isArray(payload) ? payload : [];
    return state.currentAssignments;
  }

  function buildWarehouseCard(warehouse) {
    const staffCount = Array.isArray(warehouse.staff)
      ? warehouse.staff.length
      : 0;
    const activeStatus = warehouse.is_active ? "Active" : "Inactive";
    return `
      <div class="warehouse-card">
        <div class="warehouse-card-top">
          <div class="warehouse-card-title-block">
            <h3>${safe(warehouse.name)}</h3>
            <p>${safe(warehouse.email)}</p>
          </div>
          <div class="warehouse-card-badges">
            <span class="warehouse-code">${safe(warehouse.code)}</span>
            <span class="warehouse-state-pill ${warehouse.is_active ? "active" : "inactive"}">${activeStatus}</span>
          </div>
        </div>
        <div class="warehouse-card-metrics">
          <div class="warehouse-metric">
            <span>Capacity</span>
            <strong>${warehouse.capacity ?? 0}</strong>
          </div>
          <div class="warehouse-metric">
            <span>Staff</span>
            <strong>${staffCount}</strong>
          </div>
          <div class="warehouse-metric">
            <span>City</span>
            <strong>${safe(warehouse.address?.city, "N/A")}</strong>
          </div>
        </div>
        <div class="warehouse-footer">
          <div class="assignment-chip-row">
            ${renderAssignedStaffPreview((warehouse.staff || []).slice(0, 3))}
          </div>
          <span>Open inventory, transfers, and staffing</span>
        </div>
      </div>
    `;
  }

  async function loadWarehouses() {
    warehouseContainer.innerHTML =
      '<p class="loading-text">Loading warehouses...</p>';

    try {
      const response = await fetch("/api/v1/warehouses/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to load warehouses");
      }

      state.warehouses = Array.isArray(payload) ? payload : [];

      if (!state.warehouses.length) {
        warehouseContainer.innerHTML =
          '<p class="empty-text">No warehouses found.</p>';
        return;
      }

      if (toWarehouseSelect) {
        toWarehouseSelect.innerHTML =
          '<option value="">Select Destination</option>';
        state.warehouses.forEach((warehouse) => {
          if (warehouse.id === state.activeWarehouse?.id) return;
          const option = document.createElement("option");
          option.value = warehouse.id;
          option.textContent = warehouse.name;
          toWarehouseSelect.appendChild(option);
        });
      }

      warehouseContainer.innerHTML = "";
      state.warehouses.forEach((warehouse) => {
        const wrapper = document.createElement("div");
        wrapper.innerHTML = buildWarehouseCard(warehouse);
        const card = wrapper.firstElementChild;
        card.style.cursor = "pointer";
        card.addEventListener("click", () => openDetailedStockView(warehouse));
        warehouseContainer.appendChild(card);
      });
    } catch (error) {
      warehouseContainer.innerHTML = `
        <p class="error-text">${error.message || "Failed to load warehouses."}</p>
      `;
    }
  }

  function renderWarehouseDetailHeader(warehouse) {
    const address =
      warehouse.address && typeof warehouse.address === "object"
        ? `${safe(warehouse.address.street)}, ${safe(warehouse.address.city)}, ${safe(warehouse.address.state)}, ${safe(warehouse.address.country)}`
        : "No address provided";
    const createdBy = safe(warehouse.created_by?.name, "System Admin");
    const staffCount = Array.isArray(warehouse.staff)
      ? warehouse.staff.length
      : 0;

    warehouseDetailHeader.innerHTML = `
      <div class="warehouse-detail-hero">
        <div class="warehouse-detail-main">
          <div class="warehouse-detail-title-row">
            <div>
              <span class="warehouse-detail-kicker">Warehouse Node</span>
              <h3>${safe(warehouse.name)}</h3>
            </div>
            <div class="warehouse-detail-badges">
              <span class="warehouse-code">${safe(warehouse.code)}</span>
              <span class="warehouse-state-pill ${warehouse.is_active ? "active" : "inactive"}">
                ${warehouse.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          </div>

          <p class="warehouse-detail-address">${address}</p>

          <div class="warehouse-detail-meta-grid">
            <div class="warehouse-detail-stat">
              <span>Contact Email</span>
              <strong>${safe(warehouse.email)}</strong>
            </div>
            <div class="warehouse-detail-stat">
              <span>Capacity</span>
              <strong>${warehouse.capacity ?? 0} units</strong>
            </div>
            <div class="warehouse-detail-stat">
              <span>Manager</span>
              <strong>${createdBy}</strong>
            </div>
            <div class="warehouse-detail-stat">
              <span>Assigned Staff</span>
              <strong>${staffCount}</strong>
            </div>
          </div>
        </div>

        <div class="warehouse-detail-sidecard">
          <span class="warehouse-detail-side-label">Coverage</span>
          <div class="assignment-chip-row">
            ${renderAssignedStaffPreview(warehouse.staff || [])}
          </div>
        </div>
      </div>
    `;
  }

  async function loadStockData(warehouseId) {
    try {
      stockListContainer.innerHTML =
        '<p class="loading-text">Fetching inventory list...</p>';
      const response = await fetch(`/api/v1/warehouse-stock/${warehouseId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to load stock");
      }

      state.currentWarehouseStock = Array.isArray(payload) ? payload : [];
      if (!state.currentWarehouseStock.length) {
        stockListContainer.innerHTML =
          '<p class="empty-text">No items currently in stock.</p>';
        return;
      }

      stockListContainer.innerHTML = state.currentWarehouseStock
        .map(
          (item) => `
            <div class="stock-item-row">
              <div class="stock-info">
                <span class="stock-prod-name"><strong>${item.product_name}</strong></span>
                <span class="stock-variant">${item.variant_name}</span>
                <code class="stock-sku">SKU: ${item.variant_sku}</code>
              </div>
              <div class="stock-value">
                <span class="qty-badge">${item.quantity} Qty</span>
              </div>
            </div>
          `,
        )
        .join("");
    } catch (error) {
      stockListContainer.innerHTML = `
        <p class="error-text">${error.message || "Failed to fetch stock data."}</p>
      `;
    }
  }

  async function openDetailedStockView(warehouse) {
    state.activeWarehouse = warehouse;
    renderWarehouseDetailHeader(warehouse);
    if (assignWarehouseIdInput) assignWarehouseIdInput.value = warehouse.id;
    if (fromWarehouseIdInput) fromWarehouseIdInput.value = warehouse.id;
    if (openAssignStaffBtn) {
      openAssignStaffBtn.classList.toggle("hidden", !canManageWarehouseStaff);
      openAssignStaffBtn.style.display = canManageWarehouseStaff
        ? "inline-flex"
        : "none";
    }
    hideOverlay(warehouseOverlay);
    showOverlay(stockOverlay);
    await loadStockData(warehouse.id);
  }

  function renderProductsForAssign() {
    const container = document.getElementById("assignProductResults");
    if (!container) return;

    container.innerHTML = state.products
      .map((product) => {
        const imagePath =
          product.image_url || product.image || "/static/img/placeholder.png";
        const buttons = [
          `
            <button
              type="button"
              class="v-pill"
              data-pid="${product.id}"
              data-pname="${product.name}"
              data-vname="Base Product"
              data-sku="${product.sku}"
            >
              Base Product (${product.sku})
            </button>
          `,
          ...(product.variants || []).map(
            (variant) => `
              <button
                type="button"
                class="v-pill"
                data-pid="${product.id}"
                data-pname="${product.name}"
                data-vname="${variant.name}"
                data-sku="${variant.sku}"
              >
                ${variant.name} (${variant.sku})
              </button>
            `,
          ),
        ].join("");

        return `
          <div class="picker-item">
            <img src="${imagePath}" class="picker-img" onerror="this.src='/static/img/placeholder.png'">
            <div class="picker-info">
              <div class="picker-name">${product.name}</div>
              <div class="picker-variants">${buttons}</div>
            </div>
          </div>
        `;
      })
      .join("");

    container.querySelectorAll(".v-pill").forEach((button) => {
      button.addEventListener("click", () => {
        document.getElementById("selectedAssignProdName").value =
          `${button.dataset.pname} - ${button.dataset.vname}`;
        document.getElementById("assignProdId").value = button.dataset.pid;
        document.getElementById("assignVariantSku").value = button.dataset.sku;
      });
    });
  }

  function renderStockForTransfer() {
    const container = document.getElementById("transferProductResults");
    if (!container) return;

    if (!state.currentWarehouseStock.length) {
      container.innerHTML =
        '<p class="empty-text">No items in this warehouse to transfer.</p>';
      return;
    }

    container.innerHTML = state.currentWarehouseStock
      .map(
        (item) => `
          <div class="picker-item">
            <div class="picker-info">
              <div class="picker-name">${item.product_name}</div>
              <div class="picker-variants">
                <button
                  type="button"
                  class="v-pill transfer-select-btn"
                  data-pname="${item.product_name}"
                  data-vname="${item.variant_name}"
                  data-sku="${item.variant_sku}"
                  data-qty="${item.quantity}"
                >
                  ${item.variant_name} (${item.variant_sku}) - Available: ${item.quantity}
                </button>
              </div>
            </div>
          </div>
        `,
      )
      .join("");

    container.querySelectorAll(".transfer-select-btn").forEach((button) => {
      button.addEventListener("click", () => {
        document.getElementById("selectedTransferProdName").value =
          `${button.dataset.pname} - ${button.dataset.vname} (Max: ${button.dataset.qty})`;
        document.getElementById("transferVariantSku").value =
          button.dataset.sku;
        const quantityInput = transferForm?.querySelector("[name='quantity']");
        if (quantityInput) quantityInput.max = button.dataset.qty;
      });
    });
  }

  function updateSelectionBadge() {
    const selected = assignStaffOptions.querySelectorAll(
      "input[type='checkbox']:checked",
    ).length;
    if (assignStaffSelectionBadge) {
      assignStaffSelectionBadge.textContent = `${selected} selected`;
    }
  }

  function renderAssignStaffOptions() {
    const assignedIds = new Set(
      state.currentAssignments.map((assignment) => assignment.staff_id),
    );

    assignStaffOptions.innerHTML = state.staff.length
      ? state.staff
          .map(
            (member) => `
              <div class="assign-staff-option">
                <label>
                  <input
                    type="checkbox"
                    value="${member.id}"
                    ${assignedIds.has(member.id) ? "checked" : ""}
                  />
                  <div>
                    <h4>${member.name || "Staff Member"}</h4>
                    <p>${member.email || "-"} | ${String(member.role || "staff").replace(/_/g, " ")}</p>
                  </div>
                </label>
              </div>
            `,
          )
          .join("")
      : '<div class="staff-empty-state">Create staff members first to assign them.</div>';

    assignStaffOptions
      .querySelectorAll("input[type='checkbox']")
      .forEach((checkbox) =>
        checkbox.addEventListener("change", () => updateSelectionBadge()),
      );
    updateSelectionBadge();
  }

  function renderCurrentAssignments() {
    if (assignedWarehouseStaffCount) {
      assignedWarehouseStaffCount.textContent = `${state.currentAssignments.length} assigned`;
    }

    assignedWarehouseStaffList.innerHTML = state.currentAssignments.length
      ? state.currentAssignments
          .map(
            (assignment) => `
            <div class="assigned-staff-card">
              <div class="assigned-staff-card-top">
                <div>
                  <h4>${assignment.staff?.name || "Staff Member"}</h4>
                  <p>${assignment.staff?.email || "-"} | ${String(assignment.staff?.role || "staff").replace(/_/g, " ")}</p>
                </div>
                ${
                  canManageWarehouseStaff
                    ? `
                      <button
                        type="button"
                        class="assigned-staff-remove-btn"
                        data-staff-id="${assignment.staff_id}"
                      >
                        Remove
                      </button>
                    `
                    : ""
                }
              </div>
              <p>Status: ${assignment.staff?.is_active ? "Active" : "Inactive"}</p>
            </div>
          `,
          )
          .join("")
      : '<div class="staff-empty-state">No staff assigned to this warehouse yet.</div>';

    if (canManageWarehouseStaff) {
      assignedWarehouseStaffList
        .querySelectorAll(".assigned-staff-remove-btn")
        .forEach((button) => {
          button.addEventListener("click", () =>
            removeWarehouseStaff(button.dataset.staffId),
          );
        });
    }
  }

  async function refreshWarehouseWorkspace() {
    await loadWarehouses();

    if (state.activeWarehouse?.id) {
      const nextWarehouse = state.warehouses.find(
        (warehouse) => warehouse.id === state.activeWarehouse.id,
      );
      if (nextWarehouse) {
        state.activeWarehouse = nextWarehouse;
        renderWarehouseDetailHeader(nextWarehouse);
      }
    }
  }

  async function openAssignStaffWorkspace() {
    if (!state.activeWarehouse || !canManageWarehouseStaff) return;

    try {
      assignStaffWarehouseMeta.innerHTML = `
        <strong>${state.activeWarehouse.name}</strong><br>
        ${safe(state.activeWarehouse.code)} | ${safe(state.activeWarehouse.email)}
      `;
      await Promise.all([
        fetchStaffDirectory(),
        fetchWarehouseAssignments(state.activeWarehouse.id),
      ]);
      renderAssignStaffOptions();
      renderCurrentAssignments();
      hideOverlay(stockOverlay);
      showOverlay(assignStaffOverlay);
    } catch (error) {
      showToast(error.message || "Unable to open assignment workspace");
    }
  }

  async function removeWarehouseStaff(staffId) {
    if (!staffId || !state.activeWarehouse?.id || !canManageWarehouseStaff)
      return;

    try {
      const response = await fetch(
        `/api/v1/warehouse-staff/${state.activeWarehouse.id}/${staffId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to remove warehouse staff");
      }

      showUIMessage("assignStaffMsg", "Staff member removed");
      await Promise.all([
        fetchWarehouseAssignments(state.activeWarehouse.id),
        refreshWarehouseWorkspace(),
      ]);
      renderCurrentAssignments();
      renderAssignStaffOptions();
      if (typeof window.refreshStaffWorkspace === "function") {
        await window.refreshStaffWorkspace();
      }
    } catch (error) {
      showUIMessage(
        "assignStaffMsg",
        error.message || "Unable to remove warehouse staff",
        "error",
      );
    }
  }

  async function saveWarehouseStaffAssignments() {
    if (!state.activeWarehouse?.id || !canManageWarehouseStaff) return;

    const selectedIds = Array.from(
      assignStaffOptions.querySelectorAll("input[type='checkbox']:checked"),
    ).map((checkbox) => checkbox.value);

    if (!selectedIds.length) {
      showUIMessage(
        "assignStaffMsg",
        "Select at least one staff member",
        "error",
      );
      return;
    }

    try {
      saveWarehouseStaffBtn.disabled = true;
      saveWarehouseStaffBtn.textContent = "Assigning...";

      const response = await fetch("/api/v1/warehouse-staff/bulk-assign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          warehouse_id: state.activeWarehouse.id,
          staff_ids: selectedIds,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to assign staff");
      }

      showUIMessage("assignStaffMsg", "Warehouse staff assignments updated");
      await Promise.all([
        fetchWarehouseAssignments(state.activeWarehouse.id),
        refreshWarehouseWorkspace(),
      ]);
      renderCurrentAssignments();
      renderAssignStaffOptions();
      if (typeof window.refreshStaffWorkspace === "function") {
        await window.refreshStaffWorkspace();
      }
    } catch (error) {
      showUIMessage(
        "assignStaffMsg",
        error.message || "Unable to assign staff",
        "error",
      );
    } finally {
      saveWarehouseStaffBtn.disabled = false;
      saveWarehouseStaffBtn.textContent = "Assign Selected";
    }
  }

  warehouseBtn.addEventListener("click", async (event) => {
    event.preventDefault();
    showOverlay(warehouseOverlay);
    await loadWarehouses();
  });

  closeWarehouseOverlay?.addEventListener("click", () =>
    hideOverlay(warehouseOverlay),
  );
  closeStockOverlay?.addEventListener("click", () => {
    hideOverlay(stockOverlay);
    showOverlay(warehouseOverlay);
  });
  closeAssignStockOverlay?.addEventListener("click", () => {
    hideOverlay(assignStockOverlay);
    showOverlay(stockOverlay);
  });
  closeTransferOverlay?.addEventListener("click", () => {
    hideOverlay(transferOverlay);
    showOverlay(stockOverlay);
  });
  closeAddWarehouseOverlay?.addEventListener("click", () => {
    hideOverlay(addWarehouseOverlay);
    showOverlay(warehouseOverlay);
  });
  closeAssignStaffOverlay?.addEventListener("click", () => {
    hideOverlay(assignStaffOverlay);
    showOverlay(stockOverlay);
  });

  addWarehouseBtn?.addEventListener("click", () => {
    hideOverlay(warehouseOverlay);
    showOverlay(addWarehouseOverlay);
  });

  openAssignStockBtn?.addEventListener("click", async (event) => {
    event.preventDefault();
    hideOverlay(stockOverlay);
    showOverlay(assignStockOverlay);
    if (!state.products.length) await fetchProducts();
    renderProductsForAssign();
  });

  openTransferBtn?.addEventListener("click", (event) => {
    event.preventDefault();
    hideOverlay(stockOverlay);
    showOverlay(transferOverlay);
    renderStockForTransfer();
  });

  openAssignStaffBtn?.addEventListener("click", async (event) => {
    event.preventDefault();
    await openAssignStaffWorkspace();
  });

  assignStockForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(assignStockForm);
    const payload = {
      warehouse_id: formData.get("warehouse_id"),
      product_id: formData.get("product_id"),
      variant_sku: formData.get("variant_sku"),
      quantity: Number(formData.get("quantity") || 0),
    };

    try {
      const response = await fetch("/api/v1/warehouse-stock/assign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to assign stock");
      }
      showUIMessage("assignMsg", "Stock updated successfully");
      assignStockForm.reset();
      await loadStockData(payload.warehouse_id);
      setTimeout(() => {
        hideOverlay(assignStockOverlay);
        showOverlay(stockOverlay);
      }, 900);
    } catch (error) {
      showUIMessage(
        "assignMsg",
        error.message || "Unable to assign stock",
        "error",
      );
    }
  });

  transferForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(transferForm);
    const payload = {
      from_warehouse: formData.get("from_warehouse"),
      to_warehouse: formData.get("to_warehouse"),
      variant_sku: formData.get("variant_sku"),
      quantity: Number(formData.get("quantity") || 0),
    };

    try {
      const response = await fetch("/api/v1/warehouse-stock/transfer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to transfer stock");
      }
      showUIMessage("transferMsg", "Transfer successful");
      transferForm.reset();
      await loadStockData(payload.from_warehouse);
      setTimeout(() => {
        hideOverlay(transferOverlay);
        showOverlay(stockOverlay);
      }, 900);
    } catch (error) {
      showUIMessage(
        "transferMsg",
        error.message || "Unable to transfer stock",
        "error",
      );
    }
  });

  addWarehouseForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(addWarehouseForm);
    const payload = {
      name: formData.get("name"),
      code: formData.get("code"),
      email: formData.get("email"),
      phone: formData.get("phone") || "",
      street: formData.get("street"),
      city: formData.get("city"),
      state: formData.get("state"),
      country: formData.get("country"),
      pincode: formData.get("pincode"),
      capacity: Number(formData.get("capacity") || 0),
      is_active: true,
    };

    try {
      const response = await fetch("/api/v1/warehouses/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to create warehouse");
      }

      addWarehouseForm.reset();
      hideOverlay(addWarehouseOverlay);
      showOverlay(warehouseOverlay);
      await loadWarehouses();
      if (typeof window.refreshStaffWorkspace === "function") {
        await window.refreshStaffWorkspace();
      }
    } catch (error) {
      showToast(error.message || "Unable to create warehouse");
    }
  });

  saveWarehouseStaffBtn?.addEventListener(
    "click",
    saveWarehouseStaffAssignments,
  );

  [
    warehouseOverlay,
    addWarehouseOverlay,
    stockOverlay,
    assignStockOverlay,
    transferOverlay,
    assignStaffOverlay,
  ].forEach((overlay) => {
    overlay?.addEventListener("click", (event) => {
      if (event.target !== overlay) return;
      hideOverlay(overlay);
      if (overlay === stockOverlay) {
        showOverlay(warehouseOverlay);
      }
      if (overlay === assignStaffOverlay) {
        showOverlay(stockOverlay);
      }
      if (overlay === assignStockOverlay || overlay === transferOverlay) {
        showOverlay(stockOverlay);
      }
    });
  });

  fetchProducts();
  window.refreshWarehouseWorkspace = refreshWarehouseWorkspace;
});
