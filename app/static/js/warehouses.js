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

  const token = localStorage.getItem("access_token");

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

  if (addWarehouseBtn) {
    if (role === "manager") {
      addWarehouseBtn.classList.remove("hidden");
    } else {
      addWarehouseBtn.style.display = "none";
    }
  }

  const safe = (val, fallback = "N/A") => {
    if (!val || val === "string" || val === "null") return fallback;
    return val;
  };

  function showFormMessage(message, type = "loading") {
    removeFormMessage();

    const msg = document.createElement("p");
    msg.id = "formMsg";
    msg.className =
      type === "error"
        ? "error-text"
        : type === "success"
          ? "success-text"
          : "loading-text";

    msg.innerHTML = message;

    addWarehouseForm.appendChild(msg);

    if (type !== "loading") {
      setTimeout(() => {
        msg.remove();
      }, 3000);
    }
  }

  function removeFormMessage() {
    document.getElementById("formMsg")?.remove();
  }

  warehouseBtn.addEventListener("click", async () => {
    warehouseOverlay.classList.remove("hidden");
    warehouseOverlay.style.display = "flex";
    await loadWarehouses();
  });

  closeWarehouseOverlay?.addEventListener("click", () => {
    warehouseOverlay.classList.add("hidden");
    warehouseOverlay.style.display = "none";
  });

  warehouseOverlay?.addEventListener("click", (e) => {
    if (e.target === warehouseOverlay) {
      warehouseOverlay.classList.add("hidden");
      warehouseOverlay.style.display = "none";
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

  addWarehouseOverlay?.addEventListener("click", (e) => {
    if (e.target === addWarehouseOverlay) {
      addWarehouseOverlay.style.display = "none";
      warehouseOverlay.style.display = "flex";
    }
  });

  addWarehouseForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    removeFormMessage();

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
      showFormMessage("Creating warehouse...", "loading");

      const res = await fetch("/api/v1/warehouses/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      removeFormMessage();

      if (!res.ok) {
        let msg = "Validation error";

        if (Array.isArray(data.detail)) {
          msg = data.detail
            .map((e) => `${e.loc.join(".")} → ${e.msg}`)
            .join("<br>");
        } else {
          msg = data.detail;
        }

        showFormMessage(msg, "error");
        return;
      }

      showFormMessage("Warehouse created successfully", "success");

      setTimeout(async () => {
        addWarehouseOverlay.style.display = "none";
        warehouseOverlay.style.display = "flex";
        addWarehouseForm.reset();

        await loadWarehouses();
      }, 800);
    } catch (err) {
      removeFormMessage();
      showFormMessage("Failed to create warehouse", "error");
    }
  });

  async function loadWarehouses() {
    try {
      warehouseContainer.innerHTML = `<p class="loading-text">Loading warehouses...</p>`;

      const res = await fetch("/api/v1/warehouses/", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();

      if (!Array.isArray(data)) {
        warehouseContainer.innerHTML = `<p class="error-text">Invalid response</p>`;
        return;
      }

      if (!data.length) {
        warehouseContainer.innerHTML = `<p class="empty-text">No warehouses found</p>`;
        return;
      }

      warehouseContainer.innerHTML = "";

      data.forEach((w) => {
        const card = document.createElement("div");
        card.className = "warehouse-card";

        card.innerHTML = `
          <div class="warehouse-header">
            <h3>${safe(w.name)}</h3>
            <span class="warehouse-code">${safe(w.code)}</span>
          </div>

          <div class="warehouse-grid">
            <p><strong>Email:</strong> ${safe(w.email)}</p>
            <p><strong>Phone:</strong> ${safe(w.phone)}</p>
            <p><strong>Capacity:</strong> ${w.capacity ?? 0}</p>
            <p><strong>Status:</strong> ${w.is_active ? "Active" : "Inactive"}</p>
          </div>

          <div class="warehouse-address">
            ${safe(w.address?.street)}, 
            ${safe(w.address?.city)}, 
            ${safe(w.address?.state)}, 
            ${safe(w.address?.country)} - 
            ${safe(w.address?.pincode)}
          </div>

          <div class="warehouse-footer">
            Created By: ${safe(w.created_by?.name)}
          </div>
        `;

        warehouseContainer.appendChild(card);
      });
    } catch {
      warehouseContainer.innerHTML = `<p class="error-text">Failed to load warehouses</p>`;
    }
  }
});
