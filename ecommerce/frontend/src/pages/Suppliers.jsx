import { useState, useEffect } from 'react'
import { get, post, put, del } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { useDebounce } from '../hooks/useDebounce'
import { Alert, Spinner, Empty, Modal, ConfirmDialog, Skeleton } from '../components/UI'

const PAYMENT_TERMS = ['net_15', 'net_30', 'net_60', 'net_90', 'immediate', 'advance']

function Stars({ rating }) {
  const filled = Math.round(rating || 0)
  return (
    <span className="stars">
      {'★'.repeat(filled)}
      {'☆'.repeat(5 - filled)}
      <span className="stars-value">{(rating || 0).toFixed(1)}</span>
    </span>
  )
}

function SupplierFormModal({ supplier, onClose, onSaved }) {
  const toast = useToast()
  const editing = !!supplier
  const [form, setForm] = useState({
    name: supplier?.name || '',
    contact_person: supplier?.contact_person || '',
    phone: supplier?.phone || '',
    email: supplier?.email || '',
    gst_number: supplier?.gst_number || '',
    payment_terms: supplier?.payment_terms || 'net_30',
    rating: supplier?.rating || 0,
    notes: supplier?.notes || '',
    street: supplier?.address?.street || '',
    city: supplier?.address?.city || '',
    state: supplier?.address?.state || '',
    pincode: supplier?.address?.pincode || '',
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
        payment_terms: form.payment_terms,
        rating: parseFloat(form.rating) || 0,
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
      if (form.gst_number) body.gst_number = form.gst_number

      if (editing) {
        await put('/suppliers/' + supplier._id, body)
        toast.success('Supplier updated!')
      } else {
        await post('/suppliers/', body)
        toast.success('Supplier created!')
      }
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={editing ? 'Edit Supplier' : 'Add Supplier'} onClose={onClose}>
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
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
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
            <label className="form-label">GST Number</label>
            <input
              className="form-input"
              maxLength={15}
              value={form.gst_number}
              onChange={(e) => set('gst_number', e.target.value)}
              placeholder="15-character GST"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Payment Terms</label>
            <select
              className="form-select"
              value={form.payment_terms}
              onChange={(e) => set('payment_terms', e.target.value)}
            >
              {PAYMENT_TERMS.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Rating (0–5)</label>
            <input
              className="form-input"
              type="number"
              min={0}
              max={5}
              step={0.1}
              value={form.rating}
              onChange={(e) => set('rating', e.target.value)}
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

        <div className="form-group">
          <label className="form-label">Notes</label>
          <textarea
            className="form-textarea"
            value={form.notes}
            onChange={(e) => set('notes', e.target.value)}
            rows={3}
          />
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Saving...' : editing ? 'Save Changes' : 'Create Supplier'}
        </button>
      </form>
    </Modal>
  )
}

export default function Suppliers() {
  const { user } = useAuth()
  const toast = useToast()
  const isAdmin = user?.role === 'admin'

  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editSupplier, setEditSupplier] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const debouncedSearch = useDebounce(search, 500)

  const fetchSuppliers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: 1, page_size: 50 })
      if (debouncedSearch) params.set('search', debouncedSearch)
      const data = await get('/suppliers/?' + params)
      setSuppliers(data.suppliers || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load suppliers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSuppliers()
  }, [debouncedSearch])

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await del('/suppliers/' + deleteTarget._id)
      toast.success(`${deleteTarget.name} deleted.`)
      setDeleteTarget(null)
      fetchSuppliers()
    } catch (err) {
      toast.error(err.detail || 'Delete failed')
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Suppliers</h1>
        {isAdmin && (
          <button className="btn btn-success" onClick={() => setShowCreate(true)}>
            + Add Supplier
          </button>
        )}
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            placeholder="Search by name, email, GST..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button className="search-clear" onClick={() => setSearch('')}>
              ✕
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <Skeleton count={5} height={60} />
      ) : suppliers.length === 0 ? (
        <Empty
          icon="🏭"
          message={search ? 'No suppliers match your search.' : 'No suppliers yet.'}
          action={
            isAdmin && (
              <button className="btn btn-success" onClick={() => setShowCreate(true)}>
                + Add First Supplier
              </button>
            )
          }
        />
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Email</th>
                  <th>GST</th>
                  <th>Terms</th>
                  <th>Rating</th>
                  <th>Status</th>
                  {isAdmin && <th></th>}
                </tr>
              </thead>
              <tbody>
                {suppliers.map((s) => (
                  <tr key={s._id}>
                    <td>
                      <div className="cell-primary">{s.name}</div>
                      <div className="cell-secondary">
                        {[s.address?.city, s.address?.state].filter(Boolean).join(', ')}
                      </div>
                    </td>
                    <td>
                      <div>{s.contact_person || '—'}</div>
                      <div className="cell-secondary">{s.phone}</div>
                    </td>
                    <td className="cell-mono">{s.email || '—'}</td>
                    <td className="cell-mono">{s.gst_number || '—'}</td>
                    <td>{(s.payment_terms || '').replace(/_/g, ' ')}</td>
                    <td>
                      <Stars rating={s.rating} />
                    </td>
                    <td>
                      <span className={`status-badge status-${s.status}`}>{s.status}</span>
                    </td>
                    {isAdmin && (
                      <td>
                        <div className="table-actions">
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setEditSupplier(s)}
                          >
                            ✏️
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => setDeleteTarget(s)}
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showCreate && (
        <SupplierFormModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            setShowCreate(false)
            fetchSuppliers()
          }}
        />
      )}

      {editSupplier && (
        <SupplierFormModal
          supplier={editSupplier}
          onClose={() => setEditSupplier(null)}
          onSaved={() => {
            setEditSupplier(null)
            fetchSuppliers()
          }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Supplier"
          message={`Delete "${deleteTarget.name}"? This cannot be undone.`}
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}