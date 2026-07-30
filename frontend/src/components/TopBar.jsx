import "./TopBar.css";

export default function TopBar() {
  return (
    <div className="topbar">
      <div className="container topbar__row">
        <span className="topbar__label mono">Catálogo técnico de productos</span>
        <div className="topbar__contact">
          <a href="https://wa.me/5112774085" target="_blank" rel="noreferrer" className="topbar__item">
            <svg viewBox="0 0 24 24" className="topbar__icon" aria-hidden="true">
              <path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.149-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347" />
            </svg>
            <span>Atención al cliente</span>
          </a>
          <a href="tel:+5112774085" className="topbar__item">
            <svg viewBox="0 0 24 24" className="topbar__icon" aria-hidden="true">
              <path fill="currentColor" d="M6.62 10.79a15.05 15.05 0 006.59 6.59l2.2-2.2a1 1 0 011.01-.24 11.36 11.36 0 003.57.57 1 1 0 011 1V20a1 1 0 01-1 1A17 17 0 013 4a1 1 0 011-1h3.5a1 1 0 011 1 11.36 11.36 0 00.57 3.57 1 1 0 01-.25 1.01l-2.2 2.21z" />
            </svg>
            <span>+51 (1) 277-4085</span>
          </a>
          <a href="mailto:ventas@hwstore.com.pe" className="topbar__item">
            <svg viewBox="0 0 24 24" className="topbar__icon" aria-hidden="true">
              <path fill="currentColor" d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4l-8 5-8-5V6l8 5 8-5z" />
            </svg>
            <span>ventas@hwstore.com.pe</span>
          </a>
        </div>
      </div>
    </div>
  );
}
