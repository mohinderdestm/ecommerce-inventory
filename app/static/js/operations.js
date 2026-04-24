document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token || token === "undefined" || token === "null") return;

  const role = (localStorage.getItem("user_role") || "viewer").toLowerCase();
  const navRight = document.querySelector(".nav-right");
  if (!navRight) return;

  const canManagePurchaseOrders = role === "admin" || role === "manager";
  const canViewPurchaseOrders = canManagePurchaseOrders || role === "supplier";
  const canViewInventoryMovements = role === "admin" || role === "manager";
  const canRefreshOperationalAlerts = role === "admin" || role === "manager";

  let productsCache = [];
  let suppliersCache = [];
  let warehousesCache = [];
  let latestNotificationPayload = { items: [], summary: {}, role_focus: {} };

  const toastEl = document.getElementById("toast");

  const notify = (message) => {
    if (!toastEl) return;
    toastEl.innerText = message;
    toastEl.classList.remove("hidden");
    toastEl.classList.add("show");
    setTimeout(() => {
      toastEl.classList.remove("show");
      setTimeout(() => toastEl.classList.add("hidden"), 250);
    }, 2200);
  };

  const apiFetch = async (url, options = {}) => {
    const headers = {
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    };
    const response = await fetch(url, { ...options, headers });
    let payload = null;
    try {
      payload = await response.json();
    } catch (err) {
      payload = null;
    }
    if (!response.ok) {
      const detail =
        payload?.detail || payload?.message || "Request failed. Try again.";
      throw new Error(detail);
    }
    return payload;
  };

  const formatDateTime = (raw) => {
    if (!raw) return "NA";
    try {
      return new Date(raw).toLocaleString();
    } catch (err) {
      return String(raw);
    }
  };

  const createNavButton = (id, label, classes = "") => {
    const btn = document.createElement("button");
    btn.id = id;
    btn.className = `btn ops-btn ${classes}`.trim();
    btn.type = "button";
    btn.innerText = label;
    return btn;
  };

  const notificationBtn = createNavButton(
    "notificationBtn",
    "Notifications",
    "notification-btn",
  );
  notificationBtn.innerHTML =
    'Notifications <span id="notificationBadge" class="notification-badge hidden">0</span>';
  navRight.prepend(notificationBtn);

  if (canViewPurchaseOrders) {
    navRight.prepend(createNavButton("purchaseOrdersBtn", "Purchase Orders"));
  }
  if (canViewInventoryMovements) {
    navRight.prepend(
      createNavButton("inventoryMovementsBtn", "Inventory Movements"),
    );
  }

  const overlayHtml = `
    <div id="notificationOverlay" class="overlay hidden">
      <div class="overlay-content ops-overlay-box">
        <div class="overlay-header">
          <div class="header-main">
            <h2>Notifications Center</h2>
            <span id="notificationCountPill" class="item-count-pill">0 Unread</span>
          </div>
          <button id="closeNotificationOverlay" class="close-btn" type="button">&times;</button>
        </div>
        <div class="ops-overlay-body">
          <section class="notif-hero">
            <div>
              <h3 id="notifRoleTitle">Role Focus</h3>
              <p id="notifRoleSubtitle" class="small-text">Action guidance will appear here.</p>
            </div>
            <div class="notif-summary-grid">
              <div class="notif-summary-card">
                <span class="label">Unread</span>
                <strong id="summaryUnread">0</strong>
              </div>
              <div class="notif-summary-card warning">
                <span class="label">Warning</span>
                <strong id="summaryWarning">0</strong>
              </div>
              <div class="notif-summary-card critical">
                <span class="label">Critical</span>
                <strong id="summaryCritical">0</strong>
              </div>
              <div class="notif-summary-card action">
                <span class="label">Action Required</span>
                <strong id="summaryAction">0</strong>
              </div>
            </div>
          </section>

          <div class="ops-card">
            <div class="ops-actions">
              <button id="refreshNotificationsBtn" class="btn ops-btn" type="button">Refresh Alerts</button>
              <button id="markAllNotificationsBtn" class="btn ops-btn" type="button">Mark All Read</button>
              <label class="small-text">
                <input id="includeReadNotifications" type="checkbox" />
                Show read notifications
              </label>
              <span id="notificationRefreshedAt" class="small-text"></span>
            </div>
            <div class="notif-filter-row">
              <input id="notificationSearch" placeholder="Search by title, type, message..." />
              <select id="notificationSeverityFilter">
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
              </select>
              <select id="notificationTypeFilter">
                <option value="">All Types</option>
              </select>
            </div>
            <div class="notif-chip-row">
              <button class="notif-chip active" data-chip="all" type="button">All</button>
              <button class="notif-chip" data-chip="unread" type="button">Unread</button>
              <button class="notif-chip" data-chip="action" type="button">Action Required</button>
              <button class="notif-chip" data-chip="critical" type="button">Critical</button>
            </div>
          </div>

          <div id="notificationList" class="notif-list"></div>
        </div>
      </div>
    </div>

    <div id="purchaseOrderOverlay" class="overlay hidden">
      <div class="overlay-content ops-overlay-box">
        <div class="overlay-header">
          <div class="header-main">
            <h2>Purchase Order Management</h2>
            <span id="poCountPill" class="item-count-pill">0 Orders</span>
          </div>
          <button id="closePurchaseOrderOverlay" class="close-btn" type="button">&times;</button>
        </div>
        <div class="ops-overlay-body">
          ${
            canManagePurchaseOrders
              ? `
            <div class="ops-card">
              <h3>Create Draft Purchase Order</h3>
              <form id="createPoForm" class="ops-grid-2">
                <select id="poSupplierEmail">
                  <option value="">Select Supplier (optional)</option>
                </select>
                <input id="poNotes" placeholder="Notes (optional)" />
                <div class="ops-actions">
                  <button class="btn ops-btn" type="submit">Create Draft</button>
                </div>
              </form>
            </div>
          `
              : ""
          }
          <div class="ops-card">
            <div class="ops-actions">
              <select id="poStatusFilter">
                <option value="">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="submitted">Submitted</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="partially_received">Partially Received</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <button id="refreshPoBtn" class="btn ops-btn" type="button">Refresh Orders</button>
            </div>
          </div>
          <div id="purchaseOrderList" class="notif-list"></div>
        </div>
      </div>
    </div>

    <div id="inventoryMovementOverlay" class="overlay hidden">
      <div class="overlay-content ops-overlay-box">
        <div class="overlay-header">
          <div class="header-main">
            <h2>Inventory Movement Tracking</h2>
            <span id="movementCountPill" class="item-count-pill">0 Entries</span>
          </div>
          <button id="closeInventoryMovementOverlay" class="close-btn" type="button">&times;</button>
        </div>
        <div class="ops-overlay-body">
          <div class="ops-card">
            <h3>Filters</h3>
            <div class="ops-grid">
              <select id="movementProductFilter"><option value="">All Products</option></select>
              <select id="movementWarehouseFilter"><option value="">All Warehouses</option></select>
              <select id="movementTypeFilter">
                <option value="">All Types</option>
                <option value="inward">Inward</option>
                <option value="outward">Outward</option>
                <option value="return">Return</option>
                <option value="damaged">Damaged</option>
                <option value="expired">Expired</option>
                <option value="transfer">Transfer</option>
              </select>
              <button id="refreshMovementBtn" class="btn ops-btn" type="button">Refresh</button>
            </div>
          </div>
          <div class="ops-card">
            <h3>Record Manual Movement</h3>
            <form id="createMovementForm" class="ops-grid">
              <select id="movementProductId" required><option value="">Select Product</option></select>
              <input id="movementVariantSku" placeholder="Variant SKU (optional)" />
              <select id="movementWarehouseId" required><option value="">Select Warehouse</option></select>
              <select id="movementType" required>
                <option value="inward">Inward</option>
                <option value="outward">Outward</option>
                <option value="return">Return</option>
                <option value="damaged">Damaged</option>
                <option value="expired">Expired</option>
                <option value="transfer">Transfer</option>
              </select>
              <input id="movementQuantity" type="number" min="1" placeholder="Quantity" required />
              <select id="movementDestinationWarehouseId" class="hidden">
                <option value="">Destination Warehouse (transfer)</option>
              </select>
              <input id="movementReferenceType" placeholder="Reference Type (e.g. purchase_order)" />
              <input id="movementReferenceId" placeholder="Reference ID" />
              <textarea id="movementRemarks" placeholder="Remarks"></textarea>
              <div class="ops-actions">
                <button class="btn ops-btn" type="submit">Record Movement</button>
              </div>
            </form>
          </div>
          <div class="ops-card">
            <div class="ops-table-wrap">
              <table class="ops-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Product</th>
                    <th>Warehouse</th>
                    <th>Type</th>
                    <th>Qty</th>
                    <th>Ref</th>
                    <th>By</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody id="movementTableBody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", overlayHtml);

  const setOverlayOpen = (overlayId, open) => {
    const overlay = document.getElementById(overlayId);
    if (!overlay) return;
    overlay.classList.toggle("hidden", !open);
  };

  const bindOverlayClose = (overlayId, closeBtnId) => {
    const overlay = document.getElementById(overlayId);
    const closeBtn = document.getElementById(closeBtnId);
    closeBtn?.addEventListener("click", () => setOverlayOpen(overlayId, false));
    overlay?.addEventListener("click", (event) => {
      if (event.target === overlay) setOverlayOpen(overlayId, false);
    });
  };

  bindOverlayClose("notificationOverlay", "closeNotificationOverlay");
  bindOverlayClose("purchaseOrderOverlay", "closePurchaseOrderOverlay");
  bindOverlayClose("inventoryMovementOverlay", "closeInventoryMovementOverlay");

  const renderOptionList = (rows, mapFn) =>
    rows.map((row) => mapFn(row)).join("");

  const loadReferenceData = async () => {
    const tasks = await Promise.allSettled([
      apiFetch("/api/v1/products/"),
      apiFetch("/api/v1/suppliers/"),
      apiFetch("/api/v1/warehouses/"),
    ]);

    productsCache = tasks[0].status === "fulfilled" ? tasks[0].value || [] : [];
    suppliersCache =
      tasks[1].status === "fulfilled" ? tasks[1].value || [] : [];
    warehousesCache =
      tasks[2].status === "fulfilled" ? tasks[2].value || [] : [];

    const productOptions = renderOptionList(
      productsCache,
      (p) => `<option value="${p.id || p._id}">${p.name}</option>`,
    );
    const warehouseOptions = renderOptionList(
      warehousesCache,
      (w) => `<option value="${w.id || w._id}">${w.name}</option>`,
    );
    const supplierOptions = renderOptionList(
      suppliersCache,
      (s) => `<option value="${s.email}">${s.name} (${s.email})</option>`,
    );

    ["movementProductFilter", "movementProductId"].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (id === "movementProductId") {
        el.innerHTML = `<option value="">Select Product</option>${productOptions}`;
      } else {
        el.innerHTML = `<option value="">All Products</option>${productOptions}`;
      }
    });

    [
      "movementWarehouseFilter",
      "movementWarehouseId",
      "movementDestinationWarehouseId",
    ].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (id === "movementWarehouseId") {
        el.innerHTML = `<option value="">Select Warehouse</option>${warehouseOptions}`;
      } else if (id === "movementDestinationWarehouseId") {
        el.innerHTML = `<option value="">Destination Warehouse</option>${warehouseOptions}`;
      } else {
        el.innerHTML = `<option value="">All Warehouses</option>${warehouseOptions}`;
      }
    });

    const supplierSelect = document.getElementById("poSupplierEmail");
    if (supplierSelect) {
      supplierSelect.innerHTML = `<option value="">Select Supplier (optional)</option>${supplierOptions}`;
    }
  };

  const severityIcon = (severity) => {
    if (severity === "critical") return "!";
    if (severity === "warning") return "▲";
    return "i";
  };

  const renderNotificationTypeFilterOptions = (items) => {
    const typeSelect = document.getElementById("notificationTypeFilter");
    if (!typeSelect) return;

    const uniqueTypes = Array.from(
      new Set(items.map((item) => item.type).filter(Boolean)),
    ).sort();

    typeSelect.innerHTML = [
      `<option value="">All Types</option>`,
      ...uniqueTypes.map((type) => `<option value="${type}">${type}</option>`),
    ].join("");
  };

  const applyNotificationFilters = () => {
    const payload = latestNotificationPayload || { items: [] };
    const items = payload.items || [];
    const listEl = document.getElementById("notificationList");
    if (!listEl) return;

    const search = (document.getElementById("notificationSearch")?.value || "")
      .trim()
      .toLowerCase();
    const severityFilter =
      document.getElementById("notificationSeverityFilter")?.value || "";
    const typeFilter =
      document.getElementById("notificationTypeFilter")?.value || "";
    const chip =
      document.querySelector(".notif-chip.active")?.getAttribute("data-chip") ||
      "all";

    const filtered = items.filter((item) => {
      const searchField =
        `${item.title || ""} ${item.message || ""} ${item.type || ""}`.toLowerCase();
      if (search && !searchField.includes(search)) return false;
      if (severityFilter && item.severity !== severityFilter) return false;
      if (typeFilter && item.type !== typeFilter) return false;

      if (chip === "unread" && item.is_read) return false;
      if (chip === "critical" && item.severity !== "critical") return false;
      if (
        chip === "action" &&
        !["critical", "warning"].includes(String(item.severity || "info"))
      ) {
        return false;
      }
      return true;
    });

    if (!filtered.length) {
      listEl.innerHTML = `<div class="ops-empty">No notifications matched your filters.</div>`;
      return;
    }

    listEl.innerHTML = filtered
      .map((item) => {
        const metadata = item.metadata || {};
        const actionLabel =
          metadata.impact === "review_dashboard"
            ? "Open Dashboard"
            : metadata.impact === "open_order_details"
              ? "Open Orders"
              : metadata.impact === "review_purchase_order"
                ? "Open PO"
                : metadata.impact
                  ? "Take Action"
                  : "Open Reference";
        const hasReference = Boolean(item.reference_id || item.reference_type);
        return `
          <article class="notif-item ${item.severity || "info"} ${item.is_read ? "read" : "unread"}">
            <div class="notif-row">
              <div class="notif-title-wrap">
                <span class="notif-severity-icon">${severityIcon(item.severity)}</span>
                <strong>${item.title || "Notification"}</strong>
              </div>
              <span class="small-text">${formatDateTime(item.created_at)}</span>
            </div>
            <p>${item.message || ""}</p>
            <div class="notif-meta-row">
              <span class="small-text">Type: ${item.type || "general"} | Ref: ${item.reference_type || "-"} ${item.reference_id || ""}</span>
              <span class="small-text ${item.is_read ? "" : "state-unread"}">${item.is_read ? "Read" : "Unread"}</span>
            </div>
            <div class="notif-row notif-action-row">
              ${
                !item.is_read
                  ? `<button class="btn ops-btn mark-read-btn" data-id="${item.id}" type="button">Mark Read</button>`
                  : `<span class="small-text">Acknowledged</span>`
              }
              ${
                hasReference
                  ? `<button class="btn ops-btn notif-open-ref-btn" data-reference-type="${item.reference_type || ""}" data-reference-id="${item.reference_id || ""}" type="button">${actionLabel}</button>`
                  : ""
              }
            </div>
          </article>
        `;
      })
      .join("");
  };

  const renderNotifications = (payload) => {
    latestNotificationPayload = payload || { items: [] };
    const items = payload?.items || [];
    const unreadCount = payload?.unread_count || 0;
    const summary = payload?.summary || {};
    const roleFocus = payload?.role_focus || {};

    const badge = document.getElementById("notificationBadge");
    const countPill = document.getElementById("notificationCountPill");
    const refreshedAt = document.getElementById("notificationRefreshedAt");
    const roleTitle = document.getElementById("notifRoleTitle");
    const roleSubtitle = document.getElementById("notifRoleSubtitle");

    if (countPill) countPill.innerText = `${unreadCount} Unread`;
    if (badge) {
      badge.innerText = String(unreadCount);
      badge.classList.toggle("hidden", unreadCount <= 0);
      badge.classList.toggle("critical", (summary.critical || 0) > 0);
    }
    if (refreshedAt) {
      refreshedAt.innerText = `Updated ${formatDateTime(payload?.last_refreshed)}`;
    }
    if (roleTitle) roleTitle.innerText = roleFocus.title || "Role Focus";
    if (roleSubtitle) {
      const tips = Array.isArray(roleFocus.recommended_actions)
        ? roleFocus.recommended_actions.join(" | ")
        : "";
      roleSubtitle.innerText = `${roleFocus.subtitle || ""}${tips ? ` • ${tips}` : ""}`;
    }

    document.getElementById("summaryUnread").innerText = String(
      summary.unread || unreadCount || 0,
    );
    document.getElementById("summaryWarning").innerText = String(
      summary.warning || 0,
    );
    document.getElementById("summaryCritical").innerText = String(
      summary.critical || 0,
    );
    document.getElementById("summaryAction").innerText = String(
      summary.action_required || 0,
    );

    renderNotificationTypeFilterOptions(items);
    applyNotificationFilters();
  };

  const loadNotifications = async () => {
    try {
      const includeRead =
        document.getElementById("includeReadNotifications")?.checked || false;
      const payload = await apiFetch(
        `/api/v1/notifications/?include_read=${includeRead}&limit=100`,
      );
      renderNotifications(payload);
    } catch (err) {
      notify(err.message);
    }
  };

  const openReferenceFromNotification = async (referenceType) => {
    if (referenceType === "purchase_order") {
      if (document.getElementById("purchaseOrdersBtn")) {
        document.getElementById("purchaseOrdersBtn").click();
      }
      return;
    }

    if (referenceType === "sales_order") {
      const ordersBtn = document.getElementById("adminOrdersBtn");
      if (ordersBtn && getComputedStyle(ordersBtn).display !== "none") {
        ordersBtn.click();
      }
      return;
    }

    if (referenceType === "product" || referenceType === "product_variant") {
      if (document.getElementById("inventoryMovementsBtn")) {
        document.getElementById("inventoryMovementsBtn").click();
      }
    }
  };

  notificationBtn.addEventListener("click", async () => {
    setOverlayOpen("notificationOverlay", true);
    await loadNotifications();
  });

  document
    .getElementById("includeReadNotifications")
    ?.addEventListener("change", loadNotifications);

  document
    .getElementById("refreshNotificationsBtn")
    ?.addEventListener("click", async () => {
      try {
        if (canRefreshOperationalAlerts) {
          await apiFetch("/api/v1/notifications/refresh", { method: "POST" });
        }
        await loadNotifications();
      } catch (err) {
        notify(err.message);
      }
    });

  document
    .getElementById("markAllNotificationsBtn")
    ?.addEventListener("click", async () => {
      try {
        await apiFetch("/api/v1/notifications/read-all", { method: "PUT" });
        await loadNotifications();
      } catch (err) {
        notify(err.message);
      }
    });

  document
    .getElementById("notificationSearch")
    ?.addEventListener("input", applyNotificationFilters);
  document
    .getElementById("notificationSeverityFilter")
    ?.addEventListener("change", applyNotificationFilters);
  document
    .getElementById("notificationTypeFilter")
    ?.addEventListener("change", applyNotificationFilters);

  document.querySelectorAll(".notif-chip").forEach((chipBtn) => {
    chipBtn.addEventListener("click", () => {
      document
        .querySelectorAll(".notif-chip")
        .forEach((el) => el.classList.remove("active"));
      chipBtn.classList.add("active");
      applyNotificationFilters();
    });
  });

  document
    .getElementById("notificationList")
    ?.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;

      if (target.classList.contains("mark-read-btn")) {
        const id = target.dataset.id;
        if (!id) return;
        try {
          await apiFetch(`/api/v1/notifications/${id}/read`, { method: "PUT" });
          await loadNotifications();
        } catch (err) {
          notify(err.message);
        }
      }

      if (target.classList.contains("notif-open-ref-btn")) {
        const referenceType = target.dataset.referenceType;
        await openReferenceFromNotification(referenceType);
      }
    });

  const renderPurchaseOrders = (orders) => {
    const container = document.getElementById("purchaseOrderList");
    const countPill = document.getElementById("poCountPill");
    if (!container) return;

    if (countPill) countPill.innerText = `${orders.length} Orders`;
    if (!orders.length) {
      container.innerHTML = `<div class="ops-empty">No purchase orders found.</div>`;
      return;
    }

    const productOptions = renderOptionList(
      productsCache,
      (p) => `<option value="${p.id || p._id}">${p.name}</option>`,
    );
    const warehouseOptions = renderOptionList(
      warehousesCache,
      (w) => `<option value="${w.id || w._id}">${w.name}</option>`,
    );

    container.innerHTML = orders
      .map((po) => {
        const status = po.status || "draft";
        const isEditable = canManagePurchaseOrders;
        const canAddItems = status === "draft" && isEditable;
        const canApproveReject = status === "submitted" && isEditable;
        const canReceive =
          (status === "approved" || status === "partially_received") &&
          isEditable;
        const canCancel =
          !["completed", "cancelled", "rejected"].includes(status) &&
          isEditable;

        const pendingReceiptOptions = (po.items || [])
          .filter(
            (item) =>
              Number(item.ordered_quantity || 0) -
                Number(item.received_quantity || 0) >
              0,
          )
          .map((item) => {
            const pending =
              Number(item.ordered_quantity || 0) -
              Number(item.received_quantity || 0);
            return `<option value="${item.product_id}::${item.variant_sku || ""}::${pending}">
              ${item.product_name}${item.variant_name && item.variant_name !== "Base Product" ? ` (${item.variant_name})` : ""} - Pending ${pending}
            </option>`;
          })
          .join("");

        const itemRows = (po.items || [])
          .map(
            (item) => `
              <tr>
                <td>${item.product_name || item.product_id}</td>
                <td>${item.variant_sku || "Base"}</td>
                <td>${item.ordered_quantity || 0}</td>
                <td>${item.received_quantity || 0}</td>
                <td>${Number(item.ordered_quantity || 0) - Number(item.received_quantity || 0)}</td>
              </tr>
            `,
          )
          .join("");

        return `
          <div class="ops-card po-card">
            <div class="po-header">
              <div>
                <strong>${po.po_number}</strong>
                <div class="small-text">Supplier: ${po.supplier_name || "N/A"} (${po.supplier_email || "No email"})</div>
                <div class="small-text">Created: ${formatDateTime(po.created_at)} | Updated: ${formatDateTime(po.updated_at)}</div>
              </div>
              <span class="status-chip status-${status}">${status.replace("_", " ")}</span>
            </div>

            <div class="ops-table-wrap">
              <table class="ops-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Variant SKU</th>
                    <th>Ordered</th>
                    <th>Received</th>
                    <th>Pending</th>
                  </tr>
                </thead>
                <tbody>${itemRows || `<tr><td colspan="5">No items added yet.</td></tr>`}</tbody>
              </table>
            </div>

            ${
              canAddItems
                ? `
              <form class="ops-grid add-po-item-form" data-po-id="${po.id}">
                <select name="product_id" required>
                  <option value="">Select Product</option>
                  ${productOptions}
                </select>
                <input name="variant_sku" placeholder="Variant SKU (optional)" />
                <input name="quantity" type="number" min="1" placeholder="Quantity" required />
                <input name="unit_cost" type="number" min="0" step="0.01" placeholder="Unit Cost" />
                <input name="remarks" placeholder="Item remarks" />
                <div class="ops-actions">
                  <button class="btn ops-btn" type="submit">Add Item</button>
                </div>
              </form>
            `
                : ""
            }

            ${
              canReceive
                ? `
              <form class="ops-grid receive-po-form" data-po-id="${po.id}">
                <select name="line_item" required>
                  <option value="">Select Pending Item</option>
                  ${pendingReceiptOptions}
                </select>
                <select name="warehouse_id" required>
                  <option value="">Select Warehouse</option>
                  ${warehouseOptions}
                </select>
                <input name="quantity_received" type="number" min="1" placeholder="Quantity Received" required />
                <input name="expiry_date" type="date" />
                <input name="remarks" placeholder="Receipt remarks" />
                <div class="ops-actions">
                  <button class="btn ops-btn" type="submit">Receive Stock</button>
                </div>
              </form>
            `
                : ""
            }

            ${
              isEditable
                ? `
              <form class="ops-grid-2 invoice-po-form" data-po-id="${po.id}">
                <input name="invoice_number" placeholder="Invoice Number" value="${po.invoice_metadata?.invoice_number || ""}" />
                <input name="bill_number" placeholder="Bill Number" value="${po.invoice_metadata?.bill_number || ""}" />
                <input name="invoice_date" type="date" value="${po.invoice_metadata?.invoice_date || ""}" />
                <input name="due_date" type="date" value="${po.invoice_metadata?.due_date || ""}" />
                <input name="tax_amount" type="number" min="0" step="0.01" placeholder="Tax Amount" value="${po.invoice_metadata?.tax_amount || ""}" />
                <input name="total_amount" type="number" min="0" step="0.01" placeholder="Total Amount" value="${po.invoice_metadata?.total_amount || ""}" />
                <input name="currency" placeholder="Currency" value="${po.invoice_metadata?.currency || "INR"}" />
                <input name="attachment_url" placeholder="Attachment URL" value="${po.invoice_metadata?.attachment_url || ""}" />
                <div class="ops-actions">
                  <button class="btn ops-btn" type="submit">Update Invoice</button>
                </div>
              </form>
            `
                : ""
            }

            <div class="ops-actions">
              ${
                canAddItems
                  ? `<button class="btn ops-btn po-action-btn" data-po-id="${po.id}" data-action="submit" type="button">Submit</button>`
                  : ""
              }
              ${
                canApproveReject
                  ? `<button class="btn ops-btn po-action-btn" data-po-id="${po.id}" data-action="approve" type="button">Approve</button>
                     <button class="btn ops-btn po-action-btn" data-po-id="${po.id}" data-action="reject" type="button">Reject</button>`
                  : ""
              }
              ${
                canCancel
                  ? `<button class="btn ops-btn po-action-btn" data-po-id="${po.id}" data-action="cancel" type="button">Cancel</button>`
                  : ""
              }
            </div>
          </div>
        `;
      })
      .join("");
  };

  const loadPurchaseOrders = async () => {
    try {
      const status = document.getElementById("poStatusFilter")?.value || "";
      const url = status
        ? `/api/v1/purchase-orders/?status=${status}&limit=200`
        : "/api/v1/purchase-orders/?limit=200";
      const rows = await apiFetch(url);
      renderPurchaseOrders(Array.isArray(rows) ? rows : []);
    } catch (err) {
      notify(err.message);
    }
  };

  document
    .getElementById("purchaseOrdersBtn")
    ?.addEventListener("click", async () => {
      setOverlayOpen("purchaseOrderOverlay", true);
      await loadReferenceData();
      await loadPurchaseOrders();
    });

  document
    .getElementById("refreshPoBtn")
    ?.addEventListener("click", loadPurchaseOrders);
  document
    .getElementById("poStatusFilter")
    ?.addEventListener("change", loadPurchaseOrders);

  document
    .getElementById("createPoForm")
    ?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const supplierEmail =
        document.getElementById("poSupplierEmail")?.value || null;
      const notes = document.getElementById("poNotes")?.value || null;
      try {
        await apiFetch("/api/v1/purchase-orders/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            supplier_email: supplierEmail || null,
            notes,
            items: [],
          }),
        });
        notify("Draft purchase order created");
        event.target.reset();
        await loadPurchaseOrders();
      } catch (err) {
        notify(err.message);
      }
    });

  document
    .getElementById("purchaseOrderList")
    ?.addEventListener("submit", async (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;
      event.preventDefault();
      const poId = form.dataset.poId;
      if (!poId) return;

      try {
        if (form.classList.contains("add-po-item-form")) {
          const productId = form.querySelector("[name='product_id']")?.value;
          const variantSku =
            form.querySelector("[name='variant_sku']")?.value || null;
          const quantity = Number(
            form.querySelector("[name='quantity']")?.value || 0,
          );
          const unitCost = Number(
            form.querySelector("[name='unit_cost']")?.value || 0,
          );
          const remarks = form.querySelector("[name='remarks']")?.value || null;
          await apiFetch(`/api/v1/purchase-orders/${poId}/items`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              items: [
                {
                  product_id: productId,
                  variant_sku: variantSku || null,
                  quantity,
                  unit_cost: unitCost,
                  remarks,
                },
              ],
            }),
          });
          notify("Item added to purchase order");
        } else if (form.classList.contains("receive-po-form")) {
          const lineValue =
            form.querySelector("[name='line_item']")?.value || "";
          const [productId, variantSku, pendingQtyRaw] = lineValue.split("::");
          const pendingQty = Number(pendingQtyRaw || 0);
          const warehouseId = form.querySelector(
            "[name='warehouse_id']",
          )?.value;
          const quantityReceived = Number(
            form.querySelector("[name='quantity_received']")?.value || 0,
          );
          const expiryDate =
            form.querySelector("[name='expiry_date']")?.value || null;
          const remarks = form.querySelector("[name='remarks']")?.value || null;

          if (!productId || !warehouseId) {
            notify("Select item and warehouse");
            return;
          }
          if (quantityReceived <= 0 || quantityReceived > pendingQty) {
            notify(`Received quantity must be between 1 and ${pendingQty}`);
            return;
          }

          await apiFetch(`/api/v1/purchase-orders/${poId}/receive`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              lines: [
                {
                  product_id: productId,
                  variant_sku: variantSku || null,
                  warehouse_id: warehouseId,
                  quantity_received: quantityReceived,
                  remarks,
                  expiry_date: expiryDate,
                },
              ],
            }),
          });
          notify("Receipt recorded and inventory updated");
        } else if (form.classList.contains("invoice-po-form")) {
          const payload = {};
          new FormData(form).forEach((value, key) => {
            if (value !== "") payload[key] = value;
          });
          if (payload.tax_amount !== undefined)
            payload.tax_amount = Number(payload.tax_amount);
          if (payload.total_amount !== undefined)
            payload.total_amount = Number(payload.total_amount);

          await apiFetch(`/api/v1/purchase-orders/${poId}/invoice`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          notify("Invoice metadata updated");
        }

        await loadPurchaseOrders();
      } catch (err) {
        notify(err.message);
      }
    });

  document
    .getElementById("purchaseOrderList")
    ?.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.classList.contains("po-action-btn")) return;

      const poId = target.dataset.poId;
      const action = target.dataset.action;
      if (!poId || !action) return;

      try {
        await apiFetch(`/api/v1/purchase-orders/${poId}/${action}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ remarks: null }),
        });
        notify(`Purchase order ${action} successful`);
        await loadPurchaseOrders();
      } catch (err) {
        notify(err.message);
      }
    });

  const renderMovements = (rows) => {
    const body = document.getElementById("movementTableBody");
    const countPill = document.getElementById("movementCountPill");
    if (!body) return;

    if (countPill) countPill.innerText = `${rows.length} Entries`;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="8" class="ops-empty">No movement entries found.</td></tr>`;
      return;
    }

    body.innerHTML = rows
      .map((row) => {
        const actor = row.performed_by || {};
        const qtyDisplay = `${row.delta > 0 ? "+" : ""}${row.delta || 0}`;
        return `
          <tr>
            <td>${formatDateTime(row.created_at)}</td>
            <td>
              <strong>${row.product_name || "N/A"}</strong><br />
              <span class="small-text">${row.variant_sku || "Base SKU"}</span>
            </td>
            <td>${row.warehouse_name || "N/A"}</td>
            <td>${row.movement_type || "N/A"}</td>
            <td>${qtyDisplay}</td>
            <td>${row.reference_type || "-"}<br /><span class="small-text">${row.reference_id || ""}</span></td>
            <td>${actor.name || actor.email || "System"}<br /><span class="small-text">${actor.role || "system"}</span></td>
            <td>${row.remarks || "-"}</td>
          </tr>
        `;
      })
      .join("");
  };

  const loadMovements = async () => {
    try {
      const productId =
        document.getElementById("movementProductFilter")?.value || "";
      const warehouseId =
        document.getElementById("movementWarehouseFilter")?.value || "";
      const movementType =
        document.getElementById("movementTypeFilter")?.value || "";

      const query = new URLSearchParams({ limit: "500" });
      if (productId) query.set("product_id", productId);
      if (warehouseId) query.set("warehouse_id", warehouseId);
      if (movementType) query.set("movement_type", movementType);

      const rows = await apiFetch(
        `/api/v1/inventory-movements/?${query.toString()}`,
      );
      renderMovements(Array.isArray(rows) ? rows : []);
    } catch (err) {
      notify(err.message);
    }
  };

  document
    .getElementById("inventoryMovementsBtn")
    ?.addEventListener("click", async () => {
      setOverlayOpen("inventoryMovementOverlay", true);
      await loadReferenceData();
      await loadMovements();
    });

  document
    .getElementById("refreshMovementBtn")
    ?.addEventListener("click", loadMovements);
  [
    "movementProductFilter",
    "movementWarehouseFilter",
    "movementTypeFilter",
  ].forEach((id) => {
    document.getElementById(id)?.addEventListener("change", loadMovements);
  });

  const movementTypeEl = document.getElementById("movementType");
  movementTypeEl?.addEventListener("change", () => {
    const destination = document.getElementById(
      "movementDestinationWarehouseId",
    );
    if (!destination) return;
    const isTransfer = movementTypeEl.value === "transfer";
    destination.classList.toggle("hidden", !isTransfer);
    destination.required = isTransfer;
  });

  document
    .getElementById("createMovementForm")
    ?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const movementType =
        document.getElementById("movementType")?.value || "inward";
      const payload = {
        product_id: document.getElementById("movementProductId")?.value,
        warehouse_id: document.getElementById("movementWarehouseId")?.value,
        variant_sku:
          document.getElementById("movementVariantSku")?.value || null,
        movement_type: movementType,
        quantity: Number(
          document.getElementById("movementQuantity")?.value || 0,
        ),
        destination_warehouse_id:
          movementType === "transfer"
            ? document.getElementById("movementDestinationWarehouseId")
                ?.value || null
            : null,
        reference_type:
          document.getElementById("movementReferenceType")?.value || "manual",
        reference_id:
          document.getElementById("movementReferenceId")?.value || null,
        remarks: document.getElementById("movementRemarks")?.value || null,
      };

      try {
        await apiFetch("/api/v1/inventory-movements/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        notify("Movement recorded successfully");
        event.target.reset();
        document
          .getElementById("movementDestinationWarehouseId")
          ?.classList.add("hidden");
        await loadMovements();
        await loadNotifications();
      } catch (err) {
        notify(err.message);
      }
    });

  setInterval(loadNotifications, 60000);
  loadNotifications();
});
