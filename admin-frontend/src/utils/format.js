export function formatDate(value) {
  return value ? new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium' }).format(new Date(value)) : '—'
}

export function stockLabel(product) {
  if (product.available_stock <= 0) return 'Sin stock'
  if (product.available_stock === 1) return '1 unidad disponible'
  return `${product.available_stock} unidades disponibles`
}
