import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Attach auth token if available
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('username')
        window.location.href = '/login'
      } else if (status === 403) {
        console.error('Forbidden - insufficient permissions')
      } else if (status === 500) {
        console.error('Server error - please try again later')
      }
    } else if (error.request) {
      console.error('Network error - server unreachable')
    }
    return Promise.reject(error)
  },
)

export default apiClient
