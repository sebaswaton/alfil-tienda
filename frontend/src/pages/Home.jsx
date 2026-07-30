import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import BrandMarquee from "../components/BrandMarquee";
import ProductCard from "../components/ProductCard";
import TrustRow from "../components/TrustRow";
import { useReveal, useStaggerReveal } from "../hooks/useReveal";
import { useTilt } from "../hooks/useTilt";
import { publicAsset } from "../utils/publicAsset";
import "./Home.css";

const HERO_SLIDES = [
  {
    src: `${import.meta.env.BASE_URL}hero/carousel/carrusel-1.png?v=4`,
    alt: "Infraestructura de TI para empresas: laptop, servidor, switch y punto de acceso.",
  },
  {
    src: `${import.meta.env.BASE_URL}hero/carousel/carrusel-2.png?v=4`,
    alt: "Soluciones de cómputo Alfil Store: tablet, laptop empresarial y equipo compacto.",
  },
  {
    src: `${import.meta.env.BASE_URL}hero/carousel/carrusel-3.png?v=4`,
    alt: "Infraestructura y conectividad: impresora empresarial, redes y grupo electrógeno.",
  },
];

function HeroCarousel() {
  const [activeSlide, setActiveSlide] = useState(0);
  const [paused, setPaused] = useState(false);

  const goTo = (index) => {
    setActiveSlide((index + HERO_SLIDES.length) % HERO_SLIDES.length);
  };

  const handleKeyDown = (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      goTo(activeSlide - 1);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      goTo(activeSlide + 1);
    }
  };

  useEffect(() => {
    if (paused) return undefined;
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % HERO_SLIDES.length);
    }, 6500);
    return () => window.clearInterval(timer);
  }, [paused]);

  return (
    <div
      className="hero-carousel fade-up"
      role="region"
      aria-roledescription="carrusel"
      aria-label="Presentación de soluciones Alfil"
      tabIndex="0"
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setPaused(false);
      }}
    >
      <div
        className="hero-carousel__track"
        style={{ transform: `translateX(-${activeSlide * 100}%)` }}
      >
        {HERO_SLIDES.map((slide, index) => (
          <div
            className="hero-carousel__slide"
            key={slide.src}
            aria-hidden={index !== activeSlide}
          >
            <img
              src={slide.src}
              alt={index === activeSlide ? slide.alt : ""}
              className="hero-carousel__image"
              loading={index === 0 ? "eager" : "lazy"}
              fetchPriority={index === 0 ? "high" : "auto"}
            />
          </div>
        ))}
      </div>

      <button
        className="hero-carousel__arrow hero-carousel__arrow--previous"
        type="button"
        aria-label="Imagen anterior"
        onClick={() => goTo(activeSlide - 1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m15 18-6-6 6-6" />
        </svg>
      </button>
      <button
        className="hero-carousel__arrow hero-carousel__arrow--next"
        type="button"
        aria-label="Imagen siguiente"
        onClick={() => goTo(activeSlide + 1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m9 18 6-6-6-6" />
        </svg>
      </button>

      <div className="hero-carousel__dots" aria-label="Seleccionar imagen">
        {HERO_SLIDES.map((slide, index) => (
          <button
            className="hero-carousel__dot"
            type="button"
            key={slide.src}
            aria-label={`Ir a la imagen ${index + 1} de ${HERO_SLIDES.length}`}
            aria-current={index === activeSlide ? "true" : undefined}
            onClick={() => goTo(index)}
          />
        ))}
      </div>

      <span className="sr-only" aria-live="polite" aria-atomic="true">
        Imagen {activeSlide + 1} de {HERO_SLIDES.length}
      </span>
    </div>
  );
}

function CategoryCard({ category }) {
  const tilt = useTilt(5);
  return (
    <Link ref={tilt} to={`/catalogo?category=${category.slug}`} className="category-card card bracket-corners">
      {category.image_url ? (
        <span className="category-card__photo" aria-hidden="true">
          <img src={publicAsset(category.image_url)} alt="" loading="lazy" />
        </span>
      ) : (
        <span className="category-card__visual" aria-hidden="true">
          <span className="category-card__orb">{category.name.slice(0, 2).toUpperCase()}</span>
        </span>
      )}
      <div className="category-card__body">
        <h3 className="category-card__name">{category.name}</h3>
        <p className="category-card__desc">{category.description}</p>
        <span className="btn btn-sm category-card__cta">Ver productos</span>
      </div>
    </Link>
  );
}

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [featured, setFeatured] = useState([]);

  const catHead = useReveal();
  const catGrid = useStaggerReveal(80, [categories.length]);

  useEffect(() => {
    api.getCategories().then(setCategories);
    api.getBrands().then(setBrands);
    api.getProducts({ page_size: 8 }).then((data) => setFeatured(data.items || []));
  }, []);

  return (
    <div className="home">
      <section className="home-category-nav" aria-label="Accesos rápidos al catálogo">
        <div className="container home-category-nav__track">
          {categories.map((category) => (
            <Link key={category.id} to={`/catalogo?category=${category.slug}`} className="home-category-nav__item">
              <span className="home-category-nav__visual" aria-hidden="true">
                {category.image_url ? (
                  <img src={publicAsset(category.image_url)} alt="" />
                ) : (
                  <svg viewBox="0 0 24 24"><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" /></svg>
                )}
              </span>
              <span>{category.name}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="hero">
        {/* Visible headlines live inside the artwork; this h1 keeps the
            page accessible/SEO-friendly without duplicating the text. */}
        <h1 className="sr-only">HW Store Perú — tecnología e infraestructura para tu operación</h1>
        <HeroCarousel />
      </section>

      {featured.length > 0 && (
        <section className="section featured-products">
          <div className="container">
            <div className="section-head featured-products__head">
              <div>
                <span className="eyebrow">Stock disponible</span>
                <h2 className="section-title">Equipos listos para cotizar</h2>
                <p>Una selección del inventario actual de Alfil.</p>
              </div>
              <Link to="/catalogo" className="btn btn-sm">Ver todos los productos</Link>
            </div>
            <div className="featured-products__grid">
              {featured.map((product) => <ProductCard key={product.id} product={product} />)}
            </div>
          </div>
        </section>
      )}

      <section className="section categories">
        <div className="container">
          <div className="section-head reveal" ref={catHead}>
            <div>
              <span className="eyebrow">Categorías</span>
              <h2 className="section-title">Explora nuestras categorías</h2>
            </div>
            <Link to="/catalogo" className="btn btn-sm">Ver todo el catálogo</Link>
          </div>
          <div className="categories__grid" ref={catGrid}>
            {categories.map((c) => (
              <CategoryCard key={c.id} category={c} />
            ))}
          </div>
        </div>
      </section>

      <section className="brand-strip">
        <div className="container brand-strip__head">
          <span className="eyebrow">Marcas aliadas</span>
          <span className="brand-strip__hint mono">Fabricantes líderes que integramos</span>
        </div>
        <BrandMarquee brands={brands} />
      </section>

      <TrustRow />
    </div>
  );
}
