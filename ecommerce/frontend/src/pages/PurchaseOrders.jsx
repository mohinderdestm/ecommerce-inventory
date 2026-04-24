import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { get, post, patch } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { Spinner, Empty, OrderStatus, Skeleton } from '../components/UI'

const STATUS_ACTIONS = {
  draft: [
    { action: 'submitted', label: 'Submit', cls: 'btn-primary' },
    { action: 'cancelled', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  submitted: [
    { action: 'approved', label: '✅ Approve', cls: 'btn-success' },
    { action: 'rejected', label: '✕ Reject', cls: 'btn-danger' },
    { action: 'cancelled', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  approved: [
    { action: 'receive', label: '📥 Receive', cls: 'btn-purple' },
    { action: 'cancelled', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  partially_received: [
    { action: 'receive', label: '📥 Receive More', cls: 'btn-purple' },
    { action: 'cancelled', label: '✕ Cancel', cls: 'btn-danger' },
  ],
  completed: [],
  rejected: [],
  cancelled: [],
}

function POCard({ po, onRefresh, canManage }) {
  const toast = useToast()
  const [expanded, setExpanded] = useState(false)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [showReceive, setShowReceive] = useState(false)

  // Receive state
  const [receiveData, setReceiveData] = useState(
    po.items.map(i => ({
      product_id: i.product_id,
      variant_id: i.variant_id,
      qty: 0,
      max: i.ordered_quantity - i.received_quantity
    }))
  )
  const [invoiceMetadata, setInvoiceMetadata] = useState({ invoice_number: '', invoice_date: '' })

  const handleStatusChange = async (newStatus) => {
    setLoading(true)
    try {
      await patch(`/purchase-orders/${po._id}/status`, { status: newStatus, notes })
      toast.success(`PO status updated to ${newStatus}`)
      onRefresh()
    } catch (err) {
      toast.error(err.detail || `Failed to update status`)
    } finally {
      setLoading(false)
    }
  }

  const handleReceive = async () => {
    const items = receiveData
      .filter(r => r.qty > 0)
      .map(r => ({ product_id: r.product_id, variant_id: r.variant_id, received_quantity: r.qty }))

    if (items.length === 0) {
      toast.warning('Please enter received quantities greater than 0')
      return
    }

    setLoading(true)
    try {
      const payload = {
        items,
        notes,
        invoice_metadata: invoiceMetadata.invoice_number ? { ...invoiceMetadata, invoice_date: invoiceMetadata.invoice_date || null } : null
      }
      await post(`/purchase-orders/${po._id}/receive`, payload)
      toast.success(`Items received successfully!`)
      setShowReceive(false)
      onRefresh()
    } catch (err) {
      toast.error(err.detail || 'Failed to receive items')
    } finally {
      setLoading(false)
    }
  }

  const actions = STATUS_ACTIONS[po.status] || []

  return (
    <div className={`order-card ${expanded ? 'expanded' : ''}`}>
      <div className="order-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="order-card-info">
          <div className="order-number">{po.po_number}</div>
          <div className="order-meta">
            {po.supplier_name} · {new Date(po.created_at).toLocaleDateString('en-IN')}
          </div>
        </div>
        <div className="order-card-right">
          <OrderStatus status={po.status} />
          <span className="order-expand-icon">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      <div className="order-card-summary">
        <span className="order-items-preview">
          {(po.items || []).slice(0, 3).map(i => `${i.product_name} × ${i.ordered_quantity}`).join(' · ')}
          {po.items?.length > 3 && ` + ${po.items.length - 3} more`}
        </span>
      </div>

      <div className="order-card-footer">
        <span className="order-total">
          ₹{Number(po.grand_total).toLocaleString('en-IN')}
        </span>
      </div>

      {expanded && (
        <div className="order-card-details">
          <div className="order-items-list">
            {(po.items || []).map((item, i) => (
              <div key={i} className="order-item-row" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div className="order-item-name">
                  {item.product_name} <span style={{ fontSize: '0.85em', color: '#666' }}>({item.sku})</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: '500' }}>Ordered: {item.ordered_quantity}</div>
                  <div style={{ color: 'var(--success)', fontSize: '0.9em' }}>Received: {item.received_quantity}</div>
                  <div style={{ color: 'var(--primary)', fontSize: '0.9em' }}>Cost: ₹{item.unit_cost}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="order-totals">
            <div className="order-total-row grand">
              <span>Total Cost</span>
              <span>₹{Number(po.grand_total).toLocaleString('en-IN')}</span>
            </div>
          </div>

          <div className="order-timeline">
            <h4 className="timeline-title">Status History</h4>
            {(po.status_history || []).map((h, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <div className="timeline-status">{h.status}</div>
                  {h.notes && <div className="timeline-notes">{h.notes}</div>}
                  <div className="timeline-time">{new Date(h.timestamp).toLocaleString('en-IN')}</div>
                </div>
              </div>
            ))}
          </div>

          {showReceive ? (
            <div className="receive-form" style={{ marginTop: '20px', padding: '15px', background: '#f5f7fb', borderRadius: '8px' }}>
              <h4>Receive Items</h4>
              <div className="form-group" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label className="form-label">Invoice Number</label>
                  <input className="form-input" value={invoiceMetadata.invoice_number} onChange={e => setInvoiceMetadata({ ...invoiceMetadata, invoice_number: e.target.value })} placeholder="INV-1234" />
                </div>
                <div>
                  <label className="form-label">Invoice Date</label>
                  <input type="date" className="form-input" value={invoiceMetadata.invoice_date} onChange={e => setInvoiceMetadata({ ...invoiceMetadata, invoice_date: e.target.value })} />
                </div>
              </div>
              <table style={{ width: '100%', marginBottom: '15px', textAlign: 'left' }}>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Pending</th>
                    <th>Receive Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {receiveData.map((r, i) => (
                    <tr key={i}>
                      <td>{po.items.find(item => item.product_id === r.product_id && item.variant_id === r.variant_id)?.product_name}</td>
                      <td>{r.max}</td>
                      <td>
                        <input type="number" min="0" max={r.max} className="form-input" style={{ width: '80px' }} value={r.qty} onChange={e => {
                          const val = Math.max(0, Math.min(r.max, parseInt(e.target.value) || 0));
                          const newData = [...receiveData];
                          newData[i].qty = val;
                          setReceiveData(newData);
                        }} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <input className="form-input" placeholder="Notes (optional)" value={notes} onChange={e => setNotes(e.target.value)} style={{ marginBottom: '10px' }} />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button className="btn btn-purple" onClick={handleReceive} disabled={loading}>{loading ? 'Receiving...' : 'Confirm Receipt'}</button>
                <button className="btn btn-ghost" onClick={() => setShowReceive(false)} disabled={loading}>Cancel</button>
              </div>
            </div>
          ) : (
            canManage && actions.length > 0 && (
              <div className="order-actions">
                <input className="form-input" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes..." style={{ marginBottom: '10px' }} />
                <div className="order-action-buttons">
                  {actions.map((a) => (
                    <button
                      key={a.action}
                      className={`btn ${a.cls}`}
                      disabled={loading}
                      onClick={() => {
                        if (a.action === 'receive') setShowReceive(true)
                        else handleStatusChange(a.action)
                      }}
                    >
                      {loading ? '...' : a.label}
                    </button>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}

export default function PurchaseOrders() {
  const { user } = useAuth()
  const toast = useToast()
  const canManage = user?.role === 'admin' || user?.role === 'inventory_manager'

  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')

  const STATUSES = ['', 'draft', 'submitted', 'approved', 'partially_received', 'completed', 'cancelled', 'rejected']

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ skip: 0, limit: 50 })
      if (statusFilter) params.set('status', statusFilter)
      const data = await get('/purchase-orders/?' + params)
      setOrders(data.data || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load purchase orders')
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
        <h1 className="page-title">Purchase Orders</h1>
        {canManage && (
          <Link to="/purchase-orders/create" className="btn btn-success">
            + New PO
          </Link>
        )}
      </div>

      <div className="filter-bar">
        <div className="form-group" style={{ marginBottom: 0 }}>
          <select className="form-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s ? s.replace('_', ' ') : 'All Statuses'}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary" onClick={fetchOrders}>Refresh</button>
      </div>

      {loading ? (
        <Skeleton count={3} height={120} />
      ) : orders.length === 0 ? (
        <Empty
          icon="🛒"
          message="No purchase orders found."
          action={
            canManage && (
              <Link to="/purchase-orders/create" className="btn btn-success">
                Create First PO
              </Link>
            )
          }
        />
      ) : (
        <div className="orders-list">
          {orders.map((o) => (
            <POCard key={o._id} po={o} canManage={canManage} onRefresh={fetchOrders} />
          ))}
        </div>
      )}
    </div>
  )
}
