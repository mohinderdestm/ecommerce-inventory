import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { get, post } from '../api'
import { useCart } from '../context/CartContext'
import { useToast } from '../components/Toast'
import { Alert } from '../components/UI'

export default function CreateOrder() {
  const navigate = useNavigate()
  const toast = useToast()
  const { items: cartItems, clearCart } = useCart()

  const [warehouseId, setWarehouseId] = useState('')
  const [discount, setDiscount] = useState(0)
  const [notes, setNotes] = useState('')
  const [items, setItems] = useState([{ product_id: '', variant_id: '', quantity: 1 }])
  const [shipping, setShipping] = useState({
    full_name: '', phone: '', street: '', city: '', state: '', pincode: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Pre-fill from cart if customer came from cart
  useEffect(() => {
    if (cartItems.length > 0) {
      setItems(
        cartItems.map((item) => ({
          product_id: item.product_id,
          variant_id: item.variant_id || '',
          quantity: item.quantity,
          // display only
          _name: item.product_name,
          _price: item.unit_price,
          _sku: item.sku,
          _variant_label: item.variant_label,
        })),
      )
      
      // Auto-fill warehouse with max stock
      const firstItem = cartItems[0]
      if (firstItem && firstItem.product_id) {
        get(`/warehouses/stock/product/${firstItem.product_id}`)
          .then((data) => {
            if (Array.isArray(data) && data.length > 0) {
              const bestWarehouse = data.reduce((max, current) => 
                (current.quantity > max.quantity) ? current : max
              , data[0])
              
              if (bestWarehouse && bestWarehouse.warehouse_id) {
                setWarehouseId(bestWarehouse.warehouse_id)
              }
            }
          })
          .catch(() => {})
      }
    }
  }, [])

  const addItem = () => setItems((p) => [...p, { product_id: '', variant_id: '', quantity: 1 }])
  const removeItem = (i) => setItems((p) => p.filter((_, idx) => idx !== i))
  const setItem = (i, k, v) => setItems((p) => p.map((item, idx) => (idx === i ? { ...item, [k]: v } : item)))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validItems = items
      .filter((i) => i.product_id && i.quantity > 0)
      .map((i) => ({
        product_id: i.product_id,
        quantity: parseInt(i.quantity),
        ...(i.variant_id ? { variant_id: i.variant_id } : {}),
      }))

    if (!warehouseId) return setError('Warehouse ID is required')
    if (validItems.length === 0) return setError('Add at least one item with a product ID')

    setLoading(true)
    setError('')
    try {
      const body = {
        warehouse_id: warehouseId,
        items: validItems,
        discount_percentage: parseFloat(discount) || 0,
        notes,
      }
      if (shipping.full_name) body.shipping_address = { ...shipping, country: 'India' }

      const order = await post('/sales-orders/', body)
      clearCart()  // clear cart after successful order
      toast.success(`Order ${order.order_number} created as draft!`)
      navigate('/orders')
    } catch (err) {
      setError(err.detail || 'Failed to create order')
    } finally {
      setLoading(false)
    }
  }

  const cartPreFilled = cartItems.length > 0

  return (
    <div className="page" style={{ maxWidth: 760 }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">New Sales Order</h1>
          <p className="page-subtitle">
            Creates a Draft order. Stock is not reserved until you confirm.
          </p>
        </div>
      </div>

      {cartPreFilled && (
        <div className="alert alert-info" style={{ marginBottom: 16 }}>
          🛒 {cartItems.length} item{cartItems.length !== 1 ? 's' : ''} pre-filled from your cart.
          Cart will be cleared after the order is created.
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <h3 className="card-title">Order Details</h3>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Warehouse ID *</label>
              <input className="form-input" placeholder="MongoDB ObjectId"
                value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Discount %</label>
              <input className="form-input" type="number" min={0} max={100}
                value={discount} onChange={(e) => setDiscount(e.target.value)} />
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title">Order Items</h3>
          {items.map((item, i) => (
            <div key={i} className="order-item-form">
              <div className="order-item-form-header">
                <span className="order-item-label">
                  {item._name ? (
                    <span>
                      <strong>{item._name}</strong>
                      {item._variant_label && <span className="cell-secondary"> · {item._variant_label}</span>}
                      <span className="cell-secondary"> — ₹{Number(item._price).toLocaleString('en-IN')}</span>
                    </span>
                  ) : `Item #${i + 1}`}
                </span>
                {items.length > 1 && (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => removeItem(i)}>
                    ✕ Remove
                  </button>
                )}
              </div>
              <div className="form-grid-3">
                <div className="form-group">
                  <label className="form-label">Product ID *</label>
                  <input className="form-input" value={item.product_id}
                    onChange={(e) => setItem(i, 'product_id', e.target.value)}
                    placeholder="MongoDB ObjectId" />
                </div>
                <div className="form-group">
                  <label className="form-label">Variant ID</label>
                  <input className="form-input" placeholder="Optional UUID"
                    value={item.variant_id}
                    onChange={(e) => setItem(i, 'variant_id', e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity *</label>
                  <input className="form-input" type="number" min={1} value={item.quantity}
                    onChange={(e) => setItem(i, 'quantity', e.target.value)} />
                </div>
              </div>
            </div>
          ))}
          <button type="button" className="btn btn-ghost btn-full" onClick={addItem}>
            + Add Another Item
          </button>
        </div>

        <div className="card">
          <h3 className="card-title">Shipping Address (Optional)</h3>
          <div className="form-grid">
            {[['full_name','Full Name'],['phone','Phone'],['street','Street'],
              ['city','City'],['state','State'],['pincode','Pincode']].map(([k, l]) => (
              <div key={k} className="form-group">
                <label className="form-label">{l}</label>
                <input className="form-input" value={shipping[k]}
                  onChange={(e) => setShipping((s) => ({ ...s, [k]: e.target.value }))} />
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea className="form-textarea" value={notes}
              onChange={(e) => setNotes(e.target.value)} placeholder="Special instructions..." rows={3} />
          </div>
          {error && <Alert type="error">{error}</Alert>}
          <button className="btn btn-success btn-full btn-lg" type="submit" disabled={loading}>
            {loading ? 'Creating...' : '🧾 Create Order (Draft)'}
          </button>
        </div>
      </form>
    </div>
  )
}