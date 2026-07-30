const CURRENCY_LOCALE = { PEN: "es-PE", USD: "en-US" };

/**
 * Formats a product price, or returns null if there's nothing to show yet
 * (price hasn't been defined for this product).
 */
export function formatPrice(price, currency = "PEN") {
  if (price === null || price === undefined) return null;
  const value = Number(price);
  if (Number.isNaN(value)) return null;
  return new Intl.NumberFormat(CURRENCY_LOCALE[currency] || "es-PE", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}
