import InquiryForm from "../components/InquiryForm";
import "./Contacto.css";

export default function Contacto() {
  return (
    <div className="container contacto">
      <div className="contacto__head">
        <span className="eyebrow">Hablemos</span>
        <h1 className="section-title">Contacto</h1>
        <p className="contacto__intro">
          Escríbenos para cotizaciones, soporte técnico o alianzas comerciales.
          Un asesor de HW Store te responderá directamente.
        </p>
      </div>

      <div className="contacto__grid">
        <div className="contacto__info">
          <div className="contacto__block">
            <span className="eyebrow">Central</span>
            <a href="tel:+5112774085" className="contacto__value mono">+51 (1) 277-4085</a>
          </div>
          <div className="contacto__block">
            <span className="eyebrow">Ventas</span>
            <a href="mailto:ventas@hwstore.com.pe" className="contacto__value mono">ventas@hwstore.com.pe</a>
          </div>
          <a
            className="btn btn-primary btn-block"
            href="https://wa.me/5112774085"
            target="_blank"
            rel="noreferrer"
          >
            Escribir por WhatsApp
          </a>
        </div>

        <InquiryForm title="Formulario de contacto" source="contacto" />
      </div>
    </div>
  );
}
