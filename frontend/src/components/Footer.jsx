import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div className="site-footer__col site-footer__brand">
          <div className="site-footer__logo-wrap">
            <img
              src={`${import.meta.env.BASE_URL}hw-store-peru-logo.svg`}
              alt="HW Store Perú"
              className="site-footer__logo"
            />
          </div>
          <a
            className="btn btn-sm site-footer__cta"
            href="https://wa.me/5112774085"
            target="_blank"
            rel="noreferrer"
          >
            Escríbenos por WhatsApp
          </a>
        </div>

        <div className="site-footer__col">
          <span className="eyebrow">Navegación</span>
          <Link to="/catalogo">Catálogo</Link>
          <Link to="/marcas">Marcas aliadas</Link>
          <Link to="/contacto">Contacto</Link>
        </div>

        <div className="site-footer__col">
          <span className="eyebrow">Contacto</span>
          <a href="tel:+5112774085" className="mono">+51 (1) 277-4085</a>
          <a href="mailto:ventas@hwstore.com.pe" className="mono">ventas@hwstore.com.pe</a>
        </div>
      </div>

    </footer>
  );
}
