import { Link } from "react-router-dom";
import ProductVisual from "./ProductVisual";
import { formatPrice } from "../utils/format";
import "./ProductCard.css";

export default function ProductCard({ product }) {
  const cover = product.images?.[0];
  const price = formatPrice(product.price, product.currency);

  return (
    <Link to={`/producto/${product.slug}`} className="product-card card bracket-corners">
      <div className="product-card__media">
        {cover ? (
          <div className="product-card__photo">
            <span className="product-card__brand-badge mono">{product.brand?.name}</span>
            <img src={cover.url} alt={cover.alt || product.name} loading="lazy" />
          </div>
        ) : (
          <ProductVisual product={product} />
        )}
      </div>

      <div className="product-card__body">
        <span className="tag product-card__cat">{product.category?.name}</span>
        <h3 className="product-card__name">{product.name}</h3>
        <p className="product-card__desc">{product.short_description}</p>
        {price && <div className="product-card__price">{price}</div>}
        <div className="product-card__foot">
          <span className="mono product-card__stock">{product.stock_note}</span>
          <span className="product-card__arrow mono" aria-hidden="true">Ver ficha →</span>
        </div>
      </div>
    </Link>
  );
}
