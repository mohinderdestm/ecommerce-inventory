import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import API from "../api";
import "../styles/layout.css";

export default function Layout({ children, user }) {

  const navigate = useNavigate();
  const location = useLocation();

  const [unread, setUnread] = useState(0);

  const logout = async () => {

    try {

      await API.post("/logout");
      navigate("/");

    } catch (err) {

      console.error(err);
      navigate("/");

    }

  };

 useEffect(() => {

  loadUnread();

  const interval = setInterval(() => {

    loadUnread();

  }, 5000);

  return () => clearInterval(interval);

}, []);

  const loadUnread = async () => {

    try {

      const res = await API.get(
        "/notifications/unread/count"
      );

      setUnread(res.data.count);

    } catch (err) {

      console.error(err);

    }

  };

  const isActive = (path) => {
    return location.pathname === path
      ? "nav-link active"
      : "nav-link";
  };

  return (

    <div className="layout-container">

      <header className="navbar">


        <div className="navbar-left">

          <div
            className="brand"
            onClick={() =>
              navigate("/dashboard")
            }
          >

            <div className="brand-icon">
              <div className="brand-glow"></div>
              IMS
            </div>

            <div className="brand-text">

              <h2>
                Inventory ERP
              </h2>

              <p>
                Enterprise Management Suite
              </p>

            </div>

          </div>

        </div>


        <div className="navbar-center">

          <button
            className={isActive("/products")}
            onClick={() =>
              navigate("/products")
            }
          >
            Products
          </button>

          {(user?.role === "admin" ||
            user?.role ===
              "inventory_manager") && (

            <button
              className={isActive("/dashboard")}
              onClick={() =>
                navigate("/dashboard")
              }
            >
              Dashboard
            </button>

          )}

          {user?.role === "admin" && (
            <>
              <button
                className={isActive("/orders")}
                onClick={() =>
                  navigate("/orders")
                }
              >
                Orders
              </button>

              <button
                className={isActive(
                  "/warehouses"
                )}
                onClick={() =>
                  navigate("/warehouses")
                }
              >
                Warehouses
              </button>

              <button
                className={isActive("/purchase")}
                onClick={() =>
                  navigate("/purchase")
                }
              >
                Purchase Orders
              </button>
           <button
            className={
              isActive("/admin/email-logs")
            }
            onClick={() =>
              navigate("/admin/email-logs")
            }
          >
            Email Logs
          </button>
              <button
        className={isActive("/audit-logs")}
        onClick={() =>
          navigate("/audit-logs")
        }
      >
        Audit Logs
      </button>
            </>
          )}

          {(user?.role ===
            "inventory_manager" ||
            user?.role ===
              "warehouse_staff") && (

            <button
              className={isActive(
                "/warehouses"
              )}
              onClick={() =>
                navigate("/warehouses")
              }
            >
              Warehouse
            </button>

          )}

          {user?.role === "viewer" && (
            <>
              <button
                className={isActive("/cart")}
                onClick={() =>
                  navigate("/cart")
                }
              >
                <span>🛒</span>
                Cart
              </button>

              <button
                className={isActive("/orders")}
                onClick={() =>
                  navigate("/orders")
                }
              >
                <span>📦</span>
                My Orders
              </button>
               <button
            className={isActive("/emails")}
            onClick={() => navigate("/emails")}
          >
            <span>📧</span>
            Emails
          </button>
            </>
          )}

        </div>

        <div className="navbar-right">

          <button
            className="notification-btn"
            onClick={() =>
              navigate("/notifications")
            }
          >

            🔔

            {unread > 0 && (
              <span className="notif-count">
                {unread}
              </span>
            )}

          </button>

          <div className="profile-box">

            <div className="profile-details">

              <h4>
                {user?.name || "User"}
              </h4>

              <p>
                {user?.role}
              </p>

            </div>

            <div className="profile-avatar">

              {user?.name
                ?.charAt(0)
                ?.toUpperCase() || "U"}

            </div>

          </div>

          <button
            className="logout-btn"
            onClick={logout}
          >
            Logout
          </button>

        </div>

      </header>
      <main className="main-content">

        <div className="page-shell">

          {children}

        </div>

      </main>

    </div>

  );

}



