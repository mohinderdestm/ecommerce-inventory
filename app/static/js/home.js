document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  let allProducts = [];
  const getEl = (id) => document.getElementById(id);

  const searchInput = getEl("searchInput");
  const categoryFilter = getEl("categoryFilter");
  const searchBtn = getEl("searchBtn");

  const getSafeValue = (key, fallback = "N/A") => {
    const value = localStorage.getItem(key);
    if (!value || value === "undefined" || value === "null") return fallback;
    return value;
  };

  const userEmail = getSafeValue("user_email", "");
  const userRole = getSafeValue("user_role", "viewer").toLowerCase();
  const userName =
    getSafeValue("user_name") || (userEmail ? userEmail.split("@")[0] : "User");

  const avatar = getEl("avatar");
  const nameEl = getEl("userName");
  const roleEl = getEl("userRole");
  const logoutBtn = getEl("logoutBtn");
  const addBtn = getEl("openAddProduct");
  const toast = getEl("toast");
  const container = getEl("productsContainer");

  const overlay = getEl("productOverlay");
  const deleteOverlay = getEl("deleteOverlay");
  const logoutOverlay = getEl("logoutOverlay");
  const profileOverlay = getEl("userProfileOverlay");

  const form = getEl("productForm");
  const profileDetails = getEl("profileDetails");
  const userBox = document.querySelector(".user-box");

  let editMode = false;
  let editProductId = null;
  let deleteProductId = null;

  let isSubmitting = false;

  if (addBtn && userRole === "viewer") {
    addBtn.style.display = "none";
  }

  const formatText = (text) =>
    text ? text.charAt(0).toUpperCase() + text.slice(1) : "User";

  const updateHeaderUI = () => {
    const dName = localStorage.getItem("user_name") || userName;
    const dRole = localStorage.getItem("user_role") || userRole;
    if (avatar) avatar.innerText = formatText(dName).charAt(0);
    if (nameEl) nameEl.innerText = formatText(dName);
    if (roleEl) roleEl.innerText = formatText(dRole);
  };

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

  const closeAllOverlays = () => {
    [overlay, deleteOverlay, logoutOverlay, profileOverlay].forEach((ov) =>
      ov?.classList.add("hidden"),
    );
    if (form) form.reset();
    editMode = false;
    deleteProductId = null;
  };

  window.addEventListener("click", (e) => {
    if (
      e.target === overlay ||
      e.target === deleteOverlay ||
      e.target === logoutOverlay ||
      e.target === profileOverlay ||
      e.target.classList.contains("overlay-container")
    ) {
      closeAllOverlays();
    }
  });

  [
    getEl("closeOverlay"),
    getEl("closeDeleteOverlay"),
    getEl("closeLogoutOverlay"),
    getEl("closeProfileOverlay"),
    getEl("cancelLogout"),
    getEl("cancelDelete"),
  ].forEach((btn) => {
    btn?.addEventListener("click", (e) => {
      e.preventDefault();
      closeAllOverlays();
    });
  });

  const fetchUserData = async () => {
    try {
      const res = await fetch("/api/v1/users/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      const user = data.user;

      localStorage.setItem(
        "user_name",
        user.full_name || user.name || userName,
      );
      localStorage.setItem("user_role", user.role);
      localStorage.setItem("user_email", user.email);

      if (user.role === "supplier" && user.supplier_details) {
        const s = user.supplier_details;
        localStorage.setItem("company_name", s.name || "N/A");
        localStorage.setItem("contact_name", s.contact_person || "N/A");
        localStorage.setItem("phone_number", s.phone || "N/A");
        localStorage.setItem("gst_number", s.gst || "N/A");
        localStorage.setItem("address", s.address || "N/A");
        localStorage.setItem("payment_term", s.payment_terms || "N/A");
        localStorage.setItem("business_email", user.email);
      }
      updateHeaderUI();

      if (addBtn && user.role.toLowerCase() === "viewer") {
        addBtn.style.display = "none";
      } else if (addBtn) {
        addBtn.style.display = "flex";
      }
    } catch (err) {
      console.error("Error updating profile data:", err);
    }
  };

  const renderProfile = () => {
    const role = localStorage.getItem("user_role") || userRole;
    let html = `
      <div class="profile-info-item"><label>Name:</label> <span>${formatText(localStorage.getItem("user_name") || userName)}</span></div>
      <div class="profile-info-item"><label>Role:</label> <span>${formatText(role)}</span></div>
      <div class="profile-info-item"><label>Email:</label> <span>${localStorage.getItem("user_email") || userEmail}</span></div>
    `;

    if (role === "supplier") {
      html += `
        <div class="profile-info-item"><label>Company:</label> <span>${getSafeValue("company_name")}</span></div>
        <div class="profile-info-item"><label>Contact Name:</label> <span>${getSafeValue("contact_name")}</span></div>
        <div class="profile-info-item"><label>Business Email:</label> <span>${getSafeValue("business_email")}</span></div>
        <div class="profile-info-item"><label>Phone:</label> <span>${getSafeValue("phone_number")}</span></div>
        <div class="profile-info-item"><label>GST Number:</label> <span>${getSafeValue("gst_number")}</span></div>
        <div class="profile-info-item"><label>Address:</label> <span>${getSafeValue("address")}</span></div>
        <div class="profile-info-item"><label>Payment Terms:</label> <span>${getSafeValue("payment_term")}</span></div>
      `;
    }
    profileDetails.innerHTML = html;
  };

  if (userBox) {
    userBox.style.cursor = "pointer";
    userBox.addEventListener("click", () => {
      renderProfile();
      profileOverlay.classList.remove("hidden");
    });
  }

  const performSearch = () => {
    const query = searchInput.value.trim().toLowerCase().replace(/\s+/g, " ");
    const selectedCategory = categoryFilter.value;
    const filtered = allProducts.filter((p) => {
      const pName = (p.name || "").toLowerCase().replace(/\s+/g, " ");
      const pCat = p.category || "";
      return (
        pName.includes(query) &&
        (selectedCategory === "all" || pCat === selectedCategory)
      );
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
    if (categories.includes(currentSelection))
      categoryFilter.value = currentSelection;
  };

  const connectWebSocket = () => {
    const socket = new WebSocket("ws://localhost:8000/ws");
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (
        ["PRODUCT_CREATED", "PRODUCT_UPDATED", "PRODUCT_DELETED"].includes(
          data.event,
        )
      ) {
        showToast(data.event.replace("_", " ").toLowerCase());
        loadProducts();
      }
    };
    socket.onclose = () => setTimeout(connectWebSocket, 2000);
  };
  connectWebSocket();

  if (logoutBtn)
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logoutOverlay?.classList.remove("hidden");
    });
  if (getEl("confirmLogout"))
    getEl("confirmLogout").addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/";
    });

  const confirmDeleteBtn = getEl("confirmDelete");
  if (confirmDeleteBtn)
    confirmDeleteBtn.addEventListener("click", async () => {
      if (!deleteProductId) return;
      try {
        const res = await fetch(`/api/v1/products/${deleteProductId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          showToast("Deleted product");
          closeAllOverlays();
          loadProducts();
        }
      } catch (err) {
        showToast("Server error ❌");
      }
    });

  const openOverlay = (mode = "add", product = null) => {
    if (!overlay || userRole === "viewer") return;
    overlay.classList.remove("hidden");
    if (mode === "edit" && product) {
      editMode = true;
      editProductId = product._id || product.id;
      getEl("formTitle").innerText = "Edit Product";
      const setVal = (id, val) => {
        if (getEl(id)) getEl(id).value = val ?? "";
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

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (isSubmitting) return;
      isSubmitting = true;

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
        let url = editMode
          ? `/api/v1/products/${editProductId}`
          : "/api/v1/products/";
        let method = editMode ? "PUT" : "POST";

        const res = await fetch(url, {
          method,
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });

        if (res.ok) {
          showToast(editMode ? "Updated" : "Added");
          closeAllOverlays();
          loadProducts();
        }
      } catch (err) {
        showToast("Server error ❌");
      } finally {
        isSubmitting = false;
      }
    });
  }

  const renderProducts = (products) => {
    if (!container) return;
    container.innerHTML = "";
    if (products.length === 0) {
      container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #94a3b8;">No products found.</p>`;
      return;
    }

    const currentRole = (
      localStorage.getItem("user_role") || userRole
    ).toLowerCase();

    products.forEach((p) => {
      const card = document.createElement("div");
      card.className = "product-card";

      const isAdmin = currentRole === "admin";
      const isManager = currentRole === "manager";
      const isSupplier = currentRole === "supplier";

      let actionButtonsHtml = "";
      if (isAdmin || isManager || isSupplier)
        actionButtonsHtml += `<button class="edit-btn">Edit</button>`;
      if (isAdmin || isSupplier)
        actionButtonsHtml += `<button class="delete-btn">Delete</button>`;

      card.innerHTML = `
        <div class="img-box"><img src="${p.image || "https://via.placeholder.com/300"}" /></div>
        <div class="card-body">
          <h3>${p.name}</h3>
          <p>${p.description || ""}</p>
          <div class="meta"><span class="price">₹ ${p.selling_price}</span><span class="qty">Stock: ${p.reorder_level}</span></div>
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

  fetchUserData().then(loadProducts);
});
