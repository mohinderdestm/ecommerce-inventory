document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  const getSafeValue = (key, fallback = "") => {
    const value = localStorage.getItem(key);
    if (!value || value === "undefined" || value === "null") return fallback;
    return value;
  };

  const getEl = (id) => document.getElementById(id);

  const userEmail = getSafeValue("user_email", "");

  const userRole = getSafeValue("user_role", "viewer").toLowerCase();
  const userName =
    getSafeValue("user_name") || (userEmail ? userEmail.split("@")[0] : "User");

  const avatar = getEl("avatar");
  const nameEl = getEl("userName");
  const roleEl = getEl("userRole");

  const logoutBtn = getEl("logoutBtn");
  const addBtn = getEl("openAddProduct");

  const logoutOverlay = getEl("logoutOverlay");
  const closeLogoutOverlay = getEl("closeLogoutOverlay");
  const cancelLogout = getEl("cancelLogout");
  const confirmLogout = getEl("confirmLogout");

  const overlay = getEl("productOverlay");
  const closeOverlay = getEl("closeOverlay");
  const form = getEl("productForm");

  const deleteOverlay = getEl("deleteOverlay");
  const cancelDelete = getEl("cancelDelete");
  const confirmDelete = getEl("confirmDelete");

  const container = getEl("productsContainer");
  const toast = getEl("toast");

  const saveBtn = document.querySelector("#productForm button[type='submit']");

  if (overlay) overlay.classList.add("hidden");
  if (deleteOverlay) deleteOverlay.classList.add("hidden");
  if (logoutOverlay) logoutOverlay.classList.add("hidden");

  if (addBtn && userRole === "viewer") {
    addBtn.style.display = "none";
  }

  let editMode = false;
  let editProductId = null;
  let deleteProductId = null;

  const formatText = (text) =>
    text ? text.charAt(0).toUpperCase() + text.slice(1) : "User";

  if (avatar) avatar.innerText = formatText(userName).charAt(0);
  if (nameEl) nameEl.innerText = formatText(userName);
  if (roleEl) roleEl.innerText = formatText(userRole);

  const showToast = (msg) => {
    if (!toast) return;

    toast.innerText = msg;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.classList.add("hidden"), 300);
    }, 2000);
  };

  const openLogoutOverlay = () => {
    if (logoutOverlay) logoutOverlay.classList.remove("hidden");
  };

  const closeLogoutOverlayFn = () => {
    if (logoutOverlay) logoutOverlay.classList.add("hidden");
  };

  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openLogoutOverlay();
    });
  }

  if (closeLogoutOverlay) {
    closeLogoutOverlay.addEventListener("click", closeLogoutOverlayFn);
  }

  if (cancelLogout) {
    cancelLogout.addEventListener("click", closeLogoutOverlayFn);
  }

  if (logoutOverlay) {
    logoutOverlay.addEventListener("click", (e) => {
      if (e.target === logoutOverlay) closeLogoutOverlayFn();
    });
  }

  if (confirmLogout) {
    confirmLogout.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/";
    });
  }

  const openDeleteOverlay = (id) => {
    deleteProductId = id;
    if (deleteOverlay) deleteOverlay.classList.remove("hidden");
  };

  const closeDeleteOverlay = () => {
    if (deleteOverlay) deleteOverlay.classList.add("hidden");
    deleteProductId = null;
  };

  if (cancelDelete) {
    cancelDelete.addEventListener("click", closeDeleteOverlay);
  }

  if (deleteOverlay) {
    deleteOverlay.addEventListener("click", (e) => {
      if (e.target === deleteOverlay) closeDeleteOverlay();
    });
  }

  if (confirmDelete) {
    confirmDelete.addEventListener("click", async () => {
      if (!deleteProductId) return;

      try {
        const res = await fetch(`/api/v1/products/${deleteProductId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          showToast("Delete failed ❌");
          return;
        }

        showToast("Deleted product");
        closeDeleteOverlay();
        loadProducts();
      } catch (err) {
        showToast("Server error ❌");
      }
    });
  }

  const openOverlay = (mode = "add", product = null) => {
    if (!overlay) return;

    overlay.classList.remove("hidden");

    if (mode === "edit" && product) {
      editMode = true;
      editProductId = product._id || product.id;

      const title = getEl("formTitle");
      if (title) title.innerText = "Edit Product";

      const setVal = (id, val) => {
        const el = getEl(id);
        if (el) el.value = val ?? "";
      };

      setVal("name", product.name);
      setVal("description", product.description);
      setVal("category", product.category);
      setVal("brand", product.brand);
      setVal("cost_price", product.cost_price);
      setVal("price", product.selling_price);
      setVal("quantity", product.reorder_level);
      setVal("tax", product.tax);
      setVal("unit", product.unit || "piece");
    } else {
      editMode = false;
      editProductId = null;

      const title = getEl("formTitle");
      if (title) title.innerText = "Add Product";

      if (form) form.reset();
    }
  };

  const closeOverlayFn = () => {
    if (!overlay) return;

    overlay.classList.add("hidden");
    if (form) form.reset();

    editMode = false;
    editProductId = null;
  };

  window.openOverlay = openOverlay;

  if (addBtn) {
    addBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openOverlay("add");
    });
  }

  if (closeOverlay) {
    closeOverlay.addEventListener("click", closeOverlayFn);
  }

  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeOverlayFn();
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const getVal = (id, fallback = "") => {
        const el = getEl(id);
        return el ? el.value : fallback;
      };

      const payload = {
        name: getVal("name"),
        description: getVal("description"),
        category: getVal("category"),
        brand: getVal("brand"),
        cost_price: Number(getVal("cost_price", 0)),
        selling_price: Number(getVal("price", 0)),
        reorder_level: Number(getVal("quantity", 0)),
        tax: Number(getVal("tax", 0)),
        unit: getVal("unit", "piece"),
      };

      const img = getEl("image");
      const formData = new FormData();

      Object.keys(payload).forEach((key) => {
        formData.append(key, payload[key]);
      });

      if (img && img.files && img.files[0]) {
        formData.append("image", img.files[0]);
      }

      try {
        let url = "/api/v1/products/";
        let method = "POST";

        if (editMode) {
          url = `/api/v1/products/${editProductId}`;
          method = "PUT";
        }

        const res = await fetch(url, {
          method,
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!res.ok) {
          showToast("Failed ❌");
          return;
        }

        showToast(editMode ? "Updated product" : "Added product");
        closeOverlayFn();
        loadProducts();
      } catch (err) {
        showToast("Server error ❌");
      }
    });

    if (saveBtn) {
      saveBtn.addEventListener("click", (e) => {
        e.preventDefault();
        form.requestSubmit();
      });
    }
  }

  const loadProducts = async () => {
    try {
      const res = await fetch("/api/v1/products", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      const products = Array.isArray(data) ? data : data.products || [];

      if (!container) return;
      container.innerHTML = "";

      products.forEach((p) => {
        const card = document.createElement("div");
        card.className = "product-card";

        let actionButtonsHtml = "";
        const isAdmin = userRole === "admin";
        const isManager = userRole === "manager";

        if (isAdmin || isManager) {
          actionButtonsHtml += `<button class="edit-btn">Edit</button>`;
        }
        if (isAdmin) {
          actionButtonsHtml += `<button class="delete-btn">Delete</button>`;
        }

        card.innerHTML = `
          <div class="img-box">
            <img src="${p.image || "https://via.placeholder.com/300"}" />
          </div>

          <div class="card-body">
            <h3>${p.name}</h3>
            <p>${p.description || ""}</p>

            <div class="meta">
              <span>₹ ${p.selling_price}</span>
              <span>Stock: ${p.reorder_level}</span>
            </div>

            <p>${p.brand || ""} • ${p.category || ""}</p>

            ${actionButtonsHtml ? `<div class="card-actions">${actionButtonsHtml}</div>` : ""}
          </div>
        `;

        const editBtn = card.querySelector(".edit-btn");
        const deleteBtn = card.querySelector(".delete-btn");

        if (editBtn) {
          editBtn.addEventListener("click", () => {
            openOverlay("edit", p);
          });
        }

        if (deleteBtn) {
          deleteBtn.addEventListener("click", () => {
            openDeleteOverlay(p._id || p.id);
          });
        }

        container.appendChild(card);
      });
    } catch (err) {
      console.error(err);
    }
  };

  loadProducts();
});
