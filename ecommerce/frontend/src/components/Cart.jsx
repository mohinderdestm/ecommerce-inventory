import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

function CartItem({ item }) {
  const { removeItem, updateQty } = useCart()
  return (
    <div className="cart-item">
      <div className="cart-item-img">
        {item.image
          ? <img src={item.image} alt={item.product_name} onError={(e) => { e.target.style.display = 'none' }} />
          : <span>📦</span>
        }
      </div>
      <div className="cart-item-info">
        <div className="cart-item-name">{item.product_name}</div>
        {item.variant_label && (
          <div className="cart-item-variant">{item.variant_label}</div>
        )}
        <div className="cart-item-sku">{item.sku}</div>
        <div className="cart-item-price">
          ₹{Number(item.unit_price).toLocaleString('en-IN')}
          <span className="cart-item-unit"> / {item.unit}</span>
        </div>
      </div>
      <div className="cart-item-controls">
        <div className="qty-control">
          <button className="qty-btn" onClick={() => updateQty(item.key, item.quantity - 1)}>−</button>
          <span className="qty-value">{item.quantity}</span>
          <button className="qty-btn" onClick={() => updateQty(item.key, item.quantity + 1)}>+</button>
        </div>
        <div className="cart-item-subtotal">
          ₹{Number(item.unit_price * item.quantity).toLocaleString('en-IN')}
        </div>
        <button className="cart-item-remove" onClick={() => removeItem(item.key)} title="Remove">
          🗑️
        </button>
      </div>
    </div>
  )
}

export default function Cart() {
  const { items, isOpen, setIsOpen, clearCart, totalItems, totalPrice } = useCart()
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleCheckout = () => {
    setIsOpen(false)
    navigate('/orders/create')
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div className="cart-backdrop" onClick={() => setIsOpen(false)} />

      {/* Drawer */}
      <div className="cart-drawer">
        <div className="cart-header">
          <div className="cart-title">
            🛒 Cart
            {totalItems > 0 && (
              <span className="cart-count-badge">{totalItems}</span>
            )}
          </div>
          <div className="cart-header-actions">
            {items.length > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={clearCart}>
                Clear all
              </button>
            )}
            <button className="cart-close" onClick={() => setIsOpen(false)}>✕</button>
          </div>
        </div>

        <div className="cart-body">
          {items.length === 0 ? (
            <div className="cart-empty">
              <div className="cart-empty-icon">🛒</div>
              <p>Your cart is empty</p>
              <p className="cart-empty-sub">Browse products and add items to get started</p>
              <button className="btn btn-primary" onClick={() => setIsOpen(false)}>
                Browse Products
              </button>
            </div>
          ) : (
            <div className="cart-items">
              {items.map((item) => (
                <CartItem key={item.key} item={item} />
              ))}
            </div>
          )}
        </div>

        {items.length > 0 && (
          <div className="cart-footer">
            <div className="cart-summary">
              <div className="cart-summary-row">
                <span>{totalItems} item{totalItems !== 1 ? 's' : ''}</span>
                <span className="cart-summary-total">
                  ₹{Number(totalPrice).toLocaleString('en-IN')}
                </span>
              </div>
            </div>
            <button className="btn btn-success btn-full btn-lg" onClick={handleCheckout}>
              Proceed to Order →
            </button>
            <p className="cart-note">
              You'll be able to choose warehouse and add shipping details on the next page.
            </p>
          </div>
        )}
      </div>
    </>
  )
}