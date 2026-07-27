const CSRF_COOKIE = 'alfil_admin_csrf'

function csrfToken() {
  const prefix = `${CSRF_COOKIE}=`
  const entry = document.cookie.split('; ').find((item) => item.startsWith(prefix))
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : ''
}

export class ApiError extends Error {
  constructor(message, status, details = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

function errorMessage(body, status) {
  if (Array.isArray(body?.detail)) {
    return body.detail.map((item) => `${item.loc?.at(-1) || 'Campo'}: ${item.msg}`).join(' · ')
  }
  return body?.detail || body?.message || `No se pudo completar la solicitud (${status})`
}

export async function apiRequest(path, options = {}) {
  const method = options.method || 'GET'
  const headers = { Accept: 'application/json', ...options.headers }
  const isFormData = options.body instanceof FormData
  if (options.body !== undefined && !isFormData) headers['Content-Type'] = 'application/json'
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())) {
    const token = csrfToken()
    if (token) headers['X-CSRF-Token'] = token
  }
  const response = await fetch(path, {
    ...options,
    method,
    headers,
    credentials: 'include',
    body: options.body === undefined ? undefined : isFormData ? options.body : JSON.stringify(options.body),
  })
  if (response.status === 204) return null
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(errorMessage(body, response.status), response.status, body?.detail)
  return body
}

export function queryString(params) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, value)
  })
  const result = query.toString()
  return result ? `?${result}` : ''
}
