document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  let allProducts = [];

  let currentPage = 1;
  const itemsPerPage = 10;
  let filteredProducts = [];

  const getEl = (id) => document.getElementById(id);

  const searchInput = getEl("searchInput");
  const categoryFilter = getEl("categoryFilter");
  const searchBtn = getEl("searchBtn");

  const prevPageBtn = getEl("prevPage");
  const nextPageBtn = getEl("nextPage");
  const pageNumbersContainer = getEl("pageNumbers");

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
  const detailOverlay = getEl("productDetailOverlay");
  const detailBody = getEl("productDetailBody");

  const form = getEl("productForm");
  const variantsContainer = getEl("variantsContainer");
  const addVariantBtn = getEl("addVariantBtn");
  const profileDetails = getEl("profileDetails");
  const userBox = document.querySelector(".user-box");

  let editMode = false;
  let editProductId = null;
  let deleteProductId = null;
  let isSubmitting = false;

  if (addBtn) {
    addBtn.style.display = userRole === "supplier" ? "flex" : "none";
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
    [
      overlay,
      deleteOverlay,
      logoutOverlay,
      profileOverlay,
      detailOverlay,
    ].forEach((ov) => ov?.classList.add("hidden"));
    if (form) form.reset();
    if (variantsContainer) variantsContainer.innerHTML = "";
    editMode = false;
    deleteProductId = null;
  };

  window.addEventListener("click", (e) => {
    if (
      e.target === overlay ||
      e.target === deleteOverlay ||
      e.target === logoutOverlay ||
      e.target === profileOverlay ||
      e.target === detailOverlay ||
      (e.target.classList && e.target.classList.contains("overlay-container"))
    ) {
      closeAllOverlays();
    }
  });

  [
    getEl("closeOverlay"),
    getEl("closeDeleteOverlay"),
    getEl("closeLogoutOverlay"),
    getEl("closeProfileOverlay"),
    getEl("closeDetailOverlay"),
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

      if (addBtn) {
        addBtn.style.display =
          user.role.toLowerCase() === "supplier" ? "flex" : "none";
      }
    } catch (err) {
      console.error("Error updating profile data:", err);
    }
  };

  const renderProfile = () => {
    if (!profileDetails) return;
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
      profileOverlay?.classList.remove("hidden");
    });
  }

  const updatePaginationUI = () => {
    if (!pageNumbersContainer) return;
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);

    if (prevPageBtn) prevPageBtn.disabled = currentPage === 1;
    if (nextPageBtn)
      nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;

    pageNumbersContainer.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) {
      const span = document.createElement("span");
      span.className = `page-num ${i === currentPage ? "active" : ""}`;
      span.innerText = i;
      span.addEventListener("click", () => {
        currentPage = i;
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        renderProducts(filteredProducts.slice(start, end));
        updatePaginationUI();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      pageNumbersContainer.appendChild(span);
    }
  };

  if (prevPageBtn) {
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        renderProducts(filteredProducts.slice(start, end));
        updatePaginationUI();
      }
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener("click", () => {
      const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
      if (currentPage < totalPages) {
        currentPage++;
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        renderProducts(filteredProducts.slice(start, end));
        updatePaginationUI();
      }
    });
  }

  const performSearch = () => {
    if (!searchInput || !categoryFilter) {
      filteredProducts = allProducts;
    } else {
      const query = searchInput.value.trim().toLowerCase().replace(/\s+/g, " ");
      const selectedCategory = categoryFilter.value;
      filteredProducts = allProducts.filter((p) => {
        const pName = (p.name || "").toLowerCase().replace(/\s+/g, " ");
        const pCat = p.category || "";
        return (
          pName.includes(query) &&
          (selectedCategory === "all" || pCat === selectedCategory)
        );
      });
    }

    currentPage = 1;
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    renderProducts(filteredProducts.slice(start, end));
    updatePaginationUI();
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

  const createVariantInput = (
    variant = {
      name: "",
      additional_price: null,
      reorder_level: null,
      image: "",
    },
  ) => {
    if (!variantsContainer) return;
    const div = document.createElement("div");
    div.className = "variant-item";
    div.dataset.existingImage = variant.image || "";

    const priceVal =
      variant.additional_price === 0 || variant.additional_price === null
        ? ""
        : variant.additional_price;
    const qtyVal =
      variant.reorder_level === 0 || variant.reorder_level === null
        ? ""
        : variant.reorder_level;

    div.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 5px; width: 100%;">
        <div style="display: flex; gap: 5px; align-items: center;">
            <input type="text" class="v-name" placeholder="Variant Name" value="${variant.name || ""}" required />
            <input type="number" class="v-price" placeholder="Price" value="${priceVal}" required />
            <input type="number" class="v-qty" placeholder="Stock" value="${qtyVal}" required />
            <button type="button" class="remove-variant-btn">&times;</button>
        </div>
        <input type="file" class="v-image" accept="image/*" />
        ${variant.image ? `<small style="color: #38bdf8; font-size: 10px;">Current: ${variant.image.split("/").pop()}</small>` : ""}
      </div>
    `;
    div
      .querySelector(".remove-variant-btn")
      .addEventListener("click", () => div.remove());
    variantsContainer.appendChild(div);
  };

  if (addVariantBtn) {
    addVariantBtn.addEventListener("click", () => createVariantInput());
  }

  const openOverlay = (mode = "add", product = null) => {
    if (!overlay || userRole !== "supplier") return;
    overlay.classList.remove("hidden");
    if (variantsContainer) variantsContainer.innerHTML = "";

    if (mode === "edit" && product) {
      editMode = true;
      editProductId = product._id || product.id;
      const formTitle = getEl("formTitle");
      if (formTitle) formTitle.innerText = "Edit Product";

      const setVal = (id, val) => {
        const el = getEl(id);
        if (el) el.value = val !== undefined && val !== null ? val : "";
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

      if (product.variants && Array.isArray(product.variants)) {
        product.variants.forEach((v) => createVariantInput(v));
      }
    } else {
      editMode = false;
      const formTitle = getEl("formTitle");
      if (formTitle) formTitle.innerText = "Add Product";
      form?.reset();
    }
  };

  const renderVariantDetails = (p, index) => {
    const isBase = index === -1;
    const variantData = isBase ? null : p.variants[index];

    const displayPrice = isBase
      ? p.selling_price
      : variantData.additional_price || 0;
    const displayStock = isBase
      ? p.reorder_level
      : variantData.reorder_level || 0;
    const displayTitle = isBase ? p.name : `${p.name} (${variantData.name})`;

    const displayImg =
      !isBase && variantData.image
        ? variantData.image
        : p.image || "https://via.placeholder.com/300";

    const supplier = p.supplier_details || null;
    let supplierHtml = `<p class="no-supplier">No supplier information available.</p>`;
    if (supplier && supplier.name) {
      supplierHtml = `
        <div class="supplier-card-mini">
          <div class="supplier-header-mini">
            <h4>Sold By: ${supplier.name}</h4>
          </div>
          <div class="supplier-grid-mini">
            <p><strong>Contact:</strong> ${supplier.contact_person || "N/A"}</p>
            <p><strong>Email:</strong> ${supplier.email || "N/A"}</p>
            <p><strong>Phone:</strong> ${supplier.phone || "N/A"}</p>
            <p><strong>Address:</strong> ${supplier.address || "N/A"}</p>
          </div>
        </div>
      `;
    }

    let managementHtml = "";
    const currentRole = (
      localStorage.getItem("user_role") || userRole
    ).toLowerCase();
    if (currentRole === "supplier") {
      managementHtml = `
        <div class="detail-management-actions">
            <button class="btn edit-btn-large" id="detailEditBtn">Edit Product</button>
            <button class="btn delete-btn-large" id="detailDeleteBtn">Delete Product</button>
        </div>
      `;
    }

    let switcherHtml = "";
    if (p.variants && p.variants.length > 0) {
      const totalVariants = p.variants.length;

      let dots = `<button class="variant-dot ${index === -1 ? "active" : ""}" data-idx="-1"></button>`;
      p.variants.forEach((v, i) => {
        dots += `<button class="variant-dot ${index === i ? "active" : ""}" data-idx="${i}"></button>`;
      });

      const prevIdx = index === -1 ? totalVariants - 1 : index - 1;
      const nextIdx = index === totalVariants - 1 ? -1 : index + 1;

      switcherHtml = `
        <div class="variant-nav-container">
          <button class="nav-arrow" data-idx="${prevIdx}">&#10094;</button>
          <div class="variant-switcher">${dots}</div>
          <button class="nav-arrow" data-idx="${nextIdx}">&#10095;</button>
        </div>
      `;
    }

    detailBody.innerHTML = `
      <div class="detail-grid">
        <div class="detail-img-box">
          <img src="${displayImg}" />
        </div>
        <div class="detail-info">
          <span class="detail-category">${p.category || "Uncategorized"}</span>
          <h2 class="detail-title">${displayTitle}</h2>
          <p class="detail-brand">Brand: ${p.brand || "Generic"}</p>
          <div class="detail-pricing">
             <span class="detail-price">₹ ${displayPrice}</span>
             <span class="detail-tax">+ ${p.tax}% Tax</span>
          </div>
          <p class="detail-stock">Available Stock: <strong>${displayStock} ${p.unit || "piece"}</strong></p>
          <div class="detail-desc">
            <label>Description</label>
            <p>${p.description || "No description provided."}</p>
          </div>
          ${switcherHtml}
        </div>
      </div>
      <div class="detail-footer">
        ${supplierHtml}
        ${managementHtml}
      </div>
    `;

    document.querySelectorAll(".variant-dot, .nav-arrow").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        renderVariantDetails(p, parseInt(btn.dataset.idx));
      });
    });

    if (currentRole === "supplier") {
      getEl("detailEditBtn")?.addEventListener("click", () => {
        detailOverlay.classList.add("hidden");
        openOverlay("edit", p);
      });
      getEl("detailDeleteBtn")?.addEventListener("click", () => {
        deleteProductId = p._id || p.id;
        deleteOverlay.classList.remove("hidden");
      });
    }
  };

  const openDetailOverlay = (p) => {
    if (!detailOverlay || !detailBody) return;
    detailOverlay.classList.remove("hidden");
    renderVariantDetails(p, -1);
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
      const formData = new FormData();

      const variants = [];
      const variantImages = [];

      document.querySelectorAll(".variant-item").forEach((item) => {
        variants.push({
          name: item.querySelector(".v-name").value,
          additional_price: Number(item.querySelector(".v-price").value) || 0,
          reorder_level: Number(item.querySelector(".v-qty").value) || 0,
          image: item.dataset.existingImage || "",
        });

        const vImgFile = item.querySelector(".v-image").files[0];
        variantImages.push(vImgFile || null);
      });

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
        variants: JSON.stringify(variants),
      };

      Object.keys(payload).forEach((key) => formData.append(key, payload[key]));

      const mainImg = getEl("image");
      if (mainImg?.files?.[0]) formData.append("image", mainImg.files[0]);

      variantImages.forEach((file) => {
        if (file) {
          formData.append("variant_images", file);
        } else {
          const blob = new Blob([""], { type: "application/octet-stream" });
          formData.append("variant_images", blob, "no_image.txt");
        }
      });

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
        } else {
          const errorData = await res.json();
          showToast(errorData.detail || "Upload failed");
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

    products.forEach((p) => {
      const card = document.createElement("div");
      card.className = "product-card";
      card.style.cursor = "pointer";

      card.innerHTML = `
        <div class="img-box"><img src="${p.image || "https://via.placeholder.com/300"}" /></div>
        <div class="card-body">
          <h3>${p.name}</h3>
          <p>${p.description || ""}</p>
          <div class="meta"><span class="price">₹ ${p.selling_price}</span><span class="qty">Stock: ${p.reorder_level}</span></div>
          <p class="extra">${p.brand || "Generic"} • ${p.category || "Uncategorized"}</p>
        </div>`;

      card.addEventListener("click", () => openDetailOverlay(p));
      container.appendChild(card);
    });
  };

  const loadProducts = async () => {
    try {
      const res = await fetch("/api/v1/products", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      let fetchedProducts = Array.isArray(data) ? data : data.products || [];

      const currentRole = (
        localStorage.getItem("user_role") ||
        userRole ||
        ""
      ).toLowerCase();
      const currentEmail =
        localStorage.getItem("user_email") || userEmail || "";

      if (currentRole === "supplier") {
        fetchedProducts = fetchedProducts.filter(
          (p) =>
            p.supplier_details && p.supplier_details.email === currentEmail,
        );
      }

      allProducts = fetchedProducts;
      updateCategoryDropdown(allProducts);
      performSearch();
    } catch (err) {
      console.error("Load Error:", err);
    }
  };

  fetchUserData().then(loadProducts);
});
