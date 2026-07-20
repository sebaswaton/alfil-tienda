import { useState } from "react";
import ProductVisual from "./ProductVisual";
import "./ProductGallery.css";

export default function ProductGallery({ product }) {
  const images = product?.images || [];
  const [active, setActive] = useState(0);

  // No real photos → branded schematic visual
  if (images.length === 0) {
    return (
      <div className="product-gallery product-gallery--schematic">
        <ProductVisual product={product} size="lg" />
        <p className="product-gallery__note mono">
          Imagen referencial · foto de producto disponible bajo cotización
        </p>
      </div>
    );
  }

  const accent = product.brand?.accent_color || "var(--accent)";

  return (
    <div className="product-gallery" style={{ "--pg-accent": accent }}>
      <div className="product-gallery__stage bracket-corners">
        <span className="product-gallery__badge mono">{product.brand?.name}</span>
        <img
          key={active}
          src={images[active].url}
          alt={images[active].alt || product.name}
          className="product-gallery__main"
          loading="eager"
        />
        <span className="product-gallery__index mono">
          {String(active + 1).padStart(2, "0")} / {String(images.length).padStart(2, "0")}
        </span>
      </div>

      {images.length > 1 && (
        <div className="product-gallery__thumbs">
          {images.map((img, i) => (
            <button
              key={img.id ?? i}
              className={"product-gallery__thumb" + (i === active ? " is-active" : "")}
              onClick={() => setActive(i)}
              aria-label={`Ver imagen ${i + 1}`}
            >
              <img src={img.url} alt={img.alt || ""} loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
