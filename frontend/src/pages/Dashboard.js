import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";
import { useNavigate } from "react-router-dom";
import "../styles/dashboard.css";

export default function Dashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    products: 0,
    orders: 0,
    revenue: 0,
    lowStock: 0,

    recentOrders: [],

    lowStockReport: [],
    warehouseSummary: [],

    globalLowStock: [],
    warehousePerformance: [],

    topSellingProducts: [],
    supplierReport: [],
    deadStockReport: [],
  });

  const [user, setUser] = useState(null);

  const load = async () => {
    try {
      const me = await API.get("/me");

      if (
        me.data.role !== "admin" &&
        me.data.role !== "inventory_manager"
      ) {
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

      <div
  style={{
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px"
  }}
>
  <h2>Dashboard</h2>

  <button
    className="primary-btn"
    onClick={async () => {

      try {

        const response = await API.get(
          "/dashboard/export/excel",
          {
            responseType: "blob"
          }
        );

        const blob = new Blob(
          [response.data],
          {
            type:
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          }
        );

        const url =
          window.URL.createObjectURL(blob);

        const link =
          document.createElement("a");

        link.href = url;

        link.download =
          "dashboard_report.xlsx";

        document.body.appendChild(link);

        link.click();

        link.remove();

        window.URL.revokeObjectURL(url);

      } catch (err) {

        console.log(err);

        alert("Export failed");

      }

    }}
  >
    Export Excel Report
  </button>
</div>

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
          <p>Warehouse Low Stock Alerts</p>
        </div>

      </div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Recent Orders</h3>

        {(stats.recentOrders || []).map(o => (
          <div key={o.id} className="inventory-item">
            <span>{o.customer}</span>
            <span>₹{o.total}</span>
          </div>
        ))}

      </div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Warehouse Low Stock Report</h3>

        {(stats.lowStockReport || []).length === 0 ? (
          <p>No low stock items</p>
        ) : (
          stats.lowStockReport.map((item, i) => (

            <div key={i} className="inventory-item">

              <div>
                <strong>{item.product}</strong>

                <p>
                  SKU: {item.sku}
                </p>

                <p>
                  Warehouse: {item.warehouse}
                </p>

                <p>
                  Reorder Level: {item.reorderLevel}
                </p>

                <p>
                  Suggested Reorder: {item.suggestedReorder}
                </p>
              </div>

              <div>
                <strong>
                  {item.stock} left
                </strong>

                <p
                  style={{
                    color:
                      item.status === "Critical"
                        ? "red"
                        : "orange",
                    fontWeight: "bold"
                  }}
                >
                  {item.status}
                </p>
              </div>

            </div>
          ))
        )}

      </div>

<div className="card" style={{ marginTop: "20px" }}>

  <h3>Top Selling Products</h3>

  {(stats.topSellingProducts || []).length === 0 ? (

    <p>No sales data available</p>

  ) : (

    stats.topSellingProducts.map((item, i) => (

      <div key={i} className="inventory-item">

        <div>
          <strong>{item.product}</strong>

          <p>
            SKU: {item.sku}
          </p>
        </div>

        <div>

          <strong>
            {item.sold} Sold
          </strong>

          <p>
            ₹{item.revenue.toLocaleString()}
          </p>

        </div>

      </div>

    ))

  )}

</div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Supplier-wise Purchase Report</h3>

        {(stats.supplierReport || []).map((s, i) => (

          <div key={i} className="inventory-item">

            <div>

              <strong>{s.supplier}</strong>

              <p>
                Products: {s.products}
              </p>

            </div>

            <div>

              <p>
                Stock: {s.stock}
              </p>

              <strong>
                ₹{s.value.toLocaleString()}
              </strong>

            </div>

          </div>

        ))}

      </div>


    <div className="card" style={{ marginTop: "20px" }}>

      <h3>Dead Stock Report</h3>

      {(stats.deadStockReport || []).length === 0 ? (

        <p>No dead stock found</p>

      ) : (

        stats.deadStockReport.map((item, i) => (

          <div key={i} className="inventory-item">

            <div>

              <strong>{item.product}</strong>

              <p>
                SKU: {item.sku}
              </p>

            </div>

            <div>

              <p>
                {item.stock} Units Unsold
              </p>

              <strong>
                ₹{item.inventoryValue.toLocaleString()}
              </strong>

            </div>

          </div>

        ))

      )}

    </div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Stock Summary by Warehouse</h3>

        {(stats.warehouseSummary || []).map((w, i) => (

          <div key={i} className="inventory-item">

            <div>
              <strong>{w.warehouse}</strong>

              <p>
                {w.stock} Units
              </p>
            </div>

            <div>
              <strong>
                ₹{w.value.toLocaleString()}
              </strong>

              <p>Inventory Value</p>
            </div>

          </div>
        ))}

      </div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Global Product Low Stock</h3>

        {(stats.globalLowStock || []).length === 0 ? (
          <p>No low stock products</p>
        ) : (
          stats.globalLowStock.map((item, i) => (

            <div key={i} className="inventory-item">

              <div>
                <strong>{item.product}</strong>

                <p>
                  SKU: {item.sku}
                </p>

                <p>
                  Reorder Level: {item.reorderLevel}
                </p>

                <p>
                  Suggested Reorder: {item.suggestedReorder}
                </p>
              </div>

              <div>
                <strong>
                  {item.stock} left
                </strong>

                <p
                  style={{
                    color:
                      item.status === "Critical"
                        ? "red"
                        : "orange",
                    fontWeight: "bold"
                  }}
                >
                  {item.status}
                </p>
              </div>

            </div>
          ))
        )}

      </div>

      <div className="card" style={{ marginTop: "20px" }}>

        <h3>Warehouse Performance</h3>

        {(stats.warehousePerformance || []).map((w, i) => (

          <div key={i} className="inventory-item">

            <div>
              <strong>{w.warehouse}</strong>

              <p>
                Inventory: {w.inventory} Units
              </p>
            </div>

            <div>
              <p>
                Low Stock Items: {w.lowStockItems}
              </p>

              <strong>
                ₹{w.inventoryValue.toLocaleString()}
              </strong>
            </div>

          </div>
        ))}

      </div>

    </Layout>
  );
}

