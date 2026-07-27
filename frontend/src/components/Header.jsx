import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { NavLink, useLocation } from "react-router-dom";
import { api } from "../api/client";
import HeaderSearch from "./HeaderSearch";
import "./Header.css";

const NAV = [
  { to: "/", label: "Inicio", end: true },
  { to: "/catalogo", label: "Catálogo" },
  { to: "/marcas", label: "Marcas" },
  { to: "/contacto", label: "Contacto" },
];

const CATEGORY_GUIDE = {
  laptops: [
    { title: "Equipos profesionales", items: [{ label: "Workstations móviles", q: "ZBook" }] },
    { title: "Procesamiento", items: [{ label: "Laptops con Intel Core i7", q: "i7" }] },
    { title: "Marcas disponibles", items: [{ label: "Laptops HP", brand: "hp" }] },
  ],
  computadoras: [
    { title: "Formatos de escritorio", items: [{ label: "Mini PC", q: "Mini" }, { label: "Equipos compactos SFF", q: "SFF" }, { label: "Torres empresariales", q: "Tower" }] },
    { title: "Alto rendimiento", items: [{ label: "Workstations profesionales", q: "Workstation" }, { label: "Equipos con Intel Core i7", q: "i7" }, { label: "Equipos con Intel Xeon", q: "Xeon" }] },
    { title: "Dispositivos móviles", items: [{ label: "Tablets empresariales", q: "MatePad" }] },
    { title: "Marcas disponibles", items: [{ label: "Computadoras HP", brand: "hp" }, { label: "Tablets Huawei", brand: "huawei" }] },
  ],
  "toners-y-suministros": [
    { title: "Suministros disponibles", items: [{ label: "Todos los tóners", q: "Tóner" }, { label: "Tóners de alto rendimiento", q: "X" }, { label: "Tóners de inicio", q: "inicio" }] },
    { title: "Por fabricante", items: [{ label: "Tóners HP", brand: "hp" }, { label: "Tóners Canon", brand: "canon" }] },
  ],
  componentes: [
    { title: "Visualización", items: [{ label: "Monitores empresariales", q: "Monitor" }, { label: "Monitores de 24 pulgadas", q: "P24" }, { label: "Monitores de 27 pulgadas", q: "P27" }] },
    { title: "Accesorios", items: [{ label: "Teclados para tablets", q: "Keyboard" }] },
    { title: "Respaldo de energía", items: [{ label: "Equipos UPS", q: "UPS" }] },
    { title: "Marcas disponibles", items: [{ label: "Componentes HP", brand: "hp" }, { label: "Accesorios Huawei", brand: "huawei" }, { label: "Equipos Salicru", brand: "salicru" }] },
  ],
  "redes-y-conectividad": [
    { title: "Redes empresariales", items: [{ label: "Switches administrables", q: "Switch" }, { label: "Transceivers", q: "Transceiver" }] },
    { title: "Velocidad y conexión", items: [{ label: "Conectividad 10G", q: "10G" }, { label: "Módulos SFP", q: "SFP" }, { label: "Conectividad 32G", q: "32G" }] },
    { title: "Marcas disponibles", items: [{ label: "Redes Cisco", brand: "cisco" }, { label: "Redes Huawei", brand: "huawei" }, { label: "Redes HP", brand: "hp" }, { label: "Redes Lenovo", brand: "lenovo" }] },
  ],
};

