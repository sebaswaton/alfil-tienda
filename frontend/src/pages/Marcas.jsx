import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import BrandLogo from "../components/BrandLogo";
import { useStaggerReveal } from "../hooks/useReveal";
import "./Marcas.css";

export default function Marcas() {
  const [brands, setBrands] = useState([]);
  const gridRef = useStaggerReveal(70, [brands.length]);

  useEffect(() => {
    api.getBrands().then(setBrands);
  }, []);

  return (
    <div className="container marcas">
      <div className="marcas__head">
        <span className="eyebrow">Alianzas estratégicas</span>
        <h1 className="section-title">Marcas que integramos</h1>
        <p className="marcas__intro">
          Trabajamos con fabricantes líderes en infraestructura de TI para diseñar
          soluciones robustas y soportadas a largo plazo.
        </p>
      </div>

      <div className="marcas__grid" ref={gridRef}>
        {brands.map((b) => (
          <Link
            key={b.id}
            to={`/catalogo?brand=${b.slug}`}
            className="marca-card card bracket-corners"
            style={{ "--brand-accent": b.accent_color }}
          >
            <BrandLogo brand={b} />
            <h3 className="marca-card__name">{b.name}</h3>
            <p className="marca-card__desc">{b.description}</p>
            <span className="marca-card__link mono">Ver productos →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
