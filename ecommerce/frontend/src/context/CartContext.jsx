import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('cart') || '[]')
    } catch {
      return []
    }
  })
  const [isOpen, setIsOpen] = useState(false)

  // Persist to localStorage whenever items change
  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(items))
  }, [items])

  const addItem = useCallback((product, variant = null, quantity = 1) => {
    const key = variant ? `${product._id}__${variant.variant_id}` : product._id
    setItems((prev) => {
      const existing = prev.find((i) => i.key === key)
      if (existing) {
        return prev.map((i) =>
          i.key === key ? { ...i, quantity: i.quantity + quantity } : i,
        )
      }
      return [
        ...prev,
        {
          key,
          product_id: product._id,
          product_name: product.name,
          sku: variant?.sku || product.sku,
          image: product.image_metadata?.find((m) => m.is_primary)?.url
            || product.image_metadata?.[0]?.url
            || null,
          variant_id: variant?.variant_id || null,
          variant_label: variant
            ? [variant.color, ...Object.values(variant.attributes || {})].filter(Boolean).join(' · ')
            : null,
          unit_price: variant?.selling_price ?? product.selling_price,
          quantity,
          unit: product.unit,
        },
      ]
    })
  }, [])

  const removeItem = useCallback((key) => {
    setItems((prev) => prev.filter((i) => i.key !== key))
  }, [])

  const updateQty = useCallback((key, quantity) => {
    if (quantity <= 0) {
      setItems((prev) => prev.filter((i) => i.key !== key))
    } else {
      setItems((prev) =>
        prev.map((i) => (i.key === key ? { ...i, quantity } : i)),
      )
    }
  }, [])

  const clearCart = useCallback(() => setItems([]), [])

  const totalItems = items.reduce((s, i) => s + i.quantity, 0)
  const totalPrice = items.reduce((s, i) => s + i.unit_price * i.quantity, 0)

  return (
    <CartContext.Provider
      value={{
        items,
        isOpen,
        setIsOpen,
        addItem,
        removeItem,
        updateQty,
        clearCart,
        totalItems,
        totalPrice,
      }}
    >
      {children}
    </CartContext.Provider>
  )
}

export const useCart = () => {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}