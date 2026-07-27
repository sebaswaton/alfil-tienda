import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Icon from '../components/Icon'

const navItems = [
  { to: '/productos', label: 'Productos', icon: 'products' },
  { to: '/marcas', label: 'Marcas', icon: 'brands' },
  { to: '/categorias', label: 'Categorías', icon: 'categories' },
]

export default function AdminLayout() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const current = navItems.find((item) => location.pathname.startsWith(item.to))?.label || 'Administración'
  const handleLogout = async () => { await logout(); navigate('/login', { replace: true }) }
  return <div className="admin-shell">
    <button className={`sidebar-scrim ${open ? 'is-open' : ''}`} aria-label="Cerrar menú" onClick={() => setOpen(false)} />
    <aside className={`sidebar ${open ? 'is-open' : ''}`}>
      <div className="brand-lockup"><span className="brand-lockup__mark">A</span><div><strong>ALFIL</strong><small>Administración</small></div></div>
      <nav className="sidebar__nav" aria-label="Navegación principal">
        <span className="sidebar__label">Catálogo</span>
        {navItems.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)} className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}>
          <Icon name={item.icon} /><span>{item.label}</span><Icon name="chevron" size={16} />
        </NavLink>)}
      </nav>
      <div className="sidebar__foot"><small>Catálogo central</small><strong>Alfil Computer Center</strong></div>
    </aside>
    <div className="admin-workspace">
      <header className="topbar">
        <button className="icon-button topbar__menu" aria-label="Abrir menú" onClick={() => setOpen(true)}><Icon name="menu" /></button>
        <div><span>Panel administrativo</span><strong>{current}</strong></div>
        <div className="topbar__user"><span className="avatar">{user?.email?.[0]?.toUpperCase()}</span><div><small>Administrador</small><strong>{user?.email}</strong></div><button className="icon-button" title="Cerrar sesión" aria-label="Cerrar sesión" onClick={handleLogout}><Icon name="logout" /></button></div>
      </header>
      <main className="admin-main"><Outlet /></main>
    </div>
  </div>
}
