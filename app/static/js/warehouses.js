document.addEventListener("DOMContentLoaded", () => {
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

  const token = localStorage.getItem("access_token");

  let allProductsCache = [];
  let currentWarehouseStock = [];

  let role = "";
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    role = user?.role || "";
  } catch {}
  if (!role) {
    role =
      localStorage.getItem("role") || localStorage.getItem("user_role") || "";
  }
  role = (role || "").toLowerCase().trim();

  if (warehouseBtn) {
    if (role === "admin" || role === "manager") {
      warehouseBtn.classList.remove("hidden");
      warehouseBtn.style.setProperty("display", "inline-flex", "important");
    } else {
      warehouseBtn.style.display = "none";
      return;
    }
  }

  const safe = (val, fallback = "N/A") => {
    if (val === undefined || val === null || val === "" || val === "null")
      return fallback;
    return val;
  };

  function showUIMessage(elementId, message, type = "success") {
    const msgDiv = document.getElementById(elementId);
    if (!msgDiv) return;
    msgDiv.textContent = message;
    msgDiv.className = `ui-message ${type}`;
    msgDiv.classList.remove("hidden");
    setTimeout(() => msgDiv.classList.add("hidden"), 4000);
  }

  async function fetchInitialProductData() {
    try {
      const res = await fetch("/api/v1/products/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      allProductsCache = await res.json();
    } catch (err) {
      console.error("Initial product load failed", err);
    }
  }
  fetchInitialProductData();

  function renderAllProductsForAssign() {
    const container = document.getElementById("assignProductResults");
    if (!container) return;

    container.innerHTML = allProductsCache
      .map((p) => {
        const imgPath = p.image_url || p.image || "/static/img/placeholder.png";
        return `
        <div class="picker-item">
          <img src="${imgPath}" class="picker-img" onerror="this.src='/static/img/placeholder.png'">
          <div class="picker-info">
            <div class="picker-name">${p.name}</div>
            <div class="picker-variants">
              ${p.variants
                .map(
                  (v) => `
                <button type="button" class="v-pill" 
                  data-pid="${p._id || p.id}" 
                  data-pname="${p.name}" 
                  data-vname="${v.name}" 
                  data-sku="${v.sku}">
                  ${v.name} (${v.sku})
                </button>
              `,
                )
                .join("")}
            </div>
          </div>
        </div>
      `;
      })
      .join("");

    container.querySelectorAll(".v-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        const d = btn.dataset;
        document.getElementById("selectedAssignProdName").value =
          `${d.pname} - ${d.vname}`;
        document.getElementById("assignProdId").value = d.pid;
        document.getElementById("assignVariantSku").value = d.sku;
      });
    });
  }

  function renderStockForTransfer() {
    const container = document.getElementById("transferProductResults");
    if (!container) return;

    if (currentWarehouseStock.length === 0) {
      container.innerHTML =
        '<p class="empty-text">No items in this warehouse to transfer.</p>';
      return;
    }

    container.innerHTML = currentWarehouseStock
      .map(
        (item) => `
      <div class="picker-item">
        <div class="picker-info">
          <div class="picker-name">${item.product_name}</div>
          <div class="picker-variants">
            <button type="button" class="v-pill transfer-select-btn" 
              data-pname="${item.product_name}" 
              data-vname="${item.variant_name}" 
              data-sku="${item.variant_sku}"
              data-qty="${item.quantity}">
              ${item.variant_name} (${item.variant_sku}) - Available: ${item.quantity}
            </button>
          </div>
        </div>
      </div>
    `,
      )
      .join("");

    container.querySelectorAll(".transfer-select-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const d = btn.dataset;
        document.getElementById("selectedTransferProdName").value =
          `${d.pname} - ${d.vname} (Max: ${d.qty})`;
        document.getElementById("transferVariantSku").value = d.sku;

        const qInput = document.querySelector(
          "#transferForm [name='quantity']",
        );
        if (qInput) qInput.max = d.qty;
      });
    });
  }

  warehouseBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    warehouseOverlay.classList.remove("hidden");
    warehouseOverlay.style.display = "flex";
    await loadWarehouses();
  });

  closeWarehouseOverlay?.addEventListener("click", () => {
    warehouseOverlay.style.display = "none";
  });

  async function loadWarehouses() {
    try {
      warehouseContainer.innerHTML = `<p class="loading-text">Loading warehouses...</p>`;
      const res = await fetch("/api/v1/warehouses/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      if (!Array.isArray(data) || !data.length) {
        warehouseContainer.innerHTML = `<p class="empty-text">No warehouses found</p>`;
        return;
      }

      warehouseContainer.innerHTML = "";

      if (toWarehouseSelect) {
        toWarehouseSelect.innerHTML =
          '<option value="">Select Destination</option>';

        const currentId = fromWarehouseIdInput?.value;

        data.forEach((w) => {
          const wid = w._id || w.id;

          if (wid === currentId) return;

          const opt = document.createElement("option");
          opt.value = wid;
          opt.textContent = w.name;

          toWarehouseSelect.appendChild(opt);
        });
      }

      data.forEach((w) => {
        const card = document.createElement("div");
        card.className = "warehouse-card";
        card.style.cursor = "pointer";
        card.innerHTML = `
          <div class="warehouse-header">
            <h3>${safe(w.name)}</h3>
            <span class="warehouse-code">${safe(w.code)}</span>
          </div>
          <div class="warehouse-grid">
            <p><strong>Capacity:</strong> ${w.capacity ?? 0}</p>
            <p><strong>Status:</strong> ${w.is_active ? "Active" : "Inactive"}</p>
          </div>
          <div class="warehouse-footer">Click to view details and stock</div>
        `;

        card.addEventListener("click", (e) => {
          e.stopPropagation();
          openDetailedStockView(w);
        });

        warehouseContainer.appendChild(card);
      });
    } catch {
      warehouseContainer.innerHTML = `<p class="error-text">Failed to load warehouses</p>`;
    }
  }

  function openDetailedStockView(warehouse) {
    const warehouseId = warehouse._id || warehouse.id;
    warehouseOverlay.style.display = "none";
    stockOverlay.classList.remove("hidden");
    stockOverlay.style.display = "flex";

    if (fromWarehouseIdInput) fromWarehouseIdInput.value = warehouseId;
    if (assignWarehouseIdInput) assignWarehouseIdInput.value = warehouseId;

    let addr = "No address provided";
    if (warehouse.address && typeof warehouse.address === "object") {
      addr = `${safe(warehouse.address.street)}, ${safe(warehouse.address.city)}, ${safe(warehouse.address.state)}`;
    } else if (warehouse.street) {
      addr = `${safe(warehouse.street)}, ${safe(warehouse.city)}`;
    }

    warehouseDetailHeader.innerHTML = `
      <div class="detail-grid">
        <div class="detail-col">
          <p><strong>Warehouse Name:</strong> ${safe(warehouse.name)}</p>
          <p><strong>Code:</strong> ${safe(warehouse.code)}</p>
          <p><strong>Contact Email:</strong> ${safe(warehouse.email)}</p>
        </div>
        <div class="detail-col">
          <p><strong>Location:</strong> ${addr}</p>
          <p><strong>Capacity:</strong> ${warehouse.capacity ?? 0} units</p>
          <p><strong>Manager:</strong> ${safe(warehouse.created_by?.name, "System Admin")}</p>
        </div>
      </div>
    `;

    loadStockData(warehouseId);
  }

  async function loadStockData(warehouseId) {
    try {
      stockListContainer.innerHTML =
        '<p class="loading-text">Fetching inventory list...</p>';
      const res = await fetch(`/api/v1/warehouse-stock/${warehouseId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      currentWarehouseStock = data || [];

      if (!data || data.length === 0) {
        stockListContainer.innerHTML =
          '<p class="empty-text">No items currently in stock.</p>';
        return;
      }

      stockListContainer.innerHTML = data
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
    } catch {
      stockListContainer.innerHTML =
        '<p class="error-text">Failed to fetch stock data.</p>';
    }
  }

  openAssignStockBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    stockOverlay.style.display = "none";
    assignStockOverlay.classList.remove("hidden");
    assignStockOverlay.style.display = "flex";
    renderAllProductsForAssign();
  });

  openTransferBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    stockOverlay.style.display = "none";
    transferOverlay.classList.remove("hidden");
    transferOverlay.style.display = "flex";
    renderStockForTransfer();
  });

  closeStockOverlay?.addEventListener("click", () => {
    stockOverlay.style.display = "none";
    warehouseOverlay.style.display = "flex";
  });

  closeAssignStockOverlay?.addEventListener("click", () => {
    assignStockOverlay.style.display = "none";
    stockOverlay.style.display = "flex";
  });

  closeTransferOverlay?.addEventListener("click", () => {
    transferOverlay.style.display = "none";
    stockOverlay.style.display = "flex";
  });

  assignStockForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(assignStockForm);
    const payload = {
      warehouse_id: formData.get("warehouse_id"),
      product_id: formData.get("product_id"),
      variant_sku: formData.get("variant_sku"),
      quantity: parseInt(formData.get("quantity")),
    };

    try {
      const res = await fetch("/api/v1/warehouse-stock/assign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        showUIMessage("assignMsg", "Stock updated successfully");
        assignStockForm.reset();
        setTimeout(() => {
          assignStockOverlay.style.display = "none";
          stockOverlay.style.display = "flex";
        }, 1500);
        await loadStockData(payload.warehouse_id);
      } else {
        showUIMessage("assignMsg", "Failed to update stock", "error");
      }
    } catch (err) {
      showUIMessage("assignMsg", "Connection error", "error");
    }
  });

  transferForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(transferForm);
    const payload = {
      from_warehouse: formData.get("from_warehouse"),
      to_warehouse: formData.get("to_warehouse"),
      variant_sku: formData.get("variant_sku"),
      quantity: parseInt(formData.get("quantity")),
    };

    try {
      const res = await fetch("/api/v1/warehouse-stock/transfer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        showUIMessage("transferMsg", "Transfer successful");
        transferForm.reset();
        setTimeout(() => {
          transferOverlay.style.display = "none";
          stockOverlay.style.display = "flex";
        }, 1500);
        await loadStockData(payload.from_warehouse);
      } else {
        showUIMessage("transferMsg", "Transfer failed", "error");
      }
    } catch (err) {
      showUIMessage("transferMsg", "Connection error", "error");
    }
  });

  addWarehouseBtn?.addEventListener("click", () => {
    warehouseOverlay.style.display = "none";
    addWarehouseOverlay.classList.remove("hidden");
    addWarehouseOverlay.style.display = "flex";
  });

  closeAddWarehouseOverlay?.addEventListener("click", () => {
    addWarehouseOverlay.style.display = "none";
    warehouseOverlay.style.display = "flex";
  });

  addWarehouseForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
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

    const res = await fetch("/api/v1/warehouses/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      addWarehouseOverlay.style.display = "none";
      warehouseOverlay.style.display = "flex";
      addWarehouseForm.reset();
      await loadWarehouses();
    }
  });

  document.addEventListener("click", (e) => {
    if (warehouseOverlay && e.target === warehouseOverlay) {
      warehouseOverlay.style.display = "none";
    }

    if (addWarehouseOverlay && e.target === addWarehouseOverlay) {
      addWarehouseOverlay.style.display = "none";
      warehouseOverlay.style.display = "flex";
    }

    if (stockOverlay && e.target === stockOverlay) {
      stockOverlay.style.display = "none";
      warehouseOverlay.style.display = "flex";
    }

    if (assignStockOverlay && e.target === assignStockOverlay) {
      assignStockOverlay.style.display = "none";
      stockOverlay.style.display = "flex";
    }

    if (transferOverlay && e.target === transferOverlay) {
      transferOverlay.style.display = "none";
      stockOverlay.style.display = "flex";
    }
  });
});
