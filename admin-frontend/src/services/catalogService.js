import { apiRequest, queryString } from '../api/client'

export const productService = {
  list: (params) => apiRequest(`/api/admin/products${queryString(params)}`),
  get: (id) => apiRequest(`/api/admin/products/${id}`),
  create: (data) => apiRequest('/api/admin/products', { method: 'POST', body: data }),
  update: (id, data) => apiRequest(`/api/admin/products/${id}`, { method: 'PATCH', body: data }),
  status: (id, status) => apiRequest(`/api/admin/products/${id}/status`, { method: 'PATCH', body: { status } }),
}

export const mediaService = {
  images: {
    list: (productId) => apiRequest(`/api/admin/products/${productId}/images`),
    upload: (productId, data) => apiRequest(`/api/admin/products/${productId}/images`, { method: 'POST', body: data }),
    update: (productId, imageId, data) => apiRequest(`/api/admin/products/${productId}/images/${imageId}`, { method: 'PATCH', body: data }),
    replace: (productId, imageId, data) => apiRequest(`/api/admin/products/${productId}/images/${imageId}/file`, { method: 'PUT', body: data }),
    order: (productId, orderedIds) => apiRequest(`/api/admin/products/${productId}/images/order`, { method: 'PUT', body: { ordered_ids: orderedIds } }),
    remove: (productId, imageId) => apiRequest(`/api/admin/products/${productId}/images/${imageId}`, { method: 'DELETE' }),
  },
  documents: {
    list: (productId) => apiRequest(`/api/admin/products/${productId}/documents`),
    upload: (productId, data) => apiRequest(`/api/admin/products/${productId}/documents`, { method: 'POST', body: data }),
    replace: (productId, documentId, data) => apiRequest(`/api/admin/products/${productId}/documents/${documentId}/file`, { method: 'PUT', body: data }),
    remove: (productId, documentId) => apiRequest(`/api/admin/products/${productId}/documents/${documentId}`, { method: 'DELETE' }),
  },
}

function taxonomyService(resource, assetPath) {
  const base = `/api/admin/${resource}`
  return {
    list: (params = {}) => apiRequest(`${base}${queryString(params)}`),
    get: (id) => apiRequest(`${base}/${id}`),
    create: (data) => apiRequest(base, { method: 'POST', body: data }),
    update: (id, data) => apiRequest(`${base}/${id}`, { method: 'PATCH', body: data }),
    status: (id, is_active) => apiRequest(`${base}/${id}/status`, { method: 'PATCH', body: { is_active } }),
    remove: (id) => apiRequest(`${base}/${id}`, { method: 'DELETE' }),
    asset: {
      replace: (id, data) => apiRequest(`${base}/${id}/${assetPath}`, { method: 'PUT', body: data }),
      remove: (id) => apiRequest(`${base}/${id}/${assetPath}`, { method: 'DELETE' }),
    },
  }
}

export const brandService = taxonomyService('brands', 'logo')
export const categoryService = taxonomyService('categories', 'image')
