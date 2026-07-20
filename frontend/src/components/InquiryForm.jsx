import { useState } from "react";
import { api } from "../api/client";
import "./InquiryForm.css";

export default function InquiryForm({ productId, source = "contacto", title = "Solicitar cotización" }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", message: "" });
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    setError("");
    try {
      await api.createInquiry({ ...form, product_id: productId ?? null, source });
      setStatus("success");
      setForm({ name: "", email: "", phone: "", company: "", message: "" });
    } catch (err) {
      setStatus("error");
      setError(err.message || "No se pudo enviar la solicitud.");
    }
  };

  if (status === "success") {
    return (
      <div className="inquiry-form card inquiry-form--done">
        <span className="eyebrow">Solicitud enviada</span>
        <p>
          Gracias, {form.name || "estimado cliente"}. Un asesor de Alfil se comunicará contigo
          a la brevedad para continuar con la cotización.
        </p>
        <button className="btn" onClick={() => setStatus("idle")}>Enviar otra solicitud</button>
      </div>
    );
  }

  return (
    <form className="inquiry-form card" onSubmit={submit}>
      <span className="eyebrow">{title}</span>
      <div className="inquiry-form__row">
        <label>
          <span className="mono">Nombre*</span>
          <input required value={form.name} onChange={update("name")} placeholder="Nombre completo" />
        </label>
        <label>
          <span className="mono">Empresa</span>
          <input value={form.company} onChange={update("company")} placeholder="Razón social" />
        </label>
      </div>
      <div className="inquiry-form__row">
        <label>
          <span className="mono">Correo*</span>
          <input required type="email" value={form.email} onChange={update("email")} placeholder="correo@empresa.com" />
        </label>
        <label>
          <span className="mono">Teléfono</span>
          <input value={form.phone} onChange={update("phone")} placeholder="+51 9xx xxx xxx" />
        </label>
      </div>
      <label>
        <span className="mono">Mensaje</span>
        <textarea
          rows={4}
          value={form.message}
          onChange={update("message")}
          placeholder="Cuéntanos qué necesitas: cantidades, plazos, requerimientos técnicos…"
        />
      </label>

      {status === "error" && <p className="inquiry-form__error mono">{error}</p>}

      <button className="btn btn-primary btn-block" disabled={status === "loading"} type="submit">
        {status === "loading" ? "Enviando…" : "Enviar solicitud"}
      </button>
    </form>
  );
}
