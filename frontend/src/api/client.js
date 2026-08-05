// `config.js` lets a cPanel deployment set the API hostname after `npm build`
// without rebuilding the frontend. Docker/VM builds can keep using VITE_API_URL,
// and local development still falls back to the same-origin Vite proxy.
const runtimeApiUrl = window.__ALFIL_CONFIG__?.API_URL;
const API_URL = (runtimeApiUrl ?? import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    headers: isFormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status}`);
  }
  return res.json();
}

async function adminRequest(path, options = {}) {
  const { responseType = "json", ...requestOptions } = options;
  const token = localStorage.getItem("hwstore_admin_token");
  const isFormData = requestOptions.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...requestOptions.headers,
  };
  const res = await fetch(`${API_URL}${path}`, { ...requestOptions, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message;
    const error = new Error(message || `Error ${res.status}`);
    error.status = res.status;
    error.detail = detail;
    throw error;
  }
  if (res.status === 204) return null;
  if (responseType === "blob") {
    const disposition = res.headers.get("Content-Disposition") || "";
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    return {
      blob: await res.blob(),
      filename: filenameMatch?.[1] || "plantilla_importacion_productos.xlsx",
    };
  }
  return res.json();
}

export const api = {
  getBrands: () => request("/api/brands"),
  getBrand: (slug) => request(`/api/brands/${slug}`),
  getCategories: () => request("/api/categories"),
  getProducts: (params = {}) => {
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""))
    ).toString();
    return request(`/api/products${query ? `?${query}` : ""}`);
  },
  getProduct: (slug) => request(`/api/products/${slug}`),
  getRelated: (slug) => request(`/api/products/${slug}/related`),
  createInquiry: (payload) =>
    request("/api/inquiries", { method: "POST", body: JSON.stringify(payload) }),
};

export const adminApi = {
  login: (payload) =>
    adminRequest("/api/admin/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: () => adminRequest("/api/admin/me"),
  logout: () => adminRequest("/api/admin/logout", { method: "POST" }),
  getProducts: (params = {}) => {
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, value]) => value !== ""))
    ).toString();
    return adminRequest(`/api/admin/products${query ? `?${query}` : ""}`);
  },
  getProduct: (id) => adminRequest(`/api/admin/products/${id}`),
  downloadProductTemplate: () =>
    adminRequest("/api/admin/products/template", { responseType: "blob" }),
  validateProductImport: (formData) =>
    adminRequest("/api/admin/products/import/validate", {
      method: "POST",
      body: formData,
    }),
  importProducts: (formData) =>
    adminRequest("/api/admin/products/import", {
      method: "POST",
      body: formData,
    }),
  validateProductMediaZip: (formData) =>
    adminRequest("/api/admin/products/media-import/validate", {
      method: "POST",
      body: formData,
    }),
  importProductMediaZip: (formData) =>
    adminRequest("/api/admin/products/media-import", {
      method: "POST",
      body: formData,
    }),
  createProduct: (payload) =>
    adminRequest("/api/admin/products", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProduct: (id, payload) =>
    adminRequest(`/api/admin/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  patchProduct: (id, payload) =>
    adminRequest(`/api/admin/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  setProductStatus: (id, status) =>
    adminRequest(`/api/admin/products/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  archiveProduct: (id) =>
    adminRequest(`/api/admin/products/${id}`, { method: "DELETE" }),
  uploadMedia: (slug, formData) =>
    adminRequest(`/api/products/${slug}/media`, {
      method: "POST",
      body: formData,
    }),
  getImages: (id) => adminRequest(`/api/admin/products/${id}/images`),
  uploadImage: (id, formData) =>
    adminRequest(`/api/admin/products/${id}/images`, { method: "POST", body: formData }),
  updateImage: (id, imageId, payload) =>
    adminRequest(`/api/admin/products/${id}/images/${imageId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteImage: (id, imageId) =>
    adminRequest(`/api/admin/products/${id}/images/${imageId}`, { method: "DELETE" }),
  getDocuments: (id) => adminRequest(`/api/admin/products/${id}/documents`),
  uploadDocument: (id, formData) =>
    adminRequest(`/api/admin/products/${id}/documents`, { method: "POST", body: formData }),
  deleteDocument: (id, documentId) =>
    adminRequest(`/api/admin/products/${id}/documents/${documentId}`, { method: "DELETE" }),
  listTaxonomy: (resource, params = {}) => {
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, value]) => value !== ""))
    ).toString();
    return adminRequest(`/api/admin/${resource}${query ? `?${query}` : ""}`);
  },
  createTaxonomy: (resource, payload) =>
    adminRequest(`/api/admin/${resource}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateTaxonomy: (resource, id, payload) =>
    adminRequest(`/api/admin/${resource}/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  setTaxonomyStatus: (resource, id, isActive) =>
    adminRequest(`/api/admin/${resource}/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    }),
  deleteTaxonomy: (resource, id) =>
    adminRequest(`/api/admin/${resource}/${id}`, { method: "DELETE" }),
  replaceTaxonomyAsset: (resource, id, asset, formData) =>
    adminRequest(`/api/admin/${resource}/${id}/${asset}`, { method: "PUT", body: formData }),
};
