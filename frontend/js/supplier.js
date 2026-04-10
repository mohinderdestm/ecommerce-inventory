// ============ SUPPLIER STATE ============

let supplierCurrentPage = 1;
let supplierTotalPages = 1;
let editingSupplierId = null;
let viewingSupplierId = null;
let currentSupplierDetailTab = 'info';


// ============ LOAD SUPPLIERS ============

async function loadSuppliers(page = 1) {
  const list = document.getElementById("supplierList");
  const emptyState = document.getElementById("supplierEmptyState");
  supplierCurrentPage = page;

  try {
    // Show loading
    list.innerHTML = `
      <div class="loading-card"></div>
      <div class="loading-card"></div>
      <div class="loading-card"></div>
    `;
    emptyState.style.display = "none";

    const statusFilter = document.getElementById("supplierStatusFilter").value;
    let endpoint = `/suppliers/?page=${page}&limit=12`;
    if (statusFilter) endpoint += `&status=${statusFilter}`;

    const data = await apiRequest(endpoint);
    const suppliers = data.suppliers || [];
    supplierTotalPages = Math.ceil((data.total || 0) / 12);

    // Update stats
    updateSupplierStats(data);

    if (suppliers.length === 0) {
      list.innerHTML = "";
      emptyState.style.display = "flex";
      document.getElementById("supplierPagination").innerHTML = "";
      return;
    }

    renderSuppliers(suppliers);
    renderSupplierPagination();

  } catch (err) {
    list.innerHTML = `<p class="error">Failed to load suppliers</p>`;
    console.error("Load suppliers error:", err);
  }
}


// ============ RENDER SUPPLIERS ============

function renderSuppliers(suppliers) {
  const list = document.getElementById("supplierList");
  const isAdmin = currentUser.role === 'admin';

  list.innerHTML = `
    <div class="supplier-grid">
      ${suppliers.map(s => {
        const statusClass = {
          active: 'status-active',
          inactive: 'status-inactive',
          blacklisted: 'status-out'
        }[s.status] || 'status-inactive';

        const ratingStars = renderStars(s.rating || 0);

        return `
          <div class="supplier-card" onclick="viewSupplier('${s.id}')">
            
            <div class="supplier-card-header">
              <div class="supplier-avatar">
                ${s.name.charAt(0).toUpperCase()}
              </div>
              <div class="supplier-card-title">
                <h4>${s.name}</h4>
                <span class="status-badge ${statusClass}">${s.status}</span>
              </div>
            </div>

            <div class="supplier-card-body">
              ${s.contact_person ? `
                <div class="supplier-info-row">
                  <span>👤</span>
                  <span>${s.contact_person}</span>
                </div>
              ` : ''}

              ${s.phone ? `
                <div class="supplier-info-row">
                  <span>📞</span>
                  <span>${s.phone}</span>
                </div>
              ` : ''}

              ${s.email ? `
                <div class="supplier-info-row">
                  <span>📧</span>
                  <span>${s.email}</span>
                </div>
              ` : ''}

              ${currentUser.role === 'admin' ? `
                <div class="supplier-info-row">
                  <span>💳</span>
                  <span>${s.payment_terms || 'Net 30'}</span>
                </div>
              ` : ''}

              ${s.gst_id ? `
                <div class="supplier-info-row">
                  <span>🏷️</span>
                  <span>GST: ${s.gst_id}</span>
                </div>
              ` : ''}

              <div class="supplier-rating">
                ${ratingStars}
                <span>(${s.rating || 0}/5)</span>
              </div>
            </div>

            ${isAdmin ? `
              <div class="supplier-card-actions" onclick="event.stopPropagation()">
                <button 
                  onclick="openRatingModal('${s.id}', '${s.name}', ${s.rating || 0})" 
                  title="Update Rating"
                >
                  ⭐
                </button>
                <button 
                  onclick="editSupplier('${s.id}')" 
                  title="Edit"
                >
                  ✏️
                </button>
                <button 
                  onclick="deleteSupplier('${s.id}')" 
                  class="btn-delete" 
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            ` : ''}

          </div>
        `;
      }).join('')}
    </div>
  `;
}


// ============ SUPPLIER STATS ============

function updateSupplierStats(data) {
  const suppliers = data.suppliers || [];

  document.getElementById("totalSuppliers").innerText = data.total || 0;

  const active = suppliers.filter(s => s.status === 'active').length;
  const inactive = suppliers.filter(s => s.status === 'inactive').length;
  const blacklisted = suppliers.filter(s => s.status === 'blacklisted').length;

  document.getElementById("activeSuppliers").innerText = active;
  document.getElementById("inactiveSuppliers").innerText = inactive;
  document.getElementById("blacklistedSuppliers").innerText = blacklisted;
}