function catalogHref(categorySlug, item = {}) {
  const params = new URLSearchParams({ category: categorySlug });
  if (item.q) params.set("q", item.q);
  if (item.brand) params.set("brand", item.brand);
  return `/catalogo?${params.toString()}`;
}

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedCategorySlug, setSelectedCategorySlug] = useState("");
  const location = useLocation();

  useEffect(() => {
    api.getCategories()
      .then((items) => {
        setCategories(items);
        setSelectedCategorySlug((current) => current || items[0]?.slug || "");
      })
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
    setCategoriesOpen(false);
  }, [location.pathname, location.search]);

  useEffect(() => {
    document.body.style.overflow = menuOpen || categoriesOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen, categoriesOpen]);

  useEffect(() => {
    if (!menuOpen && !categoriesOpen) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        setCategoriesOpen(false);
      }
    };
    const onResize = () => {
      if (window.innerWidth >= 880) setMenuOpen(false);
      if (window.innerWidth < 880) setCategoriesOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onResize);
    };
  }, [menuOpen, categoriesOpen]);

  const selectedCategory = categories.find((category) => category.slug === selectedCategorySlug);
  const selectedCategoryGuide = CATEGORY_GUIDE[selectedCategorySlug] || [];

  return (
    <>
    <header className={"site-header" + (scrolled ? " is-scrolled" : "")}>
      <div className="container site-header__row">
        <NavLink to="/" className="site-header__brand" aria-label="Alfil CC — inicio">
          <img src="/alfil-logo.png" alt="Alfil CC" className="site-header__logo" />
        </NavLink>

        <button
          type="button"
          className={"site-header__categories-btn" + (categoriesOpen ? " is-open" : "")}
          aria-expanded={categoriesOpen}
          aria-controls="category-mega-menu"
          onClick={() => setCategoriesOpen((open) => !open)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
          Categorías
        </button>

        <HeaderSearch className="header-search--nav site-header__search" />

        <a
          href="https://wa.me/5112774085?text=Hola%2C%20quisiera%20recibir%20asesoría%20para%20una%20cotización."
          className="site-header__sales"
          target="_blank"
          rel="noreferrer"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 14v-2a8 8 0 0116 0v2M4 14a2 2 0 012-2h1v7H6a2 2 0 01-2-2v-3zM20 14a2 2 0 00-2-2h-1v7h1a2 2 0 002-2v-3zM17 19c0 1.1-.9 2-2 2h-2" />
          </svg>
          <span><small>Atención directa</small>Hablar con un asesor</span>
        </a>

        <button
          className={"site-header__burger" + (menuOpen ? " is-open" : "")}
          onClick={() => setMenuOpen((v) => !v)}
          aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={menuOpen}
        >
          <span /><span /><span />
        </button>
      </div>

      <div className="container site-header__mobile-search">
        <HeaderSearch />
      </div>

      <div className="site-header__subnav">
        <div className="container site-header__subnav-inner">
          <nav className="site-header__nav" aria-label="Principal">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => "site-header__link" + (isActive ? " is-active" : "")}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <span className="site-header__subnav-divider" aria-hidden="true" />
          <nav className="site-header__category-links" aria-label="Categorías destacadas">
            {categories.slice(0, 6).map((category) => (
              <NavLink key={category.id} to={`/catalogo?category=${category.slug}`}>
                {category.name}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      <div
        className={"site-header__scrim" + (menuOpen || categoriesOpen ? " is-open" : "")}
        onClick={() => {
          setMenuOpen(false);
          setCategoriesOpen(false);
        }}
        aria-hidden="true"
      />

      <aside
        className={"mobile-drawer" + (menuOpen ? " is-open" : "")}
        aria-hidden={!menuOpen}
        aria-label="Navegación móvil"
      >
        <nav className="mobile-drawer__nav">
          {NAV.map((item, i) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => "mobile-drawer__link" + (isActive ? " is-active" : "")}
              style={{ "--i": i }}
            >
              <span className="mono mobile-drawer__idx">0{i + 1}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mobile-drawer__foot">
          <a className="btn btn-primary btn-block" href="https://wa.me/5112774085" target="_blank" rel="noreferrer">
            WhatsApp ventas
          </a>
          <a href="tel:+5112774085" className="mono mobile-drawer__phone">+51 (1) 277-4085</a>
        </div>
      </aside>
    </header>
    {createPortal(
      <div
        id="category-mega-menu"
        className={"site-header__mega-menu" + (categoriesOpen ? " is-open" : "")}
        aria-hidden={!categoriesOpen}
      >
        <div className="site-header__mega-shell">
          <aside className="site-header__mega-sidebar">
            <h2>Categorías</h2>
            <nav aria-label="Todas las categorías">
              {categories.map((category) => (
                <button
                  type="button"
                  key={category.id}
                  className={selectedCategorySlug === category.slug ? "is-active" : ""}
                  aria-pressed={selectedCategorySlug === category.slug}
                  onClick={() => setSelectedCategorySlug(category.slug)}
                >
                  <span>{category.name}</span>
                  <span aria-hidden="true">›</span>
                </button>
              ))}
            </nav>
          </aside>

          <section className="site-header__mega-content" aria-live="polite">
            <header className="site-header__mega-content-head">
              <div>
                <h2>{selectedCategory?.name || "Productos"}</h2>
                {selectedCategory && (
                  <NavLink to={`/catalogo?category=${selectedCategory.slug}`}>Ver todos</NavLink>
                )}
              </div>
              <button
                type="button"
                className="site-header__mega-close"
                aria-label="Cerrar menú de categorías"
                onClick={() => setCategoriesOpen(false)}
              >
                <span aria-hidden="true" />
                <span aria-hidden="true" />
              </button>
            </header>

            {selectedCategoryGuide.length > 0 ? (
              <div className="site-header__mega-groups">
                {selectedCategoryGuide.map((group) => (
                  <div className="site-header__mega-group" key={group.title}>
                    <h3>{group.title}</h3>
                    <div className="site-header__mega-group-items">
                      {group.items.map((item) => (
                        <NavLink key={item.label} to={catalogHref(selectedCategorySlug, item)}>
                          {item.label}
                        </NavLink>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="site-header__mega-empty">
                <span className="eyebrow">Catálogo</span>
                <h3>Explora {selectedCategory?.name || "esta categoría"}.</h3>
                <p>{selectedCategory?.description || "Consulta los productos disponibles en esta categoría."}</p>
                <NavLink className="btn" to={`/catalogo?category=${selectedCategorySlug}`}>Ver productos</NavLink>
              </div>
            )}
          </section>
        </div>
      </div>,
      document.body,
    )}
    </>
  );
}
