import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { get, post } from '../api'
import { useToast } from '../components/Toast'

export default function CreatePurchaseOrder() {
  const navigate = useNavigate()
  const toast = useToast()

  const [suppliers, setSuppliers] = useState([])
  const [warehouses, setWarehouses] = useState([])
  const [products, setProducts] = useState([])

  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    supplier_id: '',
    supplier_name: '',
    destination_warehouse_id: '',
    notes: '',
  })

  const [items, setItems] = useState([
    { product_id: '', product_name: '', variant_id: '', sku: '', ordered_quantity: 1, unit_cost: 0, tax_percentage: 0 }
  ])

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const [suppRes, whRes, prodRes] = await Promise.all([
          get('/suppliers/?page_size=100'),
          get('/warehouses/?page_size=100'),
          get('/products/?page_size=100')
        ])
        setSuppliers(suppRes?.suppliers || [])
        setWarehouses(whRes?.warehouses || [])
        setProducts(prodRes.products || [])
      } catch (err) {
        toast.error('Failed to load form data')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleSupplierChange = (e) => {
    const id = e.target.value
    const s = suppliers.find(x => x._id === id)
    setForm({ ...form, supplier_id: id, supplier_name: s ? s.name : '' })
  }

  const handleItemChange = (index, field, value) => {
    const newItems = [...items]
    newItems[index][field] = value

    if (field === 'product_id') {
      const p = products.find(x => x._id === value)
      if (p) {
        newItems[index].product_name = p.name
        newItems[index].sku = p.sku
        // clear variant if product changes
        newItems[index].variant_id = ''
      }
    }

    if (field === 'variant_id' && value) {
      const p = products.find(x => x._id === newItems[index].product_id)
      if (p && p.variants) {
        const v = p.variants.find(x => x._id === value)
        if (v) newItems[index].sku = v.sku
      }
    }

    setItems(newItems)
  }

  const addItem = () => {
    setItems([...items, { product_id: '', product_name: '', variant_id: '', sku: '', ordered_quantity: 1, unit_cost: 0, tax_percentage: 0 }])
  }

  const removeItem = (index) => {
    setItems(items.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.supplier_id || !form.destination_warehouse_id) {
      return toast.warning('Please select a supplier and destination warehouse')
    }

    const validItems = items.filter(i => i.product_id && i.ordered_quantity > 0 && i.unit_cost >= 0)
    if (validItems.length === 0) {
      return toast.warning('Please add at least one valid item')
    }

    setSubmitting(true)
    try {
      const payload = {
        ...form,
        items: validItems.map(i => ({
          product_id: i.product_id,
          product_name: i.product_name,
          variant_id: i.variant_id || null,
          sku: i.sku,
          ordered_quantity: Number(i.ordered_quantity),
          unit_cost: Number(i.unit_cost),
          tax_percentage: Number(i.tax_percentage)
        }))
      }
      await post('/purchase-orders/', payload)
      toast.success('Purchase Order created successfully!')
      navigate('/purchase-orders')
    } catch (err) {
      toast.error(err.detail || 'Failed to create PO')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page"><div className="page-header"><h1 className="page-title">Loading...</h1></div></div>

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Create Purchase Order</h1>
      </div>

      <div className="form-container" style={{ maxWidth: '900px' }}>
        <form onSubmit={handleSubmit} className="form">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Supplier *</label>
              <select className="form-select" value={form.supplier_id} onChange={handleSupplierChange} required>
                <option value="">Select Supplier</option>
                {suppliers.map(s => (
                  <option key={s._id} value={s._id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Destination Warehouse *</label>
              <select className="form-select" value={form.destination_warehouse_id} onChange={(e) => setForm({ ...form, destination_warehouse_id: e.target.value })} required>
                <option value="">Select Warehouse</option>
                {warehouses.map(w => (
                  <option key={w._id} value={w._id}>{w.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Notes</label>
            <textarea className="form-textarea" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} />
          </div>

          <h3 style={{ marginTop: '30px', marginBottom: '15px' }}>Items</h3>
          {items.map((item, index) => {
            const selectedProduct = products.find(p => p._id === item.product_id)
            return (
              <div key={index} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '10px', background: '#f9f9f9', padding: '10px', borderRadius: '8px' }}>
                <div style={{ flex: 2 }}>
                  <select className="form-select" value={item.product_id} onChange={(e) => handleItemChange(index, 'product_id', e.target.value)} required>
                    <option value="">Select Product</option>
                    {products.map(p => (
                      <option key={p._id} value={p._id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                {selectedProduct?.variants?.length > 0 && (
                  <div style={{ flex: 1.5 }}>
                    <select className="form-select" value={item.variant_id} onChange={(e) => handleItemChange(index, 'variant_id', e.target.value)}>
                      <option value="">Select Variant</option>
                      {selectedProduct.variants.map(v => (
                        <option key={v._id} value={v._id}>{v.name} ({v.sku})</option>
                      ))}
                    </select>
                  </div>
                )}
                <div style={{ width: '100px' }}>
                  <input type="number" min="1" className="form-input" placeholder="Qty" value={item.ordered_quantity} onChange={(e) => handleItemChange(index, 'ordered_quantity', e.target.value)} required />
                </div>
                <div style={{ width: '120px' }}>
                  <input type="number" min="0" step="0.01" className="form-input" placeholder="Unit Cost" value={item.unit_cost} onChange={(e) => handleItemChange(index, 'unit_cost', e.target.value)} required />
                </div>
                <div style={{ width: '100px' }}>
                  <input type="number" min="0" step="0.01" className="form-input" placeholder="Tax %" value={item.tax_percentage} onChange={(e) => handleItemChange(index, 'tax_percentage', e.target.value)} />
                </div>
                {items.length > 1 && (
                  <button type="button" className="btn btn-danger" onClick={() => removeItem(index)}>✕</button>
                )}
              </div>
            )
          })}

          <button type="button" className="btn btn-ghost" onClick={addItem} style={{ marginBottom: '20px' }}>+ Add Item</button>

          <div className="form-actions">
            <button type="button" className="btn btn-ghost" onClick={() => navigate('/purchase-orders')} disabled={submitting}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Creating...' : 'Create Purchase Order'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
