import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";
import { useNavigate } from "react-router-dom";
import "../styles/orders.css";

export default function Orders() {

  const navigate = useNavigate();

  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [user, setUser] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const [form, setForm] = useState({
    product_id: "",
    variant_id: "",
    quantity: 1
  });

  const load = async () => {
    try {
      const me = await API.get("/me");
      setUser(me.data);

      const [o, p, w] = await Promise.all([
        API.get("/orders"),
        API.get("/products"),
        API.get("/warehouse")
      ]);

      setOrders(o.data.data);
      setProducts(p.data.data);
      setWarehouses(w.data);

    } catch {
      alert("Error loading data");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const confirmOrder = async (id) => {
    try {
      await API.post(`/orders/${id}/confirm`);
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Error");
    }
  };

  const cancelOrder = async (id) => {
    await API.post(`/orders/${id}/cancel`);
    load();
  };

  const updateStatus = async (id, status) => {
    await API.put(`/orders/${id}/status`, { status });
    load();
  };

  const assignWarehouse = async (orderId, warehouseId) => {

    try {
      await API.put(`/orders/${orderId}/warehouse`, {
        warehouse_id: warehouseId
      });

      load();

    } catch (err) {
      alert(err.response?.data?.detail || "Error assigning warehouse");
    }
  };

  const getStatusClass = (status) => {

    switch (status) {
      case "Confirmed":
        return "status confirmed";

      case "Packed":
        return "status packed";

      case "Shipped":
        return "status shipped";

      case "Delivered":
        return "status delivered";

      case "Cancelled":
        return "status cancelled";

      default:
        return "status draft";
    }
  };

  return (
    <Layout user={user}>

      <div className="orders-page">

        <div className="orders-header">
          <div>
            <h1>Orders Management</h1>
            <p>Manage customer orders and warehouse processing</p>
          </div>

          <button
            className="back-btn"
            onClick={() => navigate("/products")}
          >
            ← Back to Products
          </button>
        </div>


        <div className="orders-grid">

          {orders.map((o) => (

            <div className="order-card" key={o.id}>

              <div className="order-top">
                <div>
                  <h3>#{o.id.slice(-6)}</h3>
                  <p>{o.user_email}</p>
                </div>

                <span className={getStatusClass(o.status)}>
                  {o.status}
                </span>
              </div>


              <div className="order-info">
                <div>
                  <span>Total</span>
                  <h2>₹{o.total}</h2>
                </div>

                <div>
                  <span>Items</span>
                  <h4>{o.items?.length || 0}</h4>
                </div>
              </div>


              <div className="warehouse-box">
                <label>Assigned Warehouse</label>

                {user?.role === "admin" ? (
                  <select
                    value={o.warehouse_id || ""}
                    onChange={(e) =>
                      assignWarehouse(o.id, e.target.value)
                    }
                  >
                    <option value="">
                      Select Warehouse
                    </option>

                    {warehouses.map((w) => (
                      <option key={w._id} value={w._id}>
                        {w.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="warehouse-name">
                    {o.warehouse_name || "Not Assigned"}
                  </div>
                )}
              </div>


              <div className="order-actions">

                <button
                  className="view-btn"
                  onClick={() => setSelectedOrder(o)}
                >
                  View Details
                </button>

                {o.status === "Draft" && user?.role === "admin" && (
                  <button
                    className="confirm-btn"
                    onClick={() => confirmOrder(o.id)}
                  >
                    Confirm
                  </button>
                )}

                {o.status !== "Cancelled" && (
                  <button
                    className="cancel-btn"
                    onClick={() => cancelOrder(o.id)}
                  >
                    Cancel
                  </button>
                )}
              </div>


              {user?.role === "admin" && (
                <select
                  className="status-select"
                  value={o.status}
                  onChange={(e) =>
                    updateStatus(o.id, e.target.value)
                  }
                >
                  <option>Draft</option>
                  <option>Confirmed</option>
                  <option>Packed</option>
                  <option>Shipped</option>
                  <option>Delivered</option>
                  <option>Cancelled</option>
                  <option>Returned</option>
                </select>
              )}

            </div>
          ))}

        </div>


        {selectedOrder && (
          <div className="modal-overlay">

            <div className="order-modal">

              <div className="modal-header">
                <div>
                  <h2>Order Details</h2>
                  <p>Order #{selectedOrder.id.slice(-6)}</p>
                </div>

                <button
                  className="close-btn"
                  onClick={() => setSelectedOrder(null)}
                >
                  ×
                </button>
              </div>


              <div className="modal-items">

                {selectedOrder.items.map((item, index) => (

                  <div className="modal-item" key={index}>

                    <img
                      src={
                        item.image
                          ? `http://localhost:8000/${item.image}`
                          : "https://via.placeholder.com/80"
                      }
                      alt="product"
                    />

                    <div>
                      <h4>{item.product_name}</h4>

                      <p>
                        {item.color} / {item.size}
                      </p>

                      <p>
                        Qty: {item.quantity}
                      </p>
                    </div>

                    <h3>
                      ₹{item.price}
                    </h3>

                  </div>
                ))}

              </div>


              <div className="modal-footer">
                <h2>
                  Total: ₹{selectedOrder.total}
                </h2>
              </div>

            </div>
          </div>
        )}

      </div>

    </Layout>
  );
}