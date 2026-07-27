export function formatAvailability(stock) {
  if (stock <= 0) return "Sin stock";
  if (stock === 1) return "1 unidad disponible";
  return `${stock} unidades disponibles`;
}
