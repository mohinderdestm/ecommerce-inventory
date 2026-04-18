import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { get } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Rehydrate from localStorage, then optionally verify with /auth/me
  useEffect(() => {
    const stored = localStorage.getItem('user')
    const token = localStorage.getItem('token')

    if (stored && token) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }

      // Verify token is still valid (non-blocking)
      get('/auth/me')
        .then((freshUser) => {
          setUser(freshUser)
          localStorage.setItem('user', JSON.stringify(freshUser))
        })
        .catch(() => {
          localStorage.removeItem('user')
          localStorage.removeItem('token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback((userData, token) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }, [])

  const updateUser = useCallback((updatedData) => {
    setUser((prev) => {
      const merged = { ...prev, ...updatedData }
      localStorage.setItem('user', JSON.stringify(merged))
      return merged
    })
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}