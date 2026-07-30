import "./BrandLogo.css";
import { publicAsset } from "../utils/publicAsset";

/**
 * Renders a brand's real logo on a light rounded plate for guaranteed
 * legibility on the dark UI. Falls back to a wordmark if no logo.
 */
export default function BrandLogo({ brand, className = "" }) {
  return (
    <div className={"brand-logo " + className} style={{ "--brand-accent": brand.accent_color }}>
      <div className="brand-logo__plate">
        {brand.logo_url ? (
          <img src={publicAsset(brand.logo_url)} alt={brand.name} loading="lazy" />
        ) : (
          <span className="brand-logo__wordmark">{brand.name}</span>
        )}
      </div>
    </div>
  );
}
