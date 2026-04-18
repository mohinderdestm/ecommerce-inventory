import { useState, useEffect, useCallback } from 'react'
import { get, put, del } from '../api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../components/Toast'
import { useDebounce } from '../hooks/useDebounce'
import {
  StatusBadge, Alert, Spinner, Empty, Modal,
  ConfirmDialog, ColorSwatch, Pagination, Skeleton,
} from '../components/UI'

const STATUS_CHIPS = [
  { label: 'All', value: '', cls: 'chip-all' },
  { label: 'Available', value: 'active', cls: 'chip-active' },
  { label: 'Unavailable', value: 'inactive', cls: 'chip-inactive' },
  { label: 'Discontinued', value: 'discontinued', cls: 'chip-discontinued' },
  { label: 'Out of Stock', value: 'out_of_stock', cls: 'chip-out_of_stock' },
]

const UNITS = ['piece', 'kg', 'gram', 'litre', 'metre', 'box', 'dozen', 'pack']

function ProductCard({ product, onEdit, onDelete, canEdit, canAddToCart, onClick, onAddToCart }) {
  const img = product.image_metadata?.find((i) => i.is_primary) || product.image_metadata?.[0]
  const isOrderable = product.status === 'active'

  return (
    <div className="product-card" onClick={onClick}>
      <div className="product-img">
        {img ? (
          <img src={img.url} alt={img.alt_text || product.name}
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
        ) : null}
        <div className="product-img-fallback" style={img ? { display: 'none' } : {}}>📦</div>
      </div>
      <div className="product-body">
        <div className="product-name">{product.name}</div>
        <div className="product-sku">SKU: {product.sku}</div>
        {product.brand && <div className="product-brand">{product.brand}</div>}
        <div className="product-price">₹{Number(product.selling_price).toLocaleString('en-IN')}</div>
        {product.reorder_level > 0 && (
          <span className="product-reorder">⚠ Reorder ≤ {product.reorder_level}</span>
        )}
      </div>
      <div className="product-footer">
        <StatusBadge status={product.status} />
        <span className="product-unit">{product.unit}</span>
      </div>
      {canAddToCart && isOrderable && (
        <button className="btn btn-cart btn-full"
          onClick={(e) => { e.stopPropagation(); onAddToCart(product) }}>
          🛒 Add to Cart
        </button>
      )}
      {canEdit && (
        <div className="product-actions">
          <button className="btn btn-ghost btn-sm"
            onClick={(e) => { e.stopPropagation(); onEdit(product) }}>✏️ Edit</button>
          <button className="btn btn-danger btn-sm"
            onClick={(e) => { e.stopPropagation(); onDelete(product) }}>🗑️</button>
        </div>
      )}
    </div>
  )
}

