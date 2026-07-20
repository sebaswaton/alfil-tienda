import "./ProductVisual.css";

export default function ProductVisual({ product, size = "md" }) {
  if (!product) return null;
  const { brand, sku } = product;
  const accent = brand?.accent_color || "#23e0c4";
  const brandMark = (brand?.name || "Alfil").slice(0, 3).toUpperCase();

  return (
    <div
      className={`product-visual product-visual--${size}`}
      style={{ "--pv-accent": accent }}
    >
      <span className="product-visual__orb" aria-hidden="true">
        <span className="product-visual__mark">{brandMark}</span>
      </span>
      <span className="product-visual__sku mono">{sku}</span>
      <span className="product-visual__brand mono">{brand?.name}</span>
    </div>
  );
}
