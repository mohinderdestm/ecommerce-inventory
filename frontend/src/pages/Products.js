import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import Layout from "../components/Layout";
import "../styles/products.css";

export default function Products() {
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [user, setUser] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  // const [warehouses, setWarehouses] = useState([]);

  const [showForm, setShowForm] = useState(false);
  const [editProduct, setEditProduct] = useState(null);
  const [search, setSearch] = useState("");
  const [showWarehouseModal, setShowWarehouseModal] = useState(false);

  const [warehouseForm, setWarehouseForm] = useState({
  name: "",
  code: "",
  address: "",
  city: "",
  state: "",
  country: "",
  pincode: ""
});

  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "",
    brand: "",
    unit: "",
    cost_price: "",
    selling_price: "",
    supplier_email: ""
  });


  // ✅ LOAD DATA
 const load = async () => {
  try {
    const me = await API.get("/me");
    setUser(me.data);

    const res = await API.get("/products");
    setProducts(res.data.data);

    if (me.data.role === "admin") {
      const resSup = await API.get("/users?supplier=true");
      setSuppliers(resSup.data);
    }

  } catch {
    navigate("/");
  }
};

  useEffect(() => {
    load();
  }, []);

const getStockStatus = (product) => {
  // 🔥 CASE 1: HAS VARIANTS
  if (product.variants && product.variants.length > 0) {
    const totalStock = product.variants.reduce(
      (sum, v) => sum + (v.stock || 0),
      0
    );

    if (totalStock === 0) return { label: "Out of Stock", class: "out" };
    if (totalStock < 10) return { label: "Low Stock", class: "low" };
    return { label: "In Stock", class: "in" };
  }

  // 🔥 CASE 2: NO VARIANTS
  return { label: "No Variants", class: "out" };
};

 const createWarehouse = async () => {
  try {
    await API.post("/warehouse", warehouseForm);

    alert("Warehouse created");

    setShowWarehouseModal(false);

    setWarehouseForm({
      name: "",
      code: "",
      address: "",
      city: "",
      state: "",
      country: "",
      pincode: ""
    });

    load(); // 🔥 VERY IMPORTANT

  } catch (err) {
    console.log(err);
    alert("Failed to create warehouse");
  }
};

  // ✅ CREATE PRODUCT
  const createProduct = async () => {
  try {
    const formData = new FormData();

    formData.append("name", form.name || "");
    formData.append("description", form.description || "");
    formData.append("category", form.category || "");
    formData.append("brand", form.brand || "");
    formData.append("unit", form.unit || "");
    formData.append("cost_price", form.cost_price || 0);
    formData.append("selling_price", form.selling_price || 0);

    if (user?.role === "admin") {
      if (!form.supplier_email) {
        alert("Select supplier");
        return;
      }
      formData.append("supplier_email", form.supplier_email);
    }

    if (form.imageFile) {
      formData.append("image", form.imageFile);
    }

    const res = await API.post("/products", formData);

    // ✅ SUCCESS ONLY IF RESPONSE EXISTS
    if (res && res.data) {
      setShowForm(false);
      setForm({
        name: "",
        description: "",
        category: "",
        brand: "",
        unit: "",
        cost_price: "",
        selling_price: "",
        supplier_email: ""
      });
      load();
    }

  } catch (err) {
    console.log("CREATE ERROR FULL:", err);
    console.log("RESPONSE:", err.response);

    // ❌ Only show error if REAL backend error
    if (err.response && err.response.status >= 400) {
      alert(err.response.data?.detail || "Create failed");
    }
  }
};

  // ✅ UPDATE PRODUCT
  const updateProduct = async () => {
    try {
      const formData = new FormData();

      formData.append("name", editProduct.name || "");
      formData.append("description", editProduct.description || "");
      formData.append("category", editProduct.category || "");
      formData.append("brand", editProduct.brand || "");
      formData.append("unit", editProduct.unit || "");
      formData.append("cost_price", editProduct.cost_price || 0);
      formData.append("selling_price", editProduct.selling_price || 0);

      if (editProduct.imageFile) {
        formData.append("image", editProduct.imageFile);
      }

      await API.put(`/products/${editProduct.id}`, formData);

      setEditProduct(null);
      load();
    } catch (err) {
      console.log("UPDATE ERROR:", err.response?.data);
      alert("Update failed");
    }
  };

  // ✅ DELETE PRODUCT
  const deleteProduct = async (id) => {
    try {
      await API.delete(`/products/${id}`);
      load();
    } catch {
      alert("Delete failed");
    }
  };
     
  

  return (
  <Layout user={user}>
    <div className="page">

      <div className="topbar">
          <input className="search" placeholder="Search..." />

          {/* <div className="profile">
            <span>{user?.name || "User"}</span>
            <small>{user?.role}</small>
          </div> */}
        </div>

      {/* 🔥 TOP BAR */}
      <div className="topbar-premium">
        <h1>Products</h1>
       

           {(user?.role === "admin" || user?.role === "supplier") && (
            <button
              className="add-btn"
              onClick={() => setShowForm(true)}
            >
              + Add Product
            </button>
          )}
        
      </div>

      {/* 🧾 PRODUCTS */}
      <div className="grid-premium">
        {products
          .filter(p =>
            p.name?.toLowerCase().includes(search.toLowerCase())
          )
          .map(p => (
            <div
              className="card-premium"
              key={p.id}
              onClick={() => navigate(`/variants/${p.id}`)}
            >
              <img
                src={
                  p.image
                    ? `http://localhost:8000/${p.image}`
                    : "https://via.placeholder.com/150"
                }
                alt="product"
              />

              <div className="card-body">
                <h3>{p.name}</h3>
                <p>{p.description}</p>

                <div className="price">₹{p.selling_price}</div>

                {(() => {
              const status = getStockStatus(p);
              return (
                <div className={`stock ${status.class}`}>
                  {status.label}
                </div>
              );
            })()}

                {/* ACTIONS */}
                <div className="card-actions">

                  {(user?.role === "admin" ||
                    (user?.role === "supplier" &&
                      p.supplier_email === user?.email)) && (
                    <button
                      className="btn edit"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditProduct(p);
                      }}
                    >
                      Edit
                    </button>
                  )}

                  {user?.role === "admin" && (
                    <button
                      className="btn delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteProduct(p.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                {user?.role === "viewer" && (
                  <button
                    className="btn add"
                    onClick={(e) => {

                      e.stopPropagation();

                      navigate(`/variants/${p.id}`);

                    }}
                  >
                    Select Variant
                  </button>
                )}

                </div>
              </div>
            </div>
          ))}
      </div>

    </div>

    {/* KEEP YOUR MODALS SAME BELOW */}
     {showForm && (
        <div className="modal">
          <div className="form">
            <h3>Add Product</h3>

            <input placeholder="Name" onChange={e => setForm({...form, name: e.target.value})}/>
            <input placeholder="Description" onChange={e => setForm({...form, description: e.target.value})}/>
            <input placeholder="Category" onChange={e => setForm({...form, category: e.target.value})}/>
            <input placeholder="Brand" onChange={e => setForm({...form, brand: e.target.value})}/>
            <input placeholder="Unit" onChange={e => setForm({...form, unit: e.target.value})}/>
            <input placeholder="Cost Price" onChange={e => setForm({...form, cost_price: e.target.value})}/>
            <input placeholder="Selling Price" onChange={e => setForm({...form, selling_price: e.target.value})}/>

            {user?.role === "admin" && (
              <select onChange={e => setForm({...form, supplier_email: e.target.value})}>
                <option value="">Select Supplier</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.email}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}

            <input type="file" onChange={e => setForm({...form, imageFile: e.target.files[0]})}/>

            <button onClick={createProduct}>Save</button>
            <button onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}
    {editProduct && (
        <div className="modal">
          <div className="form">
            <h3>Edit Product</h3>

            <input value={editProduct.name || ""} onChange={e => setEditProduct({...editProduct, name: e.target.value})}/>
            <input value={editProduct.description || ""} onChange={e => setEditProduct({...editProduct, description: e.target.value})}/>
            <input value={editProduct.category || ""} onChange={e => setEditProduct({...editProduct, category: e.target.value})}/>
            <input value={editProduct.brand || ""} onChange={e => setEditProduct({...editProduct, brand: e.target.value})}/>
            <input value={editProduct.unit || ""} onChange={e => setEditProduct({...editProduct, unit: e.target.value})}/>
            <input value={editProduct.cost_price || ""} onChange={e => setEditProduct({...editProduct, cost_price: e.target.value})}/>
            <input value={editProduct.selling_price || ""} onChange={e => setEditProduct({...editProduct, selling_price: e.target.value})}/>

            <input type="file" onChange={e => setEditProduct({...editProduct, imageFile: e.target.files[0]})}/>

            <button onClick={updateProduct}>Update</button>
            <button onClick={() => setEditProduct(null)}>Cancel</button>
          </div>
        </div>
      )}
     {showWarehouseModal && (
  <div className="modal">
    <div className="form">
      <h3>Add Warehouse</h3>

      <input placeholder="Name"
        value={warehouseForm.name}
        onChange={(e) => setWarehouseForm({...warehouseForm, name: e.target.value})}
      />

      <input placeholder="Code (WH-01)"
        value={warehouseForm.code}
        onChange={(e) => setWarehouseForm({...warehouseForm, code: e.target.value})}
      />

      <input placeholder="Address"
        value={warehouseForm.address}
        onChange={(e) => setWarehouseForm({...warehouseForm, address: e.target.value})}
      />

      <input placeholder="City"
        value={warehouseForm.city}
        onChange={(e) => setWarehouseForm({...warehouseForm, city: e.target.value})}
      />

      <input placeholder="State"
        value={warehouseForm.state}
        onChange={(e) => setWarehouseForm({...warehouseForm, state: e.target.value})}
      />

      <input placeholder="Country"
        value={warehouseForm.country}
        onChange={(e) => setWarehouseForm({...warehouseForm, country: e.target.value})}
      />

      <input placeholder="Pincode"
        value={warehouseForm.pincode}
        onChange={(e) => setWarehouseForm({...warehouseForm, pincode: e.target.value})}
      />

      <button onClick={createWarehouse}>Save</button>
      <button onClick={() => setShowWarehouseModal(false)}>Cancel</button>
    </div>
  </div>
    )}
  </Layout>
)}