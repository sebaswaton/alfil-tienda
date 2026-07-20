import { useStaggerReveal } from "../hooks/useReveal";
import "./TrustRow.css";

const ITEMS = [
  {
    title: "Asesoría especializada",
    desc: "Te ayudamos a encontrar lo que necesitas.",
    icon: (
      <path d="M4 14v-2a8 8 0 0116 0v2M4 14a2 2 0 012-2h1v7H6a2 2 0 01-2-2v-3zM20 14a2 2 0 00-2-2h-1v7h1a2 2 0 002-2v-3zM17 19c0 1.1-.9 2-2 2h-2" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
  {
    title: "Cotización sin compromiso",
    desc: "Recibe una propuesta formal y atención directa.",
    icon: (
      <path d="M6 3h9l4 4v14a1 1 0 01-1 1H6a1 1 0 01-1-1V4a1 1 0 011-1zM14 3v5h5M9 13h6M9 17h4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
  {
    title: "Envíos a todo el país",
    desc: "Llegamos a donde tu negocio nos necesite.",
    icon: (
      <path d="M3 6h11v11H3zM14 10h4l3 4v3h-7zM7 21a2 2 0 100-4 2 2 0 000 4zM17 21a2 2 0 100-4 2 2 0 000 4zM3 10H1M3 14H1" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
  {
    title: "Garantía asegurada",
    desc: "Respaldo y garantía en todos nuestros productos.",
    icon: (
      <path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5zM8.5 12l2.2 2.2 4.8-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    ),
  },
];

export default function TrustRow() {
  const gridRef = useStaggerReveal(80);
  return (
    <section className="section trust-row">
      <div className="container trust-row__grid" ref={gridRef}>
        {ITEMS.map((item) => (
          <div className="trust-item" key={item.title}>
            <span className="trust-item__icon">
              <svg viewBox="0 0 24 24" aria-hidden="true">{item.icon}</svg>
            </span>
            <div>
              <h3 className="trust-item__title">{item.title}</h3>
              <p className="trust-item__desc">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
