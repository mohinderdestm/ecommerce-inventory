import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { get, post } from '../api'
import { useToast } from '../components/Toast'
import { Alert } from '../components/UI'

const UNITS = ['piece', 'kg', 'gram', 'litre', 'metre', 'box', 'dozen', 'pack']

export default function CreateProduct() {
  const navigate = useNavigate()
  const toast = useToast()

  const [form, setForm] = useState({
    name: '',
    sku: '',
    brand: '',
    category_id: '',
    description: '',
    selling_price: '',
    cost_price: '',
    reorder_level: '',
    tax_percentage: '',
    unit: 'piece',
    barcode: '',
    weight: '',
    dimensions: { length: '', width: '', height: '' },
    image_url: '',
    status: 'active',
  })

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState([])

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await get('/categories/')
        setCategories(data.items || data)
        if ((data.items && data.items.length > 0) || (Array.isArray(data) && data.length > 0)) {
          setForm(prev => ({ ...prev, category_id: data.items ? data.items[0]._id : data[0]._id }))
        }
      } catch (err) {
        console.error('Failed to fetch categories:', err)
      }
    }
    fetchCategories()
  }, [])

  const set = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const setDimension = (field, value) => {
    setForm(prev => ({
      ...prev,
      dimensions: { ...prev.dimensions, [field]: value }
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        name: form.name,
        sku: form.sku,
        brand: form.brand || null,
        category_id: form.category_id,
        description: form.description || null,
        selling_price: parseFloat(form.selling_price) || 0,
        cost_price: parseFloat(form.cost_price) || 0,
        reorder_level: parseInt(form.reorder_level) || 0,
        tax_percentage: parseFloat(form.tax_percentage) || 0,
        unit: form.unit,
        barcode: form.barcode || null,
        status: form.status,
      }

      if (form.weight) payload.weight = parseFloat(form.weight)
      if (form.dimensions.length || form.dimensions.width || form.dimensions.height) {
        payload.dimensions = {
          length: parseFloat(form.dimensions.length) || 0,
          width: parseFloat(form.dimensions.width) || 0,
          height: parseFloat(form.dimensions.height) || 0,
        }
      }
      if (form.image_url) {
        payload.image_metadata = [
          { url: form.image_url, alt_text: form.name, is_primary: true }
        ]
      }

      await post('/products/', payload)
      toast.success(`Product ${form.name} created successfully!`)
      navigate('/products')
    } catch (err) {
      setError(err.detail || 'Failed to create product. Check SKU uniqueness.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Add New Product</h1>
      </div>

      <div className="form-container" style={{ maxWidth: '900px' }}>
        <form onSubmit={handleSubmit} className="form">

          <div className="card">
            <h3 className="card-title">Basic Info</h3>
            <div className="form-row">
              <div className="form-group" style={{ flex: 2 }}>
                <label className="form-label">Product Name *</label>
                <input className="form-input" value={form.name} onChange={(e) => set('name', e.target.value)} required placeholder="e.g. iPhone 15 Pro Max" />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label">SKU</label>
                <input className="form-input" value={form.sku} onChange={(e) => set('sku', e.target.value)} placeholder="Auto-generated if left blank" />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Brand</label>
                <input className="form-input" value={form.brand} onChange={(e) => set('brand', e.target.value)} placeholder="Apple" />
              </div>
              <div className="form-group">
                <label className="form-label">Category *</label>
                <select className="form-select" value={form.category_id} onChange={(e) => set('category_id', e.target.value)} required>
                  {categories.map(c => (
                    <option key={c._id} value={c._id}>{c.name}</option>
                  ))}
                  {categories.length === 0 && <option value="">Loading...</option>}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Unit *</label>
                <select className="form-select" value={form.unit} onChange={(e) => set('unit', e.target.value)}>
                  {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-textarea" value={form.description} onChange={(e) => set('description', e.target.value)} rows={3} placeholder="Detailed product description..." />
            </div>
          </div>

          <div className="card" style={{ marginTop: '20px' }}>
            <h3 className="card-title">Pricing & Inventory</h3>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Selling Price *</label>
                <input className="form-input" type="number" step="0.01" min="0" value={form.selling_price} onChange={(e) => set('selling_price', e.target.value)} required />
              </div>
              <div className="form-group">
                <label className="form-label">Cost Price</label>
                <input className="form-input" type="number" step="0.01" min="0" value={form.cost_price} onChange={(e) => set('cost_price', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Tax %</label>
                <input className="form-input" type="number" step="0.01" min="0" value={form.tax_percentage} onChange={(e) => set('tax_percentage', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Reorder Level</label>
                <input className="form-input" type="number" min="0" value={form.reorder_level} onChange={(e) => set('reorder_level', e.target.value)} placeholder="Alert threshold" />
              </div>
            </div>
          </div>


          <div className="card" style={{ marginTop: '20px' }}>
            <h3 className="card-title">Media</h3>
            <div className="form-group">
              <label className="form-label">Product Image URL</label>
              <input className="form-input" type="url" value={form.image_url} onChange={(e) => set('image_url', e.target.value)} placeholder="https://example.com/product.jpg" />
            </div>
            {form.image_url && (
              <div style={{ marginTop: '10px' }}>
                <img src={form.image_url} alt="Preview" style={{ maxWidth: '100%', height: 'auto', maxHeight: '200px', borderRadius: '8px' }} onError={(e) => e.target.style.display = 'none'} onLoad={(e) => e.target.style.display = 'block'} />
              </div>
            )}
          </div>

          <div className="form-actions" style={{ marginTop: '30px' }}>
            {error && <Alert type="error">{error}</Alert>}
            <button type="button" className="btn btn-ghost" onClick={() => navigate('/products')} disabled={loading}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Creating...' : 'Save Product'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