// ============ SUPPLIER PAGINATION ============

function renderSupplierPagination() {
  const container = document.getElementById("supplierPagination");

  if (supplierTotalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = '';
  html += `
    <button 
      ${supplierCurrentPage === 1 ? 'disabled' : ''} 
      onclick="loadSuppliers(${supplierCurrentPage - 1})"
    >←</button>
  `;

  for (let i = 1; i <= supplierTotalPages; i++) {
    if (
      i === 1 || 
      i === supplierTotalPages || 
      (i >= supplierCurrentPage - 2 && i <= supplierCurrentPage + 2)
    ) {
      html += `
        <button 
          class="${i === supplierCurrentPage ? 'active' : ''}" 
          onclick="loadSuppliers(${i})"
        >${i}</button>
      `;
    } else if (i === supplierCurrentPage - 3 || i === supplierCurrentPage + 3) {
      html += `<span>...</span>`;
    }
  }

  html += `
    <button 
      ${supplierCurrentPage === supplierTotalPages ? 'disabled' : ''} 
      onclick="loadSuppliers(${supplierCurrentPage + 1})"
    >→</button>
  `;

  container.innerHTML = html;
}


// ============ SUPPLIER MODAL (ADD/EDIT) ============

function openSupplierModal(supplierId = null) {
  if (currentUser.role !== 'admin') {
    alert("Only admin can manage suppliers");
    return;
  }

  editingSupplierId = supplierId;

  document.getElementById("supplierModalTitle").innerText = 
    supplierId ? "Edit Supplier" : "Add New Supplier";

  // Reset form
  document.getElementById("supplierForm").reset();
  document.getElementById("supplierId").value = "";

  // Show status only when editing
  document.getElementById("sStatusGroup").style.display = 
    supplierId ? "block" : "none";

  if (supplierId) {
    loadSupplierForEdit(supplierId);
  }

  document.getElementById("supplierModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeSupplierModal() {
  document.getElementById("supplierModal").classList.remove("active");
  document.body.style.overflow = "auto";
  editingSupplierId = null;
}

async function loadSupplierForEdit(id) {
  try {
    const s = await apiRequest(`/suppliers/${id}`);

    document.getElementById("supplierId").value = s.id;
    document.getElementById("sName").value = s.name || '';
    document.getElementById("sContactPerson").value = s.contact_person || '';
    document.getElementById("sPhone").value = s.phone || '';
    document.getElementById("sEmail").value = s.email || '';
    document.getElementById("sGstId").value = s.gst_id || '';
    document.getElementById("sPaymentTerms").value = s.payment_terms || 'Net 30';
    document.getElementById("sStatus").value = s.status || 'active';
    document.getElementById("sAddress").value = s.address || '';

  } catch (err) {
    alert("Failed to load supplier details");
    closeSupplierModal();
  }
}

async function saveSupplier() {
  const name = document.getElementById("sName").value.trim();

  if (!name) {
    alert("Please enter supplier name");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("contact_person", document.getElementById("sContactPerson").value.trim());
  formData.append("phone", document.getElementById("sPhone").value.trim());
  formData.append("email", document.getElementById("sEmail").value.trim());
  formData.append("address", document.getElementById("sAddress").value.trim());
  formData.append("gst_id", document.getElementById("sGstId").value.trim());
  formData.append("payment_terms", document.getElementById("sPaymentTerms").value);

  if (editingSupplierId) {
    formData.append("status", document.getElementById("sStatus").value);
  }

  const token = localStorage.getItem("token");

  try {
    const url = editingSupplierId 
      ? `/suppliers/${editingSupplierId}` 
      : "/suppliers/";

    const method = editingSupplierId ? "PUT" : "POST";

    const response = await fetch(url, {
      method,
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save supplier");
    }

    closeSupplierModal();
    await loadSuppliers(supplierCurrentPage);
    alert(editingSupplierId ? "Supplier updated!" : "Supplier created!");

  } catch (err) {
    alert(err.message);
  }
}

function editSupplier(id) {
  openSupplierModal(id);
}

async function deleteSupplier(id) {
  if (currentUser.role !== 'admin') {
    alert("Only admin can delete suppliers");
    return;
  }

  if (!confirm("Are you sure you want to delete this supplier?")) return;

  try {
    await apiRequest(`/suppliers/${id}`, "DELETE");
    await loadSuppliers(supplierCurrentPage);
    alert("Supplier deleted!");
  } catch (err) {
    alert(err.message);
  }
}


// ============ VIEW SUPPLIER MODAL ============

async function viewSupplier(id) {
  viewingSupplierId = id;
  currentSupplierDetailTab = 'info';

  // Reset tabs
  document.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
  document.getElementById("infoTab").classList.add('active');

  document.querySelectorAll('.supplier-detail-panel').forEach(p => p.classList.remove('active'));
  document.getElementById("supplierInfoContent").classList.add('active');

  // Show/hide edit button for admin
  const editBtn = document.getElementById("editSupplierBtn");
  editBtn.style.display = currentUser.role === 'admin' ? 'inline-block' : 'none';

  document.getElementById("viewSupplierModal").classList.add("active");
  document.body.style.overflow = "hidden";

  await loadSupplierInfo(id);
}

function closeViewSupplierModal() {
  document.getElementById("viewSupplierModal").classList.remove("active");
  document.body.style.overflow = "auto";
  viewingSupplierId = null;
}

function editCurrentSupplier() {
  closeViewSupplierModal();
  editSupplier(viewingSupplierId);
}

function switchSupplierDetailTab(tab) {
  currentSupplierDetailTab = tab;

  // Update tab buttons
  document.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(`${tab}Tab`).classList.add('active');

  // Update panels
  document.querySelectorAll('.supplier-detail-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`supplier${tab.charAt(0).toUpperCase() + tab.slice(1)}Content`).classList.add('active');

  // Load content
  if (tab === 'products') loadSupplierProducts(viewingSupplierId);
  if (tab === 'performance') loadSupplierPerformance(viewingSupplierId);
}

async function loadSupplierInfo(id) {
  const container = document.getElementById("supplierInfoContent");
  container.innerHTML = '<div class="loading-card"></div>';

  try {
    const s = await apiRequest(`/suppliers/${id}`);

    container.innerHTML = `
      <div class="supplier-detail">

        <div class="supplier-detail-header">
          <div class="supplier-avatar large">
            ${s.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2>${s.name}</h2>
            <span class="status-badge ${getStatusClass(s.status)}">${s.status}</span>
            <div class="supplier-rating">
              ${renderStars(s.rating || 0)}
              <span>(${s.rating || 0}/5)</span>
            </div>
          </div>
        </div>

        <div class="detail-grid">
          ${s.contact_person ? `
            <div class="detail-item">
              <span class="label">👤 Contact Person</span>
              <span>${s.contact_person}</span>
            </div>
          ` : ''}

          ${s.phone ? `
            <div class="detail-item">
              <span class="label">📞 Phone</span>
              <span>${s.phone}</span>
            </div>
          ` : ''}

          ${s.email ? `
            <div class="detail-item">
              <span class="label">📧 Email</span>
              <span>${s.email}</span>
            </div>
          ` : ''}

          ${currentUser.role === 'admin' ? `
            <div class="detail-item">
              <span class="label">💳 Payment Terms</span>
              <span>${s.payment_terms || 'Net 30'}</span>
            </div>
          ` : ''}

          ${s.gst_id ? `
            <div class="detail-item">
              <span class="label">🏷️ GST ID</span>
              <span>${s.gst_id}</span>
            </div>
          ` : ''}

          ${s.address ? `
            <div class="detail-item full-width">
              <span class="label">📍 Address</span>
              <span>${s.address}</span>
            </div>
          ` : ''}

          <div class="detail-item">
            <span class="label">📅 Created</span>
            <span>${new Date(s.created_at).toLocaleDateString()}</span>
          </div>

          <div class="detail-item">
            <span class="label">🔄 Updated</span>
            <span>${new Date(s.updated_at).toLocaleDateString()}</span>
          </div>
        </div>

      </div>
    `;

  } catch (err) {
    container.innerHTML = `<p class="error">Failed to load supplier details</p>`;
  }
}

async function loadSupplierProducts(id) {
  const container = document.getElementById("supplierProductsContent");
  container.innerHTML = '<div class="loading-card"></div>';

  try {
    const data = await apiRequest(`/suppliers/${id}/products`);
    const products = data.products || [];

    if (products.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span>📦</span>
          <p>No products linked to this supplier</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="supplier-products-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>SKU</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${products.map(p => `
            <tr>
              <td>
                <div class="product-cell">
                  <img 
                    src="${p.image_url || '/static/images/placeholder.png'}" 
                    alt="${p.name}"
                    onerror="this.src='/static/images/placeholder.png'"
                  >
                  <span>${p.name}</span>
                </div>
              </td>
              <td>${p.sku}</td>
              <td>₹${parseFloat(p.selling_price).toLocaleString('en-IN')}</td>
              <td>${p.quantity} ${p.unit}</td>
              <td>
                <span class="status-badge ${getStatusClass(p.status)}">
                  ${p.status}
                </span>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

  } catch (err) {
    container.innerHTML = `<p class="error">Failed to load supplier products</p>`;
  }
}

async function loadSupplierPerformance(id) {
  const container = document.getElementById("supplierPerformanceContent");
  container.innerHTML = '<div class="loading-card"></div>';

  try {
    const perf = await apiRequest(`/suppliers/${id}/performance`);

    container.innerHTML = `
      <div class="performance-grid">

        <div class="perf-card">
          <span class="perf-icon">📦</span>
          <span class="perf-value">${perf.total_products || 0}</span>
          <span class="perf-label">Total Products</span>
        </div>

        <div class="perf-card">
          <span class="perf-icon">✅</span>
          <span class="perf-value">${perf.active_products || 0}</span>
          <span class="perf-label">Active Products</span>
        </div>

        <div class="perf-card">
          <span class="perf-icon">⚠️</span>
          <span class="perf-value">${perf.low_stock_products || 0}</span>
          <span class="perf-label">Low Stock</span>
        </div>

        <div class="perf-card">
          <span class="perf-icon">❌</span>
          <span class="perf-value">${perf.out_of_stock_products || 0}</span>
          <span class="perf-label">Out of Stock</span>
        </div>

        <div class="perf-card">
          <span class="perf-icon">⭐</span>
          <span class="perf-value">${perf.rating || 0}/5</span>
          <span class="perf-label">Rating</span>
        </div>

        <div class="perf-card">
          <span class="perf-icon">💰</span>
          <span class="perf-value">
            ₹${parseFloat(perf.total_inventory_value || 0).toLocaleString('en-IN')}
          </span>
          <span class="perf-label">Inventory Value</span>
        </div>

      </div>
    `;

  } catch (err) {
    container.innerHTML = `<p class="error">Failed to load performance data</p>`;
  }
}


// ============ SEARCH ============

function handleSupplierSearch(event) {
  if (event.key === 'Enter') searchSuppliers();
}

async function searchSuppliers() {
  const query = document.getElementById("supplierSearchInput").value.trim();

  if (!query) {
    loadSuppliers();
    return;
  }

  const list = document.getElementById("supplierList");

  try {
    list.innerHTML = '<div class="loading-card"></div>';

    const data = await apiRequest(
      `/suppliers/search?q=${encodeURIComponent(query)}`
    );
    const suppliers = data.suppliers || [];

    if (suppliers.length === 0) {
      list.innerHTML = `
        <p class="no-results">No suppliers found for "${query}"</p>
      `;
      document.getElementById("supplierPagination").innerHTML = "";
      return;
    }

    renderSuppliers(suppliers);
    document.getElementById("supplierPagination").innerHTML = "";

  } catch (err) {
    list.innerHTML = `<p class="error">Search failed</p>`;
  }
}

function clearSupplierSearch() {
  document.getElementById("supplierSearchInput").value = "";
  document.getElementById("supplierStatusFilter").value = "";
  loadSuppliers();
}

function filterSuppliers() {
  loadSuppliers(1);
}


// ============ RATING MODAL ============

function openRatingModal(id, name, currentRating) {
  document.getElementById("ratingSupplierId").value = id;
  document.getElementById("ratingSupplierName").innerText = `Supplier: ${name}`;
  document.getElementById("selectedRating").value = currentRating;
  document.getElementById("selectedRatingDisplay").innerText = currentRating;

  // Highlight existing rating
  updateStarDisplay(currentRating);

  document.getElementById("ratingModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeRatingModal() {
  document.getElementById("ratingModal").classList.remove("active");
  document.body.style.overflow = "auto";
}

function setRating(value) {
  document.getElementById("selectedRating").value = value;
  document.getElementById("selectedRatingDisplay").innerText = value;
  updateStarDisplay(value);
}

function updateStarDisplay(value) {
  document.querySelectorAll('#ratingStars .star').forEach(star => {
    const starValue = parseInt(star.dataset.value);
    star.classList.toggle('active', starValue <= value);
  });
}

async function submitRating() {
  const id = document.getElementById("ratingSupplierId").value;
  const rating = document.getElementById("selectedRating").value;

  if (!rating || rating == 0) {
    alert("Please select a rating");
    return;
  }

  const formData = new FormData();
  formData.append("rating", rating);

  const token = localStorage.getItem("token");

  try {
    const response = await fetch(`/suppliers/${id}/rating`, {
      method: "PATCH",
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to update rating");
    }

    closeRatingModal();
    await loadSuppliers(supplierCurrentPage);
    alert("Rating updated!");

  } catch (err) {
    alert(err.message);
  }
}


// ============ HELPERS ============

function renderStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    stars += `<span class="star ${i <= rating ? 'active' : ''}">★</span>`;
  }
  return stars;
}

function getStatusClass(status) {
  const map = {
    active: 'status-active',
    inactive: 'status-inactive',
    blacklisted: 'status-out',
    out_of_stock: 'status-out'
  };
  return map[status] || 'status-inactive';
}