import { useState, useEffect } from 'react'
import { get, post, del } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import {
  Alert, Spinner, Empty, Modal, ConfirmDialog,
  ColorSwatch, Skeleton,
} from '../components/UI'

// ─── Categories ──────────────────────────────────────────────────────

export function Categories() {
  const { user } = useAuth()
  const toast = useToast()
  const isAdmin = user?.role === 'admin'

  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const fetchCategories = async () => {
    setLoading(true)
    try {
      const data = await get('/categories/?only_active=false')
      setCategories(Array.isArray(data) ? data : [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load categories')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCategories()
  }, [])

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await del('/categories/' + deleteTarget._id)
      toast.success(`"${deleteTarget.name}" deleted.`)
      setDeleteTarget(null)
      fetchCategories()
    } catch (err) {
      toast.error(err.detail || 'Delete failed')
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Categories</h1>
        {isAdmin && (
          <button className="btn btn-success" onClick={() => setShowCreate(true)}>
            + Add Category
          </button>
        )}
      </div>

      {loading ? (
        <Skeleton count={5} height={50} />
      ) : categories.length === 0 ? (
        <Empty
          icon="🗂️"
          message="No categories yet."
          action={
            isAdmin && (
              <button className="btn btn-success" onClick={() => setShowCreate(true)}>
                + Create First Category
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
                  <th>Slug</th>
                  <th>Type</th>
                  <th>Status</th>
                  {isAdmin && <th></th>}
                </tr>
              </thead>
              <tbody>
                {categories.map((cat) => (
                  <tr key={cat._id}>
                    <td className="cell-primary">{cat.name}</td>
                    <td className="cell-mono">{cat.slug}</td>
                    <td className="cell-secondary">
                      {cat.parent_id ? 'Subcategory' : 'Top-level'}
                    </td>
                    <td>
                      <span
                        className={`status-badge ${cat.is_active ? 'status-active' : 'status-inactive'}`}
                      >
                        {cat.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    {isAdmin && (
                      <td>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteTarget(cat)}
                        >
                          🗑️
                        </button>
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
        <CreateCatModal
          onClose={() => setShowCreate(false)}
          onSaved={() => {
            setShowCreate(false)
            fetchCategories()
          }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Category"
          message={`Delete "${deleteTarget.name}"? This cannot be undone.`}
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

function CreateCatModal({ onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({ name: '', description: '', parent_id: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const body = { name: form.name, description: form.description }
      if (form.parent_id) body.parent_id = form.parent_id
      await post('/categories/', body)
      toast.success('Category created!')
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Create Category" onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Name *</label>
          <input
            className="form-input"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-textarea"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            rows={3}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Parent ID (for subcategory)</label>
          <input
            className="form-input"
            placeholder="Leave empty for top-level"
            value={form.parent_id}
            onChange={(e) => setForm((f) => ({ ...f, parent_id: e.target.value }))}
          />
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Category'}
        </button>
      </form>
    </Modal>
  )
}

// ─── Variants ────────────────────────────────────────────────────────

export function Variants() {
  const { user } = useAuth()
  const toast = useToast()
  const canEdit = user?.role === 'admin' || user?.role === 'supplier'

  const [productId, setProductId] = useState('')
  const [product, setProduct] = useState(null)
  const [variants, setVariants] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const fetchVariants = async () => {
    if (!productId) return toast.warning('Enter a Product ID first')
    setLoading(true)

    try {
      const [pd, vd] = await Promise.all([
        get('/products/' + productId),
        get('/products/' + productId + '/variants/'),
      ])
      setProduct(pd)
      setVariants(vd.variants || [])
    } catch (err) {
      toast.error(err.detail || 'Product not found')
      setProduct(null)
      setVariants([])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await del('/products/' + productId + '/variants/' + deleteTarget)
      toast.success('Variant deleted.')
      setDeleteTarget(null)
      fetchVariants()
    } catch (err) {
      toast.error(err.detail || 'Delete failed')
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Product Variants</h1>
      </div>

      <div className="search-bar" style={{ marginBottom: 20 }}>
        <div className="search-input-wrapper" style={{ flex: 2 }}>
          <span className="search-icon">🔍</span>
          <input
            className="search-input"
            placeholder="Enter Product ID (MongoDB ObjectId)"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchVariants()}
          />
        </div>
        <button className="btn btn-primary" onClick={fetchVariants}>
          Fetch Variants
        </button>
      </div>

      {product && (
        <div className="product-info-bar">
          <div className="product-info-name">{product.name}</div>
          <div className="product-info-sku">{product.sku}</div>
        </div>
      )}

      {loading ? (
        <Skeleton count={4} height={70} />
      ) : variants.length === 0 && product ? (
        <Empty
          icon="🎨"
          message="No variants for this product."
          action={
            canEdit && (
              <button className="btn btn-success" onClick={() => setShowAdd(true)}>
                + Add First Variant
              </button>
            )
          }
        />
      ) : (
        <div className="variants-list">
          {variants.map((v) => (
            <div key={v.variant_id} className="variant-card">
              <ColorSwatch color={v.color} size={28} />
              {v.image_metadata?.[0] && (
                <img
                  src={v.image_metadata[0].url}
                  alt=""
                  className="variant-thumb"
                  onError={(e) => (e.target.style.display = 'none')}
                />
              )}
              <div className="variant-card-info">
                <div className="variant-card-name">{v.color || 'Default'}</div>
                <div className="variant-card-sku">{v.sku}</div>
                {Object.entries(v.attributes || {}).length > 0 && (
                  <div className="variant-card-attrs">
                    {Object.entries(v.attributes)
                      .map(([k, val]) => `${k}: ${val}`)
                      .join(' · ')}
                  </div>
                )}
              </div>
              <div className="variant-card-pricing">
                <div className="variant-card-price">
                  ₹{Number(v.selling_price).toLocaleString('en-IN')}
                </div>
                <div
                  className={`variant-stock ${
                    v.stock === 0 ? 'out' : v.stock <= 5 ? 'low' : 'ok'
                  }`}
                >
                  {v.stock === 0 ? 'Out of Stock' : `Stock: ${v.stock}`}
                </div>
              </div>
              {canEdit && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => setDeleteTarget(v.variant_id)}
                >
                  🗑️
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {product && canEdit && (
        <button
          className="btn btn-success"
          style={{ marginTop: 16 }}
          onClick={() => setShowAdd(true)}
        >
          + Add Variant
        </button>
      )}

      {showAdd && (
        <AddVariantModal
          productId={productId}
          onClose={() => setShowAdd(false)}
          onSaved={() => {
            setShowAdd(false)
            fetchVariants()
          }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete Variant"
          message="Are you sure? This cannot be undone."
          danger
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

function AddVariantModal({ productId, onClose, onSaved }) {
  const toast = useToast()
  const [variants, setVariants] = useState([
    { color: '', selling_price: '', cost_price: '', stock: 0, attributes: {}, img: '' },
  ])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [attrKey, setAttrKey] = useState('')
  const [attrVal, setAttrVal] = useState('')

  const upd = (i, k, v) =>
    setVariants((p) => p.map((item, idx) => (idx === i ? { ...item, [k]: v } : item)))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const body = {
        variants: variants
          .filter((v) => v.selling_price && v.cost_price)
          .map((v) => ({
            color: v.color,
            selling_price: parseFloat(v.selling_price),
            cost_price: parseFloat(v.cost_price),
            stock: parseInt(v.stock) || 0,
            attributes: v.attributes,
            ...(v.img
              ? { image_metadata: [{ url: v.img, alt_text: v.color, is_primary: true }] }
              : {}),
          })),
      }

      if (body.variants.length === 0) {
        setError('At least one variant with prices is required')
        setLoading(false)
        return
      }

      await post('/products/' + productId + '/variants/', body)
      toast.success(`${body.variants.length} variant(s) added!`)
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Add Variants" onClose={onClose} size="lg">
      <form onSubmit={handleSubmit}>
        {variants.map((v, i) => (
          <div key={i} className="variant-form-item">
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Color</label>
                <input
                  className="form-input"
                  value={v.color}
                  onChange={(e) => upd(i, 'color', e.target.value)}
                  placeholder="e.g. Black"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Image URL</label>
                <input
                  className="form-input"
                  value={v.img}
                  onChange={(e) => upd(i, 'img', e.target.value)}
                  placeholder="https://..."
                />
              </div>
              <div className="form-group">
                <label className="form-label">Selling Price *</label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  value={v.selling_price}
                  onChange={(e) => upd(i, 'selling_price', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Cost Price *</label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  value={v.cost_price}
                  onChange={(e) => upd(i, 'cost_price', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Stock</label>
                <input
                  className="form-input"
                  type="number"
                  min={0}
                  value={v.stock}
                  onChange={(e) => upd(i, 'stock', e.target.value)}
                />
              </div>
            </div>

            {Object.keys(v.attributes).length > 0 && (
              <div className="attr-chips">
                {Object.entries(v.attributes).map(([k, val]) => (
                  <span key={k} className="attr-chip">
                    {k}: {val}
                    <button
                      type="button"
                      onClick={() => {
                        const a = { ...v.attributes }
                        delete a[k]
                        upd(i, 'attributes', a)
                      }}
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="attr-add-row">
              <input
                className="form-input"
                placeholder="Key (e.g. RAM)"
                value={attrKey}
                onChange={(e) => setAttrKey(e.target.value)}
              />
              <input
                className="form-input"
                placeholder="Value (e.g. 8GB)"
                value={attrVal}
                onChange={(e) => setAttrVal(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  if (attrKey && attrVal) {
                    upd(i, 'attributes', { ...v.attributes, [attrKey]: attrVal })
                    setAttrKey('')
                    setAttrVal('')
                  }
                }}
              >
                + Add
              </button>
            </div>
          </div>
        ))}

        <button
          type="button"
          className="btn btn-ghost btn-full"
          style={{ marginBottom: 16 }}
          onClick={() =>
            setVariants((v) => [
              ...v,
              { color: '', selling_price: '', cost_price: '', stock: 0, attributes: {}, img: '' },
            ])
          }
        >
          + Add Another Variant
        </button>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Save Variants'}
        </button>
      </form>
    </Modal>
  )
}

// ─── Profile ─────────────────────────────────────────────────────────

export function Profile() {
  const { user } = useAuth()
  if (!user) return null

  const fields = [
    ['Username', user.username],
    ['Email', user.email],
    ['Full Name', user.full_name || '—'],
    ['Phone', user.phone || '—'],
    ['Role', user.role],
    ['Status', user.status],
    ['Member Since', new Date(user.created_at).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'long', year: 'numeric',
    })],
  ]

  return (
    <div className="page" style={{ maxWidth: 540 }}>
      <div className="page-header">
        <h1 className="page-title">My Profile</h1>
      </div>

      <div className="card">
        <div className="profile-header">
          <div className="profile-avatar">
            {(user.full_name || user.username || '?')[0].toUpperCase()}
          </div>
          <div className="profile-info">
            <div className="profile-name">{user.full_name || user.username}</div>
            <span className={`badge badge-${user.role}`}>{user.role?.replace('_', ' ')}</span>
          </div>
        </div>

        <div className="detail-list">
          {fields.map(([k, v]) => (
            <div key={k} className="detail-row">
              <span className="detail-label">{k}</span>
              <span className="detail-value">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}