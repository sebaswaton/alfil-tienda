import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import TopBar from "./components/TopBar";
import Header from "./components/Header";
import Footer from "./components/Footer";
import WhatsAppFloat from "./components/WhatsAppFloat";
import IntroScreen from "./components/IntroScreen";
import Home from "./pages/Home";
import Catalogo from "./pages/Catalogo";
import ProductoDetalle from "./pages/ProductoDetalle";
import Marcas from "./pages/Marcas";
import Contacto from "./pages/Contacto";
import NotFound from "./pages/NotFound";
import AdminPanel from "./pages/AdminPanel";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    // Block body (not an implicit-return arrow) so this effect never
    // returns whatever window.scrollTo() happens to return in a given
    // browser/extension environment — React would try to call a non-
    // function return value as a cleanup and crash the whole tree.
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  const { pathname } = useLocation();
  if (pathname.startsWith("/admin")) {
    return (
      <>
        <ScrollToTop />
        <Routes>
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/admin/*" element={<AdminPanel />} />
        </Routes>
      </>
    );
  }

  return (
    <div className="app-shell">
      <IntroScreen />
      <ScrollToTop />
      <TopBar />
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalogo" element={<Catalogo />} />
          <Route path="/producto/:slug" element={<ProductoDetalle />} />
          <Route path="/marcas" element={<Marcas />} />
          <Route path="/contacto" element={<Contacto />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <WhatsAppFloat />
    </div>
  );
}
