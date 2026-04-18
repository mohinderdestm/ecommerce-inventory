import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { get, post } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { Alert, Spinner, Empty, OrderStatus, Skeleton } from '../components/UI'

const STATUS_ACTIONS = {
  draft: [
    { action: 'confirm', label: '✅ Confirm', cls: 'btn-primary' },
    { action: 'cancel', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  confirmed: [
    { action: 'pack', label: '📦 Pack', cls: 'btn-warning' },
    { action: 'cancel', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  packed: [
    { action: 'ship', label: '🚚 Ship', cls: 'btn-purple' },
    { action: 'cancel', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  shipped: [
    { action: 'deliver', label: '✓ Deliver', cls: 'btn-success' },
    { action: 'return', label: '↩ Return', cls: 'btn-ghost' },
  ],
  delivered: [{ action: 'return', label: '↩ Return', cls: 'btn-ghost' }],
}

function OrderCard({ order, onRefresh, canManage }) {
  const toast = useToast()
  const [expanded, setExpanded] = useState(false)
  const [notes, setNotes] = useState('')
  const [returnReason, setReturnReason] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAction = async (action) => {
    if (action === 'return' && !returnReason) {
      toast.warning('Return reason is required')
      return
    }
    setLoading(true)
    try {
      const body = action === 'return' ? { reason: returnReason } : { notes }
      await post(`/sales-orders/${order._id}/${action}`, body)
      toast.success(`Order ${action}ed successfully!`)
      onRefresh()
    } catch (err) {
      toast.error(err.detail || `${action} failed`)
    } finally {
      setLoading(false)
    }
  }

  const actions = STATUS_ACTIONS[order.status] || []

  return (
    <div className={`order-card ${expanded ? 'expanded' : ''}`}>
      <div className="order-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="order-card-info">
          <div className="order-number">{order.order_number}</div>
          <div className="order-meta">
            {order.customer_name} ·{' '}
            {new Date(order.created_at).toLocaleDateString('en-IN', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}
          </div>
        </div>
        <div className="order-card-right">
          <OrderStatus status={order.status} />
          <span className="order-expand-icon">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      <div className="order-card-summary">
        <span className="order-items-preview">
          {(order.items || [])
            .slice(0, 3)
            .map((i) => `${i.product_name} × ${i.quantity}`)
            .join(' · ')}
          {order.items?.length > 3 && ` + ${order.items.length - 3} more`}
        </span>
      </div>

      <div className="order-card-footer">
        <span className="order-total">
          ₹{Number(order.grand_total).toLocaleString('en-IN')}
        </span>
        <span className="order-stock-status">
          {order.stock_reserved ? '🔒 Reserved' : '⏳ Not reserved'}
        </span>
      </div>

      {expanded && (
        <div className="order-card-details">
          <div className="order-items-list">
            {(order.items || []).map((item, i) => (
              <div key={i} className="order-item-row">
                <div className="order-item-name">
                  {item.product_name}{' '}
                  <span className="order-item-qty">× {item.quantity}</span>
                </div>
                <span className="order-item-total">
                  ₹{Number(item.total).toLocaleString('en-IN')}
                </span>
              </div>
            ))}
          </div>

          <div className="order-totals">
            <div className="order-total-row">
              <span>Subtotal</span>
              <span>₹{Number(order.subtotal).toLocaleString('en-IN')}</span>
            </div>
            <div className="order-total-row">
              <span>Tax</span>
              <span>₹{Number(order.tax_total).toLocaleString('en-IN')}</span>
            </div>
            {order.discount_amount > 0 && (
              <div className="order-total-row discount">
                <span>Discount</span>
                <span>-₹{Number(order.discount_amount).toLocaleString('en-IN')}</span>
              </div>
            )}
            <div className="order-total-row grand">
              <span>Total</span>
              <span>₹{Number(order.grand_total).toLocaleString('en-IN')}</span>
            </div>
          </div>

          <div className="order-timeline">
            <h4 className="timeline-title">Status History</h4>
            {(order.status_history || []).map((h, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <div className="timeline-status">{h.status}</div>
                  {h.notes && <div className="timeline-notes">{h.notes}</div>}
                  <div className="timeline-time">
                    {new Date(h.timestamp).toLocaleString('en-IN')}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {canManage && actions.length > 0 && (
            <div className="order-actions">
              <div className="form-group">
                <input
                  className="form-input"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional notes..."
                />
              </div>
              {(order.status === 'shipped' || order.status === 'delivered') && (
                <div className="form-group">
                  <textarea
                    className="form-textarea"
                    value={returnReason}
                    onChange={(e) => setReturnReason(e.target.value)}
                    placeholder="Return reason (required for returns)..."
                    rows={2}
                  />
                </div>
              )}
              <div className="order-action-buttons">
                {actions.map((a) => (
                  <button
                    key={a.action}
                    className={`btn ${a.cls}`}
                    disabled={loading}
                    onClick={() => handleAction(a.action)}
                  >
                    {loading ? '...' : a.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function SalesOrders() {
  const { user } = useAuth()
  const toast = useToast()
  const canManage = user?.role === 'admin' || user?.role === 'warehouse_staff'

  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const STATUSES = [
    '',
    'draft',
    'confirmed',
    'packed',
    'shipped',
    'delivered',
    'cancelled',
    'returned',
  ]

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: 1, page_size: 30 })
      if (statusFilter) params.set('status', statusFilter)
      if (search) params.set('search', search)
      const data = await get('/sales-orders/?' + params)
      setOrders(data.orders || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load orders')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [statusFilter])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Sales Orders</h1>
        <Link to="/orders/create" className="btn btn-success">
          + New Order
        </Link>
      </div>

      <div className="filter-bar">
        <div className="form-group" style={{ marginBottom: 0 }}>
          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s || 'All Statuses'}
              </option>
            ))}
          </select>
        </div>
        <div className="search-input-wrapper" style={{ flex: 2 }}>
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            placeholder="Search by order number or customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchOrders()}
          />
        </div>
        <button className="btn btn-primary" onClick={fetchOrders}>
          Search
        </button>
      </div>

      {loading ? (
        <Skeleton count={4} height={120} />
      ) : orders.length === 0 ? (
        <Empty
          icon="🧾"
          message="No orders found."
          action={
            <Link to="/orders/create" className="btn btn-success">
              Create First Order
            </Link>
          }
        />
      ) : (
        <div className="orders-list">
          {orders.map((o) => (
            <OrderCard key={o._id} order={o} canManage={canManage} onRefresh={fetchOrders} />
          ))}
        </div>
      )}
    </div>
  )
}