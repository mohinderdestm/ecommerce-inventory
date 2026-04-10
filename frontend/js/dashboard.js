// ============ GLOBAL STATE ============
let currentPage = 1;
let totalPages = 1;
let currentTab = 'products';
let categories = [];
let editingProductId = null;
let editingCategoryId = null;

// ✅ USER STATE
let currentUser = {
  user_id: null,
  name: null,
  role: null
};

// ============ INIT ============
(async function init() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "/";
    return;
  }

  await loadUserInfo();
  await loadCategories();
  await loadProducts();
  await loadStats();
  setupEventListeners();
  applyRoleBasedUI();
})();


// ============ ROLE-BASED UI ============
function applyRoleBasedUI() {
  const role = currentUser.role;
  const addProductBtn = document.querySelector('.header-actions .btn-primary');
  const lowStockNav = document.querySelector('[data-tab="low-stock"]');
  const addSupplierBtn = document.getElementById('addSupplierBtn');

  if (role === 'user') {
    if (addProductBtn) addProductBtn.style.display = 'none';
    if (lowStockNav) lowStockNav.style.display = 'none';
    if (addSupplierBtn) addSupplierBtn.style.display = 'none';

    document.querySelectorAll('.section-header .btn-primary').forEach(btn => {
      if (btn.textContent.includes('Category')) {
        btn.style.display = 'none';
      }
    });
  }

  if (role === 'supplier') {
    if (addSupplierBtn) addSupplierBtn.style.display = 'none';

    document.querySelectorAll('.section-header .btn-primary').forEach(btn => {
      if (btn.textContent.includes('Category')) {
        btn.style.display = 'none';
      }
    });
  }
}


// ============ PERMISSIONS ============
function canEditProduct(product) {
  if (currentUser.role === 'admin') return true;
  if (currentUser.role === 'supplier' && product.created_by === currentUser.user_id) return true;
  return false;
}

function canDeleteProduct() {
  return currentUser.role === 'admin';
}

function canAddProduct() {
  return currentUser.role === 'admin' || currentUser.role === 'supplier';
}

function canManageCategories() {
  return currentUser.role === 'admin';
}


// ============ AUTH ============
function logout() {
  localStorage.removeItem("token");
  window.location.replace("/");
}

async function loadUserInfo() {
  try {
    const data = await apiRequest("/auth/me");

    currentUser = {
      user_id: data.user.user_id,
      name: data.user.name,
      role: data.user.role
    };

    document.getElementById("userName").innerText = data.user.name || 'User';
    document.getElementById("userRole").innerText = data.user.role || 'user';
    document.body.classList.add(`role-${data.user.role}`);

  } catch (err) {
    console.error(err);
    logout();
  }
}

// ============ EVENT LISTENERS ============
function setupEventListeners() {
  // Tab navigation
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(item.dataset.tab);
    });
  });

  // Search on Enter
  document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchProducts();
  });

  // Image preview for product
  document.getElementById('pImage').addEventListener('change', function(e) {
    previewImage(e, 'imagePreview');
  });

  // Image preview for category
  document.getElementById('cImage').addEventListener('change', function(e) {
    previewImage(e, 'categoryImagePreview');
  });

  // Category change - load subcategories
  document.getElementById('pCategory').addEventListener('change', function() {
    loadSubcategories(this.value);
  });

  // Price change - calculate profit
  document.getElementById('pCostPrice').addEventListener('input', calculateProfit);
  document.getElementById('pSellingPrice').addEventListener('input', calculateProfit);

  // Close modals on outside click
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.remove('active');
        document.body.style.overflow = 'auto';
      }
    });
  });
}

// ============ TAB NAVIGATION ============
function switchTab(tab) {
  currentTab = tab;

  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.tab === tab) item.classList.add('active');
  });

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(tab + 'Tab').classList.add('active');

  if (tab === 'products') loadProducts();
  if (tab === 'categories') loadCategoryList();
  if (tab === 'low-stock') loadLowStock();
  if (tab === 'suppliers') loadSuppliers();
}

