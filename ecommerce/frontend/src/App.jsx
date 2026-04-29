import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import { ToastProvider } from './components/Toast'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import Cart from './components/Cart'
import { Spinner } from './components/UI'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Products from './pages/Products'
import Suppliers from './pages/Suppliers'
import SalesOrders from './pages/SalesOrders'
import CreateOrder from './pages/CreateOrder'
import Warehouses from './pages/Warehouses'
import InventoryMovements from './pages/InventoryMovements'
import PurchaseOrders from './pages/PurchaseOrders'
import CreatePurchaseOrder from './pages/CreatePurchaseOrder'
import AdminUsers from './pages/AdminUsers'
import CreateProduct from './pages/CreateProduct'
import ReportsAnalytics from './pages/ReportsAnalytics'
import { Categories, Variants, Profile } from './pages/OtherPages'
import './App.css'

function PrivateLayout({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="app-loading">
        <div className="app-loading-inner">
          <span className="app-loading-logo">⚡</span>
          <Spinner text="Loading your workspace..." />
        </div>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="layout">
      <Sidebar />
      <div className="main-area">
        <Navbar />
        <main className="main-content">{children}</main>
      </div>
      {/* Cart drawer — renders outside main content, full screen overlay */}
      <Cart />
    </div>
  )
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              {/* Public */}
              <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
              <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

              {/* Private */}
              <Route path="/dashboard" element={<PrivateLayout><Dashboard /></PrivateLayout>} />
              {/* Inventory / Products */}
              <Route path="/products"  element={<PrivateLayout><Products /></PrivateLayout>} />
              <Route path="/products/create" element={<PrivateLayout><CreateProduct /></PrivateLayout>} />
              <Route path="/categories"element={<PrivateLayout><Categories /></PrivateLayout>} />
              <Route path="/variants"  element={<PrivateLayout><Variants /></PrivateLayout>} />
              <Route path="/suppliers" element={<PrivateLayout><Suppliers /></PrivateLayout>} />
              <Route path="/warehouses"element={<PrivateLayout><Warehouses /></PrivateLayout>} />
              <Route path="/movements" element={<PrivateLayout><InventoryMovements /></PrivateLayout>} />
              <Route path="/orders"        element={<PrivateLayout><SalesOrders /></PrivateLayout>} />
              <Route path="/orders/create" element={<PrivateLayout><CreateOrder /></PrivateLayout>} />
              <Route path="/purchase-orders"        element={<PrivateLayout><PurchaseOrders /></PrivateLayout>} />
              <Route path="/purchase-orders/create" element={<PrivateLayout><CreatePurchaseOrder /></PrivateLayout>} />
              <Route path="/reports"                element={<PrivateLayout><ReportsAnalytics /></PrivateLayout>} />
              
              {/* Admin */}
              <Route path="/admin/users"            element={<PrivateLayout><AdminUsers /></PrivateLayout>} />
              <Route path="/profile"   element={<PrivateLayout><Profile /></PrivateLayout>} />

              {/* Redirects */}
              <Route path="/"  element={<Navigate to="/dashboard" replace />} />
              <Route path="*"  element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </CartProvider>
    </AuthProvider>
  )
}