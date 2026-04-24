import { useState, useEffect } from 'react'
import { get, put } from '../api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import { Alert, Empty, Modal, Skeleton } from '../components/UI'

function UserFormModal({ user, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    role: user.role,
    status: user.status || (user.is_active ? 'active' : 'inactive'),
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await put(`/users/${user._id}`, form)
      toast.success('User updated successfully!')
      onSaved()
    } catch (err) {
      setError(err.detail || 'Failed to update user')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={`Edit User: ${user.username}`} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Role</label>
          <select
            className="form-select"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="customer">Customer</option>
            <option value="supplier">Supplier</option>
            <option value="warehouse_staff">Warehouse Staff</option>
            <option value="inventory_manager">Inventory Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Status</label>
          <select
            className="form-select"
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>

        {error && <Alert type="error">{error}</Alert>}

        <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
    </Modal>
  )
}

export default function AdminUsers() {
  const { user: currentUser } = useAuth()
  const toast = useToast()

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [editUser, setEditUser] = useState(null)

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const data = await get('/users/?page_size=100')
      setUsers(data.users || [])
    } catch (err) {
      toast.error(err.detail || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">User Management</h1>
      </div>

      {loading ? (
        <Skeleton count={5} height={60} />
      ) : users.length === 0 ? (
        <Empty icon="👥" message="No users found." />
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u._id}>
                    <td className="cell-primary">{u.username}</td>
                    <td>{u.full_name || '—'}</td>
                    <td className="cell-mono">{u.email}</td>
                    <td>
                      <span style={{ textTransform: 'capitalize' }}>
                        {u.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge status-${u.is_active ? 'active' : 'inactive'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      {u._id !== currentUser?._id && (
                        <div className="table-actions">
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setEditUser(u)}
                          >
                            ✏️ Edit Role
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editUser && (
        <UserFormModal
          user={editUser}
          onClose={() => setEditUser(null)}
          onSaved={() => {
            setEditUser(null)
            fetchUsers()
          }}
        />
      )}
    </div>
  )
}
