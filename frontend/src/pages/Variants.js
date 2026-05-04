import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FaArrowLeft,
  FaPlus,
  FaEdit,
  FaTrash,
  FaShoppingCart,
  FaBoxOpen,
  FaRupeeSign,
  FaLayerGroup,
} from "react-icons/fa";

import API from "../api";
import Layout from "../components/Layout";

export default function VariantPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [variants, setVariants] = useState([]);
  const [user, setUser] = useState(null);
  const [product, setProduct] = useState(null);
  const [show, setShow] = useState(false);
  const [editVariant, setEditVariant] = useState(null);

  const [form, setForm] = useState({
    color: "",
    size: "",
    price: "",
    stock: "",
    imageFile: null,
  });

  const load = async () => {
    try {
      const me = await API.get("/me");
      setUser(me.data);

      const prod = await API.get("/products");
      const found = prod.data.data.find((p) => p.id === id);
      setProduct(found);

      const res = await API.get(`/variants/${id}`);
      setVariants(res.data.data);
    } catch (err) {
      console.log("LOAD ERROR:", err.response?.data);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const addVariant = async () => {
    try {
      const formData = new FormData();

      formData.append("color", form.color);
      formData.append("size", form.size);
      formData.append("price", form.price);
      formData.append("stock", form.stock);

      if (form.imageFile) {
        formData.append("image", form.imageFile);
      }

      await API.post(`/variants/${id}`, formData);

      setShow(false);

      setForm({
        color: "",
        size: "",
        price: "",
        stock: "",
        imageFile: null,
      });

      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    }
  };

  const updateVariant = async () => {
    try {
      const formData = new FormData();

      formData.append("color", editVariant.color);
      formData.append("size", editVariant.size);
      formData.append("price", editVariant.price);
      formData.append("stock", editVariant.stock);

      await API.put(`/variants/${id}/${editVariant.id}`, formData);

      setEditVariant(null);
      load();
    } catch {
      alert("Update failed");
    }
  };

  const deleteVariant = async (variantId) => {
    if (!window.confirm("Delete this variant?")) return;

    try {
      await API.delete(`/variants/${id}/${variantId}`);
      load();
    } catch {
      alert("Delete failed");
    }
  };

  const addToCart = async (variantId) => {
    try {
      await API.post("/cart/add", {
        product_id: id,
        variant_id: variantId,
        quantity: 1,
      });

      alert("Added to cart");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to add to cart");
    }
  };

  return (
    <Layout user={user}>
      <div
        style={{
          padding: "24px",
          background: "#f4f7fb",
          minHeight: "100vh",
        }}
      >
        {/* HEADER */}
        <div
          style={{
            background: "#fff",
            borderRadius: "20px",
            padding: "24px",
            marginBottom: "24px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.06)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <button
              onClick={() => navigate("/products")}
              style={{
                border: "none",
                background: "#eef2ff",
                padding: "10px 16px",
                borderRadius: "10px",
                cursor: "pointer",
                fontWeight: "600",
                marginBottom: "14px",
              }}
            >
              <FaArrowLeft /> Back
            </button>

            <h1
              style={{
                margin: 0,
                fontSize: "32px",
                color: "#111827",
              }}
            >
              {product?.name || "Product"} Variants
            </h1>

            <p
              style={{
                marginTop: "8px",
                color: "#6b7280",
              }}
            >
              Manage all product variants professionally
            </p>
          </div>

          {(user?.role === "admin" || user?.role === "supplier") && (
            <button
              onClick={() => setShow(true)}
              style={{
                background: "#4f46e5",
                color: "#fff",
                border: "none",
                padding: "14px 22px",
                borderRadius: "12px",
                cursor: "pointer",
                fontWeight: "600",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                fontSize: "15px",
              }}
            >
              <FaPlus />
              Add Variant
            </button>
          )}
        </div>

        {/* STATS */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))",
            gap: "18px",
            marginBottom: "28px",
          }}
        >
          <div className="statCard">
            <FaLayerGroup size={24} />
            <div>
              <h3>{variants.length}</h3>
              <p>Total Variants</p>
            </div>
          </div>

          <div className="statCard">
            <FaBoxOpen size={24} />
            <div>
              <h3>
                {variants.reduce((a, b) => a + Number(b.stock), 0)}
              </h3>
              <p>Total Stock</p>
            </div>
          </div>

          <div className="statCard">
            <FaRupeeSign size={24} />
            <div>
              <h3>
                ₹
                {variants.length > 0
                  ? Math.max(...variants.map((v) => Number(v.price)))
                  : 0}
              </h3>
              <p>Highest Price</p>
            </div>
          </div>
        </div>

        {/* VARIANTS GRID */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "24px",
          }}
        >
          {variants.map((v) => (
            <div
              key={v.id}
              style={{
                // width: "50%",
                background: "#fff",
                borderRadius: "22px",
                overflow: "hidden",
                boxShadow: "0 6px 20px rgba(0,0,0,0.06)",
                transition: "0.3s",
              }}
            >
              <div
                style={{
                  height: "240px",
                  background: "#f3f4f6",
                }}
              >
                <img
                  src={
                    v.image
                      ? `http://localhost:8000/${v.image}`
                      : "https://via.placeholder.com/400x300"
                  }
                  alt="variant"
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </div>

              <div style={{ padding: "22px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "14px",
                  }}
                >
                  <h3
                    style={{
                      margin: 0,
                      color: "#111827",
                    }}
                  >
                    {v.color} / {v.size}
                  </h3>

                  <span
                    style={{
                      background:
                        v.stock > 0 ? "#dcfce7" : "#fee2e2",
                      color:
                        v.stock > 0 ? "#166534" : "#991b1b",
                      padding: "6px 12px",
                      borderRadius: "999px",
                      fontSize: "12px",
                      fontWeight: "700",
                    }}
                  >
                    {v.stock > 0 ? "In Stock" : "Out of Stock"}
                  </span>
                </div>

                <div
                  style={{
                    color: "#6b7280",
                    fontSize: "14px",
                    marginBottom: "18px",
                    lineHeight: "1.8",
                  }}
                >
                  <div>SKU: {v.sku}</div>
                  <div>Price: ₹{v.price}</div>
                  <div>Stock: {v.stock}</div>
                </div>

                {(user?.role === "admin" ||
                  user?.role === "supplier") && (
                  <div
                    style={{
                      display: "flex",
                      gap: "10px",
                    }}
                  >
                    <button
                      onClick={() => setEditVariant(v)}
                      style={editBtn}
                    >
                      <FaEdit />
                      Edit
                    </button>

                    <button
                      onClick={() => deleteVariant(v.id)}
                      style={deleteBtn}
                    >
                      <FaTrash />
                      Delete
                    </button>
                  </div>
                )}

                {user?.role === "viewer" && (
                  <button
                    onClick={() => addToCart(v.id)}
                    disabled={v.stock <= 0}
                    style={{
                      width: "100%",
                      border: "none",
                      padding: "14px",
                      borderRadius: "12px",
                      cursor:
                        v.stock > 0 ? "pointer" : "not-allowed",
                      background:
                        v.stock > 0 ? "#4f46e5" : "#9ca3af",
                      color: "#fff",
                      fontWeight: "700",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "10px",
                    }}
                  >
                    <FaShoppingCart />
                    {v.stock > 0
                      ? "Add To Cart"
                      : "Out Of Stock"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* ADD MODAL */}
        {show && (
          <div style={overlay}>
            <div style={modal}>
              <h2>Add Variant</h2>

              <input
                placeholder="Color"
                value={form.color}
                onChange={(e) =>
                  setForm({
                    ...form,
                    color: e.target.value,
                  })
                }
                style={input}
              />

              <input
                placeholder="Size"
                value={form.size}
                onChange={(e) =>
                  setForm({
                    ...form,
                    size: e.target.value,
                  })
                }
                style={input}
              />

              <input
                type="number"
                placeholder="Price"
                value={form.price}
                onChange={(e) =>
                  setForm({
                    ...form,
                    price: e.target.value,
                  })
                }
                style={input}
              />

              <input
                type="number"
                placeholder="Stock"
                value={form.stock}
                onChange={(e) =>
                  setForm({
                    ...form,
                    stock: e.target.value,
                  })
                }
                style={input}
              />

              <input
                type="file"
                onChange={(e) =>
                  setForm({
                    ...form,
                    imageFile: e.target.files[0],
                  })
                }
                style={input}
              />

              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "18px",
                }}
              >
                <button
                  onClick={addVariant}
                  style={saveBtn}
                >
                  Save
                </button>

                <button
                  onClick={() => setShow(false)}
                  style={cancelBtn}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* EDIT MODAL */}
        {editVariant && (
          <div style={overlay}>
            <div style={modal}>
              <h2>Edit Variant</h2>

              <input
                value={editVariant.color}
                onChange={(e) =>
                  setEditVariant({
                    ...editVariant,
                    color: e.target.value,
                  })
                }
                style={input}
              />

              <input
                value={editVariant.size}
                onChange={(e) =>
                  setEditVariant({
                    ...editVariant,
                    size: e.target.value,
                  })
                }
                style={input}
              />

              <input
                value={editVariant.price}
                onChange={(e) =>
                  setEditVariant({
                    ...editVariant,
                    price: e.target.value,
                  })
                }
                style={input}
              />

              <input
                value={editVariant.stock}
                onChange={(e) =>
                  setEditVariant({
                    ...editVariant,
                    stock: e.target.value,
                  })
                }
                style={input}
              />

              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "18px",
                }}
              >
                <button
                  onClick={updateVariant}
                  style={saveBtn}
                >
                  Update
                </button>

                <button
                  onClick={() => setEditVariant(null)}
                  style={cancelBtn}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

const overlay = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.45)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 1000,
};

const modal = {
  background: "#fff",
  padding: "30px",
  borderRadius: "20px",
  width: "420px",
  maxWidth: "95%",
  boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
};

const input = {
  width: "100%",
  padding: "14px",
  marginTop: "14px",
  borderRadius: "12px",
  border: "1px solid #d1d5db",
  outline: "none",
  fontSize: "14px",
};

const saveBtn = {
  flex: 1,
  background: "#4f46e5",
  color: "#fff",
  border: "none",
  padding: "14px",
  borderRadius: "12px",
  cursor: "pointer",
  fontWeight: "700",
};

const cancelBtn = {
  flex: 1,
  background: "#e5e7eb",
  border: "none",
  padding: "14px",
  borderRadius: "12px",
  cursor: "pointer",
  fontWeight: "700",
};

const editBtn = {
  flex: 1,
  border: "none",
  background: "#eef2ff",
  color: "#4338ca",
  padding: "12px",
  borderRadius: "10px",
  cursor: "pointer",
  fontWeight: "600",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "8px",
};

const deleteBtn = {
  flex: 1,
  border: "none",
  background: "#fee2e2",
  color: "#b91c1c",
  padding: "12px",
  borderRadius: "10px",
  cursor: "pointer",
  fontWeight: "600",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "8px",
};



