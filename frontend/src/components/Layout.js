import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import API from "../api";
import "../styles/layout.css";

export default function Layout({ children, user }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigate = useNavigate();
  const location = useLocation();

  const logout = async () => {
    try {
      await API.post("/logout");
      navigate("/");
    } catch (err) {
      console.error(err);
      navigate("/");
    }
  };

  const isActive = (path) => {
    return location.pathname === path ? "nav-item active" : "nav-item";
  };

  return (
    <div className="layout-container">

      {/* ================= SIDEBAR ================= */}

      <aside className={`sidebar ${sidebarOpen ? "expanded" : "collapsed"}`}>

        {/* LOGO */}

        <div className="sidebar-top">
          <div className="logo-box">
            {/* <div className="logo-icon">IMS</div> */}

            {sidebarOpen && (
              <div>
                <h2>Inventory ERP</h2>
                <p>Management System</p>
              </div>
            )}
          </div>

          <button
            className="toggle-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
        </div>

        {/* USER */}

        {sidebarOpen && (
          <div className="user-card">
            <div className="avatar">
              {user?.name?.charAt(0)?.toUpperCase() || "U"}
            </div>

            <div>
              <h4>{user?.name || "User"}</h4>
              <p>{user?.role?.replace("_", " ")}</p>
            </div>
          </div>
        )}

        {/* NAVIGATION */}

        <nav className="nav-links">

          <button
            className={isActive("/products")}
            onClick={() => navigate("/products")}
          >
            <span>📦</span>
            {sidebarOpen && "Products"}
          </button>

          {(user?.role === "admin" ||
            user?.role === "inventory_manager") && (
            <button
              className={isActive("/dashboard")}
              onClick={() => navigate("/dashboard")}
            >
              <span>📊</span>
              {sidebarOpen && "Dashboard"}
            </button>
          )}

          {user?.role === "admin" && (
            <>
              <button
                className={isActive("/orders")}
                onClick={() => navigate("/orders")}
              >
                <span>🧾</span>
                {sidebarOpen && "Orders"}
              </button>

              <button
                className={isActive("/warehouses")}
                onClick={() => navigate("/warehouses")}
              >
                <span>🏭</span>
                {sidebarOpen && "Warehouses"}
              </button>

              <button
                className={isActive("/purchase")}
                onClick={() => navigate("/purchase")}
              >
                <span>📄</span>
                {sidebarOpen && "Purchase Orders"}
              </button>
            </>
          )}

          {user?.role === "inventory_manager" && (
            <button
              className={isActive("/warehouses")}
              onClick={() => navigate("/warehouses")}
            >
              <span>🏭</span>
              {sidebarOpen && "My Warehouse"}
            </button>
          )}

          {user?.role === "warehouse_staff" && (
            <button
              className={isActive("/warehouses")}
              onClick={() => navigate("/warehouses")}
            >
              <span>🏭</span>
              {sidebarOpen && "Warehouse"}
            </button>
          )}

          {user?.role === "viewer" && (
            <>
              <button
                className={isActive("/cart")}
                onClick={() => navigate("/cart")}
              >
                <span>🛒</span>
                {sidebarOpen && "My Cart"}
              </button>

              <button
                className={isActive("/orders")}
                onClick={() => navigate("/orders")}
              >
                <span>📦</span>
                {sidebarOpen && "My Orders"}
              </button>
            </>
          )}

        </nav>

        {/* LOGOUT */}

        <div className="sidebar-bottom">
          <button className="logout-btn" onClick={logout}>
            <span>🚪</span>
            {sidebarOpen && "Logout"}
          </button>
        </div>

      </aside>

      {/* ================= MAIN ================= */}

      <main className="main-content">

  
        <div className="content-wrapper">
          {children}
        </div>

      </main>

    </div>
  );
}