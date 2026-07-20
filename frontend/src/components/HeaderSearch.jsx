import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HeaderSearch.css";

export default function HeaderSearch({ className = "" }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  const submit = (e) => {
    e.preventDefault();
    const query = q.trim();
    navigate(query ? `/catalogo?q=${encodeURIComponent(query)}` : "/catalogo");
  };

  return (
    <form className={"header-search " + className} onSubmit={submit} role="search">
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Buscar productos…"
        aria-label="Buscar productos"
      />
      <button type="submit" aria-label="Buscar">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            d="M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35"
          />
        </svg>
      </button>
    </form>
  );
}
