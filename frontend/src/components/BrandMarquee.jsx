import { Link } from "react-router-dom";
import BrandLogo from "./BrandLogo";
import "./BrandMarquee.css";

export default function BrandMarquee({ brands }) {
  if (!brands?.length) return null;
  // Duplicate the list so the track can loop seamlessly.
  const loop = [...brands, ...brands];

  return (
    <div className="brand-marquee" aria-label="Marcas aliadas">
      <div className="brand-marquee__track">
        {loop.map((b, i) => (
          <Link
            key={`${b.id}-${i}`}
            to={`/catalogo?brand=${b.slug}`}
            className="brand-marquee__item brand-logo--interactive brand-logo--sm"
            aria-hidden={i >= brands.length}
            tabIndex={i >= brands.length ? -1 : 0}
          >
            <BrandLogo brand={b} />
          </Link>
        ))}
      </div>
    </div>
  );
}
