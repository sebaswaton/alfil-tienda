import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import ProductCard from "../components/ProductCard";
import "./Catalogo.css";

export default function Catalogo() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [result, setResult] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const resultsRef = useRef(null);

  const brand = searchParams.get("brand") || "";
  const category = searchParams.get("category") || "";
  const q = searchParams.get("q") || "";
  const page = Number(searchParams.get("page") || 1);

  useEffect(() => {
    api.getBrands().then(setBrands);
    api.getCategories().then(setCategories);
  }, []);

  // Keep the search box in sync when ?q= changes from outside this page
  // (e.g. the header search bar navigating here while already on /catalogo).
  useEffect(() => {
    setQuery(q);
  }, [q]);

  useEffect(() => {
    setLoading(true);
    api
      .getProducts({ brand, category, q, page, page_size: 12 })
      .then(setResult)
      .finally(() => setLoading(false));
  }, [brand, category, q, page]);

  const setParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next);
  };

  const goToPage = (nextPage) => {
    setParam("page", String(nextPage));
    window.requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const totalPages = Math.max(1, Math.ceil(result.total / 12));

  return (
    <div className="container catalogo">
      <div className="catalogo__head">
        <span className="eyebrow">Catálogo técnico</span>
        <h1 className="section-title">Productos y soluciones</h1>
        <p className="catalogo__intro">
          Filtra por marca o línea de solución. Los precios son referenciales — solicita
          cotización formal con un asesor de Alfil.
        </p>
      </div>

      <div className="catalogo__layout">
        <aside className="catalogo__filters">
          <form
            className="catalogo__search"
            onSubmit={(e) => {
              e.preventDefault();
              setParam("q", query);
            }}
          >
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar producto…"
              className="mono"
            />
            <button className="btn" type="submit">Buscar</button>
          </form>

          <div className="catalogo__filter-group">
            <span className="eyebrow">Categoría</span>
            <button
              className={"catalogo__filter-item mono" + (!category ? " is-active" : "")}
              onClick={() => setParam("category", "")}
            >
              Todas
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                className={"catalogo__filter-item mono" + (category === c.slug ? " is-active" : "")}
                onClick={() => setParam("category", c.slug)}
              >
                {c.name}
              </button>
            ))}
          </div>

          <div className="catalogo__filter-group">
            <span className="eyebrow">Marca</span>
            <button
              className={"catalogo__filter-item mono" + (!brand ? " is-active" : "")}
              onClick={() => setParam("brand", "")}
            >
              Todas
            </button>
            {brands.map((b) => (
              <button
                key={b.id}
                className={"catalogo__filter-item mono" + (brand === b.slug ? " is-active" : "")}
                onClick={() => setParam("brand", b.slug)}
              >
                {b.name}
              </button>
            ))}
          </div>
        </aside>

        <div className="catalogo__results" ref={resultsRef}>
          <div className="catalogo__results-head mono">
            {loading ? "Buscando…" : `${result.total} producto${result.total === 1 ? "" : "s"} encontrados`}
          </div>

          {!loading && result.items.length === 0 && (
            <div className="catalogo__empty card">
              <p>No encontramos productos con esos filtros.</p>
              <button className="btn" onClick={() => setSearchParams({})}>Limpiar filtros</button>
            </div>
          )}

          <div className="catalogo__grid">
            {loading
              ? Array.from({ length: 6 }).map((_, i) => <div key={i} className="skeleton catalogo__skeleton" />)
              : result.items.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>

          {totalPages > 1 && (
            <div className="catalogo__pagination">
              {Array.from({ length: totalPages }).map((_, i) => (
                <button
                  type="button"
                  key={i}
                  className={"mono" + (page === i + 1 ? " is-active" : "")}
                  onClick={() => goToPage(i + 1)}
                >
                  {String(i + 1).padStart(2, "0")}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
