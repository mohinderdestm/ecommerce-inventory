document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  if (!token || token === "undefined" || token === "null") {
    localStorage.clear();
    window.location.href = "/";
    return;
  }

  const getSafeValue = (key, fallback = "") => {
    const value = localStorage.getItem(key);
    if (!value || value === "undefined" || value === "null") {
      return fallback;
    }
    return value;
  };

  const userEmail = getSafeValue("user_email", "");
  const userRole = getSafeValue("user_role", "viewer");
  const userName =
    getSafeValue("user_name") || (userEmail ? userEmail.split("@")[0] : "User");

  const avatar = document.getElementById("avatar");
  const nameEl = document.getElementById("userName");
  const roleEl = document.getElementById("userRole");
  const logoutBtn = document.getElementById("logoutBtn");
  const addBtn = document.getElementById("openAddProduct");

  const overlay = document.getElementById("productOverlay");
  const closeOverlay = document.getElementById("closeOverlay");
  const form = document.getElementById("productForm");

  const container = document.getElementById("productsContainer");
  const toast = document.getElementById("toast");

  const formatText = (text) => {
    if (!text) return "User";
    return text.charAt(0).toUpperCase() + text.slice(1);
  };

  avatar.innerText = formatText(userName).charAt(0);
  nameEl.innerText = formatText(userName);
  roleEl.innerText = formatText(userRole);

  if (!["admin", "manager"].includes(userRole.toLowerCase())) {
    addBtn.style.display = "none";
  }

  const showToast = (msg) => {
    toast.innerText = msg;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.classList.add("hidden"), 300);
    }, 2500);
  };

  addBtn.addEventListener("click", () => {
    overlay.classList.remove("hidden");
  });

  closeOverlay.addEventListener("click", () => {
    overlay.classList.add("hidden");
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.classList.add("hidden");
    }
  });

  const loadProducts = async () => {
    try {
      const res = await fetch("/api/v1/products", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();
      const products = Array.isArray(data) ? data : data.products || [];

      container.innerHTML = "";

      if (products.length === 0) {
        container.innerHTML = "<p>No products found</p>";
        return;
      }

      products.forEach((p) => {
        const imageUrl =
          p.image || "https://via.placeholder.com/300x200?text=No+Image";

        const card = document.createElement("div");
        card.className = "product-card";

        card.innerHTML = `
          <div class="img-box">
            <img src="${imageUrl}" />
          </div>

          <div class="card-body">
            <h3>${p.name || "Unnamed Product"}</h3>
            <p>${p.description || ""}</p>

            <div class="meta">
              <span class="price">₹ ${p.selling_price}</span>
              <span class="qty">Stock: ${p.reorder_level}</span>
            </div>
          </div>
        `;

        container.appendChild(card);
        console.log("FULL API DATA:", p);
      });
    } catch (err) {
      console.error(err);
    }
  };

  loadProducts();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData();

    const nameVal = document.getElementById("name").value.trim();
    const descVal = document.getElementById("description").value.trim();
    const categoryVal = document.getElementById("category").value.trim();
    const priceVal = document.getElementById("price").value;
    const qtyVal = document.getElementById("quantity").value;

    if (!nameVal || nameVal === "undefined") {
      showToast("Product name required ❌");
      return;
    }

    formData.append("name", nameVal);
    formData.append("description", descVal || "");
    formData.append("category", categoryVal || "General");
    formData.append("brand", "default");

    formData.append("cost_price", priceVal || 0);
    formData.append("selling_price", priceVal || 0);
    formData.append("reorder_level", qtyVal || 0);

    formData.append("tax", 0);
    formData.append("unit", "piece");

    const imageInput = document.getElementById("image");
    if (imageInput.files[0]) {
      formData.append("image", imageInput.files[0]);
    }

    try {
      const res = await fetch("/api/v1/products/", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        console.log(data);
        showToast("Error creating product ❌");
        return;
      }

      showToast("Product Added 🚀");

      overlay.classList.add("hidden");
      form.reset();

      loadProducts();
    } catch (err) {
      showToast("Server error ❌");
    }
  });

  logoutBtn.addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "/";
  });
});
