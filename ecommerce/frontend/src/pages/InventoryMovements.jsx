import { useState, useEffect } from 'react'
import { get, post } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { Alert, Skeleton, Modal, Empty } from '../components/UI'

function RecordMovementModal({ onClose, onSaved }) {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    product_id: '',
    variant_id: '',
    warehouse_id: '',
    movement_type: 'inward',
    quantity: 1,
    remarks: ''
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        product_id: form.product_id,
        warehouse_id: form.warehouse_id,
        movement_type: form.movement_type,
        quantity: parseInt(form.quantity),
      }
      if (form.variant_id) payload.variant_id = form.variant_id
      if (form.remarks) payload.remarks = form.remarks

      await post('/inventory-movements/', payload)
      toast.success('Movement recorded successfully!')
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed to record movement')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Record Manual Stock Movement" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Movement Type</label>
          <select 
            className="form-input"
            value={form.movement_type}
            onChange={e => setForm(f => ({ ...f, movement_type: e.target.value }))}
          >
            <option value="inward">Inward (Add stock)</option>
            <option value="outward">Outward (Remove stock)</option>
            <option value="damaged">Damaged</option>
            <option value="expired">Expired</option>
            <option value="return">Return</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Product ID *</label>
          <input
            className="form-input"
            required
            value={form.product_id}
            onChange={e => setForm(f => ({ ...f, product_id: e.target.value }))}
          />
        </div>
        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label">Warehouse ID *</label>
            <input
              className="form-input"
              required
              value={form.warehouse_id}
              onChange={e => setForm(f => ({ ...f, warehouse_id: e.target.value }))}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Variant ID (Optional)</label>
            <input
              className="form-input"
              value={form.variant_id}
              onChange={e => setForm(f => ({ ...f, variant_id: e.target.value }))}
            />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Quantity *</label>
          <input
            className="form-input"
            type="number"
            min={1}
            required
            value={form.quantity}
            onChange={e => setForm(f => ({ ...f, quantity: e.target.value }))}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Remarks</label>
          <input
            className="form-input"
            value={form.remarks}
            onChange={e => setForm(f => ({ ...f, remarks: e.target.value }))}
            placeholder="Reason for movement"
          />
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Recording...' : 'Record Movement'}
        </button>
      </form>
    </Modal>
  )
}

function LedgerModal({ productId, onClose }) {
  const [ledger, setLedger] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    get(`/inventory-movements/ledger/${productId}`)
      .then(d => setLedger(d))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [productId])

  return (
    <Modal title={`Product Ledger: ${productId}`} onClose={onClose} size="lg">
      {loading ? (
        <Skeleton count={4} height={40} />
      ) : !ledger ? (
        <Alert type="error">Could not load ledger.</Alert>
      ) : (
        <div>
          <div className="form-grid" style={{ marginBottom: 16 }}>
            <div className="stat-box">
              <div className="stat-label">Stock Estimate</div>
              <div className="stat-value">{ledger.current_stock_estimate}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Total Inward</div>
              <div className="stat-value">{ledger.total_inward}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Total Outward</div>
              <div className="stat-value">{ledger.total_outward}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Returns</div>
              <div className="stat-value">{ledger.total_return}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Damaged / Expired</div>
              <div className="stat-value">{ledger.total_damaged + ledger.total_expired}</div>
            </div>
          </div>

          <h4 style={{ marginBottom: 12 }}>Movement History</h4>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Qty</th>
                  <th>Warehouse</th>
                  <th>Ref</th>
                </tr>
              </thead>
              <tbody>
                {ledger.movements?.map(m => (
                  <tr key={m._id}>
                    <td>{new Date(m.timestamp).toLocaleDateString()} {new Date(m.timestamp).toLocaleTimeString()}</td>
                    <td>
                      <span className={`status-badge status-${m.movement_type.toLowerCase()}`}>
                        {m.movement_type}
                      </span>
                    </td>
                    <td>{m.quantity}</td>
                    <td className="cell-mono">{m.warehouse_id.slice(-6)}</td>
                    <td>{m.reference_type}</td>
                  </tr>
                ))}
                {ledger.movements?.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center' }}>No movements recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Modal>
  )
}

export default function InventoryMovements() {
  const { user } = useAuth()
  const toast = useToast()

  const [movements, setMovements] = useState([])
  const [loading, setLoading] = useState(false)
  const [showRecordModal, setShowRecordModal] = useState(false)
  const [ledgerProductId, setLedgerProductId] = useState('')
  const [ledgerSearchInput, setLedgerSearchInput] = useState('')

  const fetchMovements = async () => {
    setLoading(true)
    try {
      const data = await get('/inventory-movements/?page_size=50')
      setMovements(data.movements || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load movements')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMovements()
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Inventory Movements</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            className="form-input"
            placeholder="Product ID for Ledger"
            value={ledgerSearchInput}
            onChange={e => setLedgerSearchInput(e.target.value)}
            style={{ width: 200 }}
          />
          <button 
            className="btn btn-secondary" 
            onClick={() => {
              if (ledgerSearchInput.trim()) setLedgerProductId(ledgerSearchInput.trim())
            }}
          >
            View Ledger
          </button>
          {['admin', 'inventory_manager'].includes(user?.role) && (
            <button className="btn btn-primary" onClick={() => setShowRecordModal(true)}>
              + Record Movement
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <Skeleton count={5} height={50} />
      ) : movements.length === 0 ? (
        <Empty icon="📋" message="No inventory movements found." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Product</th>
                <th>Warehouse</th>
                <th>Type</th>
                <th>Qty</th>
                <th>Ref Type</th>
                <th>Performed By</th>
              </tr>
            </thead>
            <tbody>
              {movements.map(m => (
                <tr key={m._id}>
                  <td>{new Date(m.timestamp).toLocaleString()}</td>
                  <td className="cell-primary" style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={() => setLedgerProductId(m.product_id)}>
                    {m.product_id}
                  </td>
                  <td className="cell-mono">{m.warehouse_id}</td>
                  <td>
                    <span className={`status-badge status-${m.movement_type.toLowerCase()}`}>
                      {m.movement_type}
                    </span>
                  </td>
                  <td>{m.quantity}</td>
                  <td>{m.reference_type}</td>
                  <td className="cell-mono">{m.performed_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showRecordModal && (
        <RecordMovementModal
          onClose={() => setShowRecordModal(false)}
          onSaved={() => {
            setShowRecordModal(false)
            fetchMovements()
          }}
        />
      )}

      {ledgerProductId && (
        <LedgerModal
          productId={ledgerProductId}
          onClose={() => setLedgerProductId('')}
        />
      )}
    </div>
  )
}
