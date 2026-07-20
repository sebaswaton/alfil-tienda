import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div className="site-footer__col site-footer__brand">
          <div className="site-footer__logo-wrap">
            <img src="/alfil-logo.png" alt="Alfil CC" className="site-footer__logo" />
          </div>
          <p className="site-footer__desc">
            Consultoría &amp; Comunicaciones. Más de 20 años integrando infraestructura de TI
            para centros de datos, redes y espacios de trabajo empresariales.
          </p>
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
          <a href="mailto:ventas@alfilcc.com" className="mono">ventas@alfilcc.com</a>
          <span className="mono site-footer__addr">Jr. Río Moquegua 271, San Luis, Lima</span>
        </div>

        <div className="site-footer__col">
          <span className="eyebrow">Horario</span>
          <span className="mono">Lun – Vie · 09:00 – 18:00</span>
          <span className="mono">Sáb · 09:00 – 13:00</span>
        </div>
      </div>

      <div className="container site-footer__bottom">
        <span className="mono">© {new Date().getFullYear()} Alfil CC — vitrina de catálogo, sin venta en línea.</span>
        <span className="mono">Diseño e integración de TI</span>
      </div>
    </footer>
  );
}
