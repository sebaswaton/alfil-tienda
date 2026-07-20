import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="container" style={{ padding: "120px 0", textAlign: "center" }}>
      <span className="eyebrow">Error 404</span>
      <h1 className="section-title" style={{ margin: "16px 0 24px" }}>Página no encontrada</h1>
      <Link to="/" className="btn btn-primary">Volver al inicio</Link>
    </div>
  );
}
