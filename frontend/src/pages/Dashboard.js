import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    products: 0,
    orders: 0,
    revenue: 0,
    lowStock: 0,
    recentOrders: []
  });

  const [user, setUser] = useState(null);

  const load = async () => {
    try {
      const me = await API.get("/me");
      if (me.data.role !== "admin" && me.data.role !== "inventory_manager") {
      navigate("/products");
      return;
    }
      setUser(me.data);

      const res = await API.get("/dashboard"); 
      setStats(res.data);

    } catch {
      window.location = "/";
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Layout user={user}>
      <h2>Dashboard</h2>

      {/* STATS */}
      <div className="stats">
        <div className="stat-card">
  <h3>{stats.products}</h3>
  <p>Total Products</p>
</div>

<div className="stat-card">
  <h3>{stats.orders}</h3>
  <p>Total Orders</p>
</div>

<div className="stat-card">
  <h3>₹{stats.revenue}</h3>
  <p>Revenue</p>
</div>

<div className="stat-card">
  <h3>{stats.lowStock}</h3>
  <p>Low Stock Alerts</p>
</div>
      </div>

      {/* RECENT ORDERS */}
      <div className="card" style={{ marginTop: "20px" }}>
        <h3>Recent Orders</h3>

       {(stats.recentOrders || []).map(o => (
          <div key={o.id} className="inventory-item">
            <span>{o.customer}</span>
            <span>₹{o.total}</span>
          </div>
        ))}
      </div>
    </Layout>
  );
}