import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { post } from '../api'
import { useToast } from '../components/Toast'
import { Alert } from '../components/UI'

const ROLES = [
  { value: 'customer', label: 'Customer', desc: 'Browse and place orders' },
  { value: 'supplier', label: 'Supplier', desc: 'Manage product supply' },
  { value: 'warehouse_staff', label: 'Warehouse Staff', desc: 'Manage inventory' },
  { value: 'admin', label: 'Admin', desc: 'Full platform access' },
]

export default function Register() {
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    phone: '',
    role: 'customer',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await post('/auth/register', form)
      toast.success('Account created successfully! Please sign in.')
      navigate('/login')
    } catch (err) {
      setError(err.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container" style={{ maxWidth: 520 }}>
        <div className="auth-header">
          <div className="auth-logo">⚡</div>
          <h1 className="auth-title">Create Account</h1>
          <p className="auth-subtitle">Join the Ecommerce Platform</p>
        </div>

        <div className="auth-card">
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Username *</label>
                <input
                  className="form-input"
                  placeholder="john_doe"
                  value={form.username}
                  onChange={(e) => set('username', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  className="form-input"
                  placeholder="John Doe"
                  value={form.full_name}
                  onChange={(e) => set('full_name', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email *</label>
                <input
                  className="form-input"
                  type="email"
                  placeholder="user@example.com"
                  value={form.email}
                  onChange={(e) => set('email', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input
                  className="form-input"
                  placeholder="+91-9876543210"
                  value={form.phone}
                  onChange={(e) => set('phone', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password *</label>
                <input
                  className="form-input"
                  type="password"
                  placeholder="Min 8 chars, 1 uppercase, 1 digit"
                  value={form.password}
                  onChange={(e) => set('password', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <select
                  className="form-select"
                  value={form.role}
                  onChange={(e) => set('role', e.target.value)}
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label} — {r.desc}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {error && <Alert type="error">{error}</Alert>}

            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? (
                <span className="btn-loading">
                  <span className="btn-spinner" />
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <p className="auth-footer">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}