// ============ STATS ============
async function loadStats() {
  try {
    const data = await apiRequest("/products/?page=1&limit=100");
    const products = data.products || [];

    document.getElementById("totalProducts").innerText = data.total || 0;

    const active = products.filter(p => p.status === 'active').length;
    document.getElementById("activeProducts").innerText = active;

    const lowStock = products.filter(p => p.quantity <= p.reorder_level && p.quantity > 0).length;
    document.getElementById("lowStockCount").innerText = lowStock;

    const outOfStock = products.filter(p => p.quantity === 0 || p.status === 'out_of_stock').length;
    document.getElementById("outOfStockCount").innerText = outOfStock;

  } catch (err) {
    console.error("Stats error:", err);
  }
}

// ============ CATEGORIES ============
async function loadCategories() {
  try {
    categories = await apiRequest("/categories/");
    populateCategoryDropdowns();
  } catch (err) {
    console.error(err);
  }
}

function populateCategoryDropdowns() {
  const filterSelect = document.getElementById("filterCategory");
  const productSelect = document.getElementById("pCategory");
  const parentSelect = document.getElementById("cParent");

  filterSelect.innerHTML = '<option value="">All Categories</option>';
  productSelect.innerHTML = '<option value="">Select Category</option>';
  parentSelect.innerHTML = '<option value="">None (This is a main category)</option>';

  categories.forEach(cat => {
    filterSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
    productSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
    parentSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
  });
}

async function loadSubcategories(categoryId) {
  const subSelect = document.getElementById("pSubcategory");
  subSelect.innerHTML = '<option value="">Select Subcategory</option>';

  if (!categoryId) return;

  try {
    const subcategories = await apiRequest(`/categories/${categoryId}/subcategories`);
    subcategories.forEach(sub => {
      subSelect.innerHTML += `<option value="${sub.id}">${sub.name}</option>`;
    });
  } catch (err) {
    console.error(err);
  }
}

