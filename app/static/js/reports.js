document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token) return;

  const getRole = () =>
    (
      localStorage.getItem("user_role") ||
      localStorage.getItem("role") ||
      "viewer"
    )
      .toLowerCase()
      .trim();

  const role = getRole();
  const reportsBtn = document.getElementById("reportsBtn");
  const reportsOverlay = document.getElementById("reportsOverlay");
  const closeReportsOverlay = document.getElementById("closeReportsOverlay");
  const reportsMenu = document.getElementById("reportsMenu");
  const reportsRoleBadge = document.getElementById("reportsRoleBadge");
  const activeReportTitle = document.getElementById("activeReportTitle");
  const activeReportSubtitle = document.getElementById("activeReportSubtitle");
  const reportMonthsInput = document.getElementById("reportMonthsInput");
  const reportLimitSelect = document.getElementById("reportLimitSelect");
  const reportInactiveDaysSelect = document.getElementById(
    "reportInactiveDaysSelect",
  );
  const refreshReportBtn = document.getElementById("refreshReportBtn");
  const downloadReportBtn = document.getElementById("downloadReportBtn");
  const reportSummaryCards = document.getElementById("reportSummaryCards");
  const reportInsightBanner = document.getElementById("reportInsightBanner");
  const reportInsightText = document.getElementById("reportInsightText");
  const reportTableTitle = document.getElementById("reportTableTitle");
  const reportGeneratedAt = document.getElementById("reportGeneratedAt");
  const reportsLoadingState = document.getElementById("reportsLoadingState");
  const reportTableWrapper = document.getElementById("reportTableWrapper");
  const reportTableHead = document.getElementById("reportTableHead");
  const reportTableBody = document.getElementById("reportTableBody");
  const reportEmptyState = document.getElementById("reportEmptyState");

  const reportConfigs = [
    {
      key: "stock-summary",
      title: "Stock Summary by Warehouse",
      description:
        "Track warehouse fill levels, stocked SKUs, and inventory concentration across locations.",
      roles: ["admin", "manager"],
      columns: [
        {
          label: "Warehouse",
          render: (row) => row.warehouse_name || "Warehouse",
        },
        { label: "Code", render: (row) => row.warehouse_code || "-" },
        { label: "Capacity", render: (row) => row.capacity ?? 0 },
        { label: "Units", render: (row) => row.total_units ?? 0 },
        { label: "Products", render: (row) => row.unique_products ?? 0 },
        { label: "Variants", render: (row) => row.unique_variants ?? 0 },
        {
          label: "Utilization",
          render: (row) =>
            row.utilization_pct === null || row.utilization_pct === undefined
              ? "-"
              : `${row.utilization_pct}%`,
        },
      ],
    },
    {
      key: "low-stock",
      title: "Low-Stock Report",
      description:
        "Highlight SKUs running at or below their alert threshold before they affect order flow.",
      roles: ["admin", "manager", "supplier"],
      columns: [
        { label: "Product", render: (row) => row.product_name || "-" },
        {
          label: "Variant",
          render: (row) => row.variant_name || "Base Product",
        },
        { label: "Available", render: (row) => row.available_stock ?? 0 },
        { label: "Threshold", render: (row) => row.low_stock_threshold ?? 0 },
        { label: "Supplier", render: (row) => row.supplier_name || "-" },
        {
          label: "Warehouse Mix",
          render: (row) => renderWarehouseMix(row.warehouses || []),
          rich: true,
        },
      ],
    },
    {
      key: "top-selling",
      title: "Top-Selling Products",
      description:
        "Measure product velocity and revenue contribution based on recent customer orders.",
      roles: ["admin", "manager", "supplier"],
      columns: [
        { label: "Rank", render: (row) => `#${row.rank || "-"}` },
        { label: "Product", render: (row) => row.product_name || "-" },
        { label: "Units Sold", render: (row) => row.units_sold ?? 0 },
        { label: "Orders", render: (row) => row.order_count ?? 0 },
        {
          label: "Revenue",
          render: (row) => formatCurrency(row.gross_revenue || 0),
        },
        {
          label: "Last Order",
          render: (row) => formatDate(row.last_order_at),
        },
      ],
    },
    {
      key: "supplier-purchases",
      title: "Supplier-wise Purchase Report",
      description:
        "Review purchase order volume, received quantity, and procurement value by supplier.",
      roles: ["admin", "manager", "supplier"],
      columns: [
        { label: "Supplier", render: (row) => row.supplier_name || "-" },
        { label: "PO Count", render: (row) => row.purchase_order_count ?? 0 },
        { label: "Open POs", render: (row) => row.open_purchase_orders ?? 0 },
        { label: "Ordered Qty", render: (row) => row.ordered_quantity ?? 0 },
        { label: "Received Qty", render: (row) => row.received_quantity ?? 0 },
        {
          label: "Ordered Value",
          render: (row) => formatCurrency(row.ordered_value || 0),
        },
      ],
    },
    {
      key: "dead-stock",
      title: "Dead Stock Report",
      description:
        "Identify stocked SKUs that have gone cold and are tying up working capital.",
      roles: ["admin", "manager", "supplier"],
      columns: [
        { label: "Product", render: (row) => row.product_name || "-" },
        {
          label: "Variant",
          render: (row) => row.variant_name || "Base Product",
        },
        { label: "Available", render: (row) => row.available_stock ?? 0 },
        {
          label: "Idle Days",
          render: (row) => row.days_idle ?? "-",
        },
        { label: "Supplier", render: (row) => row.supplier_name || "-" },
        {
          label: "Warehouse Mix",
          render: (row) => renderWarehouseMix(row.warehouses || []),
          rich: true,
        },
      ],
    },
    {
      key: "monthly-flow",
      title: "Monthly Inward vs Outward Report",
      description:
        "Compare inbound and outbound movement month by month for operational planning.",
      roles: ["admin", "manager", "supplier"],
      columns: [
        { label: "Month", render: (row) => row.month || "-" },
        { label: "Inward", render: (row) => row.inward ?? 0 },
        { label: "Outward", render: (row) => row.outward ?? 0 },
        { label: "Net", render: (row) => row.net ?? 0 },
        { label: "Movements", render: (row) => row.transaction_count ?? 0 },
      ],
    },
  ];

  const accessibleReports = reportConfigs.filter((config) =>
    config.roles.includes(role),
  );

  const state = {
    activeReportKey: accessibleReports[0]?.key || null,
    activePayload: null,
    isLoading: false,
  };

  if (!reportsBtn || !reportsOverlay || accessibleReports.length === 0) {
    if (reportsBtn) reportsBtn.style.display = "none";
    return;
  }

  reportsBtn.classList.remove("hidden");
  reportsBtn.style.display = "inline-flex";
  if (reportsRoleBadge) {
    reportsRoleBadge.textContent =
      role === "supplier"
        ? "Supplier-scoped analytics"
        : "Operations visibility";
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

  function formatCurrency(value) {
    return `INR ${Number(value || 0).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleString("en-IN", {
      year: "numeric",
      month: "short",
      day: "2-digit",
    });
  }

  function formatSummaryLabel(key) {
    return key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function renderWarehouseMix(warehouses) {
    if (!warehouses.length)
      return '<span class="report-muted-text">No warehouse stock</span>';
    return `
      <div class="report-inline-chipset">
        ${warehouses
          .map(
            (warehouse) => `
              <span class="report-inline-chip">
                ${warehouse.warehouse_name || "Warehouse"} <strong>${warehouse.quantity ?? 0}</strong>
              </span>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function buildInsight(config, payload) {
    const summary = payload?.summary || {};
    const rows = payload?.rows || [];

    if (config.key === "stock-summary" && rows.length) {
      return `${rows[0].warehouse_name} is carrying the highest load right now with ${rows[0].total_units || 0} units on hand.`;
    }
    if (config.key === "low-stock") {
      return `${summary.alert_items || 0} items are currently under their low-stock threshold, including ${summary.zero_stock_items || 0} that are already at zero.`;
    }
    if (config.key === "top-selling" && rows.length) {
      return `${rows[0].product_name} is leading the current selling window with ${rows[0].units_sold || 0} units sold.`;
    }
    if (config.key === "supplier-purchases") {
      return `${summary.suppliers_covered || 0} supplier accounts are represented in this purchasing window, with total ordered value at ${formatCurrency(summary.ordered_value || 0)}.`;
    }
    if (config.key === "dead-stock") {
      return `${summary.units_blocked || 0} units are sitting in inactive stock lines beyond the current inactivity threshold.`;
    }
    if (config.key === "monthly-flow") {
      return `Across the selected period, inward movement totals ${summary.total_inward || 0} units and outward movement totals ${summary.total_outward || 0} units.`;
    }
    return config.description;
  }

  function setLoading(isLoading) {
    state.isLoading = isLoading;
    reportsLoadingState?.classList.toggle("hidden", !isLoading);
    if (isLoading) {
      reportTableWrapper?.classList.add("hidden");
      reportEmptyState?.classList.add("hidden");
    }
    if (downloadReportBtn) downloadReportBtn.disabled = isLoading;
    if (refreshReportBtn) refreshReportBtn.disabled = isLoading;
  }

  function updateFilterAvailability() {
    const key = state.activeReportKey;
    const usesMonths = [
      "top-selling",
      "supplier-purchases",
      "monthly-flow",
    ].includes(key);
    const usesLimit = key === "top-selling";
    const usesInactiveDays = key === "dead-stock";

    if (reportMonthsInput) reportMonthsInput.disabled = !usesMonths;
    if (reportLimitSelect) reportLimitSelect.disabled = !usesLimit;
    if (reportInactiveDaysSelect)
      reportInactiveDaysSelect.disabled = !usesInactiveDays;
  }

  function renderMenu() {
    reportsMenu.innerHTML = accessibleReports
      .map(
        (config) => `
          <button
            type="button"
            class="report-menu-item ${config.key === state.activeReportKey ? "active" : ""}"
            data-report-key="${config.key}"
          >
            <span class="report-menu-title">${config.title}</span>
            <span class="report-menu-text">${config.description}</span>
          </button>
        `,
      )
      .join("");

    reportsMenu.querySelectorAll(".report-menu-item").forEach((button) => {
      button.addEventListener("click", async () => {
        const nextKey = button.dataset.reportKey;
        if (!nextKey || nextKey === state.activeReportKey) return;
        state.activeReportKey = nextKey;
        renderMenu();
        updateFilterAvailability();
        await loadReport();
      });
    });
  }

  function renderSummaryCards(payload) {
    const summary = payload?.summary || {};
    const entries = Object.entries(summary);
    if (!entries.length) {
      reportSummaryCards.innerHTML = "";
      return;
    }

    reportSummaryCards.innerHTML = entries
      .map(([key, value]) => {
        const displayValue =
          key.includes("value") || key.includes("revenue")
            ? formatCurrency(value)
            : value;
        return `
          <div class="report-summary-card">
            <span class="report-summary-label">${formatSummaryLabel(key)}</span>
            <strong class="report-summary-value">${displayValue}</strong>
          </div>
        `;
      })
      .join("");
  }

  function renderTable(config, payload) {
    const rows = payload?.rows || [];
    if (!rows.length) {
      reportTableWrapper.classList.add("hidden");
      reportEmptyState.classList.remove("hidden");
      reportTableHead.innerHTML = "";
      reportTableBody.innerHTML = "";
      return;
    }

    reportTableHead.innerHTML = `
      <tr>
        ${config.columns.map((column) => `<th>${column.label}</th>`).join("")}
      </tr>
    `;
    reportTableBody.innerHTML = rows
      .map(
        (row) => `
          <tr>
            ${config.columns
              .map((column) => {
                const value = column.render(row);
                return `<td>${column.rich ? value : `${value ?? "-"}`}</td>`;
              })
              .join("")}
          </tr>
        `,
      )
      .join("");

    reportEmptyState.classList.add("hidden");
    reportTableWrapper.classList.remove("hidden");
  }

  async function loadReport() {
    const config = accessibleReports.find(
      (entry) => entry.key === state.activeReportKey,
    );
    if (!config) return;

    setLoading(true);
    activeReportTitle.textContent = config.title;
    activeReportSubtitle.textContent = config.description;
    reportTableTitle.textContent = `${config.title} Results`;
    reportGeneratedAt.textContent = "Refreshing...";

    const params = new URLSearchParams({
      months: reportMonthsInput?.value || "6",
      limit: reportLimitSelect?.value || "10",
      inactive_days: reportInactiveDaysSelect?.value || "60",
    });

    try {
      const response = await fetch(
        `/api/v1/reports/${config.key}?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to load report");
      }

      const payload = await response.json();
      state.activePayload = payload;
      renderSummaryCards(payload);
      renderTable(config, payload);
      reportGeneratedAt.textContent = `Updated ${formatDate(payload.generated_at)}`;
      reportInsightText.textContent = buildInsight(config, payload);
      reportInsightBanner.classList.remove("hidden");
    } catch (error) {
      reportSummaryCards.innerHTML = "";
      reportTableHead.innerHTML = "";
      reportTableBody.innerHTML = "";
      reportEmptyState.textContent = error.message || "Unable to load report.";
      reportEmptyState.classList.remove("hidden");
      reportGeneratedAt.textContent = "Unavailable";
      reportInsightText.textContent =
        "We couldn't refresh this report just now.";
      reportInsightBanner.classList.remove("hidden");
      showToast(error.message || "Unable to load report");
    } finally {
      setLoading(false);
    }
  }

  async function downloadCurrentReport() {
    const config = accessibleReports.find(
      (entry) => entry.key === state.activeReportKey,
    );
    if (!config || state.isLoading) return;

    const params = new URLSearchParams({
      months: reportMonthsInput?.value || "6",
      limit: reportLimitSelect?.value || "10",
      inactive_days: reportInactiveDaysSelect?.value || "60",
    });

    try {
      downloadReportBtn.disabled = true;
      downloadReportBtn.textContent = "Preparing...";

      const response = await fetch(
        `/api/v1/reports/${config.key}/pdf?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "PDF export failed");
      }

      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename =
        match?.[1] || `${config.key.replace(/-/g, "_")}_report.pdf`;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      showToast("Report PDF downloaded");
    } catch (error) {
      showToast(error.message || "PDF export failed");
    } finally {
      downloadReportBtn.disabled = false;
      downloadReportBtn.textContent = "Download PDF";
    }
  }

  function openOverlay() {
    reportsOverlay.classList.remove("hidden");
    renderMenu();
    updateFilterAvailability();
    loadReport();
  }

  function closeOverlay() {
    reportsOverlay.classList.add("hidden");
  }

  reportsBtn.addEventListener("click", (event) => {
    event.preventDefault();
    openOverlay();
  });
  closeReportsOverlay?.addEventListener("click", closeOverlay);
  reportsOverlay.addEventListener("click", (event) => {
    if (event.target === reportsOverlay) closeOverlay();
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      !reportsOverlay.classList.contains("hidden")
    ) {
      closeOverlay();
    }
  });

  refreshReportBtn?.addEventListener("click", () => loadReport());
  downloadReportBtn?.addEventListener("click", () => downloadCurrentReport());
  reportMonthsInput?.addEventListener("change", () => {
    updateFilterAvailability();
    loadReport();
  });
  reportLimitSelect?.addEventListener("change", () => {
    updateFilterAvailability();
    loadReport();
  });
  reportInactiveDaysSelect?.addEventListener("change", () => {
    updateFilterAvailability();
    loadReport();
  });
});
