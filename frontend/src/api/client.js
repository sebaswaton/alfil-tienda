// Empty base → same-origin "/api/*", which the Vite dev proxy forwards to the
// backend. This keeps everything on one port (works through a single tunnel).
const API_URL = import.meta.env.VITE_API_URL ?? "";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status}`);
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
