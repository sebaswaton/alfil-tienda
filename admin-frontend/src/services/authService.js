import { apiRequest } from '../api/client'

export const authService = {
  login: (credentials) => apiRequest('/api/admin/auth/login', { method: 'POST', body: credentials }),
  me: () => apiRequest('/api/admin/auth/me'),
  logout: () => apiRequest('/api/admin/auth/logout', { method: 'POST' }),
}
