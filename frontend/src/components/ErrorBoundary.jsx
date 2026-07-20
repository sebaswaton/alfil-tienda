import { Component } from "react";

/**
 * Top-level safety net: if any component throws during render/commit,
 * show a minimal recovery screen instead of leaving the page permanently
 * blank (React unmounts the tree on an uncaught error with no boundary).
 */
export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("App crashed:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            background: "#f6f8f8",
            color: "#13211f",
            fontFamily: "sans-serif",
            textAlign: "center",
            padding: 24,
          }}
        >
          <p style={{ fontSize: 18, fontWeight: 600 }}>Algo salió mal cargando la página.</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "12px 24px",
              borderRadius: 999,
              border: "none",
              background: "#087f6f",
              color: "#ffffff",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Recargar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
