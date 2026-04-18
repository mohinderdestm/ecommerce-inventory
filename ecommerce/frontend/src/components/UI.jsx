const STATUS_LABELS = {
  active: 'Available',
  inactive: 'Unavailable',
  out_of_stock: 'Out of Stock',
  discontinued: 'Discontinued',
}

export function StatusBadge({ status }) {
  return (
    <span className={`status-badge status-${status}`}>
      {STATUS_LABELS[status] || status}
    </span>
  )
}

export function Alert({ type = 'info', children, onDismiss }) {
  return (
    <div className={`alert alert-${type}`}>
      <span>{children}</span>
      {onDismiss && (
        <button className="alert-dismiss" onClick={onDismiss}>
          ✕
        </button>
      )}
    </div>
  )
}

export function Spinner({ text = 'Loading...' }) {
  return (
    <div className="spinner-container">
      <div className="spinner" />
      <p className="spinner-text">{text}</p>
    </div>
  )
}

export function Skeleton({ width = '100%', height = 20, radius = 6, count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ width, height, borderRadius: radius, marginBottom: 8 }}
        />
      ))}
    </>
  )
}

export function Empty({ icon = '📭', message = 'Nothing here yet.', action }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <p className="empty-message">{message}</p>
      {action && action}
    </div>
  )
}

export function Modal({ title, onClose, children, size = 'md' }) {
  // Prevent body scroll when modal is open
  if (typeof document !== 'undefined') {
    document.body.style.overflow = 'hidden'
  }

  const handleClose = () => {
    document.body.style.overflow = ''
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && handleClose()}>
      <div className={`modal modal-${size}`}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={handleClose}>
            ✕
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function ConfirmDialog({ title, message, onConfirm, onCancel, danger = false }) {
  return (
    <Modal title={title} onClose={onCancel} size="sm">
      <p style={{ color: 'var(--text-muted)', marginBottom: 20, fontSize: '0.88rem' }}>
        {message}
      </p>
      <div className="confirm-actions">
        <button className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm}>
          Confirm
        </button>
      </div>
    </Modal>
  )
}

export const COLOR_MAP = {
  black: '#1a1a1a',
  white: '#f8fafc',
  red: '#ef4444',
  blue: '#3b82f6',
  green: '#22c55e',
  yellow: '#eab308',
  purple: '#a855f7',
  pink: '#ec4899',
  orange: '#f97316',
  grey: '#6b7280',
  gray: '#6b7280',
  gold: '#d97706',
  silver: '#94a3b8',
  brown: '#92400e',
  navy: '#1e3a5f',
  cyan: '#06b6d4',
  lavender: '#c4b5fd',
  maroon: '#9f1239',
  'midnight black': '#0a0a0a',
  'space gray': '#374151',
  'rose gold': '#f59e8b',
}

export function ColorSwatch({ color, size = 14 }) {
  const bg = COLOR_MAP[color?.toLowerCase()?.trim()] || '#475569'
  return <span className="swatch" title={color || 'Unknown'} style={{ background: bg, width: size, height: size }} />
}

export function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.ceil(total / pageSize)
  if (totalPages <= 1) return null

  // Generate page numbers with ellipsis
  const getPages = () => {
    const pages = []
    const delta = 2
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= page - delta && i <= page + delta)) {
        pages.push(i)
      } else if (pages[pages.length - 1] !== '...') {
        pages.push('...')
      }
    }
    return pages
  }

  return (
    <div className="pagination">
      <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Prev
      </button>
      <div className="pagination-pages">
        {getPages().map((p, i) =>
          p === '...' ? (
            <span key={`ellipsis-${i}`} className="pagination-ellipsis">
              …
            </span>
          ) : (
            <button
              key={p}
              className={`pagination-page ${page === p ? 'active' : ''}`}
              onClick={() => onChange(p)}
            >
              {p}
            </button>
          ),
        )}
      </div>
      <button className="btn btn-ghost btn-sm" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Next →
      </button>
    </div>
  )
}

export function OrderStatus({ status }) {
  const icons = {
    draft: '📝',
    confirmed: '✅',
    packed: '📦',
    shipped: '🚚',
    delivered: '✓',
    cancelled: '✕',
    returned: '↩',
  }
  return (
    <span className={`status-badge status-${status}`}>
      {icons[status] || ''} {status}
    </span>
  )
}

export function StatCard({ label, value, sub, color, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ color }}>
        {icon}
      </div>
      <div className="stat-info">
        <div className="stat-label">{label}</div>
        <div className="stat-value" style={{ color }}>
          {value}
        </div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
    </div>
  )
}