async function loadCategoryList() {
  const container = document.getElementById("categoryList");

  try {
    const cats = await apiRequest("/categories/tree");

    if (!cats || cats.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No categories yet</p>
          ${canManageCategories() ? `<button class="btn-primary" onclick="openCategoryModal()">+ Add Category</button>` : ''}
        </div>
      `;
      return;
    }

    const showActions = canManageCategories();

    container.innerHTML = cats.map(cat => `
      <div class="category-card">
        <div class="category-image">
          ${cat.image_url ? `<img src="${cat.image_url}" alt="${cat.name}">` : '<span class="placeholder">📁</span>'}
        </div>
        <div class="category-info">
          <h4>${cat.name}</h4>
          <p>${cat.description || 'No description'}</p>
          ${cat.subcategories && cat.subcategories.length > 0 ? `
            <div class="subcategories">
              <strong>Subcategories:</strong>
              ${cat.subcategories.map(sub => `<span class="tag">${sub.name}</span>`).join('')}
            </div>
          ` : ''}
        </div>
        ${showActions ? `
          <div class="category-actions">
            <button onclick="editCategory('${cat.id}')" title="Edit">✏️</button>
            <button onclick="deleteCategory('${cat.id}')" class="btn-delete" title="Delete">🗑️</button>
          </div>
        ` : ''}
      </div>
    `).join('');

  } catch (err) {
    container.innerHTML = `<p class="error">Failed to load categories</p>`;
  }
}

// ============ CATEGORY MODAL ============
function openCategoryModal(categoryId = null) {
  if (!canManageCategories()) {
    alert("Only admin can manage categories");
    return;
  }

  editingCategoryId = categoryId;
  document.getElementById("categoryModalTitle").innerText = categoryId ? "Edit Category" : "Add New Category";
  document.getElementById("categoryForm").reset();
  document.getElementById("categoryImagePreview").innerHTML = '<span>📷 Click to upload image</span>';

  if (categoryId) {
    loadCategoryForEdit(categoryId);
  }

  document.getElementById("categoryModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeCategoryModal() {
  document.getElementById("categoryModal").classList.remove("active");
  document.body.style.overflow = "auto";
  editingCategoryId = null;
}

async function loadCategoryForEdit(id) {
  try {
    const cat = await apiRequest(`/categories/${id}`);
    document.getElementById("categoryId").value = cat.id;
    document.getElementById("cName").value = cat.name;
    document.getElementById("cDescription").value = cat.description || '';
    document.getElementById("cParent").value = cat.parent_id || '';

    if (cat.image_url) {
      document.getElementById("categoryImagePreview").innerHTML = `<img src="${cat.image_url}" alt="Preview">`;
    }
  } catch (err) {
    alert("Failed to load category");
  }
}

async function saveCategory() {
  const name = document.getElementById("cName").value.trim();
  const description = document.getElementById("cDescription").value.trim();
  const parentId = document.getElementById("cParent").value;
  const fileInput = document.getElementById("cImage");

  if (!name) {
    alert("Please enter category name");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("description", description);
  if (parentId) formData.append("parent_id", parentId);
  if (fileInput.files[0]) formData.append("file", fileInput.files[0]);

  const token = localStorage.getItem("token");

  try {
    const url = editingCategoryId ? `/categories/${editingCategoryId}` : "/categories/";
    const method = editingCategoryId ? "PUT" : "POST";

    const response = await fetch(url, {
      method,
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save category");
    }

    closeCategoryModal();
    await loadCategories();
    loadCategoryList();
    alert(editingCategoryId ? "Category updated!" : "Category created!");

  } catch (err) {
    alert(err.message);
  }
}

function editCategory(id) {
  openCategoryModal(id);
}

// ============ DELETE CATEGORY FIXED ============
async function deleteCategory(id) {
  if (!canManageCategories()) {
    alert("Only admin can delete categories");
    return;
  }

  if (!confirm("Delete this category?")) return;

  try {
    await apiRequest(`/categories/${id}`, "DELETE");
    await loadCategories();
    loadCategoryList();
    alert("Category deleted!");
  } catch (err) {
    alert(err.message);
  }
} // ✅ FIXED: function properly closed


// ============ PRODUCTS ============
async function loadProducts(page = 1) {
  const list = document.getElementById("productList");
  const emptyState = document.getElementById("emptyState");
  currentPage = page;

  try {
    list.innerHTML = `
      <div class="loading-card"></div>
      <div class="loading-card"></div>
      <div class="loading-card"></div>
    `;

    const endpoint = currentUser.role === 'supplier' 
      ? `/products/my-products?page=${page}&limit=12`
      : `/products/?page=${page}&limit=12`;
    
    const data = await apiRequest(endpoint);
    const products = data.products || [];
    totalPages = Math.ceil(data.total / 12);

    if (products.length === 0) {
      list.innerHTML = "";
      emptyState.style.display = "flex";
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    emptyState.style.display = "none";
    renderProducts(products);
    renderPagination();

  } catch (err) {
    list.innerHTML = `<p class="error">Failed to load products</p>`;
  }
}

function renderProducts(products) {
  const list = document.getElementById("productList");

  list.innerHTML = products.map(p => {
    const stockClass = p.quantity <= p.reorder_level ? (p.quantity === 0 ? 'out-of-stock' : 'low-stock') : '';
    const statusClass = p.status === 'active' ? 'status-active' : (p.status === 'inactive' ? 'status-inactive' : 'status-out');
    const imageUrl = p.image_url || '/static/images/placeholder.png';

    const canEdit = canEditProduct(p);
    const canDelete = canDeleteProduct();
    const showActions = canEdit || canDelete;

    return `
      <div class="product-card ${stockClass}">
        <div class="product-image" onclick="viewProduct('${p.id}')">
          <img src="${imageUrl}" alt="${p.name}" onerror="this.src='/static/images/placeholder.png'">
          <span class="status-badge ${statusClass}">${p.status}</span>
        </div>
        <div class="product-info">
          <span class="sku">${p.sku}</span>
          <h4 onclick="viewProduct('${p.id}')">${p.name}</h4>
          <p class="brand">${p.brand || 'No brand'}</p>
          <div class="price-row">
            <span class="cost-price">₹${parseFloat(p.cost_price).toLocaleString('en-IN')}</span>
            <span class="selling-price">₹${parseFloat(p.selling_price).toLocaleString('en-IN')}</span>
          </div>
          <div class="stock-row">
            <span class="stock ${stockClass}">Stock: ${p.quantity} ${p.unit}</span>
            ${p.profit_margin ? `<span class="margin">+${p.profit_margin}%</span>` : ''}
          </div>
        </div>
        ${showActions ? `
          <div class="product-actions">
            ${canEdit ? `
              <button onclick="openQuantityModal('${p.id}', '${p.name}', ${p.quantity})" title="Update Stock">📦</button>
              <button onclick="editProduct('${p.id}')" title="Edit">✏️</button>
            ` : ''}
            ${canDelete ? `
              <button onclick="deleteProduct('${p.id}')" class="btn-delete" title="Delete">🗑️</button>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

function renderPagination() {
  const container = document.getElementById("pagination");

  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = '';
  html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="loadProducts(${currentPage - 1})">←</button>`;

  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
      html += `<button class="${i === currentPage ? 'active' : ''}" onclick="loadProducts(${i})">${i}</button>`;
    } else if (i === currentPage - 3 || i === currentPage + 3) {
      html += `<span>...</span>`;
    }
  }

  html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="loadProducts(${currentPage + 1})">→</button>`;

  container.innerHTML = html;
}

// ============ PRODUCT MODAL ============
function openProductModal(productId = null) {
  if (!canAddProduct()) {
    alert("You don't have permission to add products");
    return;
  }

  editingProductId = productId;
  document.getElementById("productModalTitle").innerText = productId ? "Edit Product" : "Add New Product";
  document.getElementById("productForm").reset();
  document.getElementById("imagePreview").innerHTML = '<span>📷 Click to upload image</span>';
  document.getElementById("profitMargin").innerText = '0%';
  document.getElementById("pSubcategory").innerHTML = '<option value="">Select Subcategory</option>';

  if (productId) {
    loadProductForEdit(productId);
  }

  document.getElementById("productModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeProductModal() {
  document.getElementById("productModal").classList.remove("active");
  document.body.style.overflow = "auto";
  editingProductId = null;
}

async function loadProductForEdit(id) {
  try {
    const p = await apiRequest(`/products/${id}`);

    document.getElementById("productId").value = p.id;
    document.getElementById("pName").value = p.name;
    document.getElementById("pSku").value = p.sku;
    document.getElementById("pDescription").value = p.description || '';
    document.getElementById("pCategory").value = p.category_id || '';
    document.getElementById("pBrand").value = p.brand || '';
    document.getElementById("pUnit").value = p.unit || 'pcs';
    document.getElementById("pCostPrice").value = p.cost_price;
    document.getElementById("pSellingPrice").value = p.selling_price;
    document.getElementById("pQuantity").value = p.quantity;
    document.getElementById("pReorderLevel").value = p.reorder_level;
    document.getElementById("pTax").value = p.tax_percentage;
    document.getElementById("pStatus").value = p.status;
    document.getElementById("pTags").value = (p.tags || []).join(', ');

    if (p.category_id) {
      await loadSubcategories(p.category_id);
      if (p.subcategory_id) {
        document.getElementById("pSubcategory").value = p.subcategory_id;
      }
    }

    if (p.image_url) {
      document.getElementById("imagePreview").innerHTML = `<img src="${p.image_url}" alt="Preview">`;
    }

    calculateProfit();

  } catch (err) {
    alert("Failed to load product");
    closeProductModal();
  }
}

async function saveProduct() {
  const name = document.getElementById("pName").value.trim();
  const costPrice = document.getElementById("pCostPrice").value;
  const sellingPrice = document.getElementById("pSellingPrice").value;
  const fileInput = document.getElementById("pImage");

  if (!name) {
    alert("Please enter product name");
    return;
  }

  if (!costPrice || !sellingPrice) {
    alert("Please enter cost and selling price");
    return;
  }

  if (!editingProductId && !fileInput.files[0]) {
    alert("Please select an image");
    return;
  }

  const formData = new FormData();
  formData.append("name", name);
  formData.append("description", document.getElementById("pDescription").value);
  formData.append("cost_price", costPrice);
  formData.append("selling_price", sellingPrice);
  formData.append("quantity", document.getElementById("pQuantity").value || 0);
  formData.append("reorder_level", document.getElementById("pReorderLevel").value || 10);
  formData.append("tax_percentage", document.getElementById("pTax").value || 0);
  formData.append("unit", document.getElementById("pUnit").value);
  formData.append("status", document.getElementById("pStatus").value);
  formData.append("brand", document.getElementById("pBrand").value);
  formData.append("tags", document.getElementById("pTags").value);

  const sku = document.getElementById("pSku").value.trim();
  if (sku) formData.append("sku", sku);

  const categoryId = document.getElementById("pCategory").value;
  if (categoryId) formData.append("category_id", categoryId);

  const subcategoryId = document.getElementById("pSubcategory").value;
  if (subcategoryId) formData.append("subcategory_id", subcategoryId);

  if (fileInput.files[0]) {
    formData.append("file", fileInput.files[0]);
  }

  const token = localStorage.getItem("token");

  try {
    let response;

    if (editingProductId) {
      response = await fetch(`/products/${editingProductId}`, {
        method: "PUT",
        headers: { "Authorization": "Bearer " + token },
        body: formData
      });

      if (fileInput.files[0]) {
        const imageForm = new FormData();
        imageForm.append("file", fileInput.files[0]);

        await fetch(`/products/${editingProductId}/image`, {
          method: "PUT",
          headers: { "Authorization": "Bearer " + token },
          body: imageForm
        });
      }
    } else {
      response = await fetch("/products/", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token },
        body: formData
      });
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save product");
    }

    closeProductModal();
    loadProducts();
    loadStats();
    alert(editingProductId ? "Product updated!" : "Product created!");

  } catch (err) {
    alert(err.message);
  }
}

async function editProduct(id) {
  try {
    const product = await apiRequest(`/products/${id}`);

    if (!canEditProduct(product)) {
      alert("You don't have permission to edit this product");
      return;
    }

    openProductModal(id);
  } catch (err) {
    alert("Failed to load product");
  }
}

async function deleteProduct(id) {
  if (!canDeleteProduct()) {
    alert("Only admin can delete products");
    return;
  }

  if (!confirm("Delete this product?")) return;

  try {
    await apiRequest(`/products/${id}`, "DELETE");
    loadProducts();
    loadStats();
    alert("Product deleted!");
  } catch (err) {
    alert(err.message);
  }
}

// ============ VIEW PRODUCT MODAL ============
async function viewProduct(id) {
  try {
    const p = await apiRequest(`/products/${id}`);
    const categoryName = categories.find(c => c.id === p.category_id)?.name || 'Uncategorized';
    const canEdit = canEditProduct(p);

    document.getElementById("viewProductContent").innerHTML = `
      <div class="product-detail">
        <div class="product-detail-image">
          <img src="${p.image_url}" alt="${p.name}" onerror="this.src='/static/images/placeholder.png'">
        </div>
        <div class="product-detail-info">
          <span class="sku-badge">${p.sku}</span>
          <h2>${p.name}</h2>
          <p class="brand">${p.brand || 'No brand'}</p>

          <div class="detail-row">
            <span class="label">Category:</span>
            <span>${categoryName}</span>
          </div>

          <div class="detail-row">
            <span class="label">Description:</span>
            <p>${p.description || 'No description'}</p>
          </div>

          <div class="price-detail">
            <div>
              <span class="label">Cost Price</span>
              <span class="cost">₹${parseFloat(p.cost_price).toLocaleString('en-IN')}</span>
            </div>
            <div>
              <span class="label">Selling Price</span>
              <span class="selling">₹${parseFloat(p.selling_price).toLocaleString('en-IN')}</span>
            </div>
            <div>
              <span class="label">Profit Margin</span>
              <span class="profit">${p.profit_margin}%</span>
            </div>
          </div>

          <div class="stock-detail">
            <div>
              <span class="label">In Stock</span>
              <span class="stock-value">${p.quantity} ${p.unit}</span>
            </div>
            <div>
              <span class="label">Reorder Level</span>
              <span>${p.reorder_level} ${p.unit}</span>
            </div>
            <div>
              <span class="label">Tax</span>
              <span>${p.tax_percentage}%</span>
            </div>
          </div>

          <div class="detail-row">
            <span class="label">Status:</span>
            <span class="status-badge status-${p.status}">${p.status}</span>
          </div>

          ${p.tags && p.tags.length > 0 ? `
            <div class="detail-row">
              <span class="label">Tags:</span>
              <div class="tags">${p.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
            </div>
          ` : ''}

          <div class="detail-meta">
            <small>Created: ${new Date(p.created_at).toLocaleDateString()}</small>
            <small>Updated: ${new Date(p.updated_at).toLocaleDateString()}</small>
          </div>
        </div>
      </div>
    `;

    const editBtn = document.getElementById("editProductBtn");
    if (canEdit) {
      editBtn.style.display = 'inline-block';
      editBtn.onclick = () => {
        closeViewProductModal();
        editProduct(id);
      };
    } else {
      editBtn.style.display = 'none';
    }

    document.getElementById("viewProductModal").classList.add("active");
    document.body.style.overflow = "hidden";

  } catch (err) {
    alert("Failed to load product details");
  }
}

function closeViewProductModal() {
  document.getElementById("viewProductModal").classList.remove("active");
  document.body.style.overflow = "auto";
}

// ============ QUANTITY MODAL ============
function openQuantityModal(id, name, currentStock) {
  document.getElementById("qtyProductId").value = id;
  document.getElementById("qtyProductName").innerText = name;
  document.getElementById("qtyCurrentStock").innerText = currentStock;
  document.getElementById("qtyChange").value = 0;

  document.getElementById("quantityModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeQuantityModal() {
  document.getElementById("quantityModal").classList.remove("active");
  document.body.style.overflow = "auto";
}

function changeQtyInput(delta) {
  const input = document.getElementById("qtyChange");
  input.value = parseInt(input.value || 0) + delta;
}

async function updateQuantity() {
  const productId = document.getElementById("qtyProductId").value;
  const change = parseInt(document.getElementById("qtyChange").value);

  if (change === 0) {
    alert("Please enter a quantity change");
    return;
  }

  try {
    const product = await apiRequest(`/products/${productId}`);

    if (!canEditProduct(product)) {
      alert("You don't have permission to update this product's stock");
      return;
    }

    const formData = new FormData();
    formData.append("change", change);

    const token = localStorage.getItem("token");

    const response = await fetch(`/products/${productId}/quantity`, {
      method: "PATCH",
      headers: { "Authorization": "Bearer " + token },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to update quantity");
    }

    closeQuantityModal();
    loadProducts();
    loadStats();
    if (currentTab === 'low-stock') loadLowStock();
    alert("Quantity updated!");

  } catch (err) {
    alert(err.message);
  }
}

// ============ LOW STOCK ============
async function loadLowStock() {
  const container = document.getElementById("lowStockList");

  if (currentUser.role === 'user') {
    container.innerHTML = `<p class="error">Access denied</p>`;
    return;
  }

  try {
    container.innerHTML = '<p>Loading...</p>';

    const data = await apiRequest("/products/low-stock");
    const products = data.products || [];

    if (products.length === 0) {
      container.innerHTML = `
        <div class="success-message">
          <span>✅</span>
          <p>All products are well stocked!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>SKU</th>
            <th>Current Stock</th>
            <th>Reorder Level</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${products.map(p => {
            const canEdit = canEditProduct(p);

            return `
              <tr class="${p.quantity === 0 ? 'critical' : 'warning'}">
                <td>
                  <div class="product-cell">
                    <img src="${p.image_url}" alt="${p.name}" onerror="this.src='/static/images/placeholder.png'">
                    <span>${p.name}</span>
                  </div>
                </td>
                <td>${p.sku}</td>
                <td><strong>${p.quantity}</strong> ${p.unit}</td>
                <td>${p.reorder_level} ${p.unit}</td>
                <td>
                  <span class="badge ${p.quantity === 0 ? 'badge-danger' : 'badge-warning'}">
                    ${p.quantity === 0 ? 'Out of Stock' : 'Low Stock'}
                  </span>
                </td>
                <td>
                  ${canEdit ? `
                    <button class="btn-small" onclick="openQuantityModal('${p.id}', '${p.name}', ${p.quantity})">
                      + Restock
                    </button>
                  ` : '-'}
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;

  } catch (err) {
    container.innerHTML = `<p class="error">Failed to load low stock products</p>`;
  }
}

// ============ SEARCH & FILTERS ============
async function searchProducts() {
  const search = document.getElementById("searchInput").value.trim();

  if (!search) {
    loadProducts();
    return;
  }

  const list = document.getElementById("productList");

  try {
    list.innerHTML = '<div class="loading-card"></div>';

    const data = await apiRequest(`/products/search?search=${encodeURIComponent(search)}`);
    const products = data.products || [];

    if (products.length === 0) {
      list.innerHTML = `<p class="no-results">No products found for "${search}"</p>`;
      return;
    }

    renderProducts(products);
    document.getElementById("pagination").innerHTML = "";

  } catch (err) {
    list.innerHTML = `<p class="error">Search failed</p>`;
  }
}

async function applyFilters() {
  const category = document.getElementById("filterCategory").value;
  const status = document.getElementById("filterStatus").value;
  const stockFilter = document.getElementById("filterStock").value;
  const minPrice = document.getElementById("filterMinPrice").value;
  const maxPrice = document.getElementById("filterMaxPrice").value;

  let params = new URLSearchParams();

  if (category) params.append("category_id", category);
  if (status) params.append("status", status);
  if (stockFilter === "in_stock") params.append("in_stock", "true");
  if (stockFilter === "low_stock") params.append("low_stock", "true");
  if (minPrice) params.append("min_price", minPrice);
  if (maxPrice) params.append("max_price", maxPrice);

  const list = document.getElementById("productList");

  try {
    list.innerHTML = '<div class="loading-card"></div>';

    const data = await apiRequest(`/products/search?${params.toString()}`);
    const products = data.products || [];

    if (products.length === 0) {
      list.innerHTML = `<p class="no-results">No products match the filters</p>`;
      return;
    }

    renderProducts(products);
    document.getElementById("pagination").innerHTML = "";

  } catch (err) {
    list.innerHTML = `<p class="error">Filter failed</p>`;
  }
}

function clearFilters() {
  document.getElementById("filterCategory").value = "";
  document.getElementById("filterStatus").value = "";
  document.getElementById("filterStock").value = "";
  document.getElementById("filterMinPrice").value = "";
  document.getElementById("filterMaxPrice").value = "";
  document.getElementById("searchInput").value = "";
  loadProducts();
}

// ============ HELPERS ============
function previewImage(e, previewId) {
  const file = e.target.files[0];
  const preview = document.getElementById(previewId);

  if (file) {
    const reader = new FileReader();
    reader.onload = function(e) {
      preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
  }
}

function calculateProfit() {
  const cost = parseFloat(document.getElementById("pCostPrice").value) || 0;
  const selling = parseFloat(document.getElementById("pSellingPrice").value) || 0;

  let margin = 0;
  if (cost > 0) {
    margin = ((selling - cost) / cost * 100).toFixed(2);
  }

  const display = document.getElementById("profitMargin");
  display.innerText = margin + '%';
  display.className = margin >= 0 ? 'positive' : 'negative';
} // ✅ FIXED: removed extra closing brace