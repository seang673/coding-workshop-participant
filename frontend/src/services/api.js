import axios from 'axios'

const configuredApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const configuredApiPathPrefix = import.meta.env.VITE_API_PATH_PREFIX || ''

const shouldUseDefaultCloudPrefix =
  typeof window !== 'undefined' &&
  configuredApiUrl.replace(/\/+$/, '') === window.location.origin

const apiPathPrefix = configuredApiPathPrefix ||
  (shouldUseDefaultCloudPrefix ? '/api/app' : '')

const normalizedApiUrl = configuredApiUrl.replace(/\/+$/, '')
const normalizedApiPathPrefix = apiPathPrefix
  ? `/${apiPathPrefix.replace(/^\/+|\/+$/g, '')}`
  : ''

const baseURL = `${normalizedApiUrl}${normalizedApiPathPrefix}`

const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default api
