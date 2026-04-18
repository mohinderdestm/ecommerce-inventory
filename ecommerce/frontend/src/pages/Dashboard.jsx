import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { get } from '../api'
import { useAuth } from '../context/AuthContext'
import { Spinner, StatCard, Skeleton } from '../components/UI'

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      get('/products/?page_size=1'),
      get('/suppliers/?page_size=1'),
      get('/warehouses/?page_size=1'),
      get('/sales-orders/summary'),
    ])
      .then(([products, suppliers, warehouses, orders]) => {
        setStats({
          products: products.status === 'fulfilled' ? products.value.total : '—',
          suppliers: suppliers.status === 'fulfilled' ? suppliers.value.total : '—',
          warehouses: warehouses.status === 'fulfilled' ? warehouses.value.total : '—',
          orders: orders.status === 'fulfilled' ? orders.value : {},
        })
      })
      .finally(() => setLoading(false))
  }, [])

  const totalOrders = stats
    ? Object.values(stats.orders).reduce((s, v) => s + (v.count || 0), 0)
    : 0
  const totalValue = stats
    ? Object.values(stats.orders).reduce((s, v) => s + (v.total_value || 0), 0)
    : 0

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Welcome back, {user?.full_name || user?.username} 👋
          </h1>
          <p className="page-subtitle">
            Here's a quick overview of your inventory platform.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="stats-row">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} height={100} radius={12} />
          ))}
        </div>
      ) : (
        <>
          <div className="stats-row">
            <StatCard label="Products" value={stats.products} color="var(--accent)" icon="📦" />
            <StatCard label="Suppliers" value={stats.suppliers} color="#fb923c" icon="🏭" />
            <StatCard label="Warehouses" value={stats.warehouses} color="#a78bfa" icon="🏗️" />
            <StatCard
              label="Total Orders"
              value={totalOrders}
              color="#4ade80"
              icon="🧾"
              sub={`₹${Number(totalValue).toLocaleString('en-IN')} value`}
            />
          </div>

          {Object.keys(stats.orders).length > 0 && (
            <div className="card">
              <h3 className="card-title">Orders by Status</h3>
              <div className="order-status-grid">
                {Object.entries(stats.orders).map(([status, info]) => (
                  <div key={status} className="order-status-card">
                    <div className="order-status-label">{status}</div>
                    <div className="order-status-count">{info.count}</div>
                    <div className="order-status-value">
                      ₹{Number(info.total_value).toLocaleString('en-IN')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <h3 className="card-title">Quick Actions</h3>
            <div className="quick-actions">
              <Link to="/products" className="quick-action-btn">
                <span className="quick-action-icon">📦</span>
                <span>Browse Products</span>
              </Link>
              <Link to="/orders/create" className="quick-action-btn primary">
                <span className="quick-action-icon">➕</span>
                <span>New Order</span>
              </Link>
              <Link to="/warehouses" className="quick-action-btn">
                <span className="quick-action-icon">🏗️</span>
                <span>Warehouses</span>
              </Link>
              <Link to="/suppliers" className="quick-action-btn">
                <span className="quick-action-icon">🏭</span>
                <span>Suppliers</span>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  )
}