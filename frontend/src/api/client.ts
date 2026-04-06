import axios from 'axios'

const BASE_URL = 'http://localhost:8000/api/'

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ── Token refresh state ──────────────────────────────────────────────────────
let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

function flushQueue(token: string) {
  refreshQueue.forEach((cb) => cb(token))
  refreshQueue = []
}

function clearAuth() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('username')
  window.location.href = '/login'
}

// ── Request interceptor ──────────────────────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor ─────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only attempt refresh on 401, and not on the refresh/login endpoints themselves
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('auth/refresh') &&
      !originalRequest.url?.includes('auth/login')
    ) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        clearAuth()
        return Promise.reject(error)
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await axios.post(`${BASE_URL}auth/refresh/`, { refresh: refreshToken })
        const newToken: string = res.data.access
        localStorage.setItem('access_token', newToken)
        apiClient.defaults.headers.common.Authorization = `Bearer ${newToken}`
        flushQueue(newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalRequest)
      } catch {
        clearAuth()
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response?.status === 403) {
      console.error('Forbidden - insufficient permissions')
    } else if (error.response?.status === 500) {
      console.error('Server error - please try again later')
    } else if (!error.response) {
      console.error('Network error - server unreachable')
    }

    return Promise.reject(error)
  },
)

export default apiClient
