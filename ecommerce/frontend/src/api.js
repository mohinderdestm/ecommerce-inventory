const BASE = '/api/v1'

function getToken() {
  return localStorage.getItem('token') || ''
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

export async function api(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  try {
    const res = await fetch(BASE + path, { ...options, headers })
    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      // Handle auth expiry
      if (res.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        throw new ApiError(401, 'Session expired. Please login again.')
      }
      throw new ApiError(res.status, data.detail || `Request failed (${res.status})`)
    }

    return data
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError(0, 'Network error. Please check your connection.')
  }
}

export const get = (path) => api(path)
export const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) })
export const put = (path, body) => api(path, { method: 'PUT', body: JSON.stringify(body) })
export const patch = (path, body) => api(path, { method: 'PATCH', body: JSON.stringify(body) })
export const del = (path, body) =>
  api(path, { method: 'DELETE', body: body ? JSON.stringify(body) : undefined })