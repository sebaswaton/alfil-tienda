import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import ProductGallery from "../components/ProductGallery";
import ProductCard from "../components/ProductCard";
import InquiryForm from "../components/InquiryForm";
import "./ProductoDetalle.css";

const TABS = ["Descripción", "Especificaciones", "Preguntas frecuentes"];

const DOCUMENT_LABELS = {
  datasheet: "Ficha técnica",
  manual: "Manual",
  warranty: "Garantía",
  brochure: "Brochure",
  other: "Documento",
};

function formatFileSize(bytes) {
  if (!bytes) return "PDF";
  const megabytes = bytes / (1024 * 1024);
  return megabytes >= 1 ? `PDF · ${megabytes.toFixed(1)} MB` : `PDF · ${Math.ceil(bytes / 1024)} KB`;
}

export default function ProductoDetalle() {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [activeTab, setActiveTab] = useState(TABS[0]);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    api
      .getProduct(slug)
      .then((p) => {
        setProduct(p);
        api.getRelated(slug).then(setRelated);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return <div className="container product-detail__loading skeleton" />;
  }

  if (notFound || !product) {
    return (
      <div className="container product-detail__notfound">
        <h2>Producto no encontrado</h2>
        <Link to="/catalogo" className="btn">Volver al catálogo</Link>
      </div>
    );
  }

  const whatsappHref = `https://wa.me/5112774085?text=${encodeURIComponent(`Hola, quisiera cotizar: ${product.name} (SKU ${product.sku})`)}`;
  const manufacturerSources = (product.sources || []).filter((source) => source.source_type !== "image");

  return (
    <div className="container product-detail">
      <nav className="breadcrumb mono">
        <Link to="/">Inicio</Link>
        <span>/</span>
        <Link to="/catalogo">Catálogo</Link>
        <span>/</span>
        <Link to={`/catalogo?category=${product.category.slug}`}>{product.category.name}</Link>
        <span>/</span>
        <span className="breadcrumb__current">{product.name}</span>
      </nav>

      <div className="product-detail__top">
        <div className="product-detail__gallery">
          <ProductGallery product={product} />
        </div>

        <div className="product-detail__info">
          <span className="tag" style={{ borderColor: product.brand.accent_color, color: product.brand.accent_color }}>
            {product.brand.name}
          </span>
          <h1 className="product-detail__title">{product.name}</h1>
          <p className="product-detail__short">{product.short_description}</p>

          <div className="product-detail__meta mono">
            <div>
              <span>SKU</span>
              <strong>{product.sku}</strong>
            </div>
            <div>
              <span>N° de parte</span>
              <strong>{product.part_number || "—"}</strong>
            </div>
            <div>
              <span>Disponibilidad</span>
              <strong className="product-detail__stock">{product.stock_note}</strong>
            </div>
          </div>

          {product.highlights?.length > 0 && (
            <ul className="product-detail__highlights">
              {product.highlights.map((h, i) => (
                <li key={i}><span aria-hidden="true">▸</span>{h}</li>
              ))}
            </ul>
          )}

        </div>

        <aside className="product-detail__commercial" aria-label="Opciones de cotización">
          <span className="product-detail__commercial-label">Disponible para cotizar</span>
          <h2>Cotización personalizada</h2>
          <p>Confirma precio, stock final, entrega e instalación con un asesor de Alfil.</p>
          <div className="product-detail__commercial-stock">
            <span aria-hidden="true" />
            {product.stock_note}
          </div>
          {product.documents?.length > 0 && (
            <div className="product-detail__documents">
              <div className="product-detail__documents-heading">
                <span>Documentación técnica</span>
                <small>{product.documents.length}</small>
              </div>
              <div className="product-detail__document-list">
                {product.documents.map((document) => (
                  <a
                    key={document.id}
                    className="product-detail__document"
                    href={document.download_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M6.5 2.5h7l4 4V21.5h-11z" />
                      <path d="M13.5 2.5v4h4M9 13h6M9 16h4" />
                    </svg>
                    <span>
                      <strong>{document.title}</strong>
                      <small>
                        {DOCUMENT_LABELS[document.document_type] || "Documento"}
                        {document.is_official ? " oficial" : ""} · {formatFileSize(document.size_bytes)}
                      </small>
                    </span>
                    <svg className="product-detail__document-arrow" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M12 4v11M8 11l4 4 4-4M6 20h12" />
                    </svg>
                  </a>
                ))}
              </div>
            </div>
          )}
          <a className="btn btn-primary btn-block" href={whatsappHref} target="_blank" rel="noreferrer">
            Cotizar por WhatsApp
          </a>
          <a className="btn btn-block" href="#cotizar">Solicitar cotización formal</a>
        </aside>
      </div>

      <div className="product-detail__tabs">
        <div className="product-detail__tabs-nav mono" role="tablist" aria-label="Información del producto">
          {TABS.map((tab) => (
            <button
              key={tab}
              id={`tab-${tab.toLowerCase().replaceAll(" ", "-")}`}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              aria-controls="product-tab-panel"
              className={activeTab === tab ? "is-active" : ""}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div
          id="product-tab-panel"
          className="product-detail__tabs-body"
          role="tabpanel"
          aria-live="polite"
        >
          {activeTab === "Descripción" && (
            <div className="product-detail__description-wrap">
              <p className="product-detail__description">{product.description}</p>
              {manufacturerSources.length > 0 && (
                <div className="product-detail__sources">
                  <span className="product-detail__sources-label mono">Información contrastada con fabricante</span>
                  <div className="product-detail__source-list">
                    {manufacturerSources.slice(0, 4).map((source) => (
                      <a key={source.id} href={source.url} target="_blank" rel="noreferrer">
                        <span>{source.title}</span>
                        <small>{source.match_scope === "exact" ? "Modelo exacto" : "Familia de producto"}</small>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "Especificaciones" && (
            <table className="specs-table">
              <tbody>
                {Object.entries(product.specs || {}).map(([key, value]) => (
                  <tr key={key}>
                    <th className="mono">{key}</th>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === "Preguntas frecuentes" && (
            <div className="faq">
              {(product.faqs || []).map((item, index) => (
                <details key={item.id || item.question} className="faq__item" open={index === 0}>
                  <summary>
                    <span className="faq__index mono">{String(index + 1).padStart(2, "0")}</span>
                    <h4>{item.question}</h4>
                    <span className="faq__toggle" aria-hidden="true" />
                  </summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          )}
        </div>
      </div>

      <div id="cotizar" className="product-detail__quote">
        <InquiryForm productId={product.id} source="ficha-producto" title={`Cotizar: ${product.name}`} />
      </div>

      {related.length > 0 && (
        <section className="product-detail__related">
          <span className="eyebrow">También te puede interesar</span>
          <div className="product-detail__related-grid">
            {related.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        </section>
      )}
    </div>
  );
}
