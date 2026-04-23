import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import API from "../api";
import Layout from "../components/Layout";

export default function VariantPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [variants, setVariants] = useState([]);
  const [user, setUser] = useState(null);
  const [product, setProduct] = useState(null); // ✅ NEW
  const [show, setShow] = useState(false);
  const [editVariant, setEditVariant] = useState(null);
  const [form, setForm] = useState({
  color: "",
  size: "",
  price: "",
  stock: "",
  imageFile: null
});


  const load = async () => {
    try {
      const me = await API.get("/me");
      setUser(me.data);

      const prod = await API.get("/products");
      const found = prod.data.data.find(p => p.id === id);
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
      imageFile: null
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
  try {
    await API.delete(`/variants/${id}/${variantId}`);
    load();
  } catch (err) {
    alert("Delete failed");
  }
};
  return (
    <Layout user={user}>
      <div className="page">
          <button onClick={() => navigate("/products")}>
          ← Back to Products
        </button>

        <h2>
          {product?.name || "Product"} 
        </h2>

        {/* ✅ ADD BUTTON */}
        {(user?.role === "admin" || user?.role === "supplier") && (
          <button className="primary" onClick={() => setShow(true)}>
            + Add Variant
          </button>
        )}

        {/* ✅ VARIANTS LIST */}
        <div className="grid">
          {variants.map(v => (
                <div key={v.id} className="card">
          <div key={v.id} className="card">
        <img
          src={
            v.image
              ? `http://localhost:8000/${v.image}`
              : "https://via.placeholder.com/150"
          }
          alt="variant"
        />

        <h4>{v.color} - {v.size}</h4>
        <p>SKU: {v.sku}</p>
        <p>₹{v.price}</p>
        <p>Stock: {v.stock}</p>

        {(user?.role === "admin" || user?.role === "supplier") && (
          <>
            <button onClick={() => setEditVariant(v)}>
              Edit
            </button>

            <button
              className="danger"
              onClick={() => deleteVariant(v.id)}
            >
              Delete
            </button>
          </>
        )}
      </div>
        </div>
          ))}
        </div>

        
       {show && (
        <div className="modal">
          <div className="form">
            <h3>Add Variant</h3>

            <input
              placeholder="Color"
              value={form.color}
              onChange={e => setForm({...form, color: e.target.value})}
            />

            <input
              placeholder="Size"
              value={form.size}
              onChange={e => setForm({...form, size: e.target.value})}
            />

            <input
              type="number"
              placeholder="Price"
              value={form.price}
              onChange={e => setForm({...form, price: e.target.value})}
            />

            <input
              type="number"
              placeholder="Stock"
              value={form.stock}
              onChange={e => setForm({...form, stock: e.target.value})}
            />


            <input
              type="file"
              onChange={e => setForm({...form, imageFile: e.target.files[0]})}
            />

            <button className="primary" onClick={addVariant}>
              Save
            </button>

            <button onClick={() => setShow(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {editVariant && (
      <div className="modal">
        <div className="form">
          <h3>Edit Variant</h3>

          <input value={editVariant.color} onChange={e => setEditVariant({...editVariant, color: e.target.value})}/>
          <input value={editVariant.size} onChange={e => setEditVariant({...editVariant, size: e.target.value})}/>
          <input value={editVariant.price} onChange={e => setEditVariant({...editVariant, price: e.target.value})}/>
          <input value={editVariant.stock} onChange={e => setEditVariant({...editVariant, stock: e.target.value})}/>

          <button onClick={updateVariant}>Update</button>
          <button onClick={() => setEditVariant(null)}>Cancel</button>
        </div>
      </div>
    )}

      </div>
    </Layout>
  );
}