function ProductModal({ product, onClose, canEdit, onEdit, canAddToCart }) {
  const { addItem, setIsOpen: openCart } = useCart()
  const toast = useToast()
  const [variants, setVariants] = useState([])
  const [loadingVariants, setLoadingVariants] = useState(true)
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [qty, setQty] = useState(1)
  const [activeImg, setActiveImg] = useState(
    product.image_metadata?.find((i) => i.is_primary) || product.image_metadata?.[0]
  )

  useEffect(() => {
    get(`/products/${product._id}/variants/`)
      .then((d) => setVariants(d.variants || []))
      .catch(() => {})
      .finally(() => setLoadingVariants(false))
  }, [product._id])

  const handleAddToCart = () => {
    addItem(product, selectedVariant, qty)
    toast.success(`${product.name} added to cart!`)
    openCart(true)
    onClose()
  }

  const isOrderable = product.status === 'active'
  const activeVariants = variants.filter((v) => v.is_active !== false)
  const needsVariantSelection = activeVariants.length > 0 && !selectedVariant
  const displayPrice = selectedVariant?.selling_price ?? product.selling_price

  const details = [
    ['SKU', selectedVariant?.sku || product.sku],
    ['Brand', product.brand || '—'],
    ['Price', `₹${Number(displayPrice).toLocaleString('en-IN')}`],
    ['Tax', product.tax_percentage > 0 ? `${product.tax_percentage}%` : 'None'],
    ['Unit', product.unit],
    ['Reorder Level', product.reorder_level || 0],
  ]

  return (
    <Modal title={product.name} onClose={onClose} size="lg">
      {activeImg && (
        <img src={activeImg.url} alt="" className="product-modal-hero"
          onError={(e) => (e.target.style.display = 'none')} />
      )}
      {product.image_metadata?.length > 1 && (
        <div className="product-modal-thumbs">
          {product.image_metadata.map((img, i) => (
            <img key={i} src={img.url} onClick={() => setActiveImg(img)}
              className={`product-thumb ${activeImg?.url === img.url ? 'active' : ''}`} alt="" />
          ))}
        </div>
      )}
      <div className="detail-list">
        {details.map(([k, v]) => (
          <div key={k} className="detail-row">
            <span className="detail-label">{k}</span>
            <span className="detail-value">{String(v)}</span>
          </div>
        ))}
      </div>
      {product.description && (
        <div className="product-description"><h4>Description</h4><p>{product.description}</p></div>
      )}

      {/* Variant selection */}
      {loadingVariants ? <Skeleton count={2} height={50} /> : activeVariants.length > 0 && (
        <div className="product-variants-section">
          <h4>Select Variant</h4>
          {activeVariants.map((v) => (
            <div key={v.variant_id}
              className={`variant-row selectable ${selectedVariant?.variant_id === v.variant_id ? 'selected' : ''}`}
              onClick={() => {
                setSelectedVariant(selectedVariant?.variant_id === v.variant_id ? null : v)
                if (v.image_metadata?.[0]) setActiveImg(v.image_metadata[0])
              }}>
              <ColorSwatch color={v.color} size={20} />
              <div className="variant-info">
                <div className="variant-name">{v.color || 'Default'}</div>
                <div className="variant-sku">{v.sku}</div>
                {Object.entries(v.attributes || {}).length > 0 && (
                  <div className="variant-attrs">
                    {Object.entries(v.attributes).map(([k, val]) => `${k}: ${val}`).join(' · ')}
                  </div>
                )}
              </div>
              <div className="variant-pricing">
                <div className="variant-price">₹{Number(v.selling_price).toLocaleString('en-IN')}</div>
                <div className={`variant-stock ${v.stock === 0 ? 'out' : v.stock <= 5 ? 'low' : 'ok'}`}>
                  {v.stock === 0 ? 'Out of Stock' : `Stock: ${v.stock}`}
                </div>
              </div>
              {selectedVariant?.variant_id === v.variant_id && (
                <span className="variant-selected-tick">✓</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add to Cart CTA */}
      {canAddToCart && isOrderable && (
        <div className="modal-cart-section">
          {needsVariantSelection && (
            <p className="variant-hint">← Select a variant above to continue</p>
          )}
          <div className="modal-cart-controls">
            <div className="qty-control modal-qty">
              <button className="qty-btn" onClick={() => setQty(Math.max(1, qty - 1))}>−</button>
              <span className="qty-value">{qty}</span>
              <button className="qty-btn" onClick={() => setQty(qty + 1)}>+</button>
            </div>
            <button className="btn btn-cart btn-lg" onClick={handleAddToCart}
              disabled={needsVariantSelection} style={{ flex: 1 }}>
              🛒 Add to Cart — ₹{Number(displayPrice * qty).toLocaleString('en-IN')}
            </button>
          </div>
        </div>
      )}

      {canEdit && (
        <div className="modal-actions">
          <button className="btn btn-primary" onClick={() => { onEdit(product); onClose() }}>
            ✏️ Edit Product
          </button>
        </div>
      )}
    </Modal>
  )
}

function EditModal({ product, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    name: product.name, brand: product.brand,
    selling_price: product.selling_price, cost_price: product.cost_price,
    reorder_level: product.reorder_level, tax_percentage: product.tax_percentage,
    unit: product.unit, status: product.status, description: product.description,
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSave = async (e) => {
    e.preventDefault(); setLoading(true); setError('')
    try {
      const body = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== '' && v != null))
      if (body.selling_price) body.selling_price = parseFloat(body.selling_price)
      if (body.cost_price) body.cost_price = parseFloat(body.cost_price)
      if (body.reorder_level) body.reorder_level = parseInt(body.reorder_level)
      if (body.tax_percentage) body.tax_percentage = parseFloat(body.tax_percentage)
      await put(`/products/${product._id}`, body)
      toast.success(`${product.name} updated!`)
      onSaved()
    } catch (err) { setError(err.detail || 'Update failed') } finally { setLoading(false) }
  }

  return (
    <Modal title={`Edit: ${product.name}`} onClose={onClose} size="md">
      <form onSubmit={handleSave}>
        <div className="form-grid">
          <div className="form-group"><label className="form-label">Name</label><input className="form-input" value={form.name||''} onChange={(e)=>set('name',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Brand</label><input className="form-input" value={form.brand||''} onChange={(e)=>set('brand',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Selling Price</label><input className="form-input" type="number" step="0.01" value={form.selling_price||''} onChange={(e)=>set('selling_price',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Cost Price</label><input className="form-input" type="number" step="0.01" value={form.cost_price||''} onChange={(e)=>set('cost_price',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Reorder Level</label><input className="form-input" type="number" value={form.reorder_level||''} onChange={(e)=>set('reorder_level',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Tax %</label><input className="form-input" type="number" step="0.01" value={form.tax_percentage||''} onChange={(e)=>set('tax_percentage',e.target.value)}/></div>
          <div className="form-group"><label className="form-label">Unit</label>
            <select className="form-select" value={form.unit} onChange={(e)=>set('unit',e.target.value)}>
              {UNITS.map((u)=><option key={u} value={u}>{u}</option>)}
            </select>
          </div>
          <div className="form-group"><label className="form-label">Status</label>
            <select className="form-select" value={form.status} onChange={(e)=>set('status',e.target.value)}>
              {['active','inactive','discontinued','out_of_stock'].map((s)=><option key={s} value={s}>{s.replace('_',' ')}</option>)}
            </select>
          </div>
        </div>
        <div className="form-group"><label className="form-label">Description</label>
          <textarea className="form-textarea" value={form.description||''} onChange={(e)=>set('description',e.target.value)} rows={3}/>
        </div>
        {error && <Alert type="error">{error}</Alert>}
        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
    </Modal>
  )
}

export default function Products() {
  const { user } = useAuth()
  const { addItem, setIsOpen: openCart } = useCart()
  const toast = useToast()
  const canEdit = user?.role === 'admin' || user?.role === 'supplier'
  const canAddToCart = user?.role === 'customer'

  const [products, setProducts] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [editProduct, setEditProduct] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const debouncedSearch = useDebounce(search, 500)
  const PAGE_SIZE = 12

  const fetchProducts = useCallback(async (pg = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: pg, page_size: PAGE_SIZE })
      if (statusFilter) params.set('status', statusFilter)
      if (debouncedSearch) params.set('q', debouncedSearch)
      const data = await get(`/products/?${params}`)
      setProducts(data.products || [])
      setTotal(data.total || 0)
    } catch (err) { toast.error(err.detail || 'Failed to load products') }
    finally { setLoading(false) }
  }, [statusFilter, debouncedSearch])

  useEffect(() => { fetchProducts(1); setPage(1) }, [statusFilter, debouncedSearch, fetchProducts])

  const handleQuickAddToCart = (product) => {
    addItem(product, null, 1)
    toast.success(`${product.name} added to cart!`)
    openCart(true)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await del(`/products/${deleteTarget._id}`)
      toast.success(`${deleteTarget.name} deleted.`)
      setDeleteTarget(null)
      fetchProducts(page)
    } catch (err) { toast.error(err.detail || 'Delete failed') }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Products</h1>
        <div className="page-header-actions">
          <span className="result-count">{total} product{total !== 1 ? 's' : ''}</span>
        </div>
      </div>

      <div className="chip-filters">
        {STATUS_CHIPS.map((c) => (
          <button key={c.value} className={`chip ${c.cls} ${statusFilter === c.value ? 'active' : ''}`}
            onClick={() => setStatusFilter(c.value)}>{c.label}</button>
        ))}
      </div>

      <div className="search-bar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input className="search-input" placeholder="Search by name, SKU, brand..." value={search}
            onChange={(e) => setSearch(e.target.value)} />
          {search && <button className="search-clear" onClick={() => setSearch('')}>✕</button>}
        </div>
      </div>

      {loading ? (
        <div className="products-grid">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} height={280} radius={12} />)}
        </div>
      ) : products.length === 0 ? (
        <Empty icon="📦" message={search ? `No products match "${search}"` : 'No products found.'} />
      ) : (
        <>
          <div className="products-grid">
            {products.map((p) => (
              <ProductCard key={p._id} product={p} canEdit={canEdit} canAddToCart={canAddToCart}
                onClick={() => setSelected(p)} onEdit={setEditProduct} onDelete={setDeleteTarget}
                onAddToCart={handleQuickAddToCart} />
            ))}
          </div>
          <Pagination page={page} total={total} pageSize={PAGE_SIZE}
            onChange={(pg) => { setPage(pg); fetchProducts(pg) }} />
        </>
      )}

      {selected && (
        <ProductModal product={selected} onClose={() => setSelected(null)}
          canEdit={canEdit} canAddToCart={canAddToCart}
          onEdit={(p) => { setEditProduct(p); setSelected(null) }} />
      )}
      {editProduct && (
        <EditModal product={editProduct} onClose={() => setEditProduct(null)}
          onSaved={() => { setEditProduct(null); fetchProducts(page) }} />
      )}
      {deleteTarget && (
        <ConfirmDialog title="Delete Product"
          message={`Delete "${deleteTarget.name}"? This cannot be undone.`}
          danger onConfirm={handleDelete} onCancel={() => setDeleteTarget(null)} />
      )}
    </div>
  )
}