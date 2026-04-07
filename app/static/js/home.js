document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  let allProducts = [];
  const searchInput = document.getElementById("searchInput");
  const categoryFilter = document.getElementById("categoryFilter");
  const searchBtn = document.getElementById("searchBtn");

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

  const performSearch = () => {
    const query = searchInput.value.trim().toLowerCase().replace(/\s+/g, " ");
    const selectedCategory = categoryFilter.value;

    const filtered = allProducts.filter((p) => {
      const pName = (p.name || "").toLowerCase().replace(/\s+/g, " ");
      const pCat = p.category || "";

      const matchesName = pName.includes(query);
      const matchesCategory =
        selectedCategory === "all" || pCat === selectedCategory;

      return matchesName && matchesCategory;
    });

    renderProducts(filtered);
  };

  if (searchInput) searchInput.addEventListener("input", performSearch);
  if (categoryFilter) categoryFilter.addEventListener("change", performSearch);
  if (searchBtn) searchBtn.addEventListener("click", performSearch);

  const updateCategoryDropdown = (products) => {
    if (!categoryFilter) return;
    const currentSelection = categoryFilter.value;
    const categories = [
      ...new Set(products.map((p) => p.category).filter((c) => c)),
    ];

    categoryFilter.innerHTML = '<option value="all">All Categories</option>';
    categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.innerText = formatText(cat);
      categoryFilter.appendChild(opt);
    });

    if (categories.includes(currentSelection)) {
      categoryFilter.value = currentSelection;
    }
  };

  let socket;
  const connectWebSocket = () => {
    socket = new WebSocket("ws://localhost:8000/ws");
    socket.onopen = () => console.log("✅ WebSocket Connected");
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (
        data.event === "PRODUCT_CREATED" ||
        data.event === "PRODUCT_UPDATED" ||
        data.event === "PRODUCT_DELETED"
      ) {
        showToast(data.event.replace("_", " ").toLowerCase());
        loadProducts();
      }
    };
    socket.onclose = () => setTimeout(connectWebSocket, 2000);
  };
  connectWebSocket();

  const closeLogoutOverlayFn = () => logoutOverlay?.classList.add("hidden");
  const closeDeleteOverlayFn = () => {
    deleteOverlay?.classList.add("hidden");
    deleteProductId = null;
  };
  const closeProductOverlayFn = () => {
    overlay?.classList.add("hidden");
    form?.reset();
    editMode = false;
  };

  if (logoutBtn)
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutOverlay?.classList.remove("hidden");
    });
  if (closeLogoutOverlay)
    closeLogoutOverlay.addEventListener("click", closeLogoutOverlayFn);
  if (cancelLogout)
    cancelLogout.addEventListener("click", closeLogoutOverlayFn);
  if (confirmLogout)
    confirmLogout.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/";
    });
  if (logoutOverlay)
    logoutOverlay.addEventListener("click", (e) => {
      if (e.target === logoutOverlay) closeLogoutOverlayFn();
    });

  // Delete Listeners
  if (cancelDelete)
    cancelDelete.addEventListener("click", closeDeleteOverlayFn);
  if (deleteOverlay)
    deleteOverlay.addEventListener("click", (e) => {
      if (e.target === deleteOverlay) closeDeleteOverlayFn();
    });
  if (confirmDelete)
    confirmDelete.addEventListener("click", async () => {
      if (!deleteProductId) return;
      try {
        const res = await fetch(`/api/v1/products/${deleteProductId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          showToast("Deleted product");
          closeDeleteOverlayFn();
          loadProducts();
        }
      } catch (err) {
        showToast("Server error ❌");
      }
    });

  const openOverlay = (mode = "add", product = null) => {
    if (!overlay) return;
    overlay.classList.remove("hidden");
    if (mode === "edit" && product) {
      editMode = true;
      editProductId = product._id || product.id;
      getEl("formTitle").innerText = "Edit Product";
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
      getEl("formTitle").innerText = "Add Product";
      form?.reset();
    }
  };

  window.openOverlay = openOverlay;
  if (addBtn)
    addBtn.addEventListener("click", (e) => {
      e.preventDefault();
      openOverlay("add");
    });
  if (closeOverlay)
    closeOverlay.addEventListener("click", closeProductOverlayFn);
  if (overlay)
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeProductOverlayFn();
    });

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const getVal = (id) => getEl(id)?.value || "";
      const payload = {
        name: getVal("name"),
        description: getVal("description"),
        category: getVal("category"),
        brand: getVal("brand"),
        cost_price: Number(getVal("cost_price")),
        selling_price: Number(getVal("price")),
        reorder_level: Number(getVal("quantity")),
        tax: Number(getVal("tax")),
        unit: getVal("unit"),
      };
      const img = getEl("image");
      const formData = new FormData();
      Object.keys(payload).forEach((key) => formData.append(key, payload[key]));
      if (img?.files?.[0]) formData.append("image", img.files[0]);

      try {
        let url = "/api/v1/products/";
        let method = "POST";
        if (editMode) {
          url = `/api/v1/products/${editProductId}`;
          method = "PUT";
        }
        const res = await fetch(url, {
          method,
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
        if (res.ok) {
          showToast(editMode ? "Updated" : "Added");
          closeProductOverlayFn();
          loadProducts();
        }
      } catch (err) {
        showToast("Server error ❌");
      }
    });
  }

  const renderProducts = (products) => {
    if (!container) return;
    container.innerHTML = "";
    if (products.length === 0) {
      container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #94a3b8;">No products found matching your search.</p>`;
      return;
    }

    products.forEach((p) => {
      const card = document.createElement("div");
      card.className = "product-card";
      const isAdmin = userRole === "admin";
      const isManager = userRole === "manager";
      let actionButtonsHtml = "";
      if (isAdmin || isManager)
        actionButtonsHtml += `<button class="edit-btn">Edit</button>`;
      if (isAdmin)
        actionButtonsHtml += `<button class="delete-btn">Delete</button>`;

      card.innerHTML = `
        <div class="img-box"><img src="${p.image || "https://via.placeholder.com/300"}" /></div>
        <div class="card-body">
          <h3>${p.name}</h3>
          <p>${p.description || ""}</p>
          <div class="meta">
            <span class="price">₹ ${p.selling_price}</span>
            <span class="qty">Stock: ${p.reorder_level}</span>
          </div>
          <p class="extra">${p.brand || ""} • ${p.category || ""}</p>
          ${actionButtonsHtml ? `<div class="card-actions">${actionButtonsHtml}</div>` : ""}
        </div>`;

      card
        .querySelector(".edit-btn")
        ?.addEventListener("click", () => openOverlay("edit", p));
      card.querySelector(".delete-btn")?.addEventListener("click", () => {
        deleteProductId = p._id || p.id;
        deleteOverlay.classList.remove("hidden");
      });
      container.appendChild(card);
    });
  };

  const loadProducts = async () => {
    try {
      const res = await fetch("/api/v1/products", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      allProducts = Array.isArray(data) ? data : data.products || [];

      updateCategoryDropdown(allProducts);
      performSearch();
    } catch (err) {
      console.error("Load Error:", err);
    }
  };

  loadProducts();
});
