import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

const NAV = [
  {
    label: 'Main',
    links: [{ to: '/dashboard', icon: '🏠', label: 'Dashboard' }],
  },
  {
    label: 'Catalog',
    links: [
      { to: '/products', icon: '📦', label: 'Products' },
      { to: '/categories', icon: '🗂️', label: 'Categories' },
      { to: '/variants', icon: '🎨', label: 'Variants' },
    ],
  },
  {
    label: 'Suppliers',
    links: [{ to: '/suppliers', icon: '🏭', label: 'Suppliers' }],
  },
  {
    label: 'Warehouse',
    roles: ['admin', 'warehouse_staff', 'inventory_manager'],
    links: [
      { to: '/warehouses', icon: '🏗️', label: 'Warehouses' },
      { to: '/movements', icon: '📋', label: 'Movements' }
    ],
  },
  {
    label: 'Purchases',
    roles: ['admin', 'inventory_manager'],
    links: [
      { to: '/purchase-orders', icon: '🛒', label: 'Purchase Orders' },
      { to: '/purchase-orders/create', icon: '➕', label: 'New PO' },
    ],
  },
  {
    label: 'Admin',
    roles: ['admin'],
    links: [
      { to: '/admin/users', icon: '👥', label: 'Users' },
    ],
  },
  {
    label: 'Orders',
    links: [
      { to: '/orders', icon: '🧾', label: 'Sales Orders' },
      { to: '/orders/create', icon: '➕', label: 'New Order' },
    ],
  },
  {
    label: 'Account',
    links: [{ to: '/profile', icon: '👤', label: 'My Profile' }],
  },
]

export default function Sidebar() {
  const { user } = useAuth()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="sidebar-toggle"
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Toggle sidebar"
      >
        {collapsed ? '☰' : '✕'}
      </button>

      <nav className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-logo">⚡</span>
          {!collapsed && <span className="sidebar-brand">Inventory</span>}
        </div>

        <div className="sidebar-nav">
          {NAV.map((group) => {
            if (group.roles && !group.roles.includes(user?.role)) return null
            return (
              <div key={group.label} className="sidebar-group">
                {!collapsed && <div className="sidebar-label">{group.label}</div>}
                {group.links.map((link) => (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    className={({ isActive }) =>
                      `sidebar-link ${isActive ? 'active' : ''}`
                    }
                    title={link.label}
                    onClick={() => {
                      // Auto-close on mobile
                      if (window.innerWidth < 768) setCollapsed(true)
                    }}
                  >
                    <span className="sidebar-icon">{link.icon}</span>
                    {!collapsed && <span className="sidebar-text">{link.label}</span>}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </div>

        <button
          className="sidebar-collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? '→' : '←'}
        </button>
      </nav>

      {/* Mobile overlay */}
      {!collapsed && (
        <div className="sidebar-overlay" onClick={() => setCollapsed(true)} />
      )}
    </>
  )
}