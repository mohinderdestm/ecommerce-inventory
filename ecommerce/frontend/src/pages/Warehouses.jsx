import { useState, useEffect } from 'react'
import { get, post } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { Alert, Spinner, Empty, Modal, Skeleton } from '../components/UI'

function StockModal({ warehouse, onClose, isAdmin }) {
  const toast = useToast()
  const [stock, setStock] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ product_id: '', quantity: '', notes: '' })

  useEffect(() => {
    get('/warehouses/' + warehouse._id + '/stock')
      .then((d) => setStock(d.stock || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [warehouse._id])

  const handleUpdate = async (e) => {
    e.preventDefault()
    try {
      await post('/warehouses/' + warehouse._id + '/stock', {
        product_id: form.product_id,
        quantity: parseInt(form.quantity),
        notes: form.notes,
      })
      toast.success('Stock updated!')
      const d = await get('/warehouses/' + warehouse._id + '/stock')
      setStock(d.stock || [])
      setForm({ product_id: '', quantity: '', notes: '' })
    } catch (err) {
      toast.error(err.detail || 'Failed')
    }
  }

  return (
    <Modal title={`${warehouse.name} — Stock`} onClose={onClose} size="lg">
      {loading ? (
        <Skeleton count={5} height={40} />
      ) : stock.length === 0 ? (
        <div className="empty-inline">No stock entries yet.</div>
      ) : (
        <div className="table-wrap" style={{ marginBottom: 16 }}>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((s, i) => (
                <tr key={i}>
                  <td className="cell-primary">{s.product_name || s.product_id}</td>
                  <td className="cell-mono">{s.sku || '—'}</td>
                  <td>
                    <span className={`stock-qty ${s.quantity <= 5 ? 'low' : ''}`}>
                      {s.quantity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isAdmin && (
        <>
          <hr className="divider" />
          <h4 style={{ marginBottom: 12, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Update Stock
          </h4>
          <form onSubmit={handleUpdate}>
            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Product ID</label>
                <input
                  className="form-input"
                  value={form.product_id}
                  onChange={(e) => setForm((f) => ({ ...f, product_id: e.target.value }))}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Qty (+/-)</label>
                <input
                  className="form-input"
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <input
                  className="form-input"
                  value={form.notes}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </div>
            </div>
            <button className="btn btn-primary btn-full" type="submit">
              Update Stock
            </button>
          </form>
        </>
      )}
    </Modal>
  )
}

function CreateWarehouseModal({ onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    capacity: '',
    notes: '',
    street: '',
    city: '',
    state: '',
    pincode: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const body = {
        name: form.name,
        contact_person: form.contact_person,
        phone: form.phone,
        notes: form.notes,
        address: {
          street: form.street,
          city: form.city,
          state: form.state,
          pincode: form.pincode,
          country: 'India',
        },
      }
      if (form.email) body.email = form.email
      if (form.capacity) body.capacity = parseInt(form.capacity)

      await post('/warehouses/', body)
      toast.success('Warehouse created!')
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Create Warehouse" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Name *</label>
            <input
              className="form-input"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Contact Person</label>
            <input
              className="form-input"
              value={form.contact_person}
              onChange={(e) => set('contact_person', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input
              className="form-input"
              value={form.phone}
              onChange={(e) => set('phone', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Capacity</label>
            <input
              className="form-input"
              type="number"
              min={1}
              value={form.capacity}
              onChange={(e) => set('capacity', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">City</label>
            <input
              className="form-input"
              value={form.city}
              onChange={(e) => set('city', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">State</label>
            <input
              className="form-input"
              value={form.state}
              onChange={(e) => set('state', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Pincode</label>
            <input
              className="form-input"
              value={form.pincode}
              onChange={(e) => set('pincode', e.target.value)}
            />
          </div>
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Warehouse'}
        </button>
      </form>
    </Modal>
  )
}

export default function Warehouses() {
  const { user } = useAuth()
  const toast = useToast()
  const isAdmin = user?.role === 'admin'

  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState(null)

  const fetchWarehouses = async () => {
    setLoading(true)
    try {
      const data = await get('/warehouses/?page_size=50')
      setWarehouses(data.warehouses || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load warehouses')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWarehouses()
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Warehouses</h1>
        {isAdmin && (
          <button className="btn btn-success" onClick={() => setShowCreate(true)}>
            + Add Warehouse
          </button>
        )}
      </div>

      {loading ? (
        <div className="warehouse-grid">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} height={160} radius={12} />
          ))}
        </div>
      ) : warehouses.length === 0 ? (
        <Empty
          icon="🏗️"
          message="No warehouses yet."
          action={
            isAdmin && (
              <button className="btn btn-success" onClick={() => setShowCreate(true)}>
                + Create First Warehouse
              </button>
            )
          }
        />
      ) : (
        <div className="warehouse-grid">
          {warehouses.map((wh) => (
            <div
              key={wh._id}
              className="warehouse-card"
              onClick={() => setSelected(wh)}
            >
              <div className="warehouse-card-header">
                <div className="warehouse-name">{wh.name}</div>
                <span className={`status-badge status-${wh.status}`}>{wh.status}</span>
              </div>
              {wh.address?.city && (
                <div className="warehouse-location">
                  📍 {[wh.address.city, wh.address.state].filter(Boolean).join(', ')}
                </div>
              )}
              {wh.contact_person && (
                <div className="warehouse-contact">👤 {wh.contact_person}</div>
              )}
              <div className="warehouse-meta">
                {wh.capacity && <span>Capacity: {wh.capacity.toLocaleString()}</span>}
                <span>Staff: {wh.staff_ids?.length || 0}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateWarehouseModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            setShowCreate(false)
            fetchWarehouses()
          }}
        />
      )}

      {selected && (
        <StockModal
          warehouse={selected}
          onClose={() => setSelected(null)}
          isAdmin={isAdmin}
        />
      )}
    </div>
  )
}