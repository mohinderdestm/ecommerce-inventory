document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  let allProducts = [];

  const getSafeValue = (key, fallback = "N/A") => {
    const value = localStorage.getItem(key);
    if (!value || value === "undefined" || value === "null") return fallback;
    return value;
  };

  const userEmail = getSafeValue("user_email", "");
  const userRole = getSafeValue("user_role", "viewer").toLowerCase();
  const userName =
    getSafeValue("user_name") || (userEmail ? userEmail.split("@")[0] : "User");

  const cartKey = userEmail ? `cart_${userEmail}` : "active_cart";
  let cart = JSON.parse(localStorage.getItem(cartKey)) || [];

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

  const cartBtn = getEl("cartBtn");
  const cartOverlay = getEl("cartOverlay");
  const cartItemsContainer = getEl("cartItemsContainer");
  const cartTotalValue = getEl("cartTotalValue");
  const cartBadge = getEl("cartBadge");
  const clearCartBtn = getEl("clearCartBtn");
  const placeOrderBtn = getEl("placeOrderBtn");
  const orderSuccessOverlay = getEl("orderSuccessOverlay");

  const adminOrdersBtn = getEl("adminOrdersBtn");
  const ordersOverlay = getEl("ordersOverlay");
  const ordersMasterContainer = getEl("ordersMasterContainer");
  const totalOrdersBadge = getEl("totalOrdersBadge");
  const closeOrdersOverlay = getEl("closeOrdersOverlay");

  const form = getEl("productForm");
  const variantsContainer = getEl("variantsContainer");
  const addVariantBtn = getEl("addVariantBtn");
  const baseWarehouseAllocations = getEl("baseWarehouseAllocations");
  const addBaseAllocationBtn = getEl("addBaseAllocationBtn");
  const profileDetails = getEl("profileDetails");
  const userBox = document.querySelector(".user-box");

  let editMode = false;
  let editProductId = null;
  let deleteProductId = null;
  let isSubmitting = false;
  let availableWarehouses = [];
  let warehousesLoaded = false;

  if (addBtn) {
    addBtn.style.display = userRole === "supplier" ? "flex" : "none";
  }

  const formatText = (text) =>
    text ? text.charAt(0).toUpperCase() + text.slice(1) : "User";

  const updateHeaderUI = () => {
    const dName = localStorage.getItem("user_name") || userName;
    const dRole = (localStorage.getItem("user_role") || userRole).toLowerCase();

    if (avatar) avatar.innerText = formatText(dName).charAt(0);
    if (nameEl) nameEl.innerText = formatText(dName);
    if (roleEl) roleEl.innerText = formatText(dRole);

    if (cartBtn) {
      cartBtn.style.display = dRole === "viewer" ? "flex" : "none";
    }

    if (adminOrdersBtn) {
      const canSeeOrders = dRole === "admin" || dRole === "viewer";
      adminOrdersBtn.style.display = canSeeOrders ? "flex" : "none";
      adminOrdersBtn.classList.toggle("hidden", !canSeeOrders);
    }
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

  const fetchWarehousesForProductForm = async (force = false) => {
    if (warehousesLoaded && !force) return availableWarehouses;

    try {
      const res = await fetch("/api/v1/warehouses/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      availableWarehouses = Array.isArray(data) ? data : [];
    } catch (err) {
      availableWarehouses = [];
    } finally {
      warehousesLoaded = true;
    }

    return availableWarehouses;
  };

  const buildWarehouseOptions = (selectedWarehouseId = "") => {
    const defaultOption = availableWarehouses.length
      ? '<option value="">Select Warehouse</option>'
      : '<option value="">No warehouse available</option>';

    return `${defaultOption}${availableWarehouses
      .map(
        (warehouse) => `
          <option value="${warehouse.id}" ${warehouse.id === selectedWarehouseId ? "selected" : ""}>
            ${warehouse.name}
          </option>
        `,
      )
      .join("")}`;
  };

  const addWarehouseAllocationRow = (targetContainer, allocation = {}) => {
    if (!targetContainer) return;

    const row = document.createElement("div");
    row.className = "warehouse-allocation-row";
    row.innerHTML = `
      <select class="warehouse-select">
        ${buildWarehouseOptions(allocation.warehouse_id || "")}
      </select>
      <input
        type="number"
        class="warehouse-qty"
        placeholder="Quantity"
        min="1"
        value="${allocation.quantity || ""}"
      />
      <button type="button" class="remove-warehouse-allocation-btn">&times;</button>
    `;

    row
      .querySelector(".remove-warehouse-allocation-btn")
      ?.addEventListener("click", () => row.remove());

    targetContainer.appendChild(row);
  };

  const collectWarehouseAllocations = (targetContainer) => {
    if (!targetContainer) return [];

    return Array.from(
      targetContainer.querySelectorAll(".warehouse-allocation-row"),
    )
      .map((row) => ({
        warehouse_id: row.querySelector(".warehouse-select")?.value || "",
        quantity: Number(row.querySelector(".warehouse-qty")?.value) || 0,
      }))
      .filter(
        (allocation) => allocation.warehouse_id && allocation.quantity > 0,
      );
  };

  const renderWarehouseStockSummary = (warehouseStock = [], unit = "piece") => {
    if (!warehouseStock.length) {
      return `
        <div class="warehouse-stock-summary empty">
          <span>No warehouse stock assigned yet.</span>
        </div>
      `;
    }

    return `
      <div class="warehouse-stock-summary">
        ${warehouseStock
          .map(
            (entry) => `
              <div class="warehouse-stock-chip">
                <strong>${entry.warehouse_name || "Warehouse"}</strong>
                <span>${entry.quantity} ${unit}</span>
              </div>
            `,
          )
          .join("")}
      </div>
    `;
  };

  const renderWarehouseOrderSelector = (
    warehouseStock = [],
    selectedWarehouseId = "",
    unit = "piece",
  ) => {
    const selectableWarehouses = warehouseStock.filter(
      (entry) => Number(entry.quantity) > 0,
    );
    if (!selectableWarehouses.length) return "";

    const resolvedWarehouseId =
      selectedWarehouseId &&
      selectableWarehouses.some((w) => w.warehouse_id === selectedWarehouseId)
        ? selectedWarehouseId
        : selectableWarehouses[0].warehouse_id;

    return `
      <div class="warehouse-picker-card">
        <label for="detailWarehouseSelect" class="warehouse-picker-label">
          Choose Warehouse For Order
        </label>
        <select id="detailWarehouseSelect" class="warehouse-picker-select">
          ${selectableWarehouses
            .map(
              (entry) => `
                <option value="${entry.warehouse_id}" ${entry.warehouse_id === resolvedWarehouseId ? "selected" : ""}>
                  ${entry.warehouse_name} • ${entry.quantity} ${unit}
                </option>
              `,
            )
            .join("")}
        </select>
      </div>
    `;
  };

  const closeAllOverlays = () => {
    [
      overlay,
      deleteOverlay,
      logoutOverlay,
      profileOverlay,
      detailOverlay,
      cartOverlay,
      orderSuccessOverlay,
      ordersOverlay,
    ].forEach((ov) => ov?.classList.add("hidden"));
    if (form) form.reset();
    if (variantsContainer) variantsContainer.innerHTML = "";
    if (baseWarehouseAllocations) baseWarehouseAllocations.innerHTML = "";
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
      e.target === cartOverlay ||
      e.target === ordersOverlay ||
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
    getEl("closeCartOverlay"),
    getEl("closeOrdersOverlay"),
    getEl("cancelLogout"),
    getEl("cancelDelete"),
  ].forEach((btn) => {
    btn?.addEventListener("click", (e) => {
      e.preventDefault();
      closeAllOverlays();
    });
  });

  const updateCartUI = () => {
    localStorage.setItem(cartKey, JSON.stringify(cart));

    if (!cartItemsContainer) return;
    cartItemsContainer.innerHTML = "";
    let subtotal = 0;
    let selectedCount = 0;

    if (cart.length === 0) {
      cartItemsContainer.innerHTML = `
        <div class="empty-msg">
            <p style="text-align:center; padding: 20px; color: #94a3b8;">Your cart is empty.</p>
        </div>`;
      if (getEl("cartItemCountDisplay"))
        getEl("cartItemCountDisplay").innerText = "0 Items";
    } else {
      cart.forEach((item, index) => {
        if (item.selected) {
          subtotal += item.price * item.quantity;
          selectedCount += item.quantity;
        }

        const itemDiv = document.createElement("div");
        itemDiv.className = `cart-item ${item.selected ? "" : "item-deselected"}`;
        itemDiv.innerHTML = `
          <input type="checkbox" class="item-checkbox" data-index="${index}" ${item.selected ? "checked" : ""}>
          <img src="${item.image}" alt="${item.name}" class="cart-item-img" />
          <div class="cart-item-info">
            <h4>${item.name}</h4>
            <p class="cart-warehouse-line">${item.warehouse_name || "Warehouse not selected"}</p>
            <p>₹ ${item.price} x ${item.quantity}</p>
          </div>
          <button class="remove-cart-item" data-index="${index}">&times;</button>
        `;
        cartItemsContainer.appendChild(itemDiv);
      });
      if (getEl("cartItemCountDisplay"))
        getEl("cartItemCountDisplay").innerText =
          `${selectedCount} Total Items`;
    }

    const formattedPrice = `₹ ${subtotal}`;
    if (getEl("summarySubtotal"))
      getEl("summarySubtotal").innerText = formattedPrice;
    if (cartTotalValue) cartTotalValue.innerText = formattedPrice;
    if (cartBadge) cartBadge.innerText = cart.length;

    document.querySelectorAll(".item-checkbox").forEach((cb) => {
      cb.addEventListener("change", (e) => {
        const idx = e.target.dataset.index;
        cart[idx].selected = e.target.checked;
        updateCartUI();
      });
    });

    document.querySelectorAll(".remove-cart-item").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = e.target.dataset.index;
        cart.splice(idx, 1);
        updateCartUI();
      });
    });
  };

  if (cartBtn) {
    cartBtn.addEventListener("click", () => {
      cartOverlay?.classList.remove("hidden");
      updateCartUI();
    });
  }

  if (clearCartBtn) {
    clearCartBtn.addEventListener("click", () => {
      cart = [];
      updateCartUI();
      showToast("Cart cleared");
    });
  }

  if (placeOrderBtn) {
    placeOrderBtn.addEventListener("click", async () => {
      const selectedItems = cart.filter((i) => i.selected);
      if (selectedItems.length === 0) {
        showToast("Select items to place order!");
        return;
      }
      if (selectedItems.some((item) => !item.warehouse_id)) {
        showToast("Each cart item must have a selected warehouse");
        return;
      }

      const orderPayload = {
        customer_name: localStorage.getItem("user_name") || userName,
        items: selectedItems.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
          variant_sku: item.sku || null,
          warehouse_id: item.warehouse_id || null,
        })),
      };

      try {
        const res = await fetch("/api/v1/orders/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(orderPayload),
        });

        if (!res.ok) {
          const errData = await res.json();
          console.error("Backend Error Details:", errData);
          throw new Error("Failed to save order");
        }

        const savedOrder = await res.json();

        cartOverlay?.classList.add("hidden");
        orderSuccessOverlay?.classList.remove("hidden");
        getEl("processingState")?.classList.remove("hidden");
        getEl("successState")?.classList.add("hidden");

        setTimeout(() => {
          getEl("processingState")?.classList.add("hidden");
          getEl("successState")?.classList.remove("hidden");

          if (getEl("transactionId"))
            getEl("transactionId").innerText = `#${savedOrder.id}`;

          cart = cart.filter((i) => !i.selected);
          updateCartUI();

          let count = 5;
          const countdownEl = getEl("countdown");
          const timer = setInterval(() => {
            count--;
            if (countdownEl) countdownEl.innerText = count;
            if (count <= 0) {
              clearInterval(timer);
              window.location.reload();
            }
          }, 1000);
        }, 2000);
      } catch (err) {
        showToast("Database update failed ❌");
      }
    });
  }

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
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_name");
      localStorage.removeItem("user_role");
      localStorage.removeItem("user_email");
      localStorage.removeItem("company_name");
      localStorage.removeItem("contact_name");
      localStorage.removeItem("phone_number");
      localStorage.removeItem("gst_number");
      localStorage.removeItem("address");
      localStorage.removeItem("payment_term");
      localStorage.removeItem("business_email");
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

    div.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 12px; width: 100%;">
        <div style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap;">
            <input type="text" class="v-name" placeholder="Variant Name" value="${variant.name || ""}" required />
            <input type="number" class="v-price" placeholder="Price" value="${priceVal}" required />
            <button type="button" class="remove-variant-btn">&times;</button>
        </div>
        <input type="file" class="v-image" accept="image/*" />
        ${variant.image ? `<small style="color: #38bdf8; font-size: 10px;">Current: ${variant.image.split("/").pop()}</small>` : ""}
        <div class="warehouse-allocation-block compact">
          <div class="warehouse-allocation-header">
            <label>Variant Warehouse Stock</label>
            <button type="button" class="add-variant-allocation-btn add-variant-btn">
              + Add Warehouse Stock
            </button>
          </div>
          <div class="variant-warehouse-allocations"></div>
        </div>
      </div>
    `;
    div
      .querySelector(".remove-variant-btn")
      .addEventListener("click", () => div.remove());

    const variantAllocationsContainer = div.querySelector(
      ".variant-warehouse-allocations",
    );
    div
      .querySelector(".add-variant-allocation-btn")
      ?.addEventListener("click", () =>
        addWarehouseAllocationRow(variantAllocationsContainer),
      );
    addWarehouseAllocationRow(variantAllocationsContainer);

    variantsContainer.appendChild(div);
  };

  if (addVariantBtn) {
    addVariantBtn.addEventListener("click", () => createVariantInput());
  }

  if (addBaseAllocationBtn) {
    addBaseAllocationBtn.addEventListener("click", () =>
      addWarehouseAllocationRow(baseWarehouseAllocations),
    );
  }

  const openOverlay = async (mode = "add", product = null) => {
    if (!overlay || userRole !== "supplier") return;
    await fetchWarehousesForProductForm();
    overlay.classList.remove("hidden");
    if (variantsContainer) variantsContainer.innerHTML = "";
    if (baseWarehouseAllocations) {
      baseWarehouseAllocations.innerHTML = "";
      addWarehouseAllocationRow(baseWarehouseAllocations);
    }

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

  const renderVariantDetails = (p, index, selectedWarehouseId = "") => {
    const isBase = index === -1;
    const variantData = isBase ? null : p.variants[index];

    const displayPrice = isBase
      ? p.selling_price
      : variantData.additional_price || p.selling_price;
    const displayStock = isBase
      ? (p.base_stock ?? p.stock ?? 0)
      : (variantData.stock ?? variantData.reorder_level ?? 0);
    const displayTitle = isBase ? p.name : `${p.name} (${variantData.name})`;
    const displayImg =
      !isBase && variantData.image
        ? variantData.image
        : p.image || "https://via.placeholder.com/300";
    const displaySKU = isBase ? null : variantData.sku || variantData.name;
    const warehouseStock = isBase
      ? p.warehouse_stock || []
      : variantData.warehouse_stock || [];
    const orderWarehouses = warehouseStock.filter(
      (entry) => Number(entry.quantity) > 0,
    );
    const resolvedWarehouse =
      orderWarehouses.find(
        (entry) => entry.warehouse_id === selectedWarehouseId,
      ) ||
      orderWarehouses[0] ||
      null;
    const selectedWarehouseQty = resolvedWarehouse?.quantity || 0;
    const selectedWarehouseIdValue = resolvedWarehouse?.warehouse_id || "";

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

    const currentRole = (
      localStorage.getItem("user_role") || userRole
    ).toLowerCase();

    let managementHtml = "";
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

    const canBuy = currentRole === "viewer";
    const isOutOfStock = displayStock <= 0 || !resolvedWarehouse;
    const purchaseHtml = canBuy
      ? `
      ${renderWarehouseOrderSelector(orderWarehouses, selectedWarehouseIdValue, p.unit || "piece")}
      <div class="product-actions">
          <div class="qty-control">
              <button id="qtyMinus" class="qty-btn" type="button">−</button>
              <input type="number" id="purchaseQty" value="${isOutOfStock ? 0 : 1}" min="1" max="${selectedWarehouseQty}" readonly />
              <button id="qtyPlus" class="qty-btn" type="button">+</button>
          </div>
          <button class="add-to-cart-premium" id="addToCartActionBtn" ${isOutOfStock ? "disabled" : ""}>
              <span class="icon">🛒</span>
              <span class="text">${isOutOfStock ? "Out of Stock" : "Add to Cart"}</span>
          </button>
      </div>`
      : "";

    detailBody.innerHTML = `
      <div class="detail-grid">
        <div class="detail-img-box">
          <img src="${displayImg}" id="detailMainImg" />
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
          ${purchaseHtml}
        </div>
      </div>
      <div class="detail-footer">
        ${supplierHtml}
        ${managementHtml}
      </div>
    `;

    if (canBuy) {
      const qtyInput = getEl("purchaseQty");
      getEl("detailWarehouseSelect")?.addEventListener("change", (e) => {
        renderVariantDetails(p, index, e.target.value);
      });
      getEl("qtyPlus")?.addEventListener("click", () => {
        if (parseInt(qtyInput.value) < selectedWarehouseQty)
          qtyInput.value = parseInt(qtyInput.value) + 1;
      });
      getEl("qtyMinus")?.addEventListener("click", () => {
        if (parseInt(qtyInput.value) > 1)
          qtyInput.value = parseInt(qtyInput.value) - 1;
      });

      getEl("addToCartActionBtn")?.addEventListener("click", () => {
        if (displayStock <= 0) {
          showToast("This item is out of stock in all warehouses");
          return;
        }
        if (!resolvedWarehouse) {
          showToast("Select a warehouse before adding to cart");
          return;
        }

        const qty = parseInt(qtyInput.value);
        const existingItem = cart.find(
          (i) =>
            i.id === (p._id || p.id) &&
            i.name === displayTitle &&
            i.warehouse_id === selectedWarehouseIdValue,
        );

        if (existingItem) {
          if (existingItem.quantity + qty > selectedWarehouseQty) {
            showToast("Requested quantity exceeds selected warehouse stock");
            return;
          }
          existingItem.quantity += qty;
        } else {
          cart.push({
            id: p._id || p.id,
            name: displayTitle,
            price: displayPrice,
            image: displayImg,
            quantity: qty,
            sku: displaySKU,
            warehouse_id: selectedWarehouseIdValue,
            warehouse_name: resolvedWarehouse.warehouse_name,
            selected: true,
          });
        }
        updateCartUI();
        showToast(`Added ${qty} item(s) to Cart! 🛒`);
      });
    }

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
      const warehouseAllocations = collectWarehouseAllocations(
        baseWarehouseAllocations,
      );

      document.querySelectorAll(".variant-item").forEach((item) => {
        variants.push({
          name: item.querySelector(".v-name").value,
          additional_price: Number(item.querySelector(".v-price").value) || 0,
          image: item.dataset.existingImage || "",
          warehouse_allocations: collectWarehouseAllocations(
            item.querySelector(".variant-warehouse-allocations"),
          ),
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
        reorder_level: 0,
        tax: Number(getVal("tax")),
        unit: getVal("unit"),
        variants: JSON.stringify(variants),
        warehouse_allocations: JSON.stringify(warehouseAllocations),
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
      card.innerHTML = `
        <div class="img-box"><img src="${p.image || "https://via.placeholder.com/300"}" /></div>
        <div class="card-body">
          <h3>${p.name}</h3>
          <p>${p.description || ""}</p>
          <div class="meta"><span class="price">₹ ${p.selling_price}</span><span class="qty">Stock: ${p.reorder_level}</span></div>
          <p class="extra">${p.brand || "Generic"} • ${p.category || "Uncategorized"}</p>
        </div>`;
      const stockLabel = card.querySelector(".qty");
      if (stockLabel) stockLabel.innerText = `Stock: ${p.stock || 0}`;

      const cardBody = card.querySelector(".card-body");
      if (cardBody) {
        const stockPreview = document.createElement("div");
        stockPreview.className = "warehouse-stock-preview";
        stockPreview.innerHTML = renderWarehouseStockSummary(
          p.warehouse_stock || [],
          p.unit || "piece",
        );
        cardBody.appendChild(stockPreview);
      }
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

  const handleConfirmOrder = async (orderId) => {
    try {
      const res = await fetch(`/api/v1/orders/${orderId}/confirm`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        showToast("Order confirmed! ✅");
        loadAllOrders();
      } else {
        showToast("Failed to confirm order.");
      }
    } catch (err) {
      showToast("Server error during confirmation.");
    }
  };

  const handleCancelOrder = async (orderId) => {
    try {
      const res = await fetch(`/api/v1/orders/${orderId}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        showToast("Order cancelled! ❌");
        loadAllOrders();
      } else {
        showToast("Failed to cancel order.");
      }
    } catch (err) {
      showToast("Server error during cancellation.");
    }
  };

  const loadAllOrders = async () => {
    if (!ordersMasterContainer) return;

    ordersMasterContainer.innerHTML =
      '<div class="loading-state">Fetching latest orders...</div>';

    try {
      const res = await fetch("/api/v1/orders/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      let orders = await res.json();

      const dRole = (
        localStorage.getItem("user_role") || userRole
      ).toLowerCase();
      const dName = localStorage.getItem("user_name") || userName;

      if (dRole === "viewer") {
        orders = orders.filter((o) => o.customer_name === dName);
      }

      if (totalOrdersBadge)
        totalOrdersBadge.innerText = `${orders.length} Total Orders`;

      if (!orders || orders.length === 0) {
        ordersMasterContainer.innerHTML =
          '<p class="empty-msg">No customer orders found.</p>';
        return;
      }

      ordersMasterContainer.innerHTML = "";
      orders.forEach((order) => {
        const card = document.createElement("div");
        card.className = "order-card";

        let orderTotal = 0;
        const itemsHtml = order.items
          .map((item) => {
            const productRef = allProducts.find(
              (p) => (p._id || p.id) === item.product_id,
            );

            // Defaults
            let imgUrl = productRef
              ? productRef.image
              : "https://via.placeholder.com/100";
            let pName = productRef
              ? productRef.name
              : `Product ID: ${item.product_id}`;
            let pPrice = productRef ? productRef.selling_price : 0;
            let variantDisplay = item.variant_sku
              ? `SKU: ${item.variant_sku}`
              : "Standard";

            if (productRef && productRef.variants && item.variant_sku) {
              const variantMatch = productRef.variants.find(
                (v) => v.sku === item.variant_sku,
              );
              if (variantMatch) {
                imgUrl = variantMatch.image || imgUrl;

                pPrice = variantMatch.additional_price || pPrice;
                pName = `${productRef.name} (${variantMatch.name})`;
                variantDisplay = "Selected Variant";
              }
            }

            orderTotal += pPrice * item.quantity;

            return `
            <div class="order-item-row">
              <img src="${imgUrl}" alt="Product" class="order-item-img" />
              <div class="item-details">
                <p class="item-name" style="font-weight: 600; color: #f8fafc;">${pName}</p>
                <p class="item-meta" style="font-size: 12px; color: #94a3b8;">
                  Qty: ${item.quantity} | <span class="variant-label">${variantDisplay}</span>
                </p>
              </div>
            </div>
          `;
          })
          .join("");

        let actionBtnHtml = "";
        const isPending =
          (order.status || "pending").toLowerCase() === "pending";

        if (isPending) {
          if (dRole === "admin") {
            actionBtnHtml = `<button class="btn confirm-order-btn" style="background: #22c55e; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;" data-id="${order.id}">Confirm Order</button>`;
          } else if (dRole === "viewer") {
            actionBtnHtml = `<button class="btn cancel-order-btn" style="background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;" data-id="${order.id}">Cancel Order</button>`;
          }
        }

        card.innerHTML = `
          <div class="order-card-header" style="display: flex; justify-content: space-between; padding-bottom: 10px; border-bottom: 1px solid #334155;">
            <div class="user-info">
              <strong>Customer:</strong> <span class="cust-name">${order.customer_name || "Guest"}</span> 
            </div>
            <span class="order-id" style="color: #38bdf8;">#ORD-${order.id.slice(-6).toUpperCase()}</span>
          </div>
          <div class="order-items-list" style="margin: 15px 0;">
            ${itemsHtml}
          </div>
          <div class="order-card-footer" style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #334155; padding-top: 10px;">
            <div class="order-total" style="font-weight: bold;">Total: <span style="color: #22c55e;">₹ ${orderTotal}</span></div>
            <div style="display: flex; gap: 10px; align-items: center;">
              ${actionBtnHtml}
              <div class="status-pill status-${(order.status || "pending").toLowerCase()}">${order.status || "Pending"}</div>
            </div>
          </div>
        `;

        const cBtn = card.querySelector(".confirm-order-btn");
        if (cBtn)
          cBtn.addEventListener("click", () => handleConfirmOrder(order.id));

        const xBtn = card.querySelector(".cancel-order-btn");
        if (xBtn)
          xBtn.addEventListener("click", () => handleCancelOrder(order.id));

        ordersMasterContainer.appendChild(card);
      });
    } catch (err) {
      console.error("Order Load Error:", err);
      ordersMasterContainer.innerHTML =
        '<p class="error-msg">Failed to load orders. Please try again.</p>';
    }
  };

  if (adminOrdersBtn) {
    adminOrdersBtn.addEventListener("click", () => {
      ordersOverlay?.classList.remove("hidden");
      loadAllOrders();
    });
  }

  fetchUserData().then(() => {
    loadProducts();
    updateCartUI();
    if (userRole === "supplier") fetchWarehousesForProductForm();
  });
});
