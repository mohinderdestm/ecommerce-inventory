

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FaWarehouse,
  FaUsers,
  FaBoxes,
  FaExchangeAlt,
  FaMapMarkerAlt,
  FaPlus,
  FaEye,
  FaUserTie
} from "react-icons/fa";

import API from "../api";
import Layout from "../components/Layout";
import "../styles/warehouse.css";

export default function Warehouses() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [users, setUsers] = useState([]);

  const [showModal, setShowModal] = useState(false);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [viewWarehouse, setViewWarehouse] = useState(null);

  const [selectedUser, setSelectedUser] = useState("");

  const [inventoryModal, setInventoryModal] = useState(null);
  const [inventoryForm, setInventoryForm] = useState({
    sku: "",
    quantity: ""
  });

  const [transferModal, setTransferModal] = useState(null);
  const [targetWarehouse, setTargetWarehouse] = useState("");
  const [transferForm, setTransferForm] = useState({
    sku: "",
    quantity: 0
  });

  const [form, setForm] = useState({
    name: "",
    code: "",
    address: "",
    city: "",
    state: "",
    country: "",
    pincode: ""
  });

  const load = async () => {
    try {
      const me = await API.get("/me");
      setUser(me.data);

      if (!["admin", "inventory_manager", "warehouse_staff"].includes(me.data.role)) {
        navigate("/products");
        return;
      }

      const [wres, ures] = await Promise.all([
        API.get("/warehouse"),
        API.get("/users")
      ]);

      setWarehouses(wres.data);
      setUsers(ures.data);
    } catch {
      navigate("/");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const createWarehouse = async () => {
    await API.post("/warehouse", form);

    setShowModal(false);

    setForm({
      name: "",
      code: "",
      address: "",
      city: "",
      state: "",
      country: "",
      pincode: ""
    });

    load();
  };

  const assignUser = async () => {
    if (!selectedUser) return alert("Select user");

    await API.post("/warehouse/assign", {
      warehouse_id: selectedWarehouse,
      user_id: selectedUser
    });

    setSelectedWarehouse(null);
    setSelectedUser("");
    load();
  };

  const addInventory = async () => {
    await API.post("/warehouse/inventory/add", {
      warehouse_id: inventoryModal,
      sku: inventoryForm.sku,
      quantity: parseInt(inventoryForm.quantity)
    });

    setInventoryModal(null);
    setInventoryForm({ sku: "", quantity: "" });
    load();
  };

  const currentWarehouse = warehouses.find(
    w => w._id === transferModal
  ) || {};

  return (
    <Layout user={user}>
      <div className="warehouse-page">

        <div className="warehouse-header">
          <div>
            <h1>
              <FaWarehouse /> Warehouses
            </h1>
            <p>Manage inventory warehouses and logistics</p>
          </div>

          <div className="warehouse-header-actions">
            <button
              className="secondary-btn"
              onClick={() => navigate("/products")}
            >
              Back to Products
            </button>

            {user?.role === "admin" && (
              <button
                className="primary-btn"
                onClick={() => setShowModal(true)}
              >
                <FaPlus /> Add Warehouse
              </button>
            )}
          </div>
        </div>

        <div className="warehouse-stats">
          <div className="stat-card">
            <h3>{warehouses.length}</h3>
            <p>Total Warehouses</p>
          </div>

          <div className="stat-card">
            <h3>
              {warehouses.reduce((a, b) => a + (b.staff?.length || 0), 0)}
            </h3>
            <p>Total Staff</p>
          </div>

          <div className="stat-card">
            <h3>
              {warehouses.reduce((a, b) => a + (b.inventory?.length || 0), 0)}
            </h3>
            <p>Inventory Items</p>
          </div>
        </div>

        <div className="warehouse-grid">
          {warehouses.map(w => (
            <div className="warehouse-card" key={w._id}>

              <div className="warehouse-top">
                <div>
                  <h2>{w.name}</h2>
                  <span>{w.code}</span>
                </div>

                <div className="warehouse-badge">
                  Active
                </div>
              </div>

              <div className="warehouse-info">
                <p>
                  <FaMapMarkerAlt /> {w.city}
                </p>

                <p>
                  <FaUserTie />
                  {w.manager?.name || "No manager assigned"}
                </p>

                <p>
                  <FaUsers /> {w.staff?.length || 0} Staff Members
                </p>

                <p>
                  <FaBoxes /> {w.inventory?.length || 0} Inventory Items
                </p>
              </div>

              <div className="warehouse-actions">
                {user?.role === "admin" && (
                  <>
                    <button
                      className="dark-btn"
                      onClick={() => setSelectedWarehouse(w._id)}
                    >
                      <FaUsers /> Assign Staff
                    </button>

                    <button
                      className="warning-btn"
                      onClick={() => setTransferModal(w._id)}
                    >
                      <FaExchangeAlt /> Transfer
                    </button>
                  </>
                )}

                {user?.role === "inventory_manager" && (
                  <button
                    className="success-btn"
                    onClick={() => setInventoryModal(w._id)}
                  >
                    <FaBoxes /> Manage Inventory
                  </button>
                )}

                <button
                  className="primary-btn"
                  onClick={() => setViewWarehouse(w)}
                >
                  <FaEye /> View Details
                </button>
              </div>
            </div>
          ))}
        </div>

        {showModal && (
          <div className="modal-overlay">
            <div className="modal-box">
              <h2>Create Warehouse</h2>

              {Object.keys(form).map(key => (
                <input
                  key={key}
                  placeholder={key}
                  value={form[key]}
                  onChange={e =>
                    setForm({ ...form, [key]: e.target.value })
                  }
                />
              ))}

              <div className="modal-actions">
                <button
                  className="secondary-btn"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>

                <button
                  className="primary-btn"
                  onClick={createWarehouse}
                >
                  Save Warehouse
                </button>
              </div>
            </div>
          </div>
        )}

        {selectedWarehouse && (
          <div className="modal-overlay">
            <div className="modal-box">
              <h2>Assign Staff</h2>

              <select onChange={e => setSelectedUser(e.target.value)}>
                <option value="">Select User</option>

                {users
                  .filter(
                    u =>
                      u.role === "inventory_manager" ||
                      u.role === "warehouse_staff"
                  )
                  .map(u => (
                    <option key={u._id} value={u._id}>
                      {u.name} ({u.role})
                    </option>
                  ))}
              </select>

              <div className="modal-actions">
                <button
                  className="secondary-btn"
                  onClick={() => setSelectedWarehouse(null)}
                >
                  Cancel
                </button>

                <button
                  className="primary-btn"
                  onClick={assignUser}
                >
                  Assign
                </button>
              </div>
            </div>
          </div>
        )}

        {inventoryModal && (
          <div className="modal-overlay">
            <div className="modal-box">
              <h2>Add Inventory</h2>

              <input
                placeholder="SKU"
                onChange={e =>
                  setInventoryForm({
                    ...inventoryForm,
                    sku: e.target.value
                  })
                }
              />

              <input
                type="number"
                placeholder="Quantity"
                onChange={e =>
                  setInventoryForm({
                    ...inventoryForm,
                    quantity: e.target.value
                  })
                }
              />

              <div className="modal-actions">
                <button
                  className="secondary-btn"
                  onClick={() => setInventoryModal(null)}
                >
                  Cancel
                </button>

                <button
                  className="primary-btn"
                  onClick={addInventory}
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {viewWarehouse && (
  <div className="modal-overlay">
    <div className="warehouse-details-modal">

      {/* HEADER */}
      <div className="details-hero">

        <div className="details-hero-left">
          <div className="details-icon">
            <FaWarehouse />
          </div>

          <div>
            <span className="warehouse-status">
              Active Warehouse
            </span>

            <h2>{viewWarehouse.name}</h2>

            <p>
              {viewWarehouse.code}
            </p>
          </div>
        </div>

        <button
          className="close-details-btn"
          onClick={() => setViewWarehouse(null)}
        >
          ✕
        </button>

      </div>

      {/* BODY */}
      <div className="details-content">

        {/* TOP STATS */}
        <div className="details-stats">

          <div className="details-stat-card">
            <FaUsers />
            <div>
              <h4>{viewWarehouse.staff?.length || 0}</h4>
              <p>Staff Members</p>
            </div>
          </div>

          <div className="details-stat-card">
            <FaBoxes />
            <div>
              <h4>{viewWarehouse.inventory?.length || 0}</h4>
              <p>Inventory Items</p>
            </div>
          </div>

          <div className="details-stat-card">
            <FaUserTie />
            <div>
              <h4>
                {viewWarehouse.manager?.name
                  ? "Assigned"
                  : "None"}
              </h4>
              <p>Manager Status</p>
            </div>
          </div>

        </div>

        {/* INFO GRID */}
        <div className="details-info-grid">

          {/* LOCATION */}
          <div className="modern-detail-card">

            <div className="modern-card-header">
              <FaMapMarkerAlt />
              <h3>Warehouse Location</h3>
            </div>

            <div className="location-info">

              <div className="info-row">
                <span>Address</span>
                <strong>{viewWarehouse.address}</strong>
              </div>

              <div className="info-row">
                <span>City</span>
                <strong>{viewWarehouse.city}</strong>
              </div>

              <div className="info-row">
                <span>State</span>
                <strong>{viewWarehouse.state}</strong>
              </div>

              <div className="info-row">
                <span>Country</span>
                <strong>{viewWarehouse.country}</strong>
              </div>

              <div className="info-row">
                <span>Pincode</span>
                <strong>{viewWarehouse.pincode}</strong>
              </div>

            </div>

          </div>

          {/* MANAGER */}
          <div className="modern-detail-card">

            <div className="modern-card-header">
              <FaUserTie />
              <h3>Warehouse Manager</h3>
            </div>

            {viewWarehouse.manager ? (
              <div className="manager-box">

                <div className="manager-avatar">
                  {viewWarehouse.manager.name.charAt(0)}
                </div>

                <div>
                  <h4>{viewWarehouse.manager.name}</h4>
                  <p>Inventory Manager</p>
                </div>

              </div>
            ) : (
              <div className="empty-state-small">
                No manager assigned
              </div>
            )}

          </div>

        </div>

        {/* STAFF */}
        <div className="details-section">

          <div className="section-title">
            <FaUsers />
            <h3>Assigned Staff</h3>
          </div>

          {viewWarehouse.staff?.length > 0 ? (
            <div className="staff-modern-grid">

              {viewWarehouse.staff.map(staff => (
                <div
                  className="staff-modern-card"
                  key={staff.id}
                >
                  <div className="staff-avatar">
                    {staff.name.charAt(0)}
                  </div>

                  <div>
                    <h4>{staff.name}</h4>
                    <p>{staff.email}</p>
                  </div>
                </div>
              ))}

            </div>
          ) : (
            <div className="empty-state">
              No staff assigned
            </div>
          )}

        </div>

        {/* INVENTORY */}
        <div className="details-section">

          <div className="section-title">
            <FaBoxes />
            <h3>Warehouse Inventory</h3>
          </div>

          {viewWarehouse.inventory?.length > 0 ? (

            <div className="inventory-modern-list">

              {viewWarehouse.inventory.map(item => (

                <div
                  className="inventory-modern-card"
                  key={item.sku}
                >

                  <div className="inventory-image-wrapper">

                    <img
                      src={
                        item.image
                          ? `http://localhost:8000/${item.image}`
                          : "https://via.placeholder.com/120"
                      }
                      alt="product"
                    />

                  </div>

                  <div className="inventory-modern-content">

                    <div className="inventory-top-row">

                      <div>
                        <h4>{item.product_name}</h4>
                        <span>{item.sku}</span>
                      </div>

                      <div className="stock-badge">
                        {item.quantity} Units
                      </div>

                    </div>

                    <div className="inventory-data-grid">

                      <div>
                        <span>Warehouse Stock</span>
                        <strong>{item.quantity}</strong>
                      </div>

                      <div>
                        <span>Total Global Stock</span>
                        <strong>{item.stock}</strong>
                      </div>

                      <div>
                        <span>Price</span>
                        <strong>
                          ₹{item.price || 0}
                        </strong>
                      </div>

                    </div>

                  </div>

                  <button
                    className="danger-btn inventory-delete-btn"
                    onClick={async () => {

                      await API.post(
                        "/warehouse/inventory/delete",
                        {
                          warehouse_id: viewWarehouse._id,
                          sku: item.sku
                        }
                      );

                      load();

                      setViewWarehouse(prev => ({
                        ...prev,
                        inventory: prev.inventory.filter(
                          i => i.sku !== item.sku
                        )
                      }));

                    }}
                  >
                    Delete
                  </button>

                </div>

              ))}

            </div>

          ) : (
            <div className="empty-state">
              No inventory available
            </div>
          )}

        </div>

      </div>

    </div>
  </div>
)}

        {transferModal && (
          <div className="modal-overlay">
            <div className="modal-box">
              <h2>Transfer Inventory</h2>

              <select onChange={e => setTargetWarehouse(e.target.value)}>
                <option value="">Select Destination</option>

                {warehouses
                  .filter(w => w._id !== transferModal)
                  .map(w => (
                    <option key={w._id} value={w._id}>
                      {w.name}
                    </option>
                  ))}
              </select>

              <select
                onChange={e =>
                  setTransferForm({
                    ...transferForm,
                    sku: e.target.value
                  })
                }
              >
                <option value="">Select SKU</option>

                {currentWarehouse?.inventory?.map(item => (
                  <option key={item.sku} value={item.sku}>
                    {item.sku} ({item.quantity})
                  </option>
                ))}
              </select>

              <input
                type="number"
                placeholder="Quantity"
                onChange={e =>
                  setTransferForm({
                    ...transferForm,
                    quantity: Number(e.target.value)
                  })
                }
              />

              <div className="modal-actions">
                <button
                  className="secondary-btn"
                  onClick={() => setTransferModal(null)}
                >
                  Cancel
                </button>

                <button
                  className="primary-btn"
                  onClick={async () => {
                    await API.post(
                      "/warehouse/inventory/transfer",
                      {
                        from_warehouse: transferModal,
                        to_warehouse: targetWarehouse,
                        sku: transferForm.sku,
                        quantity: transferForm.quantity
                      }
                    );

                    setTransferModal(null);
                    load();
                  }}
                >
                  Transfer Inventory
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </Layout>
  );
}



