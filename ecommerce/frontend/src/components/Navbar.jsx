import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useNavigate } from 'react-router-dom'

const ROLE_COLORS = {
  admin: 'badge-admin',
  customer: 'badge-customer',
  supplier: 'badge-supplier',
  warehouse_staff: 'badge-warehouse_staff',
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const { totalItems, setIsOpen } = useCart()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">⚡</span>
        <span className="navbar-title">Smart Inventory</span>
      </div>

      {user && (
        <div className="navbar-right">
          {/* Cart button — only for customers */}
          {user.role === 'customer' && (
            <button className="cart-nav-btn" onClick={() => setIsOpen(true)}>
              🛒
              {totalItems > 0 && (
                <span className="cart-nav-badge">{totalItems > 99 ? '99+' : totalItems}</span>
              )}
            </button>
          )}

          <span className={`badge ${ROLE_COLORS[user.role] || ''}`}>
            {user.role?.replace('_', ' ')}
          </span>
          <div className="navbar-user">
            <div className="navbar-avatar">
              {(user.full_name || user.username || '?')[0].toUpperCase()}
            </div>
            <span className="navbar-username">{user.full_name || user.username}</span>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
            ↪ Logout
          </button>
        </div>
      )}
    </header>
  )
}